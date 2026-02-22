from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
from fastapi.exceptions import RequestValidationError

from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.engine import Base, engine
from app.api.routers import auth, events, public, uploads, posts

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (using run_sync for AsyncEngine)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Error during database initialization: {e}")
    yield
    # Cleanup on shutdown (if needed)

description = """
Nexr Forms API helps you manage events, tracking, and form responses efficiently. 🚀

## Features
* **Authentication**: Secure user registration and login.
* **Events**: Create and manage events with custom fields.
* **Public**: Access public event info and submit registrations.
* **Uploads**: Handle file uploads for images and documents.
* **Posts**: Manage news and updates.

"""

tags_metadata = [
    {"name": "auth", "description": "Operations with users and authentication."},
    {"name": "events", "description": "Manage events and registrations (Organizer access)."},
    {"name": "public", "description": "Public endpoints for event details and registration."},
    {"name": "uploads", "description": "Endpoints for uploading and managing files."},
    {"name": "posts", "description": "Manage blog posts and updates."},
]

app = FastAPI(
    title="Nexr Forms API",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

origins = [
    "https://nexr-forms.vercel.app",
    "https://forms.vercel.app",
    "https://nexr-forms-frontend.vercel.app",
    "https://nexr-forms-backend.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global Exception: {exc}")
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )
    # Manually add CORS headers for 500 errors to avoid browser 'CORS blocked' mask
    origin = request.headers.get("origin")
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    elif "*" in origins or not origins:
         response.headers["Access-Control-Allow-Origin"] = "*"
    
    return response

# Validation Exception Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc}")
    print(f"Validation Error Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

from fastapi.staticfiles import StaticFiles
import os
import shutil
import tempfile
from fastapi import File, UploadFile

# CORS
"""app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
# Create uploads dir in temp if not exists
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount StaticFiles
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    import uuid
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_location = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": unique_filename}


@app.get("/")
async def root():
    return {"status": "Backend is running"}

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(public.router, prefix="/api/public", tags=["public"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
