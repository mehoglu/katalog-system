"""
Tests für Encoding Detection Service
CONTEXT D-13, D-14, D-19: Encoding-Erkennung mit charset-normalizer
"""
import pytest
from pathlib import Path
import tempfile

from app.services.encoding import detect_encoding, convert_to_utf8, validate_german_umlauts


# ===== FIXTURES =====

@pytest.fixture
def temp_dir():
    """Temporäres Verzeichnis für Tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def csv_windows1252(temp_dir):
    """CSV mit Windows-1252 Encoding und deutschen Umlauten"""
    csv_path = temp_dir / "test_windows1252.csv"
    # Windows-1252 encoded string with German umlauts
    content = "Artikelnummer;Beschreibung;Preis\n001;Müllbehälter groß;29.99\n002;Bürotür;149.00\n"
    csv_path.write_bytes(content.encode("windows-1252"))
    return csv_path


@pytest.fixture
def csv_utf8(temp_dir):
    """CSV mit UTF-8 Encoding"""
    csv_path = temp_dir / "test_utf8.csv"
    content = "Artikelnummer;Beschreibung;Preis\n001;Müllbehälter groß;29.99\n002;Bürotür;149.00\n"
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def csv_mojibake(temp_dir):
    """CSV mit Mojibake (falsch dekodierte Umlaute)"""
    csv_path = temp_dir / "test_mojibake.csv"
    # UTF-8 bytes interpreted as Windows-1252 creates mojibake
    original = "Müllbehälter".encode("utf-8")
    mojibake = original.decode("windows-1252")
    content = f"Artikelnummer;Beschreibung\n001;{mojibake}\n"
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


# ===== TEST ENCODING DETECTION =====

def test_detect_windows1252_encoding(csv_windows1252):
    """
    Detect Windows-1252 encoding correctly
    CONTEXT D-13: charset-normalizer kann Windows-1252 erkennen
    """
    result = detect_encoding(csv_windows1252)
    
    assert result.detected_encoding.lower() in ["windows-1252", "cp1252"]
    assert result.confidence > 0.7  # High confidence
    assert not result.is_fallback


def test_detect_utf8_encoding(csv_utf8):
    """
    Detect UTF-8 encoding correctly
    """
    result = detect_encoding(csv_utf8)
    
    assert result.detected_encoding.lower() == "utf-8"
    assert result.confidence > 0.7
    assert not result.is_fallback


def test_encoding_confidence_threshold(temp_dir):
    """
    Test confidence threshold logic
    CONTEXT D-14: Fallback auf Windows-1252 bei niedriger Confidence
    """
    # Create file with ambiguous encoding
    ambiguous_path = temp_dir / "ambiguous.csv"
    ambiguous_path.write_text("ID;Name\n1;Test\n", encoding="ascii")
    
    result = detect_encoding(ambiguous_path)
    
    # ASCII-only content may have lower confidence
    assert result.detected_encoding is not None
    if result.confidence < 0.7:
        assert result.needs_confirmation
        # Should fallback to Windows-1252
        assert result.detected_encoding.lower() in ["windows-1252", "cp1252"]
        assert result.is_fallback


# ===== TEST ENCODING CONVERSION =====

def test_convert_windows1252_to_utf8_preserves_umlauts(csv_windows1252, temp_dir):
    """
    Convert Windows-1252 to UTF-8 preserving German umlauts
    CRITICAL TEST: "Müllbehälter" muss korrekt sein
    CONTEXT D-16: Umlaute validieren nach Konversion
    """
    output_path = temp_dir / "converted.csv"
    
    success, error = convert_to_utf8(
        csv_windows1252,
        output_path,
        "windows-1252"
    )
    
    assert success
    assert error is None
    assert output_path.exists()
    
    # Verify content
    converted_content = output_path.read_text(encoding="utf-8")
    assert "Müllbehälter" in converted_content
    assert "Bürotür" in converted_content
    # No mojibake
    assert "Ã¼" not in converted_content
    assert "Ã¶" not in converted_content


def test_convert_utf8_to_utf8_is_noop(csv_utf8, temp_dir):
    """
    Converting UTF-8 to UTF-8 should work without issues
    """
    output_path = temp_dir / "converted_utf8.csv"
    
    success, error = convert_to_utf8(
        csv_utf8,
        output_path,
        "utf-8"
    )
    
    assert success
    assert output_path.exists()
    
    # Content should be identical
    original = csv_utf8.read_text(encoding="utf-8")
    converted = output_path.read_text(encoding="utf-8")
    assert original == converted


def test_convert_with_invalid_encoding_fails(csv_utf8, temp_dir):
    """
    Conversion with invalid encoding should fail gracefully
    """
    output_path = temp_dir / "output.csv"
    
    success, error = convert_to_utf8(
        csv_utf8,
        output_path,
        "invalid-encoding-xyz"
    )
    
    assert not success
    assert error is not None
    assert "encoding" in error.lower() or "unknown" in error.lower()


# ===== TEST MOJIBAKE DETECTION =====

def test_validate_german_umlauts_detects_correct_encoding(csv_utf8):
    """
    Validate that correctly encoded German umlauts pass
    CONTEXT D-16: Validierung deutscher Umlaute
    """
    is_valid, issues = validate_german_umlauts(csv_utf8)
    
    assert is_valid
    assert len(issues) == 0


def test_validate_german_umlauts_detects_mojibake(csv_mojibake):
    """
    Detect mojibake patterns (Ã¼, Ã¶, Ã¤, ÃŸ)
    CRITICAL: German text corruption detection
    """
    is_valid, issues = validate_german_umlauts(csv_mojibake)
    
    assert not is_valid
    assert len(issues) > 0
    # Should detect mojibake pattern
    assert any("Ã" in issue or "mojibake" in issue.lower() for issue in issues)


def test_validate_german_umlauts_with_no_umlauts(temp_dir):
    """
    Files without umlauts should pass validation
    """
    simple_csv = temp_dir / "simple.csv"
    simple_csv.write_text("ID;Name;Price\n1;Test;10.00\n", encoding="utf-8")
    
    is_valid, issues = validate_german_umlauts(simple_csv)
    
    assert is_valid
    assert len(issues) == 0


# ===== INTEGRATION TEST =====

def test_full_encoding_pipeline(csv_windows1252, temp_dir):
    """
    End-to-end test: Detect → Convert → Validate
    CONTEXT D-13 + D-14 + D-16: Vollständiger Encoding-Workflow
    """
    # Step 1: Detect
    detection = detect_encoding(csv_windows1252)
    assert detection.detected_encoding.lower() in ["windows-1252", "cp1252"]
    
    # Step 2: Convert
    output_path = temp_dir / "final.csv"
    success, error = convert_to_utf8(
        csv_windows1252,
        output_path,
        detection.detected_encoding
    )
    assert success
    
    # Step 3: Validate
    is_valid, issues = validate_german_umlauts(output_path)
    assert is_valid
    assert len(issues) == 0
    
    # Verify final content
    final_content = output_path.read_text(encoding="utf-8")
    assert "Müllbehälter" in final_content
