"""
Jobs API: fetch jobs ranked by profile match.
Ranking: matching job type > within hour cap > within commute radius.
"""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.models import User, Job, Profile
from app.api.auth import get_current_user

router = APIRouter()


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _rank_job(job: Job, profile: Profile) -> int:
    """
    Lower score = better match. 0 is perfect.
    +0 if job_type matches looking_for
    +10 if not in looking_for
    +0 if pay_max <= hour_cap_term (or no cap)
    +5 if above cap
    +0 if within commute radius
    +5 if outside commute radius
    """
    score = 0
    looking = profile.looking_for or []
    type_map = {
        "internship_domain": "internship",
        "fulltime_domain": "full_time",
        "parttime_domain": "part_time",
        "parttime_any": "casual",
    }
    preferred_types = {type_map.get(lt) for lt in looking if type_map.get(lt)}

    if job.job_type not in preferred_types:
        score += 10

    # Hour cap check (simple: flag if pay_max implies more hours; we just use job_type proxy)
    cap = profile.hour_cap_term or profile.weekly_hour_cap
    if cap and job.job_type == "full_time":
        score += 5  # Full-time implies >cap hours during term

    # Commute radius
    if profile.lat and profile.lng and job.lat and job.lng:
        dist = _haversine_km(profile.lat, profile.lng, job.lat, job.lng)
        radius = profile.commute_radius_km or 10
        if dist > radius:
            score += 5

    return score


@router.get("")
async def list_jobs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    job_type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return jobs ranked by profile match."""
    # Load profile
    prof_result = await db.execute(select(Profile).filter(Profile.user_id == user.id))
    profile = prof_result.scalars().first()

    # Fetch all jobs (TODO: add DB-level filtering for large datasets)
    query = select(Job)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    result = await db.execute(query)
    jobs: List[Job] = result.scalars().all()

    if profile:
        jobs.sort(key=lambda j: _rank_job(j, profile))

    # Paginate
    paginated = jobs[offset: offset + limit]

    return {
        "total": len(jobs),
        "items": [
            {
                "id": j.id,
                "title": j.title,
                "employer": j.employer,
                "location": j.location,
                "job_type": j.job_type,
                "pay_text": j.pay_text,
                "pay_min": j.pay_min,
                "pay_max": j.pay_max,
                "source": j.source,
                "source_url": j.source_url,
                "description": j.description,
                "contact_email": j.contact_email,
                "posted_at": j.posted_at.isoformat() if j.posted_at else None,
                "scraped_at": j.scraped_at.isoformat() if j.scraped_at else None,
            }
            for j in paginated
        ],
    }
