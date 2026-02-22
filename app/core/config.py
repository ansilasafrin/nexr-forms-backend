import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Use DATABASE_URL, or SUPABASE_URL if provided (Supabase usually provides a connection string)
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")
    
    if not DATABASE_URL:
        # Fallback for local development
        DATABASE_URL = "postgresql://postgres:1234@localhost:5432/eventflow"
        print("WARNING: Neither DATABASE_URL nor SUPABASE_URL set. Falling back to local default.")
    else:
        # Log that we found a database URL (don't print the whole thing for security)
        print(f"INFO: Database connection string found. Type: {DATABASE_URL.split(':')[0]}")
        
        # Ensure sslmode=require for remote Supabase connections
        if "localhost" not in DATABASE_URL and "sslmode=" not in DATABASE_URL:
            if "?" in DATABASE_URL:
                DATABASE_URL += "&sslmode=require"
            else:
                DATABASE_URL += "?sslmode=require"
            print("INFO: Appended sslmode=require to DATABASE_URL")

    SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey_replace_this_in_production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()
