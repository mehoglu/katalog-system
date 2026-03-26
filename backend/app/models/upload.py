from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

class UploadSession(BaseModel):
    """Upload-Session Metadaten"""
    upload_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    upload_dir: Path
    csv_files: list[str] = []
    image_count: int = 0
    
class CSVUploadResponse(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int
    uploaded_at: datetime
    path: str  # Relative path from uploads/
    
class ImageUploadResponse(BaseModel):
    upload_id: str
    image_count: int
    total_size_bytes: int
    uploaded_at: datetime
    image_dir: str
