"""
Scrape API: admin-triggered scrape run + user-facing status endpoint.
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, Profile
from app.api.auth import get_current_user

router = APIRouter()


from fastapi import BackgroundTasks

@router.post("/start")
async def start_scrape(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User-triggered: start scraping for the current user."""
    from app.services.scrape_runner import run_search_plan
    
    # Check if user has completed onboarding by checking their profile
    prof_result = await db.execute(select(Profile).filter(Profile.user_id == user.id))
    profile = prof_result.scalars().first()
    
    if not profile or not profile.onboarding_done:
        raise HTTPException(status_code=400, detail="Please complete onboarding first")
    
    # Reset scrape status
    user.scrape_status = "pending"
    user.scrape_job_count = 0
    await db.commit()
    
    # Queue background scrape
    async def _run_scrape_bg() -> None:
        """Create a fresh DB session for the background task."""
        from app.core.database import AsyncSessionLocal
        from app.services.telegram_bot import send_telegram_message
        
        async with AsyncSessionLocal() as db_bg:
            # Re-fetch user in new session to check telegram
            result = await db_bg.execute(select(User).filter(User.id == user.id))
            u = result.scalars().first()
            chat_id = u.telegram_chat_id if u else None
            
            if chat_id:
                await send_telegram_message(chat_id, "🔍 <b>Manual Job Scan</b> started from Dashboard...")
                
            await run_search_plan(user.id, db_bg)
            
            # Re-fetch after scan to get updated job count
            if chat_id:
                from app.models.models import Job
                import asyncio
                
                result = await db_bg.execute(select(User).filter(User.id == user.id))
                u = result.scalars().first()
                if u:
                    await send_telegram_message(chat_id, f"✅ <b>Scan Complete!</b>\n\nFound {u.scrape_job_count} matching opportunities. Check your dashboard to view them.")
                    if u.scrape_job_count > 0:
                        num_to_fetch = min(u.scrape_job_count, 5)
                        job_result = await db_bg.execute(select(Job).order_by(Job.scraped_at.desc()).limit(num_to_fetch))
                        new_jobs = job_result.scalars().all()
                        
                        for job in new_jobs:
                            msg_text = f"🏢 <b>{job.employer}</b>\n💼 <b>{job.title}</b>\n📍 {job.location}"
                            if job.pay_text:
                                msg_text += f"\n💰 {job.pay_text}"
                                
                            markup = {
                                "inline_keyboard": [
                                    [{"text": "Apply on Company Site", "url": job.source_url}]
                                ]
                            } if job.source_url else None
                            
                            await send_telegram_message(chat_id, msg_text, reply_markup=markup)
                            await asyncio.sleep(0.5)
    
    background_tasks.add_task(_run_scrape_bg)
    
    return {"status": "started", "message": "Scraping started. Check status for updates."}


@router.post("/run")
async def run_scrapers(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_admin_key: str = Header(...)
):
    """Admin-triggered: run all registered scrapers for all users."""
    if x_admin_key != settings.SCRAPER_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    # Trigger background scrape for all users with profiles
    from app.services.scrape_runner import run_search_plan
    
    result = await db.execute(select(User).filter(User.profile.has()))
    users = result.scalars().all()
    
    for u in users:
        # Note: in a real production system, use Celery/Redis for queueing
        background_tasks.add_task(run_search_plan, u.id, db)

    return {"status": "started", "message": f"Scrapers triggered for {len(users)} users."}


from app.services.scrape_runner import scrape_messages

@router.get("/status")
async def scrape_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current scrape status, job count, and live progress message for the logged-in user."""
    result = await db.execute(select(User).filter(User.id == user.id))
    fresh_user = result.scalars().first()
    return {
        "status": fresh_user.scrape_status or "pending",
        "job_count": fresh_user.scrape_job_count or 0,
        "message": scrape_messages.get(user.id, "Finding jobs for you..."),
    }
