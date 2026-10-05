"""
Careers Page Finder

Given an employer's website, finds the careers/jobs page URL.

Strategy (in order):
  1. Fetch homepage, scan links whose text or href matches career keywords.
  2. Try common paths: /careers, /jobs, /join-us, /work-with-us, /hiring, /vacancies.
  3. Check sitemap.xml for careers-related URLs.
  4. If all fail, return None and cache a negative result for 14 days.

Results are cached in CareersPageCache (positive: 7 days, negative: 14 days).
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CareersPageCache
from app.scraper import http_client

logger = logging.getLogger(__name__)

# ── Career keyword patterns ───────────────────────────────────────────────────
# Per-language keywords loaded from config; English defaults always included.
_DEFAULT_LINK_KEYWORDS = re.compile(
    r"career|job|hiring|join\s*us|work\s*with\s*us|vacanc|we.re\s*hiring|"
    r"employment|opportunit|apply\s*now|open\s*position",
    re.IGNORECASE,
)

_COMMON_PATHS = [
    "/careers", "/jobs", "/join-us", "/work-with-us",
    "/hiring", "/vacancies", "/employment", "/opportunities",
    "/careers/search", "/jobs/search", "/about/careers",
    "/en/careers", "/en/jobs",
]

POSITIVE_CACHE_DAYS = 7
NEGATIVE_CACHE_DAYS = 14


# ── Domain helpers ────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.").lower()
    except Exception:
        return ""


def _base(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


# ── Cache helpers ─────────────────────────────────────────────────────────────

async def _get_cache(domain: str, db: AsyncSession) -> Optional[CareersPageCache]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CareersPageCache).where(
            CareersPageCache.domain == domain,
            CareersPageCache.expires_at > now,
        )
    )
    return result.scalars().first()


async def _set_cache(
    domain: str,
    careers_url: Optional[str],
    confidence: float,
    method: str,
    db: AsyncSession,
) -> None:
    now = datetime.now(timezone.utc)
    days = POSITIVE_CACHE_DAYS if careers_url else NEGATIVE_CACHE_DAYS
    expires = now + timedelta(days=days)

    existing = await db.execute(
        select(CareersPageCache).where(CareersPageCache.domain == domain)
    )
    row = existing.scalars().first()
    if row:
        row.careers_url = careers_url
        row.confidence = confidence
        row.method = method
        row.cached_at = now
        row.expires_at = expires
    else:
        db.add(CareersPageCache(
            domain=domain,
            careers_url=careers_url,
            confidence=confidence,
            method=method,
            cached_at=now,
            expires_at=expires,
        ))
    await db.commit()


# ── Strategy 1: Homepage link scan ───────────────────────────────────────────

def _find_career_links(html: str, base_url: str) -> list[Tuple[str, float]]:
    """
    Return a list of (url, confidence) pairs from career-matching links.
    Confidence: 1.0 = exact keyword in text, 0.7 = keyword in href only.
    """
    soup = BeautifulSoup(html, "lxml")
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = (a.get_text(strip=True) or "")
        full_url = urljoin(base_url, href)

        # Skip external domains
        if _domain(full_url) != _domain(base_url) and _domain(base_url) not in _domain(full_url):
            continue

        text_match = bool(_DEFAULT_LINK_KEYWORDS.search(text))
        href_match = bool(_DEFAULT_LINK_KEYWORDS.search(href))

        if text_match:
            found.append((full_url, 1.0))
        elif href_match:
            found.append((full_url, 0.7))

    # Sort by confidence desc; deduplicate by URL
    seen = set()
    result = []
    for url, conf in sorted(found, key=lambda x: -x[1]):
        if url not in seen:
            seen.add(url)
            result.append((url, conf))
    return result


# ── Strategy 2: Common paths ──────────────────────────────────────────────────

async def _try_common_paths(base_url: str) -> Optional[Tuple[str, float]]:
    for path in _COMMON_PATHS:
        url = base_url.rstrip("/") + path
        try:
            html = await http_client.fetch(url, rate_limit=1.5, check_robots=False, use_cache=True)
            if html and len(html) > 500:
                soup = BeautifulSoup(html, "lxml")
                title = soup.title.get_text(strip=True).lower() if soup.title else ""
                # Confirm it's actually a jobs page
                if _DEFAULT_LINK_KEYWORDS.search(title) or _DEFAULT_LINK_KEYWORDS.search(html[:2000]):
                    return url, 0.8
        except Exception:
            continue
    return None


# ── Strategy 3: sitemap.xml ───────────────────────────────────────────────────

async def _try_sitemap(base_url: str) -> Optional[Tuple[str, float]]:
    sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
    try:
        xml = await http_client.fetch(sitemap_url, rate_limit=1.5, check_robots=False, use_cache=True)
        if not xml:
            return None
        # Find any URL containing career keywords
        urls = re.findall(r"<loc>(.*?)</loc>", xml)
        for url in urls:
            if _DEFAULT_LINK_KEYWORDS.search(url):
                return url.strip(), 0.6
    except Exception:
        pass
    return None


# ── Main finder ───────────────────────────────────────────────────────────────

async def find_careers_page(
    website: str,
    db: AsyncSession,
) -> Optional[str]:
    """
    Find the careers page URL for a given employer website.
    Returns the URL string, or None if not found.
    Caches result in CareersPageCache.
    """
    if not website:
        return None

    # Normalise URL
    if not website.startswith("http"):
        website = "https://" + website.lstrip("/")

    base = _base(website)
    domain = _domain(website)

    if not domain:
        return None

    # ── Cache check ───────────────────────────────────────────────────────────
    cached = await _get_cache(domain, db)
    if cached:
        logger.debug(f"Careers page cache hit for {domain}: {cached.careers_url}")
        return cached.careers_url

    logger.info(f"Finding careers page for {domain}")

    # ── Strategy 1: Homepage link scan ───────────────────────────────────────
    try:
        html = await http_client.fetch(website, rate_limit=2.0, check_robots=True, use_cache=True)
        if html:
            links = _find_career_links(html, base)
            if links:
                careers_url, conf = links[0]
                logger.info(f"Found via link scan: {careers_url} (conf={conf})")
                await _set_cache(domain, careers_url, conf, "link_text", db)
                return careers_url
    except Exception as e:
        logger.debug(f"Homepage fetch failed for {domain}: {e}")

    # ── Strategy 2: Common paths ──────────────────────────────────────────────
    result = await _try_common_paths(base)
    if result:
        careers_url, conf = result
        logger.info(f"Found via common path: {careers_url}")
        await _set_cache(domain, careers_url, conf, "common_path", db)
        return careers_url

    # ── Strategy 3: Sitemap ───────────────────────────────────────────────────
    result = await _try_sitemap(base)
    if result:
        careers_url, conf = result
        logger.info(f"Found via sitemap: {careers_url}")
        await _set_cache(domain, careers_url, conf, "sitemap", db)
        return careers_url

    # ── No page found — cache negative result ─────────────────────────────────
    logger.info(f"No careers page found for {domain}")
    await _set_cache(domain, None, 0.0, "not_found", db)
    return None
