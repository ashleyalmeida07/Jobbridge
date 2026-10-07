# JobBridge - GradGuide Assignment

Welcome to **JobBridge**, a dedicated job discovery platform tailored specifically for international students. JobBridge aggregates part-time, casual, and internship roles while taking into account the unique constraints international students face, such as visa restrictions, work-hour caps, and the need for hyper-local casual work.

[INSERT YOUR VIDEO WALKTHROUGH LINK HERE]

---

## 🛠️ The Scraper Implementation

In strict adherence to the assignment requirements, **no job board APIs or LLM auto-scraping SaaS tools were used**. The scraper was built entirely from scratch in Python.

**How it works:**
1. **Direct HTML Parsing:** The scraper uses `httpx` to make polite, rate-limited HTTP requests and `BeautifulSoup4` to parse the raw HTML.
2. **Modular Architecture:** The system uses a `BaseScraper` class. We built dedicated implementations for major hubs (like Seek) and direct employer career portals (like Woolworths and McDonald's).
3. **Dynamic Rendering Fallback:** For websites heavily reliant on client-side React/Vue rendering (where `httpx` returns empty DOMs), the scraper employs a lazy-loaded `playwright` headless Chromium instance to wait for the DOM to settle before extracting the HTML.
4. **Resilience & Politeness:** We implemented custom retry mechanisms, exponential backoff, user-agent rotation, and strict concurrency limits to avoid overwhelming the target servers.
5. **Standardization:** Extracted data (Title, Employer, Pay, Location, Job Type, etc.) is cleansed and mapped into a normalized PostgreSQL `Job` schema. Duplicate prevention is enforced via cryptographic hashing of the job URL and employer.

---

## ✨ The 3 Custom Features & Rationale

When designing JobBridge, we focused on the specific pain points international students experience when arriving in a new country.

### 1. Visa & Work-Hour Awareness Analysis
**The Problem:** International students often have strict visa constraints (e.g., a 48-hour per fortnight cap). Standard job boards bury working hour expectations and visa/sponsorship requirements deep within blocks of text, leading students to waste time applying for jobs they legally cannot accept.
**The Solution:** During the scraping pipeline, the backend automatically analyzes the raw job description to extract and flag:
- Whether work rights/citizenship are strictly required.
- If sponsorship is available.
- The estimated weekly hours.
**Why it matters:** It acts as a safety net, ensuring international students don't accidentally breach their visa conditions or waste energy on exclusionary listings.

### 2. Hyper-Local Campus Proximity Discovery
**The Problem:** Most international students rely on local cafes, retail stores, and delivery gigs for their first jobs. These "everyday jobs" are rarely posted on expensive, massive job boards like LinkedIn.
**The Solution:** The app features a geographic discovery engine. By taking the student's campus location and a search radius, JobBridge queries OpenStreetMap (OSM) nodes to discover local businesses (e.g., local cafes, restaurants). It then programmatically finds their career pages and scrapes them.
**Why it matters:** It unlocks the "hidden job market" of local, walk-in, and casual jobs that are critical for international student survival but entirely missed by traditional job aggregators.

### 3. Automated Daily Telegram Alerts
**The Problem:** Part-time and casual roles in retail and hospitality fill up incredibly quickly. International students, who are busy with studies, don't have the time to constantly refresh job boards.
**The Solution:** JobBridge features a personalized cron-job that runs every morning at 9:00 AM. It finds new jobs matching the student's profile, filters out previously seen duplicates, and sends a beautifully formatted summary directly to their Telegram app with an inline "Apply" button.
**Why it matters:** It meets the students where they already are (messaging apps) and gives them a competitive advantage by allowing them to apply the moment a casual job opens up.

---

## 🚀 Running the App Locally

### Backend Setup (FastAPI & PostgreSQL)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
# Requires a .env file with DATABASE_URL and GOOGLE_CLIENT_ID
uvicorn app.main:app --reload
```

### Frontend Setup (Next.js & Tailwind)
```bash
cd frontend
npm install
npm run dev
```
