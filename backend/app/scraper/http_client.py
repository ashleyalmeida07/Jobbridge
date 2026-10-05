"""
Shared async HTTP client for all scrapers.

Features:
- Clear User-Agent  
- Configurable timeouts
- Exponential backoff (3 retries by default)
- Per-domain delay enforcement
- In-memory response cache for the lifetime of a scrape run
- robots.txt checking via urllib.robotparser (cached per domain)
"""

import asyncio
import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "JobBridge/1.0 (+https://github.com/jobbridge; contact@jobbridge.app)"
DEFAULT_TIMEOUT = 20.0
MAX_RETRIES = 3
BASE_BACKOFF = 2.0  # seconds; doubles each retry

# ── Module-level state ────────────────────────────────────────────────────────

# _domain_last_request[domain] = monotonic timestamp of last request
_domain_last_request: dict[str, float] = {}

# _response_cache[url] = (html_body, timestamp)
_response_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 3600  # 1 hour

# _robots[domain] = RobotFileParser (or None if fetch failed)
_robots: dict[str, Optional[RobotFileParser]] = {}


# ── Rate-limit helper ─────────────────────────────────────────────────────────

async def _respect_rate_limit(domain: str, delay: float) -> None:
    now = time.monotonic()
    last = _domain_last_request.get(domain, 0.0)
    wait = delay - (now - last)
    if wait > 0:
        logger.debug(f"Rate-limit: sleeping {wait:.2f}s for {domain}")
        await asyncio.sleep(wait)
    _domain_last_request[domain] = time.monotonic()


# ── robots.txt helper ─────────────────────────────────────────────────────────

async def _get_robots(domain: str, base_url: str) -> Optional[RobotFileParser]:
    if domain in _robots:
        return _robots[domain]
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    rp = RobotFileParser(robots_url)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(robots_url, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                rp = None  # no robots.txt = allow all
    except Exception:
        rp = None
    _robots[domain] = rp
    return rp


def is_allowed(url: str, robots: Optional[RobotFileParser]) -> bool:
    if robots is None:
        return True
    return robots.can_fetch(USER_AGENT, url)


# ── Main fetch function ───────────────────────────────────────────────────────

async def fetch(
    url: str,
    *,
    rate_limit: float = 2.0,
    base_url: str = "",
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    use_cache: bool = True,
    check_robots: bool = True,
) -> str:
    """
    Fetch a URL and return the response body as a string.

    Args:
        url: Target URL.
        rate_limit: Minimum seconds between requests to the same domain.
        base_url: Used to locate robots.txt.
        headers: Extra request headers (merged with defaults).
        use_cache: Return cached response if available within CACHE_TTL.
        check_robots: Skip URLs disallowed by robots.txt.

    Returns:
        HTML/text body.

    Raises:
        httpx.HTTPError on non-recoverable errors after retries.
    """
    parsed = urlparse(url)
    domain = parsed.netloc

    # Build full URL with params for cache key
    if params:
        import urllib.parse
        qs = urllib.parse.urlencode(params)
        cache_url = f"{url}?{qs}" if "?" not in url else f"{url}&{qs}"
    else:
        cache_url = url

    # Cache check
    if use_cache and cache_url in _response_cache:
        body, ts = _response_cache[cache_url]
        if time.time() - ts < CACHE_TTL:
            logger.debug(f"Cache hit: {cache_url}")
            return body

    # robots.txt check
    if check_robots:
        robots = await _get_robots(domain, base_url or f"{parsed.scheme}://{domain}")
        if not is_allowed(url, robots):
            logger.warning(f"robots.txt disallows: {url} — skipping")
            return ""

    # Rate limit
    await _respect_rate_limit(domain, rate_limit)

    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9"
    }
    if headers:
        req_headers.update(headers)

    # Fetch with retries
    last_exc: Exception = RuntimeError("Unknown error")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=req_headers, params=params)
                resp.raise_for_status()
                body = resp.text
                if use_cache:
                    _response_cache[cache_url] = (body, time.time())
                return body

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403, 404, 400):
                logger.warning(f"Fetch blocked or invalid (HTTP {status}) for {cache_url}. Not retrying.")
                raise exc
                
            last_exc = exc
            wait = BASE_BACKOFF ** attempt
            if status == 429:
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                    
            logger.warning(f"Fetch attempt {attempt}/{MAX_RETRIES} failed for {cache_url}: {exc}. Retrying in {wait}s")
            await asyncio.sleep(wait)
            
        except httpx.RequestError as exc:
            last_exc = exc
            wait = BASE_BACKOFF ** attempt
            logger.warning(f"Fetch attempt {attempt}/{MAX_RETRIES} failed for {cache_url}: {exc}. Retrying in {wait}s")
            await asyncio.sleep(wait)

    raise last_exc


async def fetch_json(
    url: str,
    *,
    rate_limit: float = 2.0,
    base_url: str = "",
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    use_cache: bool = True,
    check_robots: bool = False,  # XHR endpoints usually not in robots.txt
) -> dict | list:
    """Fetch a JSON API endpoint and return parsed dict/list."""
    parsed = urlparse(url)
    domain = parsed.netloc

    # Build full URL with params for cache key
    if params:
        qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        cache_url = f"{url}?{qs}"
    else:
        cache_url = url

    if use_cache and cache_url in _response_cache:
        body, ts = _response_cache[cache_url]
        if time.time() - ts < CACHE_TTL:
            import json
            return json.loads(body)

    await _respect_rate_limit(domain, rate_limit)

    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-AU,en;q=0.9",
    }
    if headers:
        req_headers.update(headers)

    last_exc: Exception = RuntimeError("Unknown")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url, headers=req_headers, params=params)
                resp.raise_for_status()
                body = resp.text
                if use_cache:
                    _response_cache[cache_url] = (body, time.time())
                return resp.json()
        except Exception as exc:
            last_exc = exc
            wait = BASE_BACKOFF ** attempt
            logger.warning(f"JSON fetch attempt {attempt}/{MAX_RETRIES} failed for {url}: {exc}")
            await asyncio.sleep(wait)

    raise last_exc


def clear_cache() -> None:
    """Clear the in-memory response cache (call between scrape runs in tests)."""
    _response_cache.clear()
    _domain_last_request.clear()
