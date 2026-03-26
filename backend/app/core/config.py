from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # App
    app_name: str = "Katalog API"
    debug: bool = True
    
    # Upload
    upload_dir: Path = Path("uploads")
    max_csv_size_mb: int = 50
    max_image_size_mb: int = 10
    allowed_csv_extensions: set[str] = {".csv"}
    allowed_image_extensions: set[str] = {".jpg", ".jpeg", ".png", ".gif"}
    
    class Config:
        env_file = ".env"

settings = Settings()
