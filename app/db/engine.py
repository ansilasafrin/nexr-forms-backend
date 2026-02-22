from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 1. Transform the URL to use +asyncpg
async_db_url = settings.DATABASE_URL
if async_db_url.startswith("postgresql://"):
    async_db_url = async_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

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
