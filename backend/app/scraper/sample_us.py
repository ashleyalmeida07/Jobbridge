"""
Sample US scraper — returns placeholder jobs for the US market.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from app.scraper.base import BaseScraper


SAMPLE_JOBS_US = [
    {"title": "Software Engineering Intern", "employer": "Google", "location": "Mountain View, CA",
     "pay_text": "$50/hr", "pay_min": 50.0, "pay_max": 55.0, "job_type": "internship",
     "description": "Work on real Google products with a team of engineers.", "contact_email": "intern@google.com"},
    {"title": "Barista", "employer": "Starbucks", "location": "Seattle, WA",
     "pay_text": "$17–$20/hr", "pay_min": 17.0, "pay_max": 20.0, "job_type": "part_time",
     "description": "Create the Starbucks experience for our customers.", "contact_email": ""},
    {"title": "Crew Member", "employer": "McDonald's", "location": "New York, NY",
     "pay_text": "$16/hr", "pay_min": 16.0, "pay_max": 16.0, "job_type": "casual",
     "description": "Flexible hours serving food and helping customers.", "contact_email": ""},
    {"title": "Data Analyst Intern", "employer": "Meta", "location": "Menlo Park, CA",
     "pay_text": "$45/hr", "pay_min": 45.0, "pay_max": 50.0, "job_type": "internship",
     "description": "Analyse product data to drive decisions.", "contact_email": ""},
    {"title": "Campus Library Assistant", "employer": "MIT", "location": "Cambridge, MA",
     "pay_text": "$15/hr", "pay_min": 15.0, "pay_max": 15.0, "job_type": "part_time",
     "description": "Support students and researchers in the library.", "contact_email": "hr@mit.edu"},
]


class SampleUSScraper(BaseScraper):
    name = "sample_us"
    country = "US"
    BASE_URL = "https://example-jobs.com"

    async def fetch(self, url: str) -> str:
        return ""

    def parse(self, html: str) -> List[Dict[str, Any]]:
        return random.sample(SAMPLE_JOBS_US, k=min(4, len(SAMPLE_JOBS_US)))

    async def run(self, keywords: List[str] = None, location: str = "", job_type: str = "") -> List[Dict[str, Any]]:
        raw_jobs = self.parse("")
        normalised = []
        for j in raw_jobs:
            j["source"] = self.name
            j["source_url"] = f"{self.BASE_URL}/jobs/{j['title'].replace(' ', '-').lower()}-{random.randint(1000,9999)}"
            j["posted_at"] = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))).isoformat()
            normalised.append(self.normalize(j))
        return normalised
