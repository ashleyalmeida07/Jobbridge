# scrape_runs table — add to models
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    avatar = Column(String)
    gmail_refresh_token_enc = Column(Text)
    telegram_chat_id = Column(String)
    scrape_status = Column(String, default="pending")
    scrape_job_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    email_queues = relationship("EmailQueue", back_populates="user")
    prep_notes = relationship("PrepNote", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    # Step 1
    full_name = Column(String)
    domain = Column(String)
    education_level = Column(String)
    grad_date = Column(String)

    # Step 2
    looking_for = Column(ARRAY(String))
    any_field_categories = Column(ARRAY(String))
    availability = Column(ARRAY(String))
    preferred_max_hours = Column(Integer)

    # Step 3
    country = Column(String)
    city = Column(String)
    campus_address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    commute_radius_km = Column(Integer, default=10)

    # Step 4
    visa_type = Column(String)
    hour_cap_term = Column(Integer)
    hour_cap_break = Column(Integer)
    work_rights_confirmed = Column(Boolean)
    needs_sponsorship = Column(String)

    # Step 5
    languages = Column(ARRAY(String))
    local_language_level = Column(String)
    comfort_customer_facing = Column(Boolean)

    # Step 6
    resume_path = Column(String)

    # Legacy / computed
    job_types = Column(ARRAY(String))
    skills = Column(ARRAY(String))
    weekly_hour_cap = Column(Integer)

    onboarding_done = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    source_url = Column(String, unique=True, index=True)
    title = Column(String)
    employer = Column(String)
    location = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    pay_text = Column(String)
    pay_min = Column(Float)
    pay_max = Column(Float)
    pay_period = Column(String)  # hourly | weekly | yearly | daily
    job_type = Column(String)
    category = Column(String)    # food_cafe | retail | delivery | etc.
    description = Column(Text)
    contact_email = Column(String)
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    dedupe_hash = Column(String, unique=True, index=True)

    analysis = relationship("JobAnalysis", back_populates="job", uselist=False)
    applications = relationship("Application", back_populates="job")
    email_queues = relationship("EmailQueue", back_populates="job")
    prep_notes = relationship("PrepNote", back_populates="job")


class JobAnalysis(Base):
    __tablename__ = "job_analysis"

    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    trust_score = Column(Float)
    red_flags = Column(ARRAY(String))
    pay_label = Column(String)
    hours_per_week = Column(Integer)
    shift_info = Column(String)
    work_rights_required = Column(Boolean)
    sponsorship = Column(String)
    language_requirement = Column(String)

    job = relationship("Job", back_populates="analysis")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String)
    applied_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    followup_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    subject = Column(String)
    body = Column(Text)
    status = Column(String)
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="email_queues")
    job = relationship("Job", back_populates="email_queues")


class DailyQuota(Base):
    __tablename__ = "daily_quota"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    date = Column(Date, primary_key=True)
    count = Column(Integer, default=0)


class PrepNote(Base):
    __tablename__ = "prep_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    content = Column(Text)

    user = relationship("User", back_populates="prep_notes")
    job = relationship("Job", back_populates="prep_notes")


class ScrapeRun(Base):
    """Records each scraper run: status, count, errors — for monitoring and debugging."""
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = admin/cron run
    source = Column(String, index=True)        # scraper id e.g. "seek_au"
    country = Column(String)
    keywords = Column(ARRAY(String))
    location = Column(String)
    status = Column(String, default="pending")  # pending | running | done | failed
    jobs_found = Column(Integer, default=0)
    jobs_saved = Column(Integer, default=0)
    error_msg = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))


class DiscoveredEmployer(Base):
    """
    Employers found via Overpass API near a user's location.
    Cached for 7 days per area tile (lat/lng rounded to 2 decimal places).
    """
    __tablename__ = "discovered_employers"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String, index=True)          # Overpass node/way id
    name = Column(String, nullable=False)
    category = Column(String, index=True)        # food_cafe | retail | etc.
    lat = Column(Float)
    lng = Column(Float)
    address = Column(String)
    website = Column(String)
    brand = Column(String)                       # normalised brand name for deduplication
    area_key = Column(String, index=True)        # "lat2dp:lng2dp" tile key
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


class CareersPageCache(Base):
    """
    Caches the careers page URL found for each employer website.
    Positive hits cached 7 days; negative hits (no page found) 14 days.
    """
    __tablename__ = "careers_page_cache"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True)  # e.g. "example.com.au"
    careers_url = Column(String)                      # null = no page found
    confidence = Column(Float)                        # 0.0–1.0
    method = Column(String)                           # link_text | common_path | sitemap
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
