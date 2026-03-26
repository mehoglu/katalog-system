import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil

from app.main import app
from app.core.config import settings

@pytest.fixture
def client():
    """Test client für FastAPI"""
    return TestClient(app)

@pytest.fixture
def test_upload_dir(tmp_path):
    """Temporary upload directory für Tests"""
    upload_dir = tmp_path / "test_uploads"
    upload_dir.mkdir()
    
    # Override settings
    settings.upload_dir = upload_dir
    
    yield upload_dir
    
    # Cleanup
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV file"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "Artikelnummer,Bezeichnung1,Preis\n"
        "D80950,Müllbehälter 120L,45.99\n"
        "D80951,Abfalltonne 240L,89.99\n",
        encoding="utf-8"
    )
    return csv_file

@pytest.fixture
def sample_image(tmp_path):
    """Create minimal image file"""
    image_file = tmp_path / "test_image.jpg"
    # Minimal JPEG header
    image_file.write_bytes(b'\xFF\xD8\xFF\xE0' + b'\x00' * 100)
    return image_file
