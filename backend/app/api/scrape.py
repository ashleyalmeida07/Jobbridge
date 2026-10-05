"""
Scrape API: admin-triggered scrape run + user-facing status endpoint.
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.api.auth import get_current_user

router = APIRouter()


from fastapi import BackgroundTasks

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
