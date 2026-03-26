from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from datetime import datetime
import aiofiles

from app.core.config import settings
from app.models.upload import CSVUploadResponse, ImageUploadResponse

router = APIRouter()

def create_upload_session() -> tuple[str, Path]:
    """Erstellt Zeitstempel-Ordner für Upload-Session (CONTEXT D-03)"""
    upload_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    upload_dir = settings.upload_dir / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_id, upload_dir

@router.post("/upload/csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
):
    """
    Upload CSV file
    
    CONTEXT D-06: Getrennte Upload-Schritte (CSVs zuerst)
    RESEARCH: Streaming upload für große Dateien
    """
    # Validierung: CSV extension
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected .csv, got {Path(file.filename).suffix}"
        )
    
    # Validierung: File size (Basic check, real size validated during upload)
    if file.size and file.size > settings.max_csv_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.max_csv_size_mb}MB allowed."
        )
    
    # Create upload session with timestamp folder
    upload_id, upload_dir = create_upload_session()
    
    # Save file with streaming (memory-efficient for large files)
    csv_path = upload_dir / file.filename
    file_size = 0
    
    async with aiofiles.open(csv_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks (RESEARCH pattern)
            file_size += len(chunk)
            await f.write(chunk)
    
    return CSVUploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        size_bytes=file_size,
        uploaded_at=datetime.now(),
        path=str(csv_path.relative_to(settings.upload_dir))
    )

@router.post("/upload/images/{upload_id}", response_model=ImageUploadResponse)
async def upload_images(
    upload_id: str,
    files: list[UploadFile] = File(...),
):
    """
    Upload multiple image files for existing upload session
    
    CONTEXT D-06: Getrennte Upload-Schritte (Bilder nach CSVs)
    """
    upload_dir = settings.upload_dir / upload_id
    
    # Validate upload session exists
    if not upload_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Upload session {upload_id} not found. Upload CSV first."
        )
    
    # Create bilder subdirectory (matches PROJECT.md structure)
    images_dir = upload_dir / "bilder"
    images_dir.mkdir(exist_ok=True)
    
    total_size = 0
    uploaded_count = 0
    
    for image in files:
        # Validate image extension
        ext = Path(image.filename).suffix.lower()
        if ext not in settings.allowed_image_extensions:
            # Skip invalid files, don't block entire upload
            continue
        
        # Save image
        image_path = images_dir / image.filename
        file_size = 0
        
        async with aiofiles.open(image_path, 'wb') as f:
            while chunk := await image.read(16384):  # 16KB chunks for images
                file_size += len(chunk)
                await f.write(chunk)
        
        total_size += file_size
        uploaded_count += 1
    
    return ImageUploadResponse(
        upload_id=upload_id,
        image_count=uploaded_count,
        total_size_bytes=total_size,
        uploaded_at=datetime.now(),
        image_dir=str(images_dir.relative_to(settings.upload_dir))
    )

@router.get("/upload/{upload_id}")
async def get_upload_session(upload_id: str):
    """Get upload session info"""
    upload_dir = settings.upload_dir / upload_id
    
    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    # Count CSVs and images
    csv_files = list(upload_dir.glob("*.csv"))
    images_dir = upload_dir / "bilder"
    image_files = []
    if images_dir.exists():
        for ext in settings.allowed_image_extensions:
            image_files.extend(images_dir.glob(f"*{ext}"))
    
    return {
        "upload_id": upload_id,
        "csv_count": len(csv_files),
        "csv_files": [f.name for f in csv_files],
        "image_count": len(image_files),
        "upload_dir": str(upload_dir)
    }
