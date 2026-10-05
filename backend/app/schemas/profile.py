from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date


# ── Step schemas (one per onboarding step) ──────────────────────────────────

class Step1Schema(BaseModel):
    """About you"""
    full_name: str
    domain: str
    education_level: str  # undergraduate | postgraduate | phd
    grad_date: Optional[str] = None

    @field_validator("education_level")
    @classmethod
    def validate_edu(cls, v: str) -> str:
        valid = {"undergraduate", "postgraduate", "phd", "diploma", "other"}
        if v not in valid:
            raise ValueError(f"education_level must be one of {valid}")
        return v


class Step2Schema(BaseModel):
    """What are you looking for?"""
    looking_for: List[str]
    any_field_categories: Optional[List[str]] = None
    availability: List[str]
    preferred_max_hours: Optional[int] = None

    @field_validator("looking_for")
    @classmethod
    def validate_looking_for(cls, v: List[str]) -> List[str]:
        valid = {
            "internship_domain", "fulltime_domain",
            "parttime_domain", "parttime_any"
        }
        for item in v:
            if item not in valid:
                raise ValueError(f"Invalid looking_for value: {item}")
        return v


class Step3Schema(BaseModel):
    """Location"""
    country: str
    city: str
    campus_address: Optional[str] = None
    commute_radius_km: Optional[int] = 10
    # lat/lng filled server-side via geocoding


class Step4Schema(BaseModel):
    """Visa and work rights"""
    visa_type: str
    hour_cap_term: Optional[int] = None
    hour_cap_break: Optional[int] = None
    work_rights_confirmed: Optional[bool] = None
    needs_sponsorship: str  # yes | no | maybe

    @field_validator("needs_sponsorship")
    @classmethod
    def validate_sponsorship(cls, v: str) -> str:
        if v not in {"yes", "no", "maybe"}:
            raise ValueError("needs_sponsorship must be yes | no | maybe")
        return v


class Step5Schema(BaseModel):
    """Language and comfort"""
    languages: List[str]
    local_language_level: str  # none | basic | conversational | fluent
    comfort_customer_facing: bool

    @field_validator("local_language_level")
    @classmethod
    def validate_lang_level(cls, v: str) -> str:
        valid = {"none", "basic", "conversational", "fluent"}
        if v not in valid:
            raise ValueError(f"local_language_level must be one of {valid}")
        return v


class Step6Schema(BaseModel):
    """Resume + Telegram – handled separately via file upload / link-token"""
    pass


# ── Full profile schemas ──────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    """Legacy generic update (kept for backward compat)"""
    country: Optional[str] = None
    city: Optional[str] = None
    campus_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    visa_type: Optional[str] = None
    weekly_hour_cap: Optional[int] = None
    job_types: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    local_language_level: Optional[str] = None


class ProfileResponse(BaseModel):
    """Full profile as returned to the client"""
    user_id: int

    # Step 1
    full_name: Optional[str] = None
    domain: Optional[str] = None
    education_level: Optional[str] = None
    grad_date: Optional[str] = None

    # Step 2
    looking_for: Optional[List[str]] = None
    any_field_categories: Optional[List[str]] = None
    availability: Optional[List[str]] = None
    preferred_max_hours: Optional[int] = None

    # Step 3
    country: Optional[str] = None
    city: Optional[str] = None
    campus_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    commute_radius_km: Optional[int] = None

    # Step 4
    visa_type: Optional[str] = None
    hour_cap_term: Optional[int] = None
    hour_cap_break: Optional[int] = None
    work_rights_confirmed: Optional[bool] = None
    needs_sponsorship: Optional[str] = None

    # Step 5
    languages: Optional[List[str]] = None
    local_language_level: Optional[str] = None
    comfort_customer_facing: Optional[bool] = None

    # Step 6
    resume_path: Optional[str] = None
    onboarding_done: bool = False

    model_config = {"from_attributes": True}
