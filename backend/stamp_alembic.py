import asyncio, sys
sys.path.insert(0, '.')
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
url = url.split('?')[0] + '?ssl=require'
engine = create_async_engine(url)

async def stamp():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))
        await conn.execute(text("DELETE FROM alembic_version"))
        await conn.execute(text("INSERT INTO alembic_version VALUES ('0003_discovery_tables')"))
    print('Alembic stamped at 0003_discovery_tables')
    await engine.dispose()

asyncio.run(stamp())
