import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback for local development, but alert if likely in production
        DATABASE_URL = "postgresql://postgres:1234@localhost:5432/eventflow"
        print("WARNING: DATABASE_URL not set. Using local development default.")

    SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey_replace_this_in_production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()
