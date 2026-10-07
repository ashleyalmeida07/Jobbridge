from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, encrypt_token, decode_access_token
from app.models.models import User, Profile
import jwt

router = APIRouter()
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/google/login")
async def login_via_google(request: Request, connect_gmail: bool = False):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    kwargs = {
        "access_type": "offline",
        "prompt": "consent"
    }
    # If the user wants to connect gmail later for cold emailing
    if connect_gmail:
        kwargs["scope"] = "openid email profile https://www.googleapis.com/auth/gmail.send"
        
    return await oauth.google.authorize_redirect(request, redirect_uri, **kwargs)

@router.get("/google/callback")
async def auth_via_google(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Authorization failed")

    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="User info missing")

    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name")
    avatar = user_info.get("picture")

    refresh_token = token.get("refresh_token")

    result = await db.execute(select(User).filter(User.google_id == google_id))
    user = result.scalars().first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar=avatar,
        )
        if refresh_token:
            user.gmail_refresh_token_enc = encrypt_token(refresh_token)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update user info and optionally token
        user.name = name
        user.avatar = avatar
        if refresh_token:
            user.gmail_refresh_token_enc = encrypt_token(refresh_token)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(subject=user.id)

    # Check whether onboarding is complete to decide redirect
    prof_result = await db.execute(select(Profile).filter(Profile.user_id == user.id))
    profile = prof_result.scalars().first()
    onboarding_done = profile.onboarding_done if profile else False
    redirect_url = f"{settings.FRONTEND_URL}/jobs" if onboarding_done else f"{settings.FRONTEND_URL}/onboarding"

    res = RedirectResponse(url=redirect_url)
    is_production = "localhost" not in settings.FRONTEND_URL
    res.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none" if is_production else "lax",
        secure=is_production,
        max_age=30 * 24 * 60 * 60,  # 30 days
    )
    return res

async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
        return None
    token = token.split(" ")[1]
    
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None

    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.get("/me")
async def get_me(user: User = Depends(get_current_user_optional), db: AsyncSession = Depends(get_db)):
    if not user:
        return Response(status_code=204)
        
    from app.models.models import Profile
    prof_result = await db.execute(select(Profile).filter(Profile.user_id == user.id))
    profile = prof_result.scalars().first()
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar": user.avatar,
        "has_gmail_connected": bool(user.gmail_refresh_token_enc),
        "onboarding_done": profile.onboarding_done if profile else False,
        "scrape_status": user.scrape_status or "pending",
    }

@router.post("/logout")
async def logout(response: Response):
    res = Response(status_code=200, content="Logged out")
    is_production = "localhost" not in settings.FRONTEND_URL
    res.delete_cookie(
        "access_token",
        httponly=True,
        samesite="none" if is_production else "lax",
        secure=is_production
    )
    return res
