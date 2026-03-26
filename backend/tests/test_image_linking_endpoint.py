"""
Integration tests for image linking API endpoint.
Tests POST /api/images/link with mocked file system.
"""
import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_image_linking_success(temp_upload_dir):
    """Test successful image linking (IMAGE-01, IMAGE-02)."""
    # Create upload directory with merged_products.json
    upload_id = "test_upload"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json with 2 products
    merged_data = [
        {
            "artikelnummer": "210100125",
            "data": {"bezeichnung1": "Product 1"},
            "sources": {"bezeichnung1": "edi_export"}
        },
        {
            "artikelnummer": "210100225",
            "data": {"bezeichnung1": "Product 2"},
            "sources": {"bezeichnung1": "edi_export"}
        }
    ]
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    # Create manual_image_mapping.json
    image_mapping = {
        "mappings": {
            "210100125": [
                {"filename": "210100125A.jpg", "path": "assets/bilder/210100125A.jpg", "type": "front"}
            ],
            "210100225": [
                {"filename": "210100225A.jpg", "path": "assets/bilder/210100225A.jpg", "type": "front"}
            ]
        }
    }
    mapping_path = temp_upload_dir / "manual_image_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(image_mapping, f)
    
    # Mock settings.upload_dir and image mapping path
    with patch("app.api.image_linking.settings.upload_dir", str(temp_upload_dir)):
        with patch("app.api.image_linking.Path") as mock_path:
            # Mock Path(".planning/manual_image_mapping.json") to point to our temp file
            def path_side_effect(arg):
                if arg == ".planning/manual_image_mapping.json":
                    return mapping_path
                return Path(arg)
            mock_path.side_effect = path_side_effect
            
            # Call endpoint
            response = client.post(
                "/api/images/link",
                json={"upload_id": upload_id}
            )
    
    # Assert success
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_products"] == 2
    assert data["products_with_images"] == 2
    assert data["products_without_images"] == 0
    
    # Verify merged_products.json was updated
    with open(merged_products_path) as f:
        products = json.load(f)
    assert "images" in products[0]["data"]
    assert len(products[0]["data"]["images"]) == 1
    assert products[0]["data"]["images"][0]["filename"] == "210100125A.jpg"


def test_missing_merged_products_file(temp_upload_dir):
    """Test 404 error when merged_products.json missing."""
    upload_id = "test_upload"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    # Don't create merged_products.json
    
    with patch("app.api.image_linking.settings.upload_dir", str(temp_upload_dir)):
        response = client.post(
            "/api/images/link",
            json={"upload_id": upload_id}
        )
    
    assert response.status_code == 404
    assert "merged_products.json not found" in response.json()["detail"]


def test_missing_image_mapping_file(temp_upload_dir):
    """Test 404 error when manual_image_mapping.json missing."""
    upload_id = "test_upload"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json
    merged_data = [{"artikelnummer": "210100125", "data": {}, "sources": {}}]
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    with patch("app.api.image_linking.settings.upload_dir", str(temp_upload_dir)):
        with patch("app.api.image_linking.Path") as mock_path:
            # Mock Path to return non-existent file for image mapping
            def path_side_effect(arg):
                if arg == ".planning/manual_image_mapping.json":
                    fake_path = Path("/nonexistent/file.json")
                    return fake_path
                return Path(arg)
            mock_path.side_effect = path_side_effect
            
            response = client.post(
                "/api/images/link",
                json={"upload_id": upload_id}
            )
    
    assert response.status_code == 404
    assert "manual_image_mapping.json not found" in response.json()["detail"]


def test_image_statistics_accuracy(temp_upload_dir):
    """Test statistics accuracy with mixed matches (IMAGE-01, IMAGE-04)."""
    upload_id = "test_upload"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json with 5 products
    merged_data = [
        {"artikelnummer": "210100125", "data": {}, "sources": {}},
        {"artikelnummer": "210100225", "data": {}, "sources": {}},
        {"artikelnummer": "210100325", "data": {}, "sources": {}},
        {"artikelnummer": "999999998", "data": {}, "sources": {}},
        {"artikelnummer": "999999999", "data": {}, "sources": {}}
    ]
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    # Create image mapping with only 3 matches
    image_mapping = {
        "mappings": {
            "210100125": [{"filename": "210100125.jpg", "path": "assets/bilder/210100125.jpg", "type": "main"}],
            "210100225": [{"filename": "210100225.jpg", "path": "assets/bilder/210100225.jpg", "type": "main"}],
            "210100325": [{"filename": "210100325.jpg", "path": "assets/bilder/210100325.jpg", "type": "main"}]
        }
    }
    mapping_path = temp_upload_dir / "manual_image_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(image_mapping, f)
    
    with patch("app.api.image_linking.settings.upload_dir", str(temp_upload_dir)):
        with patch("app.api.image_linking.Path") as mock_path:
            def path_side_effect(arg):
                if arg == ".planning/manual_image_mapping.json":
                    return mapping_path
                return Path(arg)
            mock_path.side_effect = path_side_effect
            
            response = client.post(
                "/api/images/link",
                json={"upload_id": upload_id}
            )
    
    # Assert statistics
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] == 5
    assert data["products_with_images"] == 3
    assert data["products_without_images"] == 2
    assert data["unused_image_mappings"] == 0  # All mappings used
