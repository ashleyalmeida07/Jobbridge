"""
Generic board scraper — driven entirely by config/boards.yaml.
No employer names are hardcoded here.

For each board entry:
  1. Build search URLs from url_template.
  2. Fetch each page.
  3. Try JSON-LD first (if json_ld: true).
  4. Fall back to CSS selectors from the YAML config.
  5. Normalise and return jobs.

Adding a new board = adding a YAML entry only.
"""

import logging
import pathlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup

from app.scraper import http_client
from app.scraper.generic_extractor import extract_json_ld
from app.scraper.normalise import (
    parse_pay, classify_job_type, classify_category,
    parse_posted_date, extract_email, make_dedupe_hash,
)

logger = logging.getLogger(__name__)

_BOARDS_CONFIG: Optional[Dict] = None


def _load_boards() -> Dict:
    global _BOARDS_CONFIG
    # Always reload so config changes take effect without restart
    p = pathlib.Path(__file__).parent.parent.parent / "config" / "boards.yaml"
    with open(p) as f:
        _BOARDS_CONFIG = yaml.safe_load(f)
    return _BOARDS_CONFIG


def get_boards_for_country(country: str) -> List[Dict]:
    cfg = _load_boards()
    return [
        b for b in cfg.get("countries", {}).get(country.upper(), {}).get("boards", [])
        if b.get("enabled", True)
    ]


# ── URL builder ───────────────────────────────────────────────────────────────

def _build_urls(board: Dict, keyword: str, city: str, country: str) -> List[tuple[str, dict]]:
    from urllib.parse import urlparse, parse_qsl
    
    template = board["url_template"]
    parsed = urlparse(template)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    query_template = dict(parse_qsl(parsed.query))
    
    urls_with_params = []
    
    # Clean up whitespace that causes encoding issues
    kw = keyword.strip()
    c = city.strip()
    ctry = country.strip().lower()

    for page in range(1, board.get("max_pages", 2) + 1):
        params = {}
        for k, v in query_template.items():
            val = v.replace("{keyword}", kw).replace("{city}", c).replace("{country}", ctry).replace("{page}", str(page))
            params[k] = val
        urls_with_params.append((base_url, params))
        
    return urls_with_params


# ── CSS selector extractor ────────────────────────────────────────────────────

def _extract_with_selectors(html: str, board: Dict, page_url: str) -> List[Dict[str, Any]]:
    selectors = board.get("selectors", {})
    list_sel = selectors.get("list_item", "")
    if not list_sel:
        return []

    soup = BeautifulSoup(html, "lxml")
    base = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
    jobs = []

    for card in soup.select(list_sel):
        def _text(sel):
            if not sel:
                return ""
            el = card.select_one(sel)
            return el.get_text(strip=True) if el else ""

        def _href(sel):
            if not sel:
                return ""
            el = card.select_one(sel)
            if not el:
                return ""
            href = el.get("href", "")
            return urljoin(base, href) if href else ""

        title = _text(selectors.get("title"))
        if not title:
            continue

        jobs.append({
            "title":       title,
            "employer":    _text(selectors.get("employer")),
            "location":    _text(selectors.get("location")),
            "pay_text":    _text(selectors.get("pay")),
            "job_type":    _text(selectors.get("job_type")),
            "posted_text": _text(selectors.get("date")),
            "source_url":  _href(selectors.get("link")),
        })

    return jobs


# ── Normaliser ────────────────────────────────────────────────────────────────

def _normalise(raw: Dict, board_id: str) -> Dict[str, Any]:
    title    = raw.get("title", "").strip()
    employer = raw.get("employer", "").strip()
    location = raw.get("location", "").strip()

    pay = parse_pay(raw.get("pay_text", ""))
    jtype   = raw.get("job_type") or classify_job_type(title, raw.get("description", ""))
    cat     = classify_category(title, raw.get("description", ""))
    posted  = parse_posted_date(raw.get("posted_text", ""))
    email   = extract_email(raw.get("description", ""))
    d_hash  = make_dedupe_hash(employer, title, location)

    return {
        "source":        board_id,
        "source_url":    raw.get("source_url", ""),
        "title":         title,
        "employer":      employer,
        "location":      location,
        "pay_text":      pay.pay_text or raw.get("pay_text", ""),
        "pay_min":       pay.pay_min,
        "pay_max":       pay.pay_max,
        "pay_period":    pay.pay_period,
        "job_type":      jtype,
        "category":      cat,
        "description":   raw.get("description", ""),
        "contact_email": email,
        "posted_at":     posted,
        "dedupe_hash":   d_hash,
    }


