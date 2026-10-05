import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import User
from app.api.auth import get_current_user

router = APIRouter()

# In-memory store for link tokens (just for scaffolding)
# In production, use Redis or a DB table with expiration
LINK_TOKENS = {}

@router.post("/link-token")
async def generate_link_token(user: User = Depends(get_current_user)):
    token = secrets.token_urlsafe(16)
    LINK_TOKENS[token] = user.id
    return {"token": token, "bot_username": "JobBridgeBot"}

# The bot handler itself would typically run as a background task or webhooks
# POST /telegram/webhook ...
