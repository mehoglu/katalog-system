"""
Integration tests for review API endpoints.
Phase 6: Data Review & Correction
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
    test_upload_id = "test_review_001"
    upload_path = mock_upload_dir / test_upload_id
    upload_path.mkdir()
    
    merged_data = {
        "total_products": 2,
        "edi_only": 0,
        "matched": 2,
        "merge_timestamp": "2026-03-26T10:00:00",
        "products": [
            {
                "artikelnummer": "D80950",
                "data": {
                    "artikelnummer": "D80950",
                    "bezeichnung1": "Deckenfluter LED",
                    "bezeichnung1_enhanced": "Eleganter LED-Deckenfluter mit modernem Design",
                    "bezeichnung2": "Stehlampe mit Dimmer",
                    "preis": "89.99",
                    "hoehe_cm": "180",
                    "breite_cm": "30",
                    "tiefe_cm": "30",
                    "gewicht_kg": "3.5",
                    "bild_paths": ["bilder/D80950.jpg"]
                },
                "sources": {
                    "artikelnummer": "edi_export",
                    "bezeichnung1": "edi_export",
                    "bezeichnung1_enhanced": "llm_enhancement",
                    "bezeichnung2": "edi_export",
                    "preis": "preisliste",
                    "hoehe_cm": "edi_export",
                    "breite_cm": "edi_export",
                    "tiefe_cm": "edi_export",
                    "gewicht_kg": "edi_export",
                    "bild_paths": "image_linking"
                }
            },
            {
                "artikelnummer": "D80951",
                "data": {
                    "artikelnummer": "D80951",
                    "bezeichnung1": "Tischlampe",
                    "preis": "29.99",
                    "hoehe_cm": "45"
                },
                "sources": {
                    "artikelnummer": "edi_export",
                    "bezeichnung1": "edi_export",
                    "preis": "preisliste",
                    "hoehe_cm": "edi_export"
                }
            }
        ]
    }
    
    merged_path = upload_path / "merged_products.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    return test_upload_id, merged_path


def test_get_review_all_products(mock_merged_products):
    """Test GET /api/review/{upload_id} returns all products."""
    upload_id, merged_path = mock_merged_products
    
    response = client.get(f"/api/review/{upload_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["total_products"] == 2
    assert data["upload_id"] == upload_id
    assert len(data["products"]) == 2
    
    # Verify first product
    product1 = data["products"][0]
    assert product1["artikelnummer"] == "D80950"
    assert product1["data"]["bezeichnung1"] == "Deckenfluter LED"
    assert product1["data"]["bezeichnung1_enhanced"] == "Eleganter LED-Deckenfluter mit modernem Design"
    assert product1["data"]["preis"] == "89.99"
    assert product1["sources"]["bezeichnung1"] == "edi_export"
    assert product1["sources"]["bezeichnung1_enhanced"] == "llm_enhancement"
    assert product1["sources"]["preis"] == "preisliste"
    assert product1["sources"]["bild_paths"] == "image_linking"


def test_get_review_missing_file(mock_upload_dir):
    """Test GET returns 404 for non-existent upload_id."""
    response = client.get("/api/review/nonexistent_upload")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_patch_field_success(mock_merged_products):
    """Test PATCH /api/review/{upload_id}/product updates field."""
    upload_id, merged_path = mock_merged_products
    
    # Update bezeichnung1 for D80950
    update_request = {
        "artikelnummer": "D80950",
        "field_name": "bezeichnung1",
        "field_value": "Moderner LED-Deckenfluter"
    }
    
    response = client.patch(f"/api/review/{upload_id}/product", json=update_request)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response
    assert data["success"] is True
    assert data["product"]["data"]["bezeichnung1"] == "Moderner LED-Deckenfluter"
    assert data["product"]["sources"]["bezeichnung1"] == "manual_edit"
    
    # Verify file was updated
    with open(merged_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)
    
    product1 = updated_data["products"][0]
    assert product1["data"]["bezeichnung1"] == "Moderner LED-Deckenfluter"
    assert product1["sources"]["bezeichnung1"] == "manual_edit"


def test_patch_field_preserves_structure(mock_merged_products):
    """Test PATCH preserves all other fields and sources."""
    upload_id, merged_path = mock_merged_products
    
    # Read original data
    with open(merged_path, "r", encoding="utf-8") as f:
        original_data = json.load(f)
    
    # Update single field (preis)
    update_request = {
        "artikelnummer": "D80950",
        "field_name": "preis",
        "field_value": "99.99"
    }
    
    response = client.patch(f"/api/review/{upload_id}/product", json=update_request)
    assert response.status_code == 200
    
    # Read updated data
    with open(merged_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)
    
    product1_original = original_data["products"][0]
    product1_updated = updated_data["products"][0]
    
    # Verify only preis changed
    assert product1_updated["data"]["preis"] == "99.99"
    assert product1_updated["sources"]["preis"] == "manual_edit"
    
    # Verify all other fields unchanged
    assert product1_updated["data"]["bezeichnung1"] == product1_original["data"]["bezeichnung1"]
    assert product1_updated["data"]["bezeichnung1_enhanced"] == product1_original["data"]["bezeichnung1_enhanced"]
    assert product1_updated["data"]["hoehe_cm"] == product1_original["data"]["hoehe_cm"]
    
    # Verify all other sources unchanged
    assert product1_updated["sources"]["bezeichnung1"] == product1_original["sources"]["bezeichnung1"]
    assert product1_updated["sources"]["bezeichnung1_enhanced"] == product1_original["sources"]["bezeichnung1_enhanced"]
    assert product1_updated["sources"]["bild_paths"] == product1_original["sources"]["bild_paths"]
    
    # Verify second product completely unchanged
    assert updated_data["products"][1] == original_data["products"][1]


def test_patch_product_not_found(mock_merged_products):
    """Test PATCH returns 404 for invalid artikelnummer."""
    upload_id, _ = mock_merged_products
    
    update_request = {
        "artikelnummer": "INVALID_ART_NR",
        "field_name": "bezeichnung1",
        "field_value": "Test"
    }
    
    response = client.patch(f"/api/review/{upload_id}/product", json=update_request)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
