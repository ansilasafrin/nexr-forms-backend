from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Log connection attempt (obfuscated)
db_url_log = settings.DATABASE_URL
if "@" in db_url_log:
    parts = db_url_log.split("@")
    db_url_log = parts[0].split(":")[0] + ":****@" + parts[1]
print(f"INFO: Initializing database engine with: {db_url_log}")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
