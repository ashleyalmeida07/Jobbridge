"""
Scraper C: Woolworths Group careers (retail)

Technique: JSON API via SmartRecruiters public endpoint.
  GET https://api.smartrecruiters.com/v1/companies/WoolworthsGroupLimited/postings
  Params: limit, offset, q (keyword), city, country

No HTML parsing needed — pure XHR/JSON.

Rate limit: 3 s (SmartRecruiters has rate limits; conservative is safe).
robots.txt: SmartRecruiters API endpoint is not listed in robots.txt (API, not crawlable page).

Response shape:
  { totalFound: N, content: [{ id, name, location.city, compensation.label, ... }] }
"""

from typing import Any, Dict, List

from app.scraper.base import BaseScraper

SR_API = "https://api.smartrecruiters.com/v1/companies/WoolworthsGroupLimited/postings"
BASE_JOB_URL = "https://careers.woolworthsgroup.com.au"


class WoolworthsAUScraper(BaseScraper):
    name = "woolworths_au"
    country = "AU"
    base_url = "https://careers.woolworthsgroup.com.au"
    needs_js = False
    rate_limit_seconds = 3.0
    check_robots = False  # hitting the JSON API, not the website

    PAGE_SIZE = 25
    MAX_PAGES = 2

    def build_search_urls(
        self, keywords: List[str], location: str, job_type: str
    ) -> List[str]:
        # We override run() for JSON APIs; this is only used for the HTML fallback.
        city = location.split(",")[0].strip() if location else ""
        kw = " ".join(keywords[:2])
        return [f"{self.base_url}/search/?q={kw}&location={city}"]

    async def run(
        self,
        keywords: List[str],
        location: str = "",
        job_type: str = "",
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Override run() to use JSON API instead of HTML parsing."""
        city = location.split(",")[0].strip() if location else ""
        kw = " ".join(keywords[:2])
        results = []

        for page in range(self.MAX_PAGES):
            if len(results) >= limit:
                break
            try:
                data = await self._fetch_json(
                    SR_API,
                    params={
                        "limit":   str(self.PAGE_SIZE),
                        "offset":  str(page * self.PAGE_SIZE),
                        "q":       kw,
                        "city":    city,
                        "country": "au",
                    },
                )
                items = data.get("content", []) if isinstance(data, dict) else []
                if not items:
                    break
                for item in items:
                    if len(results) >= limit:
                        break
                    raw = self._extract(item)
                    results.append(self.normalize(raw))
            except Exception as e:
                self.logger.error(f"Woolworths API page {page} failed: {e}")
                break

        return results

    @staticmethod
    def _extract(item: Dict) -> Dict[str, Any]:
        loc = item.get("location", {})
        comp = item.get("compensation", {}) or {}
        job_id = item.get("id", "")

        return {
            "title":      item.get("name", ""),
            "employer":   "Woolworths Group",
            "location":   f"{loc.get('city', '')}, {loc.get('regionCode', '')}".strip(", "),
            "pay_text":   comp.get("label", ""),
            "job_type":   item.get("typeOfEmployment", ""),
            "category":   "retail",
            "description": item.get("customField", [{}])[0].get("valueLabel", "") if item.get("customField") else "",
            "source_url": f"{BASE_JOB_URL}/job/{job_id}",
        }