# ── Main runner ───────────────────────────────────────────────────────────────

async def scrape_board(
    board: Dict,
    keyword: str,
    city: str,
    country: str,
    *,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Scrape one job board with one keyword+city combo.
    Returns normalised job dicts.
    """
    board_id = board["id"]
    rate_limit = board.get("rate_limit", 3)
    use_json_ld = board.get("json_ld", True)
    urls = _build_urls(board, keyword, city, country)
    results: List[Dict[str, Any]] = []

    for url, params in urls:
        if len(results) >= limit:
            break
        try:
            html = await http_client.fetch(
                url, rate_limit=rate_limit, base_url=url, params=params, check_robots=True
            )
            if not html:
                continue

            # JSON-LD first
            if use_json_ld:
                jobs = extract_json_ld(html, url)
                if jobs:
                    results.extend(_normalise(j, board_id) for j in jobs)
                    continue

            # CSS selectors fallback
            jobs = _extract_with_selectors(html, board, url)
            results.extend(_normalise(j, board_id) for j in jobs)

        except Exception as e:
            import httpx
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code in (400, 401, 403, 404):
                    logger.warning(f"Board {board_id} blocked us (HTTP {e.response.status_code}). Skipping entirely.")
                    raise e
            logger.error(f"Board {board_id} failed for {url}: {e}")
            continue

    return results[:limit]


async def _enrich_emails(jobs: List[Dict[str, Any]], rate_limit: float = 4.0) -> List[Dict[str, Any]]:
    """Fetch job detail pages to extract contact emails for cold outreach."""
    for job in jobs:
        if job.get("contact_email"):
            continue  # already have one
        detail_url = job.get("source_url", "")
        if not detail_url or not detail_url.startswith("http"):
            continue
        try:
            html = await http_client.fetch(
                detail_url, rate_limit=rate_limit, check_robots=True
            )
            if html:
                email = extract_email(html)
                if email:
                    job["contact_email"] = email
                    logger.info(f"Found contact email {email} on {detail_url}")
                # Also try to fill description if empty
                if not job.get("description"):
                    soup = BeautifulSoup(html, "lxml")
                    desc_el = soup.select_one(
                        "[class*='description'], [class*='job-detail'], "
                        "[data-testid='jobDescription'], .job-description, "
                        "article, .content"
                    )
                    if desc_el:
                        job["description"] = desc_el.get_text(separator="\n", strip=True)[:2000]
        except Exception as e:
            logger.debug(f"Could not fetch detail page {detail_url}: {e}")
            continue
    return jobs


async def scrape_all_boards(
    keywords: List[str],
    city: str,
    country: str,
    *,
    limit_per_board: int = 50,
) -> List[Dict[str, Any]]:
    """Scrape all enabled boards for a country with the given keywords."""
    boards = get_boards_for_country(country)
    results = []
    for board in boards:
        for kw in keywords[:3]:  # max 3 keywords per board to stay polite
            try:
                jobs = await scrape_board(board, kw, city, country, limit=limit_per_board)
                results.extend(jobs)
                logger.info(f"Board {board['id']} / '{kw}': {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"Board {board['id']} crashed: {e}")

    # Enrich top results with emails from detail pages (max 10 to be polite)
    if results:
        to_enrich = [j for j in results if j.get("source_url") and not j.get("contact_email")][:10]
        if to_enrich:
            logger.info(f"Enriching {len(to_enrich)} jobs with email extraction from detail pages")
            await _enrich_emails(to_enrich)

    return results
