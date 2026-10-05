"""
Employer Discovery via OpenStreetMap Overpass API.

Given a user's lat/lng, radius, and category list, this module:
1. Queries Overpass for matching OSM nodes/ways with a name.
2. Groups results by brand (normalised name).
3. Caches results in discovered_employers for 7 days per 0.01° tile.
4. Respects Overpass usage policy: max 1 request/second, clear User-Agent.

Usage:
    employers = await discover_employers(lat, lng, radius_km, categories, db)
    # Returns List[DiscoveredEmployer]
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DiscoveredEmployer

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

_OSM_CONFIG: Optional[Dict] = None

def _load_osm_config() -> Dict:
    global _OSM_CONFIG
    if _OSM_CONFIG is None:
        import pathlib
        cfg_path = pathlib.Path(__file__).parent.parent.parent / "config" / "osm_categories.yaml"
        with open(cfg_path) as f:
            _OSM_CONFIG = yaml.safe_load(f)
    return _OSM_CONFIG

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_USER_AGENT = "JobBridge/1.0 (student job discovery; +https://github.com/jobbridge)"
OVERPASS_RATE_LIMIT = 1.0   # seconds between requests
CACHE_DAYS = 7

_last_overpass_request = 0.0


def _area_key(lat: float, lng: float, radius_km: float) -> str:
    """
    Tile key rounding to ~1 km grid (0.01°).
    Different radii get different keys so a 5 km result isn't reused for a 50 km search.
    """
    return f"{lat:.2f}:{lng:.2f}:r{int(radius_km)}"


def _normalise_brand(name: str) -> str:
    """Lower-case, strip legal suffixes and punctuation for brand dedup."""
    name = name.lower()
    name = re.sub(r"\b(pty|ltd|limited|inc|llc|co|group|australia|au)\b", "", name)
    name = re.sub(r"[^\w\s]", "", name).strip()
    return re.sub(r"\s+", " ", name)


def _extract_domain(website: str) -> Optional[str]:
    if not website:
        return None
    try:
        p = urlparse(website if "//" in website else f"https://{website}")
        return p.netloc.lstrip("www.").lower() or None
    except Exception:
        return None


# ── Overpass query builder ────────────────────────────────────────────────────

def _build_overpass_query(
    lat: float, lng: float, radius_m: int, osm_tags: List[str]
) -> str:
    """
    Build an Overpass QL query for nodes AND ways with any of the given tags,
    within radius_m metres of (lat, lng), that have a name tag.
    """
    union_parts = []
    for tag in osm_tags:
        if "=" in tag:
            k, v = tag.split("=", 1)
            union_parts.append(
                f'  node["{k}"="{v}"]["name"](around:{radius_m},{lat},{lng});\n'
                f'  way["{k}"="{v}"]["name"](around:{radius_m},{lat},{lng});\n'
            )
        else:
            union_parts.append(
                f'  node["{tag}"]["name"](around:{radius_m},{lat},{lng});\n'
                f'  way["{tag}"]["name"](around:{radius_m},{lat},{lng});\n'
            )

    union = "".join(union_parts)
    return (
        f"[out:json][timeout:30];\n"
        f"(\n{union});\n"
        f"out center tags;"
    )


# ── Overpass fetcher ──────────────────────────────────────────────────────────

async def _fetch_overpass(query: str) -> Dict:
    global _last_overpass_request

    # Rate limit: 1 req/s
    wait = OVERPASS_RATE_LIMIT - (time.monotonic() - _last_overpass_request)
    if wait > 0:
        await asyncio.sleep(wait)

    async with httpx.AsyncClient(timeout=35) as client:
        resp = await client.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": OVERPASS_USER_AGENT},
        )
        resp.raise_for_status()
        _last_overpass_request = time.monotonic()
        return resp.json()


# ── Main discovery function ───────────────────────────────────────────────────

async def discover_employers(
    lat: float,
    lng: float,
    radius_km: float,
    categories: List[str],
    db: AsyncSession,
) -> List[DiscoveredEmployer]:
    """
    Discover employers near (lat, lng) within radius_km for the given categories.
    Results are cached in the DB for 7 days.

    Returns: list of DiscoveredEmployer ORM objects.
    """
    if not lat or not lng or not categories:
        return []

    key = _area_key(lat, lng, radius_km)
    now = datetime.now(timezone.utc)

    # ── Cache check ───────────────────────────────────────────────────────────
    cache_result = await db.execute(
        select(DiscoveredEmployer).where(
            DiscoveredEmployer.area_key == key,
            DiscoveredEmployer.category.in_(categories),
            DiscoveredEmployer.expires_at > now,
        )
    )
    cached = cache_result.scalars().all()
    if cached:
        logger.info(f"Discovery cache hit: {len(cached)} employers for key={key}")
        return list(cached)

    cfg = _load_osm_config()
    radius_m = int(radius_km * 1000)
    expires = now + timedelta(days=CACHE_DAYS)

    new_employers: List[DiscoveredEmployer] = []
    seen_brands: set = set()

    for category in categories:
        cat_cfg = cfg.get("categories", {}).get(category)
        if not cat_cfg:
            logger.warning(f"No OSM config for category: {category}")
            continue

        osm_tags = cat_cfg.get("osm_tags", [])
        if not osm_tags:
            continue

        query = _build_overpass_query(lat, lng, radius_m, osm_tags)
        logger.info(f"Querying Overpass for category={category}, radius={radius_km}km")

        try:
            data = await _fetch_overpass(query)
        except Exception as e:
            logger.error(f"Overpass query failed for {category}: {e}")
            continue

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name", "").strip()

            if not name or len(name) < cfg.get("min_name_length", 3):
                continue

            # Get coordinates (use centre for ways)
            if element.get("type") == "way":
                centre = element.get("center", {})
                e_lat = centre.get("lat")
                e_lng = centre.get("lon")
            else:
                e_lat = element.get("lat")
                e_lng = element.get("lon")

            website = tags.get("website") or tags.get("contact:website") or ""
            brand = tags.get("brand") or _normalise_brand(name)
            brand_key = (category, _normalise_brand(brand))

            # Deduplicate chains — only one entry per brand+category per query
            if brand_key in seen_brands:
                continue
            seen_brands.add(brand_key)

            # Build address from OSM addr tags
            addr_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:suburb", ""),
                tags.get("addr:city", ""),
                tags.get("addr:state", ""),
            ]
            address = ", ".join(p for p in addr_parts if p)

            employer = DiscoveredEmployer(
                osm_id=str(element.get("id", "")),
                name=name,
                category=category,
                lat=e_lat,
                lng=e_lng,
                address=address,
                website=website,
                brand=brand,
                area_key=key,
                discovered_at=now,
                expires_at=expires,
            )
            db.add(employer)
            new_employers.append(employer)

    if new_employers:
        await db.commit()
        for e in new_employers:
            await db.refresh(e)

    logger.info(f"Discovered {len(new_employers)} new employers for key={key}")
    return new_employers + list(cached)


async def get_discovery_stats(db: AsyncSession) -> Dict:
    """Return discovery stats for monitoring."""
    result = await db.execute(select(DiscoveredEmployer))
    employers = result.scalars().all()
    return {
        "total": len(employers),
        "by_category": {
            cat: sum(1 for e in employers if e.category == cat)
            for cat in set(e.category for e in employers)
        },
    }
