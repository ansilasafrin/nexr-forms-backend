from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.db.engine import Base, engine
from app.api.routers import auth, events, public, uploads, posts

from fastapi.middleware.cors import CORSMiddleware
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Forms API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nexr-forms.vercel.app",  # test frontend
        "https://forms.vercel.app",  # Production Frontend
        "http://localhost:3000"      # local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global Exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

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
