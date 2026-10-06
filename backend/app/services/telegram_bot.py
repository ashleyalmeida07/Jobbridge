import asyncio
import httpx
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import User
from app.services.scrape_runner import run_search_plan
from app.api.telegram import LINK_TOKENS

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = AsyncIOScheduler()

async def send_telegram_message(chat_id: str, text: str):
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except Exception as e:
            logger.error(f"Failed to send telegram message: {e}")

async def process_telegram_update(update: dict):
    msg = update.get("message", {})
    text = msg.get("text", "")
    chat_id = msg.get("chat", {}).get("id")
    
    if not text or not chat_id:
        return
        
    chat_id = str(chat_id)
    
    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            token = parts[1]
            user_id = LINK_TOKENS.get(token)
            if user_id:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(User).filter(User.id == user_id))
                    user = result.scalars().first()
                    if user:
                        user.telegram_chat_id = chat_id
                        await db.commit()
                        await send_telegram_message(chat_id, "✅ Your Telegram account has been successfully linked to JobBridge! You will now receive daily job alerts here.")
                        del LINK_TOKENS[token]
            else:
                await send_telegram_message(chat_id, "❌ Invalid or expired link token.")
        else:
            await send_telegram_message(chat_id, "Welcome to JobBridge! Please link your account from the dashboard settings.")
    elif text.startswith("/scan"):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).filter(User.telegram_chat_id == chat_id))
            user = result.scalars().first()
            if user:
                asyncio.create_task(run_daily_scan_for_user(user.id, chat_id))
            else:
                await send_telegram_message(chat_id, "❌ Please link your account first.")

async def telegram_poller():
    """Long-polls the Telegram API for new messages (e.g., /start <token>)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram polling disabled.")
        return
        
    offset = 0
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
    logger.info("Starting Telegram poller...")
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{url}?offset={offset}&timeout=30", timeout=40)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("result", []):
                        offset = item["update_id"] + 1
                        await process_telegram_update(item)
        except Exception as e:
            logger.error(f"Telegram poller error: {e}")
            await asyncio.sleep(5)

async def run_daily_scan_for_user(user_id: int, chat_id: str):
    """Runs the scan and sends results to Telegram."""
    try:
        async with AsyncSessionLocal() as db:
            await send_telegram_message(chat_id, "🔍 <b>Daily Job Scan</b> starting now...")
            await run_search_plan(user_id, db)
            
            # Fetch user to get scrape_job_count
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            if user:
                await send_telegram_message(chat_id, f"✅ <b>Scan Complete!</b>\n\nFound {user.scrape_job_count} matching opportunities today. Check your dashboard to view them and apply.")
    except Exception as e:
        logger.error(f"Daily scan failed for user {user_id}: {e}")
        await send_telegram_message(chat_id, "❌ Your daily job scan failed to run. We will try again tomorrow.")

async def trigger_daily_scans():
    """Triggered by APScheduler every day to run scans for all users with a linked Telegram."""
    logger.info("Triggering daily scans...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.telegram_chat_id.isnot(None)))
        users = result.scalars().all()
        
        for user in users:
            # We spawn a background task for each user so they don't block each other
            asyncio.create_task(run_daily_scan_for_user(user.id, user.telegram_chat_id))

def start_background_tasks():
    # Start poller
    asyncio.create_task(telegram_poller())
    
    # Schedule daily scans (e.g., at 9:00 AM UTC, or configure based on user)
    # For now, we will run it every day at 9:00 AM UTC. 
    # (To show the user it works immediately, I'll also add a command /scan)
    scheduler.add_job(trigger_daily_scans, CronTrigger(hour=9, minute=0))
    scheduler.start()
