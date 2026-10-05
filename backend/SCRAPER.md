# SCRAPER.md — JobBridge Scraper Architecture

## Overview

JobBridge uses **location-driven discovery** — it finds real employers near the user using OpenStreetMap data rather than scraping fixed lists of brands. No employer names are hardcoded anywhere in the Python code.

---

## Architecture

```
User Profile (lat, lng, radius, categories, domain)
        │
        ▼
┌─────────────────────────┐
│  search_plan.py         │  Translates profile → employer_tasks + board_tasks
└────────────┬────────────┘
             │
     ┌───────┴────────────────────┐
     │                            │
     ▼                            ▼
┌─────────────┐          ┌────────────────┐
│ Employer    │          │ Board Scraper  │
│ Discovery   │          │ (boards.yaml)  │
│ Pipeline    │          └───────┬────────┘
└──────┬──────┘                  │
       │                         │ JSON-LD or CSS selectors
       ▼                         │
┌──────────────┐                 │
│ discovery.py │  Overpass API   │
│ OSM query    │                 │
└──────┬───────┘                 │
       │                         │
       ▼                         │
┌──────────────┐                 │
│ careers_     │  Finds careers  │
│ finder.py    │  page URL       │
└──────┬───────┘                 │
       │                         │
       ▼                         │
┌──────────────┐                 │
│ generic_     │  Extracts jobs  │
│ extractor.py │  (4 strategies) │
└──────┬───────┘                 │
       │                         │
       └──────────┬──────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ scrape_runner  │  Deduplicate + upsert jobs
         │ .py            │  Record ScrapeRun per source
         └────────────────┘
```

---

## A. Employer Discovery (`app/scraper/discovery.py`)

**Method**: Overpass API (OpenStreetMap)  
**Technique**: HTTP POST to `overpass-api.de/api/interpreter` with QL query  
**Rate limit**: 1 request/second, hard-coded via monotonic timer  
**User-Agent**: `JobBridge/1.0 (student job discovery; +https://github.com/jobbridge)`  
**Cache**: `discovered_employers` DB table — 7 days per 0.01° tile (≈1 km grid)  

**OSM tag mapping** (configured in `config/osm_categories.yaml`):
| Category | OSM Tags |
|---|---|
| food_cafe | `amenity=cafe`, `amenity=fast_food`, `amenity=restaurant` |
| retail | `shop=supermarket`, `shop=clothes`, `shop=department_store` |
| warehouse | `building=warehouse`, `office=logistics` |
| campus | `amenity=university`, `amenity=library` |
| tutoring | `amenity=school`, `amenity=college` |

**Known limitations**: Overpass can be slow (5–30s) and has usage quotas. The 7-day cache significantly reduces API calls for the same area.

---

## B. Careers Page Finder (`app/scraper/careers_finder.py`)

**Strategies** (in order):
1. **Homepage link scan** — fetch homepage, find `<a>` tags matching career keywords. Confidence 1.0 for text match, 0.7 for href match.
2. **Common paths** — try `/careers`, `/jobs`, `/join-us`, `/hiring`, etc. Returns if page title or first 2000 chars match career keywords.
3. **sitemap.xml** — fetch sitemap, find `<loc>` entries with career keyword in URL.
4. **Negative cache** — cache 14 days if no page found.

**Cache**: `careers_page_cache` DB table. Positive results: 7 days. Negative: 14 days.

**Known limitations**: Some employers (e.g. those using third-party ATSs like WorkDay, Greenhouse) may redirect the careers page to an external domain — the scraper follows these successfully.

---

## C. Generic Job Extractor (`app/scraper/generic_extractor.py`)

**Strategies** (in order, stops on first success):

### 1. JSON-LD (schema.org/JobPosting)
- Parses `<script type="application/ld+json">` blocks
- Handles single object, array, and `@graph` forms
- Fields: title, hiringOrganization, jobLocation, baseSalary, employmentType, datePosted, url
- **No HTML parsing needed**; highest fidelity

