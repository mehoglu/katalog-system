"""
Unit tests for CSV merge service.
Validates FUSION requirements and CONTEXT decisions.
"""
import pytest
from pathlib import Path
from app.services.csv_merge import merge_csv_data
from app.models.merge import MergeResult, MergedProduct


@pytest.fixture
def sample_edi_csv(tmp_path):
    """Create realistic EDI Export CSV with semicolon delimiter"""
    csv_content = """Artikelnummer;Bezeichnung1;Bezeichnung2;Gewicht;USER_Farbe;USER_Material
210100125;VERSANDTASCHE AUS WELLPAPPE CD;sk m. Aufreißfaden braun;0.028;braun;1.20e KLS
210100225;VERSANDTASCHE AUS WELLPAPPE DVD;sk m. Aufreißfaden braun;0.045;braun;1.20e KLS
999999999;TESTPRODUKT OHNE PREIS;nur in EDI;0.100;schwarz;Test Material"""
    
    csv_file = tmp_path / "edi.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


@pytest.fixture
def sample_preisliste_csv(tmp_path):
    """Create realistic Preisliste CSV with semicolon delimiter"""
    csv_content = """Artikelnummer;preis;menge1;menge2;menge3;menge4;menge5
210100125;1.50;100;500;1000;5000;10000
210100225;2.00;50;250;500;2500;5000
888888888;3.00;25;100;250;1000;2500"""
    
    csv_file = tmp_path / "preisliste.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


def test_merge_basic(sample_edi_csv, sample_preisliste_csv):
    """Test basic merge functionality - FUSION-01"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    assert isinstance(result, MergeResult)
    assert result.total_products == 3  # All EDI products preserved (D-01)
    assert result.matched == 2  # 210100125, 210100225 in both
    assert result.edi_only == 1  # 999999999 only in EDI
    assert len(result.products) == 3


def test_field_priority(sample_edi_csv, sample_preisliste_csv):
    """Test field-specific conflict resolution - FUSION-02, D-05, D-06"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    # Find matched product
    product = next(p for p in result.products if p.artikelnummer == "210100125")
    
    # Preisliste wins for price fields (D-05)
    assert product.data.get("preis") == 1.50
    assert product.data.get("menge1") == 100
    assert product.sources.get("preis") == "preisliste"
    assert product.sources.get("menge1") == "preisliste"
    
    # EDI wins for master data (D-06)
    assert product.data.get("gewicht") == 0.028
    assert product.data.get("user_farbe") == "braun"
    assert product.sources.get("gewicht") == "edi_export"
    assert product.sources.get("user_farbe") == "edi_export"


def test_missing_price(sample_edi_csv, sample_preisliste_csv):
    """Test products without price match - FUSION-03, D-03, D-09"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    # Find EDI-only product
    product = next(p for p in result.products if p.artikelnummer == "999999999")
    
    # Product exists with null price (D-03, D-09)
    assert product.data.get("preis") is None
    assert product.sources.get("preis") is None
    
    # EDI data preserved
    assert product.data.get("bezeichnung1") == "TESTPRODUKT OHNE PREIS"
    assert product.data.get("gewicht") == 0.100
    assert product.sources.get("gewicht") == "edi_export"


def test_source_tracking(sample_edi_csv, sample_preisliste_csv):
    """Test source tracking completeness - D-12, D-14"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    for product in result.products:
        # Every field in data must have a source entry (D-14)
        assert set(product.data.keys()) == set(product.sources.keys())
        
        # Sources must be valid (D-14)
        for field, source in product.sources.items():
            assert source in [None, "edi_export", "preisliste"], \
                f"Invalid source '{source}' for field '{field}' in product {product.artikelnummer}"


def test_left_join_preserves_all_edi(sample_edi_csv, sample_preisliste_csv):
    """Test left join preserves all EDI products - D-01, D-02"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    # All 3 EDI products must be in result
    artikelnummern = {p.artikelnummer for p in result.products}
    assert "210100125" in artikelnummern
    assert "210100225" in artikelnummern
    assert "999999999" in artikelnummern
    
    # Product only in Preisliste (888888888) should NOT be in result (D-02)
    assert "888888888" not in artikelnummern


def test_merge_result_structure(sample_edi_csv, sample_preisliste_csv):
    """Test MergeResult structure - FUSION-04"""
    result = merge_csv_data(sample_edi_csv, sample_preisliste_csv)
    
    # Verify result structure
    assert hasattr(result, "total_products")
    assert hasattr(result, "edi_only")
    assert hasattr(result, "matched")
    assert hasattr(result, "merge_timestamp")
    assert hasattr(result, "products")
    
    # Verify timestamp format
    assert "T" in result.merge_timestamp  # ISO format
    
    # Verify counts add up
    assert result.total_products == result.edi_only + result.matched


def test_null_handling(sample_edi_csv, tmp_path):
    """Test null value handling - D-09, D-10"""
    # Create Preisliste with explicit nulls represented as empty fields
    preisliste_content = """Artikelnummer;preis;menge1
210100125;;100"""
    preisliste_file = tmp_path / "preisliste_nulls.csv"
    preisliste_file.write_text(preisliste_content, encoding="utf-8")
    
    result = merge_csv_data(sample_edi_csv, preisliste_file)
    product = result.products[0]
    
    # Null price should be None, not empty string (D-09)
    assert product.data.get("preis") is None
    assert product.sources.get("preis") is None
    
    # Non-null fields work normally
    assert product.data.get("menge1") == 100
    assert product.sources.get("menge1") == "preisliste"
