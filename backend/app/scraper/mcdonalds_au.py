"""
Scraper B: McDonald's Australia careers page

Technique: Static HTML — McDonald's AU uses a Phenom People / iCIMS ATS.
URL pattern: https://careers.mcdonalds.com.au/search-jobs/results?ActiveFacetID=0&CurrentPage={n}&RecordsPerPage=25&Distance=50&RadiusUnitType=0&Keywords={kw}&Location={loc}

The response is either:
  - A full HTML page (older ATS)
  - A JSON-like partial render

We fall back gracefully on missing selectors.

Rate limit: 4 s (conservative for a brand career site).
robots.txt: Allows /search-jobs and /search-jobs/results.
"""

import re
from typing import Any, Dict, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper


class McDonaldsAUScraper(BaseScraper):
    name = "mcdonalds_au"
    country = "AU"
    base_url = "https://careers.mcdonalds.com.au"
    needs_js = False
    rate_limit_seconds = 4.0
    check_robots = True

    MAX_PAGES = 2

    def build_search_urls(
        self, keywords: List[str], location: str, job_type: str
    ) -> List[str]:
        kw = quote_plus(" ".join(keywords[:2]))
        city = location.split(",")[0].strip() if location else ""
        loc = quote_plus(city)
        urls = []
        for page in range(1, self.MAX_PAGES + 1):
            urls.append(
                f"{self.base_url}/search-jobs/results"
                f"?ActiveFacetID=0&CurrentPage={page}&RecordsPerPage=25"
                f"&Distance=50&RadiusUnitType=0&Keywords={kw}&Location={loc}"
            )
        return urls

    def parse_list(self, html: str, url: str = "") -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # iCIMS / Phenom ATS selectors (common patterns)
        cards = (
            soup.select("li.job-item")
            or soup.select("article.job-listing")
            or soup.select("div.search-result-item")
            or soup.select("tr.data-row")
        )

        if not cards:
            # Fallback: look for any job title links
            links = soup.select('a[href*="/jobs/"]') or soup.select('a[class*="job"]')
            for link in links:
                href = link.get("href", "")
                source_url = href if href.startswith("http") else self.base_url + href
                title = link.get_text(strip=True)
                if title:
                    jobs.append({
                        "title":      title,
                        "employer":   "McDonald's Australia",
                        "location":   "",
                        "pay_text":   "",
                        "job_type":   "casual",
                        "source_url": source_url,
                    })
            return jobs

        for card in cards:
            title_el = (
                card.select_one(".job-title")
                or card.select_one("h3")
                or card.select_one("h2")
                or card.select_one("a")
            )
            loc_el = card.select_one(".job-location") or card.select_one(".location")
            link_el = card.select_one("a")

            source_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                source_url = href if href.startswith("http") else self.base_url + href

            jobs.append({
                "title":      title_el.get_text(strip=True) if title_el else "Crew Member",
                "employer":   "McDonald's Australia",
                "location":   loc_el.get_text(strip=True) if loc_el else "",
                "pay_text":   "",   # McD's doesn't publish pay publicly
                "job_type":   "casual",
                "category":   "food_cafe",
                "source_url": source_url,
            })

        return jobs
