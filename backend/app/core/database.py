from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Since we use Neon (Postgres), the URL might start with postgresql:// or postgres://
# asyncpg needs postgresql+asyncpg://
url = settings.DATABASE_URL
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
elif url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg does not support 'sslmode=require' or 'channel_binding=require' directly in the query string 
# the way psycopg2 does. It expects 'ssl=require'.
if "?sslmode=require" in url:
    url = url.replace("?sslmode=require", "?ssl=require")
if "&channel_binding=require" in url:
    url = url.replace("&channel_binding=require", "")

engine = create_async_engine(url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