### 2. Embedded JSON (`__NEXT_DATA__`, window state)
- Regex extracts JSON blobs from `<script>` tags
- Recursively walks the object tree looking for arrays of job-like dicts
- Works for Next.js, Nuxt.js, and custom SPA apps

### 3. Heuristic HTML
- Finds block elements (`article`, `section`, `li`, `div`) containing:
  - A heading (`h2`–`h4`)  
  - At least one link  
  - Job signal text (`apply`, `full-time`, `per hour`, etc.)
- Follows up to 20 detail links to enrich description/location/pay

### 4. Playwright Retry (needs_js fallback)
- Only triggered if strategies 1–3 return no results
- Launches headless Chromium, blocks images/fonts/media
- Re-applies strategies 1–3 on the rendered DOM
- Requires `playwright install chromium` to be run once

---

## D. Job Boards (`app/scraper/board_scraper.py` + `config/boards.yaml`)

**Configured boards for AU**: Jora, Adzuna, CareerOne  
**Adding a new board**: add a YAML entry only — no Python changes

**Per-board strategy**:
1. If `json_ld: true` → try JSON-LD from search results page first
2. Fall back to CSS selectors defined in the board's `selectors` block
3. Normalise via shared `normalise.py` pipeline

**Rate limits** (configured per board in YAML):
| Board | Rate limit | Max pages |
|---|---|---|
| jora_au | 3s | 3 |
| adzuna_au | 4s | 2 |
| careerone_au | 3s | 2 |

---

## E. Normalisation (`app/scraper/normalise.py`)

All normalisation is rule-based. No AI/LLM used.

| Field | Method |
|---|---|
| pay_min, pay_max, pay_period | Regex: ranges, currency symbols, `/hr`, `/yr`, `p.a.` |
| job_type | Keyword rules: `part-time`, `casual`, `intern`, `full-time` |
| category | Keyword rules: 7 categories (food_cafe, retail, delivery, tutoring, warehouse, campus, professional) |
| posted_at | Handles: `today`, `3 days ago`, `1 week ago`, ISO dates, `DD MMM YYYY` |
| contact_email | Regex on description and contact sections |
| dedupe_hash | `SHA-256(employer + title + location)[0:40]` — lowercase, trimmed |

---

## F. Runner (`app/services/scrape_runner.py`)

- Concurrency cap: `asyncio.Semaphore(2)` — max 2 employer pipelines at once
- Each source wrapped in `try/except` — one failure never stops the run
- Per-source `ScrapeRun` record: status, jobs_found, jobs_saved, error_msg, timing
- Upserts on `dedupe_hash` conflict; refreshes `scraped_at` on duplicate URL

---

## G. CLI Usage

```bash
# Activate venv
cd backend && venv\Scripts\activate   # Windows
source venv/bin/activate               # Linux/macOS

# List configured boards
python -m app.scraper.cli boards --country AU

# Scrape all AU boards with a keyword
python -m app.scraper.cli run --country AU --keyword "barista" --city "Melbourne" --limit 30

# Scrape one specific board
python -m app.scraper.cli run --source jora_au --keyword "warehouse" --city "Sydney"

# Discover employers near a location
python -m app.scraper.cli discover --lat -37.81 --lng 144.96 --radius 10 --categories food_cafe retail

# Find careers page for a website
python -m app.scraper.cli find-careers https://www.starbucks.com.au

# Extract jobs from a URL
python -m app.scraper.cli extract https://careers.example.com.au/jobs
```

---

## H. robots.txt Policy

- All scrapers check `robots.txt` via Python's `urllib.robotparser` before fetching.
- Disallowed paths are skipped and logged at `WARNING` level.
- Board and discovery API endpoints have `check_robots=False` (hitting JSON APIs, not crawlable pages).
- The Overpass API does not have robots.txt restrictions.

---

## I. Adding a New Country

1. Add visa types and defaults to `app/core/country_config.py`
2. Add boards to `config/boards.yaml` under the new country code
3. No other Python changes needed — everything else is data-driven.
