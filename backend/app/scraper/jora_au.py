"""
Scraper D: Jora.com.au — student and part-time job board

Technique: Static HTML with clearly structured job cards.
Jora is owned by SEEK and allows crawling per their robots.txt.

URL pattern: https://au.jora.com/jobs?q={keywords}&l={location}&jt=parttime&p={page}

HTML structure (verified):
  <article class="job-card"> 
    <a class="job-link" href="/job/{id}">
      <h2 class="job-title">...</h2>
      <p class="company">...</p>
      <p class="location">...</p>
      <p class="listing-work-type">...</p>
      <p class="date">...</p>
    </a>
    <p class="salary-info">...</p>
  </article>

Rate limit: 3 s.
robots.txt: Allows /jobs paths.
"""

from typing import Any, Dict, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper

BASE = "https://au.jora.com"


class JoraAUScraper(BaseScraper):
    """
    Scraper D: Jora.com.au — campus/student/part-time job board.
    Static HTML scraper. Jora allows crawling (generous robots.txt).
    """
    name = "jora_au"
    country = "AU"
    base_url = BASE
    needs_js = False
    rate_limit_seconds = 3.0
    check_robots = True

    MAX_PAGES = 3

    # Work type param map
    _JT_MAP = {
        "part_time":  "parttime",
        "casual":     "casual",
        "full_time":  "fulltime",
        "internship": "internship",
    }

    def build_search_urls(
        self, keywords: List[str], location: str, job_type: str
    ) -> List[str]:
        kw = quote_plus(" ".join(keywords[:3]))
        loc = quote_plus(location.split(",")[0].strip() if location else "")
        jt = self._JT_MAP.get(job_type, "parttime")
        urls = []
        for page in range(1, self.MAX_PAGES + 1):
            urls.append(f"{BASE}/jobs?q={kw}&l={loc}&jt={jt}&p={page}")
        return urls

    def parse_list(self, html: str, url: str = "") -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        cards = soup.select("article.job-card") or soup.select("div.job-card")
        if not cards:
            # Fallback: any article with a job-like link
            cards = soup.select("article") or soup.select('[class*="result"]')

        for card in cards:
            title_el  = card.select_one("h2") or card.select_one("h3") or card.select_one(".job-title")
            emp_el    = card.select_one(".company") or card.select_one("[class*='company']")
            loc_el    = card.select_one(".location") or card.select_one("[class*='location']")
            pay_el    = card.select_one(".salary-info") or card.select_one("[class*='salary']")
            type_el   = card.select_one(".listing-work-type") or card.select_one("[class*='work-type']")
            date_el   = card.select_one(".date") or card.select_one("time")
            link_el   = card.select_one("a.job-link") or card.select_one("a[href*='/job/']") or card.select_one("a")

            source_url = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                source_url = href if href.startswith("http") else BASE + href

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue  # skip non-job cards

            jobs.append({
                "title":       title,
                "employer":    emp_el.get_text(strip=True) if emp_el else "",
                "location":    loc_el.get_text(strip=True) if loc_el else "",
                "pay_text":    pay_el.get_text(strip=True) if pay_el else "",
                "job_type":    type_el.get_text(strip=True) if type_el else "",
                "posted_text": date_el.get_text(strip=True) if date_el else "",
                "source_url":  source_url,
            })

        return jobs
