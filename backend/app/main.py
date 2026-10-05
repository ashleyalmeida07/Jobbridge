from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.telegram import router as telegram_router
from app.api.scrape import router as scrape_router
from app.api.jobs import router as jobs_router
from app.api.email import router as email_router

app = FastAPI(title=settings.PROJECT_NAME)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
app.include_router(scrape_router, prefix="/scrape", tags=["scrape"])
app.include_router(email_router, prefix="/email", tags=["email"])

@app.get("/config/{country_code}")
async def country_config(country_code: str):
    """Return visa types and config for a country — used by onboarding Step 4."""
    from app.core.country_config import COUNTRY_CONFIG
    code = country_code.upper()
    config = COUNTRY_CONFIG.get(code)
    if not config:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No config for country: {code}")
    return {"country": code, **config}
