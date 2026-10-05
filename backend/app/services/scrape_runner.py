"""
Scrape Runner v2 — executes a search plan end-to-end.

Pipeline per run:
  1. For each employer_task → discover_employers() via Overpass
  2. For each discovered employer with a website → find_careers_page()
  3. For each careers page found → extract_jobs() (generic extractor, 4 strategies)
  4. For each board_task → scrape_all_boards() (YAML-driven)
  5. Deduplication + upsert into jobs table
  6. ScrapeRun record per source (status, count, error)

Concurrency: max 2 employer pipelines in flight at once (asyncio.Semaphore).
One failing source never stops the run.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import Job, ScrapeRun, User
from app.scraper.board_scraper import scrape_all_boards
from app.scraper.careers_finder import find_careers_page
from app.scraper.discovery import discover_employers
from app.scraper.generic_extractor import extract_jobs
from app.services.search_plan import build_search_plan

logger = logging.getLogger(__name__)

# In-memory dictionary to store real-time scraping progress for the frontend
scrape_messages = {}

def set_scrape_msg(user_id: int, msg: str):
    scrape_messages[user_id] = msg

CONCURRENCY = 2   # max simultaneous employer pipelines
_sem = asyncio.Semaphore(CONCURRENCY)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _upsert_job(job: Dict[str, Any], db: AsyncSession) -> bool:
    """Insert job if not already present (dedupe on dedupe_hash or source_url). Returns True if new."""
    d_hash = job.get("dedupe_hash")
    src_url = job.get("source_url", "")

    if d_hash:
        r = await db.execute(select(Job).filter(Job.dedupe_hash == d_hash))
        if r.scalars().first():
            return False

    if src_url:
        r = await db.execute(select(Job).filter(Job.source_url == src_url))
        existing = r.scalars().first()
        if existing:
            # Refresh scraped_at even on duplicate
            existing.scraped_at = datetime.now(timezone.utc)
            await db.commit()
            return False

    row = Job(
        source=job.get("source", ""),
        source_url=src_url,
        title=job.get("title", ""),
        employer=job.get("employer", ""),
        location=job.get("location", ""),
        lat=job.get("lat"),
        lng=job.get("lng"),
        pay_text=job.get("pay_text"),
        pay_min=job.get("pay_min"),
        pay_max=job.get("pay_max"),
        pay_period=job.get("pay_period"),
        job_type=job.get("job_type", ""),
        category=job.get("category", ""),
        description=job.get("description", ""),
        contact_email=job.get("contact_email"),
        posted_at=job.get("posted_at"),
        scraped_at=datetime.now(timezone.utc),
        dedupe_hash=d_hash,
    )
    db.add(row)
    await db.commit()
    return True


async def _record_run(
    db: AsyncSession,
    source: str,
    country: str,
    keywords: List[str],
    location: str,
    status: str,
    jobs_found: int,
    jobs_saved: int,
    error_msg: Optional[str],
    started_at: datetime,
    user_id: Optional[int] = None,
) -> None:
    run = ScrapeRun(
        user_id=user_id,
        source=source,
        country=country,
        keywords=keywords,
        location=location,
        status=status,
        jobs_found=jobs_found,
        jobs_saved=jobs_saved,
        error_msg=error_msg,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()


# ── Employer pipeline ─────────────────────────────────────────────────────────

async def _run_employer_pipeline(
    employer,
    db: AsyncSession,
    user_id: Optional[int],
    country: str,
) -> int:
    """Run discovery → careers finder → extractor for one employer. Returns saved count."""
    async with _sem:
        website = employer.website or ""
        name = employer.name or ""
        if not website:
            return 0
            
        if user_id:
            set_scrape_msg(user_id, f"Analyzing local business: {name} ({website})...")

        started = datetime.now(timezone.utc)
        source_id = f"employer:{name.lower().replace(' ', '_')}"
        saved = 0

        try:
            careers_url = await find_careers_page(website, db)
            if not careers_url:
                if user_id:
                    set_scrape_msg(user_id, f"Skipped {name}: No careers page found.")
                await _record_run(
                    db, source_id, country, [], name,
                    "done", 0, 0, "No careers page found", started, user_id
                )
                return 0

            if user_id:
                set_scrape_msg(user_id, f"Crawling careers page: {careers_url}...")

            jobs = await extract_jobs(careers_url, employer_name=name)
            for job in jobs:
                job["source"] = source_id
                if await _upsert_job(job, db):
                    saved += 1
                    
            if user_id and saved > 0:
                set_scrape_msg(user_id, f"Found {saved} jobs at {name}!")

            await _record_run(
                db, source_id, country, [], name,
                "done", len(jobs), saved, None, started, user_id
            )
        except Exception as e:
            logger.error(f"Employer pipeline failed for {name}: {e}")
            if user_id:
                set_scrape_msg(user_id, f"Error crawling {name}: {e}")
            await _record_run(
                db, source_id, country, [], name,
                "failed", 0, 0, str(e), started, user_id
            )

        return saved


# ── Board pipeline ────────────────────────────────────────────────────────────

async def _run_board_task(
    task: Dict[str, Any],
    db: AsyncSession,
    user_id: Optional[int],
) -> int:
    started = datetime.now(timezone.utc)
    keywords = task["keywords"]
    city = task["city"]
    country = task["country"]
    saved = 0
    
    if user_id:
        set_scrape_msg(user_id, f"Scraping major job boards for {keywords[0]} roles in {city}...")

    try:
        jobs = await scrape_all_boards(keywords, city, country)
        
        if user_id:
            if len(jobs) > 0:
                set_scrape_msg(user_id, f"Found {len(jobs)} potential listings. Filtering for duplicates and visa constraints...")
            else:
                set_scrape_msg(user_id, f"No jobs returned from job boards for {keywords[0]}. They might be blocking automated requests right now.")

        for job in jobs:
            if await _upsert_job(job, db):
                saved += 1
                
        if user_id and saved > 0:
            set_scrape_msg(user_id, f"Successfully saved {saved} new matching jobs from job boards!")
        elif user_id and len(jobs) > 0:
            set_scrape_msg(user_id, f"No new jobs saved (all {len(jobs)} were duplicates or didn't meet criteria).")

        await _record_run(
            db, f"boards:{country}", country, keywords, city,
            "done", len(jobs), saved, None, started, user_id
        )
    except Exception as e:
        logger.error(f"Board task failed: {e}")
        if user_id:
            set_scrape_msg(user_id, f"Error reaching job boards: {e}. Moving on to next task...")
        await _record_run(
            db, f"boards:{country}", country, keywords, city,
            "failed", 0, 0, str(e), started, user_id
        )

    return saved


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_search_plan(user_id: int, db: AsyncSession) -> None:
    """
    Full pipeline for a user:
      1. Load profile → build search plan
      2. Run employer discovery tasks (Overpass → careers finder → extractor)
      3. Run board tasks (YAML boards)
      4. Update user.scrape_status and scrape_job_count
    """
    from sqlalchemy.orm import joinedload
    result = await db.execute(select(User).options(joinedload(User.profile)).filter(User.id == user_id))
    user = result.scalars().first()
    if not user or not user.profile:
        logger.warning(f"run_search_plan: no user/profile for id={user_id}")
        return

    user.scrape_status = "running"
    await db.commit()
    set_scrape_msg(user_id, "Building search plan based on your profile...")

    total_saved = 0
    try:
        plan = build_search_plan(user.profile)
        country = (user.profile.country or "AU").upper()

        # ── Employer discovery tasks ───────────────────────────────────────────
        employer_coros = []
        for task in plan["employer_tasks"]:
            set_scrape_msg(user_id, f"Scanning {task['categories'][0]}s near you using OSM data...")
            employers = await discover_employers(
                task["lat"], task["lng"], task["radius_km"],
                task["categories"], db
            )
            logger.info(f"Discovered {len(employers)} employers near user {user_id}")
            if user_id:
                set_scrape_msg(user_id, f"Discovered {len(employers)} local businesses to scan.")
                
            for employer in employers:
                employer_coros.append(
                    _run_employer_pipeline(employer, db, user_id, country)
                )

        # Run with concurrency cap
        if employer_coros:
            results = await asyncio.gather(*employer_coros, return_exceptions=True)
            for r in results:
                if isinstance(r, int):
                    total_saved += r
                elif isinstance(r, Exception):
                    logger.error(f"Employer coro error: {r}")

        # ── Board tasks ────────────────────────────────────────────────────────
        for task in plan["board_tasks"]:
            set_scrape_msg(user_id, f"Scraping {task['keywords'][0]} roles in {task['city']}...")
            saved = await _run_board_task(task, db, user_id)
            total_saved += saved

        set_scrape_msg(user_id, f"Found {total_saved} jobs!")

        user.scrape_status = "done"
        user.scrape_job_count = total_saved
    except Exception as e:
        logger.error(f"run_search_plan crashed for user {user_id}: {e}")
        user.scrape_status = "failed"

    await db.commit()
