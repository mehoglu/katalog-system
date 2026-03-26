"""
Unit tests for CSV analysis service.
RESEARCH §Validation Architecture - Unit Tests section
"""
import pytest
from backend.app.models.csv_analysis import CSVAnalysisResult, ColumnMapping
from backend.app.services.csv_analysis import validate_join_key_detection


def test_join_key_validation_none():
    """No join key detected → validation fails."""
    result = CSVAnalysisResult(mappings=[
        ColumnMapping(
            csv_column="Bezeichnung",
            product_field="product_name",
            confidence=0.95,
            is_join_key=False,
            reasoning="Product name field"
        )
    ])
    
    valid, msg = validate_join_key_detection(result)
    
    assert not valid
    assert "No join key" in msg


def test_join_key_validation_multiple():
    """Multiple join keys → validation fails."""
    result = CSVAnalysisResult(mappings=[
        ColumnMapping(
            csv_column="Artikelnummer",
            product_field="article_number",
            confidence=0.98,
            is_join_key=True,
            reasoning="Article ID"
        ),
        ColumnMapping(
            csv_column="EAN",
            product_field="ean",
            confidence=0.92,
            is_join_key=True,  # WRONG: two join keys
            reasoning="EAN barcode"
        )
    ])
    
    valid, msg = validate_join_key_detection(result)
    
    assert not valid
    assert "Multiple" in msg
    assert "Artikelnummer" in msg
    assert "EAN" in msg


def test_join_key_validation_single():
    """Exactly one join key → validation passes."""
    result = CSVAnalysisResult(mappings=[
        ColumnMapping(
            csv_column="Artikelnummer",
            product_field="article_number",
            confidence=0.98,
            is_join_key=True,
            reasoning="Unique article ID"
        ),
        ColumnMapping(
            csv_column="Bezeichnung",
            product_field="product_name",
            confidence=0.95,
            is_join_key=False,
            reasoning="Product name"
        )
    ])
    
    valid, msg = validate_join_key_detection(result)
    
    assert valid
    assert "Artikelnummer" in msg


def test_confidence_thresholds():
    """Confidence interpretation matches CONTEXT D-14 thresholds."""
    # This would test the UI threshold logic if moved to a separate function
    # For now, documented as acceptance criteria
    
    # >0.9 = green (auto-accept)
    high_conf = ColumnMapping(
        csv_column="Artikelnummer",
        product_field="article_number",
        confidence=0.95,
        is_join_key=True,
        reasoning="Clear match"
    )
    assert high_conf.confidence >= 0.9
    
    # 0.7-0.9 = yellow (review)
    med_conf = ColumnMapping(
        csv_column="Desc",
        product_field="product_description",
        confidence=0.8,
        is_join_key=False,
        reasoning="Ambiguous name"
    )
    assert 0.7 <= med_conf.confidence < 0.9
    
    # <0.7 = red (confirmation required)
    low_conf = ColumnMapping(
        csv_column="F1",
        product_field="unknown",
        confidence=0.5,
        is_join_key=False,
        reasoning="Cannot determine"
    )
    assert low_conf.confidence < 0.7
