"""
Tests for CSV sampling service.
"""
import pytest
from pathlib import Path
import tempfile

from app.services.csv_sampling import sample_csv_for_llm


@pytest.fixture
def temp_dir():
    """Temporary directory for test CSVs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def small_csv(temp_dir):
    """CSV with 5 rows (small)."""
    csv_path = temp_dir / "small.csv"
    content = """Artikelnummer;Bezeichnung;Preis
D001;Müllbehälter;29.99
D002;Bürotür;149.00
D003;Schreibtisch;399.99
D004;Stuhl;89.99
D005;Regal;199.99"""
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


@pytest.fixture
def large_csv(temp_dir):
    """CSV with 500 rows (large)."""
    csv_path = temp_dir / "large.csv"
    lines = ["Artikelnummer;Bezeichnung;Preis"]
    for i in range(500):
        lines.append(f"D{i:03d};Produkt {i};{10 + i}.99")
    csv_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path


def test_sample_small_csv_uses_all_rows(small_csv):
    """Small CSV (<=10 rows) returns all rows."""
    result = sample_csv_for_llm(small_csv, max_rows=10)
    
    # Should contain all 5 data rows + header
    lines = result.strip().split("\n")
    assert len(lines) == 6  # 1 header + 5 data rows
    assert "D001" in result
    assert "D005" in result


def test_sample_large_csv_uses_intelligent_sampling(large_csv):
    """Large CSV (>10 rows) uses first 5 + random 5."""
    result = sample_csv_for_llm(large_csv, max_rows=10)
    
    # Should contain exactly 10 rows + header
    lines = result.strip().split("\n")
    assert len(lines) == 11  # 1 header + 10 data rows
    
    # Should include first 5
    assert "D000" in result
    assert "D004" in result


def test_sample_uses_semicolon_delimiter(small_csv):
    """Output uses semicolon delimiter (German standard)."""
    result = sample_csv_for_llm(small_csv)
    
    assert ";" in result
    assert "Artikelnummer;Bezeichnung;Preis" in result


def test_sample_empty_csv_raises_error(temp_dir):
    """Empty CSV raises ValueError."""
    empty_csv = temp_dir / "empty.csv"
    empty_csv.write_text("Artikelnummer;Bezeichnung\n", encoding="utf-8")
    
    with pytest.raises(ValueError, match="empty"):
        sample_csv_for_llm(empty_csv)


def test_sample_invalid_csv_raises_error(temp_dir):
    """Unreadable CSV raises ValueError."""
    bad_csv = temp_dir / "bad.csv" 
    bad_csv.write_text("not a csv!", encoding="utf-8")
    
    with pytest.raises(ValueError, match="Cannot read"):
        sample_csv_for_llm(bad_csv)
