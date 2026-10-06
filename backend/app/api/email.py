"""
Cold Email API: manage email templates, schedule, and queue.

Endpoints:
  GET  /email/settings      — get user's email settings (daily limit, schedule)
  PUT  /email/settings      — update settings
  GET  /email/templates     — get user's email templates
  PUT  /email/templates     — save/update a template
  GET  /email/queue         — list queued/sent emails
  POST /email/queue         — queue a batch of cold emails
  POST /email/send-now      — send one email immediately (test)
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models.models import User, Job, EmailQueue, DailyQuota
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class EmailSettings(BaseModel):
    daily_limit: int = 10
    send_hour: int = 9          # hour of day (0-23) in user's timezone
    send_minute: int = 0
    auto_send: bool = False     # whether n8n/cron should auto-send
    default_subject: str = "Regarding open positions at {company}"
    default_body: str = (
        "Hi {company} Team,\n\n"
        "I'm a student currently studying in {city} and I noticed your "
        "company has open positions. I'm reaching out to express my interest "
        "in the {job_title} role.\n\n"
        "I'd love the opportunity to discuss how my skills and enthusiasm "
        "could contribute to your team.\n\n"
        "Best regards,\n{user_name}"
    )

class EmailQueueItem(BaseModel):
    job_id: int
    to_email: str
    subject: str
    body: str

class QueueBatchRequest(BaseModel):
    items: List[EmailQueueItem]

class EmailQueueResponse(BaseModel):
    id: int
    job_id: int
    subject: str
    body: str
    status: str
    scheduled_at: Optional[str]
    sent_at: Optional[str]
    job_title: Optional[str] = None
    employer: Optional[str] = None
    contact_email: Optional[str] = None


# ── In-memory settings store (per-user) ──────────────────────────────────────
# In production, persist these in a DB table. For now, module-level dict.

_user_email_settings: dict[int, dict] = {}


def _get_settings(user_id: int) -> dict:
    if user_id not in _user_email_settings:
        defaults = EmailSettings()
        _user_email_settings[user_id] = defaults.model_dump()
    return _user_email_settings[user_id]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_email_settings(user: User = Depends(get_current_user)):
    return _get_settings(user.id)


@router.put("/settings")
async def update_email_settings(
    settings: EmailSettings,
    user: User = Depends(get_current_user),
):
    _user_email_settings[user.id] = settings.model_dump()
    return {"ok": True, **_user_email_settings[user.id]}


@router.get("/templates")
async def get_templates(user: User = Depends(get_current_user)):
    s = _get_settings(user.id)
    return {
        "subject": s["default_subject"],
        "body": s["default_body"],
    }


@router.put("/templates")
async def update_templates(
    subject: str = "",
    body: str = "",
    user: User = Depends(get_current_user),
):
    s = _get_settings(user.id)
    if subject:
        s["default_subject"] = subject
    if body:
        s["default_body"] = body
    return {"ok": True, "subject": s["default_subject"], "body": s["default_body"]}


@router.get("/queue")
async def list_queue(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List queued/sent/failed emails for the current user."""
    query = select(EmailQueue).filter(EmailQueue.user_id == user.id)
    if status:
        query = query.filter(EmailQueue.status == status)
    query = query.order_by(EmailQueue.id.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.scalars().all()
    
    items = []
    for eq in rows:
        # Load associated job info
        job_result = await db.execute(select(Job).filter(Job.id == eq.job_id))
        job = job_result.scalars().first()
        items.append({
            "id": eq.id,
            "job_id": eq.job_id,
            "subject": eq.subject,
            "body": eq.body,
            "status": eq.status,
            "scheduled_at": eq.scheduled_at.isoformat() if eq.scheduled_at else None,
            "sent_at": eq.sent_at.isoformat() if eq.sent_at else None,
            "job_title": job.title if job else None,
            "employer": job.employer if job else None,
            "contact_email": job.contact_email if job else None,
        })
    
    return {"total": len(items), "items": items}


@router.post("/queue")
async def queue_batch(
    req: QueueBatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue a batch of emails to be sent later."""
    settings = _get_settings(user.id)
    
    queued = 0
    for item in req.items:
        eq = EmailQueue(
            user_id=user.id,
            job_id=item.job_id,
            subject=item.subject,
            body=item.body,
            status="queued",
            scheduled_at=datetime.now(timezone.utc),
        )
        db.add(eq)
        queued += 1
    
    await db.commit()
    return {"queued": queued}


@router.get("/contacts")
async def list_contacts(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List jobs that have a contact_email — these are cold email targets."""
    result = await db.execute(
        select(Job)
        .filter(Job.contact_email.isnot(None))
        .filter(Job.contact_email != "")
        .order_by(Job.scraped_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    return {
        "total": len(jobs),
        "items": [
            {
                "id": j.id,
                "title": j.title,
                "employer": j.employer,
                "location": j.location,
                "contact_email": j.contact_email,
                "source": j.source,
                "source_url": j.source_url,
            }
            for j in jobs
        ],
    }


@router.get("/stats")
async def email_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return email sending stats for the dashboard."""
    total_q = await db.execute(
        select(func.count(EmailQueue.id)).filter(EmailQueue.user_id == user.id)
    )
    total = total_q.scalar() or 0
    
    sent_q = await db.execute(
        select(func.count(EmailQueue.id)).filter(
            EmailQueue.user_id == user.id,
            EmailQueue.status == "sent"
        )
    )
    sent = sent_q.scalar() or 0
    
    pending_q = await db.execute(
        select(func.count(EmailQueue.id)).filter(
            EmailQueue.user_id == user.id,
            EmailQueue.status == "queued"
        )
    )
    pending = pending_q.scalar() or 0
    
    contacts_q = await db.execute(
        select(func.count(Job.id)).filter(
            Job.contact_email.isnot(None),
            Job.contact_email != ""
        )
    )
    contacts = contacts_q.scalar() or 0
    
    return {
        "total_queued": total,
        "total_sent": sent,
        "total_pending": pending,
        "total_contacts": contacts,
    }


class UpdateStatusRequest(BaseModel):
    status: str

@router.put("/queue/{item_id}/status")
async def update_email_status(
    item_id: int,
    req: UpdateStatusRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a queued email (e.g. called by n8n after sending)."""
    result = await db.execute(select(EmailQueue).filter(EmailQueue.id == item_id, EmailQueue.user_id == user.id))
    eq = result.scalars().first()
    if not eq:
        raise HTTPException(status_code=404, detail="Item not found")
        
    eq.status = req.status
    if req.status == "sent":
        eq.sent_at = datetime.now(timezone.utc)
        
    await db.commit()
    return {"ok": True, "status": eq.status}
