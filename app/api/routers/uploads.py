from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import tempfile
from pathlib import Path
from app.api.endpoints.common import UploadResponse, MessageResponse

router = APIRouter()

# Upload directory in temp
UPLOAD_DIR = Path(tempfile.gettempdir()) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/", response_model=UploadResponse, tags=["uploads"], summary="Upload a file", description="Upload an image or document to the server. Returns the filename and access URL.")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return its URL"""
    try:
        # Validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return file URL
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "url": f"/uploads/{unique_filename}",
            "size": len(contents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{filename}", response_model=MessageResponse, tags=["uploads"], summary="Delete a file", description="Permanently delete an uploaded file from the server.")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    os.remove(file_path)
    return {"message": "File deleted successfully"}
