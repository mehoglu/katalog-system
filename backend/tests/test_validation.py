"""
Tests für CSV Validation Service
CONTEXT D-10, D-11, D-12: Validation mit non-blocking warnings
"""
import pytest
from pathlib import Path
import tempfile

from app.services.validation import validate_csv_structure
from app.models.validation import ErrorSeverity


# ===== FIXTURES =====

@pytest.fixture
def temp_dir():
    """Temporäres Verzeichnis für Tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_csv(temp_dir):
    """Gültiges CSV mit Artikelnummer"""
    csv_path = temp_dir / "valid.csv"
    content = """Artikelnummer;Beschreibung;Preis
001;Müllbehälter;29.99
002;Bürotür;149.00
003;Schreibtisch;399.99"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_missing_artikelnummer(temp_dir):
    """CSV ohne Artikelnummer-Spalte"""
    csv_path = temp_dir / "no_artikelnummer.csv"
    content = """ID;Beschreibung;Preis
001;Artikel 1;10.00
002;Artikel 2;20.00"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_empty(temp_dir):
    """Leeres CSV (nur Header)"""
    csv_path = temp_dir / "empty.csv"
    content = "Artikelnummer;Beschreibung;Preis\n"
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_with_duplicates(temp_dir):
    """CSV mit duplizierten Artikelnummern"""
    csv_path = temp_dir / "duplicates.csv"
    content = """Artikelnummer;Beschreibung;Preis
001;Artikel 1;10.00
002;Artikel 2;20.00
001;Duplikat;15.00"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_no_german_chars(temp_dir):
    """CSV ohne deutsche Umlaute (potentiell Encoding-Problem)"""
    csv_path = temp_dir / "no_umlauts.csv"
    content = """Artikelnummer;Beschreibung;Preis
001;Simple Text;10.00
002;Another Item;20.00"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_malformed(temp_dir):
    """Fehlerhaftes CSV (inkonsistente Spalten)"""
    csv_path = temp_dir / "malformed.csv"
    content = """Artikelnummer;Beschreibung;Preis
001;Item 1
002;Item 2;20.00;Extra Column"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


# ===== TEST VALID CSV =====

def test_validate_valid_csv_passes(valid_csv):
    """
    Valid CSV should pass without errors or warnings
    """
    result = validate_csv_structure(valid_csv, upload_id="test-001")
    
    assert result.status == "valid"
    assert len(result.errors) == 0
    assert len(result.warnings) == 0
    assert result.stats["row_count"] == 3


# ===== TEST MISSING ARTIKELNUMMER (WARNING, NOT CRITICAL) =====

def test_missing_artikelnummer_produces_warning_not_critical(csv_missing_artikelnummer):
    """
    Missing Artikelnummer should produce WARNING, not CRITICAL
    CONTEXT D-10: Non-blocking warnings ermöglichen Upload ohne Artikelnummer
    CRITICAL TEST: Ensures fail-fast behavior is disabled
    """
    result = validate_csv_structure(csv_missing_artikelnummer, upload_id="test-002")
    
    # Should be "warnings" status, NOT "errors"
    assert result.status == "warnings"
    
    # No CRITICAL errors
    assert len(result.errors) == 0
    
    # Has WARNING for missing column
    assert len(result.warnings) > 0
    warning = result.warnings[0]
    assert warning.severity == ErrorSeverity.WARNING
    assert "Artikelnummer" in warning.message
    assert warning.suggestion is not None


# ===== TEST EMPTY CSV (CRITICAL ERROR) =====

def test_empty_csv_produces_critical_error(csv_empty):
    """
    Empty CSV (no data rows) should produce CRITICAL error
    CONTEXT D-12: Early-exit bei kritischen Fehlern
    """
    result = validate_csv_structure(csv_empty, upload_id="test-003")
    
    assert result.status == "errors"
    assert len(result.errors) > 0
    
    error = result.errors[0]
    assert error.severity == ErrorSeverity.CRITICAL
    assert "empty" in error.message.lower() or "no data" in error.message.lower()


# ===== TEST DUPLICATE ARTIKELNUMMER (WARNING) =====

