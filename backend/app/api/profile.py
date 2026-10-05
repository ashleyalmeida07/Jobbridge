"""
Profile API: per-step onboarding saves + /complete to trigger scraping.
"""
import os
from typing import Union
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.models import User, Profile
from app.api.auth import get_current_user
from app.schemas.profile import (
    ProfileResponse, ProfileUpdate,
    Step1Schema, Step2Schema, Step3Schema, Step4Schema, Step5Schema,
)
from app.services.geocode import geocode
from app.services.scrape_runner import run_search_plan

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Helper ──────────────────────────────────────────────────────────────────

async def _get_or_create_profile(user: User, db: AsyncSession) -> Profile:
    result = await db.execute(select(Profile).filter(Profile.user_id == user.id))
    profile = result.scalars().first()
    if not profile:
        profile = Profile(user_id=user.id, full_name=user.name)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


# ── GET /profile ─────────────────────────────────────────────────────────────

@router.get("", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    return profile


# ── PUT /profile/step/1 ──────────────────────────────────────────────────────

@router.put("/step/1", response_model=ProfileResponse)
async def save_step1(
    data: Step1Schema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    profile.full_name = data.full_name
    profile.domain = data.domain
    profile.education_level = data.education_level
    profile.grad_date = data.grad_date
    # Also update the user's display name
    user.name = data.full_name
    await db.commit()
    await db.refresh(profile)
    return profile


# ── PUT /profile/step/2 ──────────────────────────────────────────────────────

@router.put("/step/2", response_model=ProfileResponse)
async def save_step2(
    data: Step2Schema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    profile.looking_for = data.looking_for
    profile.any_field_categories = data.any_field_categories
    profile.availability = data.availability
    profile.preferred_max_hours = data.preferred_max_hours
    # Also mirror to legacy job_types field
    profile.job_types = data.looking_for
    await db.commit()
    await db.refresh(profile)
    return profile


# ── PUT /profile/step/3 ──────────────────────────────────────────────────────

@router.put("/step/3", response_model=ProfileResponse)
async def save_step3(
    data: Step3Schema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    profile.country = data.country
    profile.city = data.city
    profile.campus_address = data.campus_address
    profile.commute_radius_km = data.commute_radius_km or 10

    # Geocode the address via OSM Nominatim
    address = f"{data.campus_address or data.city}, {data.country}"
    coords = await geocode(address)
    if coords:
        profile.lat, profile.lng = coords

    await db.commit()
    await db.refresh(profile)
    return profile


# ── PUT /profile/step/4 ──────────────────────────────────────────────────────

@router.put("/step/4", response_model=ProfileResponse)
async def save_step4(
    data: Step4Schema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    profile.visa_type = data.visa_type
    profile.hour_cap_term = data.hour_cap_term
    profile.hour_cap_break = data.hour_cap_break
    profile.work_rights_confirmed = data.work_rights_confirmed
    profile.needs_sponsorship = data.needs_sponsorship
    # Mirror to legacy field
    profile.weekly_hour_cap = data.hour_cap_term
    await db.commit()
    await db.refresh(profile)
    return profile


# ── PUT /profile/step/5 ──────────────────────────────────────────────────────

@router.put("/step/5", response_model=ProfileResponse)
async def save_step5(
    data: Step5Schema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    profile.languages = data.languages
    profile.local_language_level = data.local_language_level
    profile.comfort_customer_facing = data.comfort_customer_facing
    await db.commit()
    await db.refresh(profile)
    return profile


# ── POST /profile/resume (Step 6 – optional) ─────────────────────────────────

@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5 MB")

    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_resume.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    profile = await _get_or_create_profile(user, db)
    profile.resume_path = file_path
    await db.commit()
    return {"status": "ok", "resume_path": file_path}


# ── POST /profile/complete ────────────────────────────────────────────────────

@router.post("/complete")
async def complete_onboarding(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark onboarding as done and kick off the background scrape pipeline.
    """
    profile = await _get_or_create_profile(user, db)
    profile.onboarding_done = True
    user.scrape_status = "pending"
    user.scrape_job_count = 0
    await db.commit()

    # Queue background scrape — FastAPI BackgroundTasks runs after the response
    background_tasks.add_task(_run_scrape_bg, user.id)

    return {"status": "ok", "message": "Onboarding complete. Scraping in progress."}


async def _run_scrape_bg(user_id: int) -> None:
    """Create a fresh DB session for the background task."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await run_search_plan(user_id, db)


# ── PUT /profile (legacy generic update) ─────────────────────────────────────

@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(user, db)
    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile
