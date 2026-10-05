"""
Scraper A: Seek.com.au (Australia's largest job board)

Technique: Static HTML with __NEXT_DATA__ JSON blob embedded in a <script> tag.
No JS execution needed — the full search results are serialised into the page.

Selectors / Data path (verified from network inspection):
  <script id="__NEXT_DATA__">{ props.pageProps.jobSearch.results: [...] }</script>

Each result object has:
  id, title, advertiser.description, salary.label, workType,
  teaser, locations[0].label, listingDate, jobAdType, solMetadata.jobId

Rate limit: 3 s between requests (well within polite limits).
robots.txt: seek.com.au/robots.txt allows /barista-jobs/ paths.
"""

import json
import re
from typing import Any, Dict, List
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper


class SeekAUScraper(BaseScraper):
    name = "seek_au"
    country = "AU"
    base_url = "https://www.seek.com.au"
    needs_js = False
    rate_limit_seconds = 3.0
    check_robots = True

    # Max pages to fetch per keyword set (each page has ~22 results)
    MAX_PAGES = 3

    def build_search_urls(
        self, keywords: List[str], location: str, job_type: str
    ) -> List[str]:
        # Build Seek-style search URLs
        # e.g. /barista-jobs/in-Melbourne-VIC?page=1&worktype=242
        WORK_TYPE_MAP = {
            "full_time":  "242",
            "part_time":  "243",
            "casual":     "244",
            "internship": "245",
        }
        kw_slug = "-".join(k.lower().replace(" ", "-") for k in keywords[:3])
        loc_slug = location.replace(", ", "-").replace(" ", "-")
        wt = WORK_TYPE_MAP.get(job_type, "")

        urls = []
        for page in range(1, self.MAX_PAGES + 1):
            path = f"/{quote_plus(kw_slug)}-jobs"
            if loc_slug:
                path += f"/in-{loc_slug}"
            qs = f"page={page}"
            if wt:
                qs += f"&worktype={wt}"
            urls.append(f"{self.base_url}{path}?{qs}")
        return urls

    def parse_list(self, html: str, url: str = "") -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Primary path: __NEXT_DATA__ JSON
        nd_tag = soup.find("script", id="__NEXT_DATA__")
        if nd_tag and nd_tag.string:
            try:
                data = json.loads(nd_tag.string)
                results = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("jobSearch", {})
                    .get("results", [])
                )
                for r in results:
                    jobs.append(self._parse_next_data_result(r))
                return jobs
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: HTML job cards (class-based)
        cards = soup.select('article[data-automation="normalJob"]')
        for card in cards:
            title_el  = card.select_one('[data-automation="jobTitle"]')
            emp_el    = card.select_one('[data-automation="jobCompany"]')
            loc_el    = card.select_one('[data-automation="jobLocation"]')
            pay_el    = card.select_one('[data-automation="jobSalary"]')
            link_el   = card.select_one('a[data-automation="jobTitle"]')
            type_el   = card.select_one('[data-automation="jobWorkType"]')
            date_el   = card.select_one('[data-automation="jobListingDate"]')

            source_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                source_url = href if href.startswith("http") else self.base_url + href

            jobs.append({
                "title":      title_el.get_text(strip=True) if title_el else "",
                "employer":   emp_el.get_text(strip=True) if emp_el else "",
                "location":   loc_el.get_text(strip=True) if loc_el else "",
                "pay_text":   pay_el.get_text(strip=True) if pay_el else "",
                "job_type":   type_el.get_text(strip=True) if type_el else "",
                "posted_text": date_el.get_text(strip=True) if date_el else "",
                "source_url": source_url,
            })

        return jobs

    @staticmethod
    def _parse_next_data_result(r: Dict) -> Dict[str, Any]:
        advertiser = r.get("advertiser", {})
        salary = r.get("salary", {})
        locations = r.get("locations", [{}])

        job_id = r.get("id") or r.get("solMetadata", {}).get("jobId", "")
        source_url = f"https://www.seek.com.au/job/{job_id}" if job_id else ""

        return {
            "title":       r.get("title", ""),
            "employer":    advertiser.get("description", ""),
            "location":    locations[0].get("label", "") if locations else "",
            "pay_text":    salary.get("label", ""),
            "job_type":    r.get("workType", ""),
            "posted_text": r.get("listingDate", ""),
            "description": r.get("teaser", ""),
            "source_url":  source_url,
        }
