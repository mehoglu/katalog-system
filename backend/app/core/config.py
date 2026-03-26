from pydantic_settings import BaseSettings
from pydantic import Field
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
    
    # Anthropic Configuration (Phase 2)
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    anthropic_model_primary: str = Field(default="claude-3-5-haiku-20241022", env="ANTHROPIC_MODEL_PRIMARY")
    anthropic_model_fallback: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL_FALLBACK")
    
    class Config:
        env_file = ".env"

settings = Settings()
