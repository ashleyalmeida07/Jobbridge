"""
BaseScraper: every scraper inherits from this class.

Subclasses must set class-level attributes and implement:
  parse_list(html) -> list of raw dicts (one per job card)
  parse_detail(html, url) -> dict  (optional; enrich a single job)

run() orchestrates fetch → parse_list → (optionally) parse_detail → normalize.
"""

import logging
from typing import Any, Dict, List, Optional

from app.scraper import http_client
from app.scraper.normalise import (
    PayResult, parse_pay, classify_job_type,
    classify_category, parse_posted_date,
    extract_email, make_dedupe_hash,
)

logger = logging.getLogger(__name__)


class BaseScraper:
    # ── Required class attributes ─────────────────────────────────────────────
    name: str = "base"
    country: str = "AU"
    base_url: str = ""
    needs_js: bool = False          # True → Playwright; False → httpx
    rate_limit_seconds: float = 3.0

    # ── Optional: set to False to disable robots.txt check for this scraper ──
    check_robots: bool = True

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"scraper.{self.name}")

    # ── Methods to override ───────────────────────────────────────────────────

    def build_search_urls(self, keywords: List[str], location: str, job_type: str) -> List[str]:
        """
        Return a list of search result page URLs to fetch for this keyword/location combo.
        Override in subclasses.
        """
        raise NotImplementedError(f"{self.name}.build_search_urls() not implemented")

    def parse_list(self, html: str, url: str = "") -> List[Dict[str, Any]]:
        """
        Parse a search results page and return a list of raw job dicts.
        Each dict should have at minimum: title, employer, location, source_url.
        """
        raise NotImplementedError(f"{self.name}.parse_list() not implemented")

    def parse_detail(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Parse a job detail page and return an enriched dict.
        Override only if the scraper fetches individual job pages.
        """
        return {}

    # ── Normalisation (shared) ────────────────────────────────────────────────

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the shared normalisation pipeline to a raw job dict.
        Returns a dict ready to be inserted into the jobs table.
        """
        title    = raw.get("title", "").strip()
        employer = raw.get("employer", "").strip()
        location = raw.get("location", "").strip()

        pay: PayResult = parse_pay(raw.get("pay_text", ""))
        jtype    = raw.get("job_type") or classify_job_type(title, raw.get("description", ""))
        category = raw.get("category") or classify_category(title, raw.get("description", ""))
        posted   = raw.get("posted_at") or parse_posted_date(raw.get("posted_text", ""))
        email    = raw.get("contact_email") or extract_email(raw.get("description", ""))
        d_hash   = raw.get("dedupe_hash") or make_dedupe_hash(employer, title, location)

        return {
            "source":        self.name,
            "source_url":    raw.get("source_url", ""),
            "title":         title,
            "employer":      employer,
            "location":      location,
            "pay_text":      pay.pay_text or raw.get("pay_text", ""),
            "pay_min":       raw.get("pay_min") if raw.get("pay_min") is not None else pay.pay_min,
            "pay_max":       raw.get("pay_max") if raw.get("pay_max") is not None else pay.pay_max,
            "pay_period":    raw.get("pay_period") or pay.pay_period,
            "job_type":      jtype,
            "category":      category,
            "description":   raw.get("description", ""),
            "contact_email": email,
            "posted_at":     posted,
            "dedupe_hash":   d_hash,
        }

    # ── Fetch helpers ─────────────────────────────────────────────────────────

    async def _fetch_html(self, url: str) -> str:
        if self.needs_js:
            from app.scraper.browser import get_page_html
            return await get_page_html(url)
        return await http_client.fetch(
            url,
            rate_limit=self.rate_limit_seconds,
            base_url=self.base_url,
            check_robots=self.check_robots,
        )

    async def _fetch_json(self, url: str, params: dict | None = None) -> Any:
        return await http_client.fetch_json(
            url,
            rate_limit=self.rate_limit_seconds,
            base_url=self.base_url,
            params=params,
        )

    # ── Entry point ───────────────────────────────────────────────────────────

    async def run(
        self,
        keywords: List[str],
        location: str = "",
        job_type: str = "",
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Orchestrates search URL generation → fetch → parse → normalize.
        Returns list of normalised job dicts (up to `limit`).
        """
        search_urls = self.build_search_urls(keywords, location, job_type)
        results: List[Dict[str, Any]] = []

        for url in search_urls:
            if len(results) >= limit:
                break
            try:
                html = await self._fetch_html(url)
                if not html:
                    continue
                raw_jobs = self.parse_list(html, url)
                for raw in raw_jobs:
                    if len(results) >= limit:
                        break
                    # Optional detail fetch
                    if raw.get("source_url") and hasattr(self, "_fetch_detail") and self._fetch_detail:
                        try:
                            detail_html = await self._fetch_html(raw["source_url"])
                            extra = self.parse_detail(detail_html, raw["source_url"])
                            raw.update(extra)
                        except Exception as e:
                            self.logger.warning(f"Detail fetch failed for {raw.get('source_url')}: {e}")
                    results.append(self.normalize(raw))
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                continue

        return results
