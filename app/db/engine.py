from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 1. Transform the URL to use +asyncpg
async_db_url = settings.DATABASE_URL or ""

# Handle both postgres:// and postgresql:// for asyncpg
if async_db_url.startswith("postgres://"):
    async_db_url = async_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif async_db_url.startswith("postgresql://"):
    async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg doesn't support sslmode=require in the connection string like psycopg2
# We strip it and will handle SSL via connect_args if needed, 
# although often asyncpg handles it if the URL is correct or via environment.
if "sslmode=" in async_db_url:
    # Basic stripping for now to avoid asyncpg errors
    import re
    async_db_url = re.sub(r'[\?&]sslmode=[^&]*', '', async_db_url)

# Log connection attempt (obfuscated)
db_url_log = async_db_url
if "@" in db_url_log:
    parts = db_url_log.split("@")
    db_url_log = parts[0].split(":")[0] + ":****@" + parts[1]
print(f"INFO: Initializing async database engine with: {db_url_log}")

engine = create_async_engine(
    async_db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass
