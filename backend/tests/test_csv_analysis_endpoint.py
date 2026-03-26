"""
Integration tests for CSV analysis endpoint.
RESEARCH §Validation Architecture - Integration Tests + Manual Verification
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.main import app
from backend.app.models.csv_analysis import CSVAnalysisResult, ColumnMapping


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_analysis_result():
    """Mock successful analysis result."""
    return CSVAnalysisResult(mappings=[
        ColumnMapping(
            csv_column="Artikelnummer",
            product_field="article_number",
            confidence=0.98,
            is_join_key=True,
            reasoning="Clear article ID pattern"
        ),
        ColumnMapping(
            csv_column="Bezeichnung1",
            product_field="product_name",
            confidence=0.95,
            is_join_key=False,
            reasoning="Product name field"
        ),
        ColumnMapping(
            csv_column="Preis",
            product_field="price",
            confidence=0.92,
            is_join_key=False,
            reasoning="Price field"
        )
    ])


@pytest.mark.asyncio
@patch("backend.app.api.csv_analysis.analyze_csv_structure")
async def test_analyze_csv_endpoint_success(mock_analyze, client, mock_analysis_result):
    """Successful CSV analysis returns mappings."""
    # Mock the analysis service to avoid Claude API calls
    mock_analyze.return_value = mock_analysis_result
    
    # Assume upload_id "test-session" exists from Phase 1
    response = client.post("/api/analyze/csv/test-session")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure (Requirement CSV-03)
    assert "upload_id" in data
    assert "mappings" in data
    assert "join_key" in data
    assert data["join_key"] == "Artikelnummer"  # Requirement CSV-02
    
    # Verify confidence handling (CONTEXT D-14)
    assert "requires_confirmation" in data
    assert data["requires_confirmation"] == False  # All confidence >0.9


@pytest.mark.asyncio
@patch("backend.app.api.csv_analysis.analyze_csv_structure")
async def test_analyze_csv_endpoint_low_confidence(mock_analyze, client):
    """Low confidence mappings flagged for user."""
    # Mock result with low confidence mapping
    low_conf_result = CSVAnalysisResult(mappings=[
        ColumnMapping(
            csv_column="Artikelnummer",
            product_field="article_number",
            confidence=0.98,
            is_join_key=True,
            reasoning="Clear"
        ),
        ColumnMapping(
            csv_column="F1",
            product_field="unknown",
            confidence=0.5,  # LOW CONFIDENCE
            is_join_key=False,
            reasoning="Ambiguous"
        )
    ])
    mock_analyze.return_value = low_conf_result
    
    response = client.post("/api/analyze/csv/test-session")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should flag for confirmation (CONTEXT D-15)
    assert data["requires_confirmation"] == True
    assert data["low_confidence_count"] == 1


@pytest.mark.asyncio
async def test_analyze_csv_endpoint_not_found(client):
    """Non-existent upload_id returns 404."""
    response = client.post("/api/analyze/csv/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@patch("backend.app.api.csv_analysis.analyze_csv_structure")
async def test_analyze_csv_endpoint_no_join_key(mock_analyze, client):
    """Analysis with no join key returns 422."""
    # Mock validation failure
    mock_analyze.side_effect = ValueError("No join key detected")
    
    response = client.post("/api/analyze/csv/test-session")
    
    assert response.status_code == 422
    assert "join key" in response.json()["detail"].lower()