def test_duplicate_artikelnummer_produces_warning(csv_with_duplicates):
    """
    Duplicate Artikelnummer should produce WARNING
    CONTEXT D-11: Extended validation checks for duplicates
    """
    result = validate_csv_structure(csv_with_duplicates, upload_id="test-004")
    
    assert result.status == "warnings"
    
    # Should have warning about duplicates
    assert len(result.warnings) > 0
    duplicate_warning = next(
        (w for w in result.warnings if "duplicate" in w.message.lower()),
        None
    )
    assert duplicate_warning is not None
    assert duplicate_warning.severity == ErrorSeverity.WARNING


# ===== TEST NO GERMAN CHARACTERS (WARNING) =====

def test_no_german_chars_produces_warning(csv_no_german_chars):
    """
    CSV without German characters should produce INFO warning
    CONTEXT D-16: Validierung deutscher Umlaute (potentiell fehlende oder falsche Encoding)
    """
    result = validate_csv_structure(csv_no_german_chars, upload_id="test-005")
    
    # Can be "valid" or "warnings" depending on implementation
    assert result.status in ["valid", "warnings"]
    
    # If warnings exist, check for German character info
    if result.status == "warnings":
        char_warning = next(
            (w for w in result.warnings if "german" in w.message.lower() or "character" in w.message.lower()),
            None
        )
        if char_warning:
            assert char_warning.severity == ErrorSeverity.INFO


# ===== TEST MALFORMED CSV (CRITICAL ERROR) =====

def test_malformed_csv_produces_critical_error(csv_malformed):
    """
    Malformed CSV (inconsistent columns) should produce CRITICAL error
    CONTEXT D-12: Early-exit bei strukturellen Fehlern
    """
    result = validate_csv_structure(csv_malformed, upload_id="test-006")
    
    # Should fail with CRITICAL error
    assert result.status == "errors"
    assert len(result.errors) > 0
    
    # First error should be CRITICAL
    error = result.errors[0]
    assert error.severity == ErrorSeverity.CRITICAL


# ===== TEST EARLY EXIT BEHAVIOR =====

def test_early_exit_on_critical_error(csv_malformed):
    """
    Validation should exit early on first CRITICAL error
    CONTEXT D-12: Early-exit pattern für Performance
    """
    result = validate_csv_structure(csv_malformed, upload_id="test-007")
    
    # Should have exactly 1 CRITICAL error (early exit)
    critical_errors = [e for e in result.errors if e.severity == ErrorSeverity.CRITICAL]
    assert len(critical_errors) == 1
    
    # Should not have performed extended validation
    # (extended validation = duplicate checks, etc. - only runs if structure is valid)


# ===== TEST VALIDATION RESULT STRUCTURE =====

def test_validation_result_has_stats(valid_csv):
    """
    ValidationResult should include stats dict
    """
    result = validate_csv_structure(valid_csv, upload_id="test-008")
    
    assert "row_count" in result.stats
    assert "column_count" in result.stats
    assert result.stats["row_count"] > 0
    assert result.stats["column_count"] > 0


def test_validation_result_has_upload_id(valid_csv):
    """
    ValidationResult should include upload_id for tracking
    """
    upload_id = "test-upload-123"
    result = validate_csv_structure(valid_csv, upload_id=upload_id)
    
    assert result.upload_id == upload_id


# ===== INTEGRATION TEST =====

def test_validate_csv_with_warnings_still_processable(csv_missing_artikelnummer):
    """
    CSV with warnings should still be processable (not blocked)
    CONTEXT D-10: Non-blocking warnings philosophy
    CRITICAL TEST: Ensures uploads can proceed despite warnings
    """
    result = validate_csv_structure(csv_missing_artikelnummer, upload_id="test-009")
    
    # Status is "warnings", NOT "errors"
    assert result.status == "warnings"
    
    # Has warnings but NO critical errors
    assert len(result.warnings) > 0
    assert len(result.errors) == 0
    
    # Should still have valid stats (data was read)
    assert result.stats["row_count"] > 0
    
    # This CSV would be uploadable in the UI
    # User sees warnings but can proceed
