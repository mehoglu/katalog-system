"""
Integration tests for catalog generation.
Phase 7: Professional HTML Catalog Output
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


client = TestClient(app)


@pytest.fixture
def mock_upload_dir(tmp_path, monkeypatch):
    """Create temporary upload directory with test data."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    return upload_dir


@pytest.fixture
def mock_merged_products(mock_upload_dir):
    """Create test merged_products.json with 2 products."""
    test_upload_id = "test_catalog_001"
    upload_path = mock_upload_dir / test_upload_id
    upload_path.mkdir()
    
    merged_data = {
        "total_products": 2,
        "products": [
            {
                "artikelnummer": "D80950",
                "data": {
                    "artikelnummer": "D80950",
                    "bezeichnung1": "Deckenfluter LED",
                    "bezeichnung1_enhanced": "Eleganter LED-Deckenfluter",
                    "bezeichnung2": "Stehlampe mit Dimmer",
                    "preis": "89.99",
                    "hoehe_cm": "180",
                    "breite_cm": "30",
                    "tiefe_cm": "30",
                    "gewicht_kg": "3.5",
                    "bild_paths": ["bilder/D80950.jpg"]
                },
                "sources": {}
            },
            {
                "artikelnummer": "D80951",
                "data": {
                    "artikelnummer": "D80951",
                    "bezeichnung1": "Tischlampe"
                },
                "sources": {}
            }
        ]
    }
    
    merged_path = upload_path / "merged_products.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    return test_upload_id, upload_path


def test_generate_catalog_success(mock_merged_products):
    """Test POST /api/catalog/generate returns success."""
    upload_id, upload_path = mock_merged_products
    
    response = client.post(
        "/api/catalog/generate",
        json={"upload_id": upload_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["success"] is True
    assert data["total_products"] == 2
    assert data["files_generated"] == 3  # 2 products + 1 index
    assert "catalog" in data["output_path"]
    
    # Verify catalog directory created
    catalog_dir = upload_path / "catalog"
    assert catalog_dir.exists()
    
    # Verify index.html exists
    index_html = catalog_dir / "index.html"
    assert index_html.exists()
    
    # Verify product HTML files exist
    product1_html = catalog_dir / "D80950.html"
    product2_html = catalog_dir / "D80951.html"
    assert product1_html.exists()
    assert product2_html.exists()


def test_catalog_html_structure(mock_merged_products):
    """Test generated HTML has correct structure and A4 format."""
    upload_id, upload_path = mock_merged_products
    
    # Generate catalog
    response = client.post(
        "/api/catalog/generate",
        json={"upload_id": upload_id}
    )
    assert response.status_code == 200
    
    # Read generated product HTML
    catalog_dir = upload_path / "catalog"
    product_html_path = catalog_dir / "D80950.html"
    
    with open(product_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Verify A4 format CSS present
    assert "@page" in html_content
    assert "A4" in html_content
    assert "@media print" in html_content
    
    # Verify product data appears
    assert "D80950" in html_content
    assert "Deckenfluter LED" in html_content
    assert "Eleganter LED-Deckenfluter" in html_content
    assert "89.99" in html_content
    
    # Verify embedded CSS (no external stylesheets)
    assert "<style>" in html_content
    assert "<link rel=" not in html_content or "stylesheet" not in html_content


def test_catalog_missing_merged_products(mock_upload_dir):
    """Test POST returns 404 for non-existent upload_id."""
    response = client.post(
        "/api/catalog/generate",
        json={"upload_id": "nonexistent_upload"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_catalog_handles_missing_fields(mock_upload_dir):
    """Test catalog generation handles products with missing fields."""
    test_upload_id = "test_catalog_missing"
    upload_path = mock_upload_dir / test_upload_id
    upload_path.mkdir()
    
    # Product with minimal data (no price, no images, no dimensions)
    merged_data = {
        "total_products": 1,
        "products": [
            {
                "artikelnummer": "MINIMAL001",
                "data": {
                    "artikelnummer": "MINIMAL001",
                    "bezeichnung1": "Minimal Product"
                },
                "sources": {}
            }
        ]
    }
    
    merged_path = upload_path / "merged_products.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    # Generate catalog
    response = client.post(
        "/api/catalog/generate",
        json={"upload_id": test_upload_id}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify HTML generated without errors
    catalog_dir = upload_path / "catalog"
    product_html = catalog_dir / "MINIMAL001.html"
    assert product_html.exists()
    
    # Read HTML and verify it doesn't have errors
    with open(product_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should handle missing fields gracefully
    assert "MINIMAL001" in html_content
    assert "Minimal Product" in html_content
