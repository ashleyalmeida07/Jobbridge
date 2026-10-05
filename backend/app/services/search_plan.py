"""
Search Plan Builder (v2) — location-driven, no hardcoded employers.

Produces two kinds of tasks:
  1. employer_tasks — discovered employers near user (Overpass → careers finder → extractor)
  2. board_tasks    — job board queries built from user's keywords and location

Both are consumed by scrape_runner.run_search_plan().
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.country_config import CATEGORY_KEYWORDS, DOMAIN_KEYWORDS

logger = logging.getLogger(__name__)


def _keywords_for_profile(profile) -> Dict[str, List[str]]:
    """
    Return a dict: {job_type_key: [keyword, ...]} from the user's profile.
    e.g. {"internship_domain": ["software engineer intern", ...], "parttime_any": ["barista", ...]}
    """
    result: Dict[str, List[str]] = {}
    looking: List[str] = profile.looking_for or []
    domain: str = profile.domain or "Other"
    any_cats: List[str] = profile.any_field_categories or []

    domain_kws = DOMAIN_KEYWORDS.get(domain, DOMAIN_KEYWORDS["Other"])

    if "internship_domain" in looking:
        result["internship_domain"] = domain_kws[:3] + ["intern", "student"]

    if "fulltime_domain" in looking:
        result["fulltime_domain"] = domain_kws[:3]

    if "parttime_domain" in looking:
        result["parttime_domain"] = domain_kws[:3]

    if "parttime_any" in looking:
        cats = any_cats if any_cats else ["retail", "hospitality", "delivery", "cafe"]
        kws: List[str] = [c.replace("_", " ") for c in cats]
        result["parttime_any"] = kws[:5]

    return result


def build_search_plan(profile) -> Dict[str, Any]:
    """
    Build the full search plan for a user profile.

    Returns a dict with two lists:
      employer_tasks: [{lat, lng, radius_km, categories}]  — for discovery pipeline
      board_tasks:    [{keywords, city, country, job_type}] — for board scraper
    """
    country = (profile.country or "AU").upper()
    city = profile.city or ""
    lat = profile.lat
    lng = profile.lng
    radius_km = profile.commute_radius_km or 10
    looking: List[str] = profile.looking_for or []
    any_cats: List[str] = profile.any_field_categories or []

    kw_map = _keywords_for_profile(profile)

    # ── Employer discovery tasks ───────────────────────────────────────────────
    employer_tasks = []
    if lat and lng:
        # Map looking_for to OSM categories
        categories_needed: List[str] = []
        if "parttime_any" in looking:
            cats = any_cats if any_cats else ["food_cafe", "retail", "warehouse"]
            categories_needed.extend(cats)
        if any(t in looking for t in ("internship_domain", "fulltime_domain", "parttime_domain")):
            categories_needed.extend(["campus", "tutoring"])

        if categories_needed:
            employer_tasks.append({
                "lat":        lat,
                "lng":        lng,
                "radius_km":  radius_km,
                "categories": list(set(categories_needed)),
            })

    # ── Job board tasks ───────────────────────────────────────────────────────
    board_tasks = []
    job_type_map = {
        "internship_domain": "internship",
        "fulltime_domain":   "full_time",
        "parttime_domain":   "part_time",
        "parttime_any":      "casual",
    }
    for looking_key, keywords in kw_map.items():
        job_type = job_type_map.get(looking_key, "")
        board_tasks.append({
            "keywords": keywords,
            "city":     city,
            "country":  country,
            "job_type": job_type,
        })

    return {
        "employer_tasks": employer_tasks,
        "board_tasks":    board_tasks,
    }
