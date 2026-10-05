import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
if "?sslmode=" in db_url:
    db_url = db_url.split("?")[0]

async def test():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT COUNT(*) FROM jobs;"))
        print(f"JOB COUNT: {res.scalar()}")

if __name__ == "__main__":
    asyncio.run(test())
