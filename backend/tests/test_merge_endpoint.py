"""
Integration tests for merge API endpoint.
Tests full workflow via FastAPI TestClient.
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


@pytest.fixture
def test_edi_csv(tmp_path):
    """Create realistic EDI Export CSV with semicolon delimiter"""
    csv_content = """Artikelnummer;Bezeichnung1;Bezeichnung2;EANNummer;Gewicht;USER_Farbe;USER_Material
210100125;VERSANDTASCHE AUS WELLPAPPE CD;sk m. Aufreißfaden braun;4250414103682;0.028;braun;1.20e KLS
210100225;VERSANDTASCHE AUS WELLPAPPE DVD;sk m. Aufreißfaden braun;4250414103705;0.045;braun;1.20e KLS
999999999;TESTPRODUKT OHNE PREIS;nur in EDI;1234567890123;0.100;schwarz;Test Material"""
    
    upload_dir = tmp_path / "2026-03-26_test_edi"
    upload_dir.mkdir()
    csv_file = upload_dir / "EDI_Export_Artikeldaten.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return upload_dir


@pytest.fixture
def test_preisliste_csv(tmp_path):
    """Create realistic Preisliste CSV with semicolon delimiter"""
    csv_content = """Artikelnummer;preis;menge1;menge2;menge3;menge4;menge5
210100125;1.50;100;500;1000;5000;10000
210100225;2.00;50;250;500;2500;5000
888888888;3.00;25;100;250;1000;2500"""
    
    upload_dir = tmp_path / "2026-03-26_test_preisliste"
    upload_dir.mkdir()
    csv_file = upload_dir / "preisliste.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return upload_dir


@pytest.fixture
def mock_uploads(test_edi_csv, test_preisliste_csv, monkeypatch):
    """Mock upload_dir to use test fixtures"""
    monkeypatch.setattr(settings, "upload_dir", test_edi_csv.parent)
    return {
        "edi_id": test_edi_csv.name,
        "preisliste_id": test_preisliste_csv.name
    }


def test_merge_endpoint_success(mock_uploads):
    """Test successful merge with matched and unmatched products"""
    response = client.post("/api/merge/csv", json={
        "edi_upload_id": mock_uploads["edi_id"],
        "preisliste_upload_id": mock_uploads["preisliste_id"]
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert data["success"] is True
    assert data["total_products"] == 3
    assert data["matched"] == 2  # 210100125, 210100225
    assert data["edi_only"] == 1  # 999999999
    assert "merge_file" in data
    assert "timestamp" in data
    
    # Verify JSON file was created (construct full path from mocked upload_dir)
    merge_file = settings.upload_dir / mock_uploads["edi_id"] / "merged_products.json"
    assert merge_file.exists()
    
    # Validate JSON structure
    merge_data = json.loads(merge_file.read_text())
    assert len(merge_data["products"]) == 3
    
    # Check product with price match
    product_with_price = next(p for p in merge_data["products"] if p["artikelnummer"] == "210100125")
    assert product_with_price["data"]["preis"] == 1.50
    assert product_with_price["data"]["bezeichnung1"] == "VERSANDTASCHE AUS WELLPAPPE CD"
    assert product_with_price["sources"]["preis"] == "preisliste"
    assert product_with_price["sources"]["bezeichnung1"] == "edi_export"
    
    # Check product without price match (D-03 from CONTEXT)
    product_no_price = next(p for p in merge_data["products"] if p["artikelnummer"] == "999999999")
    assert product_no_price["data"]["preis"] is None
    assert product_no_price["data"]["bezeichnung1"] == "TESTPRODUKT OHNE PREIS"
    assert product_no_price["sources"]["preis"] is None
    assert product_no_price["sources"]["gewicht"] == "edi_export"


def test_merge_invalid_upload_id(mock_uploads):
    """Test error handling for missing upload ID"""
    response = client.post("/api/merge/csv", json={
        "edi_upload_id": "nonexistent",
        "preisliste_upload_id": mock_uploads["preisliste_id"]
    })
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_conflict_resolution_priority(mock_uploads):
    """Validate field-specific priority rules (D-05, D-06 from CONTEXT)"""
    response = client.post("/api/merge/csv", json={
        "edi_upload_id": mock_uploads["edi_id"],
        "preisliste_upload_id": mock_uploads["preisliste_id"]
    })
    
    merge_file = settings.upload_dir / mock_uploads["edi_id"] / "merged_products.json"
    merge_data = json.loads(merge_file.read_text())
    
    product = next(p for p in merge_data["products"] if p["artikelnummer"] == "210100225")
    
    # Preisliste wins for price fields
    assert product["data"]["preis"] == 2.00
    assert product["data"]["menge1"] == 50
    assert product["sources"]["preis"] == "preisliste"
    assert product["sources"]["menge1"] == "preisliste"
    
    # EDI wins for master data
    assert product["data"]["gewicht"] == 0.045
    assert product["data"]["user_farbe"] == "braun"
    assert product["sources"]["gewicht"] == "edi_export"
    assert product["sources"]["user_farbe"] == "edi_export"


def test_source_tracking_accuracy(mock_uploads):
    """Verify every field has correct source attribution (D-14 from CONTEXT)"""
    response = client.post("/api/merge/csv", json={
        "edi_upload_id": mock_uploads["edi_id"],
        "preisliste_upload_id": mock_uploads["preisliste_id"]
    })
    
    merge_file = settings.upload_dir / mock_uploads["edi_id"] / "merged_products.json"
    merge_data = json.loads(merge_file.read_text())
    
    for product in merge_data["products"]:
        # Every field in data must have a source entry
        assert set(product["data"].keys()) == set(product["sources"].keys())
        
        # Sources must be valid
        for field, source in product["sources"].items():
            assert source in [None, "edi_export", "preisliste"], \
                f"Invalid source '{source}' for field '{field}'"
