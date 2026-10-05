"""
Generic Job Extractor

Attempts to extract job listings from any careers page URL using 4 strategies:

  1. JSON-LD (schema.org/JobPosting)     — highest fidelity, no HTML parsing
  2. Embedded JSON (__NEXT_DATA__, window.__state__, etc.) — common in SPAs
  3. Heuristic HTML parsing              — find repeated blocks with job signals
  4. Playwright retry                    — only if page appeared empty (JS-rendered)

All extraction is rule-based. No AI/LLM is used anywhere.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.scraper import http_client
from app.scraper.normalise import (
    parse_pay, classify_job_type, classify_category,
    parse_posted_date, extract_email, make_dedupe_hash,
)

logger = logging.getLogger(__name__)

MAX_DETAIL_LINKS = 20  # max job detail pages to follow per employer

# ── Signals used by heuristic HTML parser ─────────────────────────────────────
_JOB_SIGNAL_RE = re.compile(
    r"apply|full[\s-]time|part[\s-]time|casual|intern|per\s*hour|\$/hr|vacancies?|"
    r"we.re\s*hiring|join\s*our\s*team|open\s*role|open\s*position",
    re.IGNORECASE,
)
_HEADING_TAGS = {"h1", "h2", "h3", "h4"}
_BLOCK_TAGS = {"article", "section", "li", "div"}


# ── Strategy 1: JSON-LD ───────────────────────────────────────────────────────

def extract_json_ld(html: str, page_url: str = "") -> List[Dict[str, Any]]:
    """
    Parse <script type="application/ld+json"> blocks and extract JobPosting entries.
    """
    soup = BeautifulSoup(html, "lxml")
    jobs = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # May be a single object or a list
        items = data if isinstance(data, list) else [data]
        for item in items:
            # Handle @graph arrays
            if item.get("@type") == "WebPage":
                graph = item.get("@graph", [])
                items = graph + items
                continue
            if item.get("@type") in ("JobPosting", "jobPosting"):
                jobs.append(_parse_json_ld_job(item, page_url))

    return jobs


def _parse_json_ld_job(item: Dict, page_url: str) -> Dict[str, Any]:
    loc = item.get("jobLocation", {})
    addr = loc.get("address", {}) if isinstance(loc, dict) else {}
    if isinstance(addr, str):
        location_str = addr
    else:
        parts = [
            addr.get("streetAddress", ""),
            addr.get("addressLocality", ""),
            addr.get("addressRegion", ""),
        ]
        location_str = ", ".join(p for p in parts if p)

    sal = item.get("baseSalary", {}) or {}
    val = sal.get("value", {}) if isinstance(sal, dict) else {}
    if isinstance(val, dict):
        pay_min = val.get("minValue")
        pay_max = val.get("maxValue") or val.get("value")
        pay_period = _normalise_period(val.get("unitText", ""))
        pay_text = f"${pay_min}–${pay_max} {pay_period}".strip() if pay_min else ""
    else:
        pay_min = pay_max = None
        pay_period = None
        pay_text = ""

    employer = item.get("hiringOrganization", {})
    employer_name = employer.get("name", "") if isinstance(employer, dict) else str(employer)

    apply_url = item.get("url") or item.get("identifier", {}).get("value") or page_url
    if isinstance(apply_url, dict):
        apply_url = apply_url.get("value", page_url)

    title = item.get("title") or item.get("name", "")
    desc = _clean_description(item.get("description", ""))

    return {
        "title":         title,
        "employer":      employer_name,
        "location":      location_str,
        "pay_text":      pay_text,
        "pay_min":       pay_min,
        "pay_max":       pay_max,
        "pay_period":    pay_period,
        "job_type":      _normalise_job_type(item.get("employmentType", "")),
        "description":   desc,
        "posted_text":   item.get("datePosted", ""),
        "contact_email": extract_email(desc),
        "source_url":    apply_url,
    }


def _normalise_period(text: str) -> Optional[str]:
    t = text.upper()
    if "HOUR" in t: return "hourly"
    if "WEEK" in t: return "weekly"
    if "YEAR" in t or "ANNUM" in t: return "yearly"
    if "MONTH" in t: return "monthly"
    return None


def _normalise_job_type(text: str) -> str:
    t = text.upper().replace("_", " ")
    if "FULL" in t: return "full_time"
    if "PART" in t: return "part_time"
    if "CASUAL" in t or "TEMPORARY" in t: return "casual"
    if "INTERN" in t or "CONTRACT" in t: return "internship"
    return "full_time"


def _clean_description(html_or_text: str) -> str:
    if "<" in html_or_text:
        return BeautifulSoup(html_or_text, "lxml").get_text(" ", strip=True)[:3000]
    return html_or_text[:3000]


# ── Strategy 2: Embedded JSON ─────────────────────────────────────────────────

_JSON_BLOBS = [
    re.compile(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', re.DOTALL),
    re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*(?:</script>|$)', re.DOTALL),
    re.compile(r'window\.__STATE__\s*=\s*({.+?});\s*(?:</script>|$)', re.DOTALL),
    re.compile(r'window\.pageData\s*=\s*({.+?});\s*', re.DOTALL),
]

_JOB_ARRAY_KEYS = [
    "jobs", "jobList", "results", "listings", "postings",
    "data", "items", "vacancies", "openings", "positions",
]


def extract_embedded_json(html: str, page_url: str = "") -> List[Dict[str, Any]]:
    """Find JSON blobs embedded in the page and extract job arrays from them."""
    jobs = []
    for pattern in _JSON_BLOBS:
        m = pattern.search(html)
        if not m:
            continue
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        found = _walk_for_jobs(data)
        if found:
            jobs.extend(_parse_generic_job_dict(j, page_url) for j in found)
            break
    return jobs


def _walk_for_jobs(data: Any, depth: int = 0) -> List[Dict]:
    """Recursively walk a JSON structure looking for a list of job dicts."""
    if depth > 6:
        return []
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and _looks_like_job(data[0]):
            return data
        for item in data:
            found = _walk_for_jobs(item, depth + 1)
            if found:
                return found
    elif isinstance(data, dict):
        for key in _JOB_ARRAY_KEYS:
            if key in data:
                found = _walk_for_jobs(data[key], depth + 1)
                if found:
                    return found
        for v in data.values():
            found = _walk_for_jobs(v, depth + 1)
            if found:
                return found
    return []


def _looks_like_job(obj: Dict) -> bool:
    """Heuristic: dict has title/name-like key and at least one more job field."""
    keys = {k.lower() for k in obj.keys()}
    has_title = bool({"title", "name", "jobtitle", "position"} & keys)
    has_other = bool({"location", "employer", "salary", "type", "url", "id", "description"} & keys)
    return has_title and has_other


def _parse_generic_job_dict(obj: Dict, page_url: str) -> Dict[str, Any]:
    """Best-effort extraction from an unknown job dict shape."""
    def _get(*keys):
        for k in keys:
            for key in obj:
                if key.lower() == k.lower():
                    return obj[key]
        return ""

    title = str(_get("title", "name", "jobTitle", "position") or "")
    employer = str(_get("employer", "company", "organization", "hiringOrganization") or "")
    location = str(_get("location", "city", "jobLocation", "address") or "")
    pay = str(_get("salary", "compensation", "pay", "wage") or "")
    url = str(_get("url", "link", "applyUrl", "href", "jobUrl") or page_url)
    desc = str(_get("description", "teaser", "summary", "snippet") or "")
    jtype = str(_get("type", "employmentType", "workType", "jobType") or "")
    posted = str(_get("datePosted", "postedDate", "date", "listingDate") or "")

    return {
        "title":       title,
        "employer":    employer,
        "location":    location,
        "pay_text":    pay,
        "job_type":    _normalise_job_type(jtype) if jtype else None,
        "description": desc[:3000],
        "posted_text": posted,
        "source_url":  url if url.startswith("http") else "",
    }


# ── Strategy 3: Heuristic HTML ────────────────────────────────────────────────

def extract_heuristic_html(html: str, page_url: str = "") -> List[Dict[str, Any]]:
    """
    Find repeated structural blocks that look like job listings:
    - A heading inside a block element
    - At least one link (apply / job detail)
    - Job signal text nearby (full-time, apply, per hour, etc.)
    """
    soup = BeautifulSoup(html, "lxml")
    base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
    jobs = []

    # Find all block elements with a heading inside
    for block in soup.find_all(_BLOCK_TAGS):
        heading = block.find(_HEADING_TAGS)
        if not heading:
            continue
        title = heading.get_text(strip=True)
        if not title or len(title) < 3 or len(title) > 200:
            continue

        block_text = block.get_text(" ", strip=True)
        if not _JOB_SIGNAL_RE.search(block_text):
            continue

        # Get link
        link = block.find("a", href=True)
        href = link["href"] if link else ""
        source_url = urljoin(base, href) if href else page_url

        # Extract employer (check meta or parent context)
        employer = ""
        for emp_sel in [".company", ".employer", "[class*='company']", "[class*='employer']"]:
            el = block.select_one(emp_sel)
            if el:
                employer = el.get_text(strip=True)
                break

        # Pay / type
        pay_el = block.select_one("[class*='salary'],[class*='pay'],[class*='wage']")
        type_el = block.select_one("[class*='type'],[class*='work-type'],[class*='contract']")
        date_el = block.select_one("time,[class*='date'],[class*='listed']")

        jobs.append({
            "title":       title,
            "employer":    employer,
            "location":    "",  # often not in card; picked up from detail page
            "pay_text":    pay_el.get_text(strip=True) if pay_el else "",
            "job_type":    type_el.get_text(strip=True) if type_el else "",
            "posted_text": date_el.get_text(strip=True) if date_el else "",
            "source_url":  source_url,
        })

        if len(jobs) >= MAX_DETAIL_LINKS * 2:
            break

    return jobs


# ── Main extractor ────────────────────────────────────────────────────────────

async def extract_jobs(
    careers_url: str,
    employer_name: str = "",
    *,
    follow_links: bool = True,
) -> List[Dict[str, Any]]:
    """
    Extract jobs from a careers page URL.
    Tries all 4 strategies in order, uses Playwright only if page is empty.

    Returns normalised job dicts.
    """
    # ── Fetch page ────────────────────────────────────────────────────────────
    html = await _safe_fetch(careers_url)

    if not html:
        return []

    # ── Strategy 1: JSON-LD ───────────────────────────────────────────────────
    jobs = extract_json_ld(html, careers_url)
    if jobs:
        logger.info(f"JSON-LD: {len(jobs)} jobs from {careers_url}")
        return _finalise(jobs, employer_name, careers_url)

    # ── Strategy 2: Embedded JSON ─────────────────────────────────────────────
    jobs = extract_embedded_json(html, careers_url)
    if jobs:
        logger.info(f"Embedded JSON: {len(jobs)} jobs from {careers_url}")
        return _finalise(jobs, employer_name, careers_url)

    # ── Strategy 3: Heuristic HTML ────────────────────────────────────────────
    jobs = extract_heuristic_html(html, careers_url)
    if jobs:
        logger.info(f"Heuristic HTML: {len(jobs)} jobs from {careers_url}")
        if follow_links:
            jobs = await _enrich_with_detail(jobs[:MAX_DETAIL_LINKS], employer_name, careers_url)
        return _finalise(jobs, employer_name, careers_url)

    # ── Strategy 4: Playwright retry ─────────────────────────────────────────
    logger.info(f"Trying Playwright for {careers_url}")
    try:
        from app.scraper.browser import get_page_html
        html = await get_page_html(careers_url)
        if html:
            jobs = (
                extract_json_ld(html, careers_url)
                or extract_embedded_json(html, careers_url)
                or extract_heuristic_html(html, careers_url)
            )
            if jobs:
                logger.info(f"Playwright: {len(jobs)} jobs from {careers_url}")
                return _finalise(jobs, employer_name, careers_url)
    except ImportError:
        logger.debug("Playwright not installed; skipping strategy 4")
    except Exception as e:
        logger.warning(f"Playwright failed for {careers_url}: {e}")

    logger.info(f"No jobs found at {careers_url}")
    return []


async def _safe_fetch(url: str) -> str:
    try:
        return await http_client.fetch(url, rate_limit=2.0, check_robots=True, use_cache=True)
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return ""


async def _enrich_with_detail(
    jobs: List[Dict], employer_name: str, base_url: str
) -> List[Dict]:
    """Follow detail page links and merge extra fields (description, location, pay)."""
    enriched = []
    for job in jobs:
        detail_url = job.get("source_url", "")
        if not detail_url or detail_url == base_url:
            enriched.append(job)
            continue
        try:
            html = await _safe_fetch(detail_url)
            if not html:
                enriched.append(job)
                continue
            # Try JSON-LD on detail page first
            detail_jobs = extract_json_ld(html, detail_url)
            if detail_jobs:
                merged = {**job, **detail_jobs[0]}
            else:
                # Extract description directly
                soup = BeautifulSoup(html, "lxml")
                desc_el = (
                    soup.select_one("[class*='description']")
                    or soup.select_one("[class*='details']")
                    or soup.select_one("main")
                )
                if desc_el:
                    job["description"] = desc_el.get_text(" ", strip=True)[:3000]
                merged = job
            enriched.append(merged)
        except Exception as e:
            logger.debug(f"Detail fetch failed for {detail_url}: {e}")
            enriched.append(job)
    return enriched


def _finalise(
    jobs: List[Dict], employer_name: str, source_url: str
) -> List[Dict[str, Any]]:
    """Apply normalisation fields to each extracted job dict."""
    result = []
    for job in jobs:
        title    = job.get("title", "").strip()
        employer = (job.get("employer") or employer_name or "").strip()
        location = job.get("location", "").strip()

        if not title:
            continue

        pay = parse_pay(job.get("pay_text", ""))
        jtype = job.get("job_type") or classify_job_type(title, job.get("description", ""))
        cat   = classify_category(title, job.get("description", ""))
        posted = parse_posted_date(job.get("posted_text", ""))
        email  = job.get("contact_email") or extract_email(job.get("description", ""))
        d_hash = make_dedupe_hash(employer, title, location)

        result.append({
            "title":         title,
            "employer":      employer,
            "location":      location,
            "pay_text":      pay.pay_text or job.get("pay_text", ""),
            "pay_min":       job.get("pay_min") if job.get("pay_min") is not None else pay.pay_min,
            "pay_max":       job.get("pay_max") if job.get("pay_max") is not None else pay.pay_max,
            "pay_period":    job.get("pay_period") or pay.pay_period,
            "job_type":      _normalise_job_type(jtype) if jtype and "_" not in jtype else jtype,
            "category":      cat,
            "description":   job.get("description", ""),
            "contact_email": email,
            "posted_at":     posted,
            "source_url":    job.get("source_url") or source_url,
            "dedupe_hash":   d_hash,
        })

    return result
