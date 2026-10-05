"""
Sample scraper for Australia — returns placeholder jobs with realistic structure.
Replace parse() with real HTML parsing once the target site is confirmed.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from app.scraper.base import BaseScraper


SAMPLE_JOBS_AU = [
    {"title": "Barista", "employer": "The Coffee Club", "location": "Melbourne, VIC",
     "pay_text": "$25–$28/hr", "pay_min": 25.0, "pay_max": 28.0, "job_type": "casual",
     "description": "Serve great coffee and friendly service at our busy café.", "contact_email": ""},
    {"title": "Retail Sales Assistant", "employer": "Cotton On", "location": "Sydney, NSW",
     "pay_text": "$24/hr", "pay_min": 24.0, "pay_max": 24.0, "job_type": "part_time",
     "description": "Assist customers, manage stock, and process sales.", "contact_email": ""},
    {"title": "Software Engineer Intern", "employer": "Atlassian", "location": "Sydney, NSW",
     "pay_text": "$35/hr", "pay_min": 35.0, "pay_max": 40.0, "job_type": "internship",
     "description": "12-week internship building features across our cloud platform.", "contact_email": "careers@atlassian.com"},
    {"title": "Warehouse Picker/Packer", "employer": "Amazon Fulfillment", "location": "Melbourne, VIC",
     "pay_text": "$28/hr", "pay_min": 28.0, "pay_max": 28.0, "job_type": "casual",
     "description": "Pick, pack, and ship customer orders in our fulfilment centre.", "contact_email": ""},
    {"title": "Graduate Business Analyst", "employer": "Deloitte", "location": "Brisbane, QLD",
     "pay_text": "$65,000–$75,000/yr", "pay_min": 65000.0, "pay_max": 75000.0, "job_type": "full_time",
     "description": "Join our graduate program and work with leading clients.", "contact_email": "grad@deloitte.com.au"},
    {"title": "Food Delivery Driver", "employer": "DoorDash", "location": "Adelaide, SA",
     "pay_text": "$20–$30/hr", "pay_min": 20.0, "pay_max": 30.0, "job_type": "casual",
     "description": "Flexible food delivery — set your own hours.", "contact_email": ""},
    {"title": "Private Maths Tutor", "employer": "Self-employed", "location": "Online / Any city",
     "pay_text": "$30–$50/hr", "pay_min": 30.0, "pay_max": 50.0, "job_type": "casual",
     "description": "Help high school and university students with mathematics.", "contact_email": ""},
    {"title": "Campus Bookshop Assistant", "employer": "University of Melbourne", "location": "Melbourne, VIC",
     "pay_text": "$26/hr", "pay_min": 26.0, "pay_max": 26.0, "job_type": "part_time",
     "description": "Assist students finding textbooks and campus resources.", "contact_email": "hr@unimelb.edu.au"},
]


class SampleAUScraper(BaseScraper):
    name = "sample_au"
    country = "AU"
    # Skips actual HTTP fetch — pure sample data
    BASE_URL = "https://example-jobs.com.au"

    async def fetch(self, url: str) -> str:
        return ""  # No real fetch for sample

    def parse(self, html: str) -> List[Dict[str, Any]]:
        # Return a shuffled subset to simulate varying results
        return random.sample(SAMPLE_JOBS_AU, k=min(5, len(SAMPLE_JOBS_AU)))

    async def run(self, keywords: List[str] = None, location: str = "", job_type: str = "") -> List[Dict[str, Any]]:
        """Run scraper and return normalised job dicts."""
        raw_jobs = self.parse("")
        normalised = []
        for j in raw_jobs:
            j["source"] = self.name
            j["source_url"] = f"{self.BASE_URL}/jobs/{j['title'].replace(' ', '-').lower()}-{random.randint(1000,9999)}"
            j["posted_at"] = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7))).isoformat()
            normalised.append(self.normalize(j))
        return normalised
