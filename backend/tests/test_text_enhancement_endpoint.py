"""
Integration tests for text enhancement API endpoint.
Tests POST /api/texts/enhance with mocked Anthropic API.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.text_enhancement import EnhancementResult

client = TestClient(app)


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Create temporary upload directory."""
    return tmp_path


def test_text_enhancement_success(temp_upload_dir):
    """Test successful text enhancement (TEXT-01, TEXT-02)."""
    # Create upload directory with merged_products.json
    upload_id = "test_upload"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json with 2 products
    merged_data = {
        "total_products": 2,
        "products": [
            {
                "artikelnummer": "210100125",
                "data": {"bezeichnung1": "VERSANDTASCHE 145x190x25mm"},
                "sources": {"bezeichnung1": "edi_export"}
            },
            {
                "artikelnummer": "210100225",
                "data": {"bezeichnung1": "KARTON 305x220x100mm"},
                "sources": {"bezeichnung1": "edi_export"}
            }
        ]
    }
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    # Mock settings.upload_dir
    with patch("app.api.text_enhancement.settings.upload_dir", str(temp_upload_dir)):
        # Mock enhance_product_texts to avoid real Claude API calls
        mock_result = EnhancementResult(
            total_products=2,
            enhanced_count=2,
            skipped_count=0,
            processing_time=5.2
        )
        
        with patch("app.api.text_enhancement.enhance_product_texts", return_value=mock_result):
            response = client.post(
                "/api/texts/enhance",
                json={"upload_id": upload_id, "batch_size": 30}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["total_products"] == 2
            assert data["enhanced_count"] == 2
            assert data["skipped_count"] == 0
            assert data["processing_time"] == 5.2


def test_missing_merged_products_file(temp_upload_dir):
    """Test 404 when merged_products.json missing."""
    upload_id = "nonexistent"
    
    with patch("app.api.text_enhancement.settings.upload_dir", str(temp_upload_dir)):
        response = client.post(
            "/api/texts/enhance",
            json={"upload_id": upload_id}
        )
        
        assert response.status_code == 404
        assert "merged_products.json not found" in response.json()["detail"]


def test_custom_batch_size(temp_upload_dir):
    """Test configurable batch size (TEXT-04)."""
    # Create upload directory with merged_products.json
    upload_id = "test_batch"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    merged_data = {
        "total_products": 1,
        "products": [
            {
                "artikelnummer": "210100125",
                "data": {"bezeichnung1": "TEST"},
                "sources": {}
            }
        ]
    }
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    with patch("app.api.text_enhancement.settings.upload_dir", str(temp_upload_dir)):
        mock_result = EnhancementResult(
            total_products=1,
            enhanced_count=1,
            skipped_count=0,
            processing_time=1.0
        )
        
        with patch("app.api.text_enhancement.enhance_product_texts", return_value=mock_result) as mock_enhance:
            response = client.post(
                "/api/texts/enhance",
                json={"upload_id": upload_id, "batch_size": 20}
            )
            
            assert response.status_code == 200
            
            # Verify service was called with custom batch_size
            mock_enhance.assert_called_once()
            call_args = mock_enhance.call_args
            assert call_args.kwargs["batch_size"] == 20


def test_enhancement_statistics_accuracy(temp_upload_dir):
    """Test statistics match service output."""
    upload_id = "test_stats"
    upload_dir = temp_upload_dir / upload_id
    upload_dir.mkdir()
    
    merged_data = {
        "total_products": 10,
        "products": [
            {"artikelnummer": f"210{i:06d}", "data": {"bezeichnung1": "TEST"}, "sources": {}}
            for i in range(10)
        ]
    }
    merged_products_path = upload_dir / "merged_products.json"
    with open(merged_products_path, "w") as f:
        json.dump(merged_data, f)
    
    with patch("app.api.text_enhancement.settings.upload_dir", str(temp_upload_dir)):
        # Mock service to return specific statistics
        mock_result = EnhancementResult(
            total_products=10,
            enhanced_count=8,
            skipped_count=2,
            processing_time=12.5
        )
        
        with patch("app.api.text_enhancement.enhance_product_texts", return_value=mock_result):
            response = client.post(
                "/api/texts/enhance",
                json={"upload_id": upload_id}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response matches service output exactly
            assert data["total_products"] == 10
            assert data["enhanced_count"] == 8
            assert data["skipped_count"] == 2
            assert data["processing_time"] == 12.5
