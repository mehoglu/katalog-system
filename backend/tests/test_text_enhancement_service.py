"""
Unit tests for text enhancement service.

Covers TEXT-01 through TEXT-04 requirements with mocked Anthropic API.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock
import tempfile

from app.services.text_enhancement import (
    enhance_product_texts,
    extract_critical_terms,
    quality_check_preservation
)
from app.models.text_enhancement import EnhancementResult


class TestExtractCriticalTerms:
    """Test critical term extraction for quality checks."""
    
    def test_extracts_measurements(self):
        """Test extraction of measurements from text."""
        text = "VERSANDTASCHE 145x190x25mm, Gewicht 0.028kg"
        terms = extract_critical_terms(text)
        
        # Check that at least one measurement was found
        assert len(terms) > 0
        assert any("mm" in t or "kg" in t for t in terms)
    
    def test_extracts_technical_codes(self):
        """Test extraction of technical codes (VE, KLS, etc.)."""
        text = "VE 4x25 St., KLS braun, WS 70"
        terms = extract_critical_terms(text)
        
        assert "ve" in terms
        assert "kls" in terms
        assert "ws" in terms
    
    def test_handles_empty_text(self):
        """Test extraction handles empty/None text."""
        assert extract_critical_terms("") == set()
        assert extract_critical_terms(None) == set()


class TestQualityCheckPreservation:
    """Test preservation quality checks (TEXT-03)."""
    
    def test_passes_when_all_terms_preserved(self):
        """Test quality check passes when measurements preserved."""
        original = "VERSANDTASCHE 145x190x25mm"
        enhanced = "Versandtasche (145×190×25 mm)"
        
        assert quality_check_preservation(original, enhanced) is True
    
    def test_fails_when_measurement_missing(self):
        """Test quality check fails when measurement removed."""
        original = "VERSANDTASCHE 145x190x25mm"
        enhanced = "Versandtasche für CDs"  # Missing measurements!
        
        assert quality_check_preservation(original, enhanced) is False
    
    def test_fails_when_technical_code_missing(self):
        """Test quality check fails when technical code removed."""
        original = "Packung VE 4x25 St."
        enhanced = "Packung mit 100 Stück"  # Missing VE!
        
        assert quality_check_preservation(original, enhanced) is False


class TestEnhanceProductTexts:
    """Test main enhancement function (TEXT-01, TEXT-02, TEXT-04)."""
    
    @pytest.fixture
    def temp_products_file(self, tmp_path):
        """Create temporary merged_products.json for testing."""
        products_data = {
            "total_products": 3,
            "matched": 3,
            "edi_only": 0,
            "merge_timestamp": "2026-03-26T10:00:00",
            "products": [
                {
                    "artikelnummer": "210100125",
                    "data": {
                        "bezeichnung1": "VERSANDTASCHE AUS WELLPAPPE CD, 145x190x25mm",
                        "bezeichnung2": "sk m. Aufreißfaden, braun, VE 4x25 St."
                    },
                    "sources": {
                        "bezeichnung1": "edi_export",
                        "bezeichnung2": "edi_export"
                    }
                },
                {
                    "artikelnummer": "210100225",
                    "data": {
                        "bezeichnung1": "VERSANDTASCHE AUS WELLPAPPE DVD, 150x250x50mm",
                        "bezeichnung2": "sk m. Aufreißfaden, weiß, VE 4x25 St."
                    },
                    "sources": {
                        "bezeichnung1": "edi_export",
                        "bezeichnung2": "edi_export"
                    }
                },
                {
                    "artikelnummer": "210100325",
                    "data": {
                        "bezeichnung1": "KARTON MIT AUTOMATIKBODEN 305x220x100mm"
                    },
                    "sources": {
                        "bezeichnung1": "edi_export"
                    }
                }
            ]
        }
        
        file_path = tmp_path / "merged_products.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(products_data, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    @pytest.mark.asyncio
    async def test_basic_enhancement(self, temp_products_file):
        """Test basic enhancement with mocked Claude API (TEXT-01, TEXT-02)."""
        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps([
            {
                "artikelnummer": "210100125",
                "bezeichnung1": "Versandtasche aus Wellpappe für CDs (145×190×25 mm)",
                "bezeichnung2": "Selbstklebend mit Aufreißfaden, braun. Verpackungseinheit: 4×25 Stück."
            },
            {
                "artikelnummer": "210100225",
                "bezeichnung1": "Versandtasche aus Wellpappe für DVDs (150×250×50 mm)",
                "bezeichnung2": "Selbstklebend mit Aufreißfaden, weiß. Verpackungseinheit: 4×25 Stück."
            },
            {
                "artikelnummer": "210100325",
                "bezeichnung1": "Karton mit Automatikboden (305×220×100 mm)",
                "bezeichnung2": None
            }
        ], ensure_ascii=False))]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await enhance_product_texts(temp_products_file, batch_size=30)
            
            # Verify result statistics
            assert result.total_products == 3
            assert result.enhanced_count == 3
            assert result.skipped_count == 0
            assert result.processing_time > 0
            
            # Verify file was updated
            with open(temp_products_file, "r", encoding="utf-8") as f:
                updated_data = json.load(f)
            
            # Check first product has enhanced texts
            first_product = updated_data["products"][0]
            assert "bezeichnung1_enhanced" in first_product["data"]
            assert "llm_enhancement" == first_product["sources"]["bezeichnung1_enhanced"]
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, tmp_path):
        """Test batch processing with 60 products (TEXT-04)."""
        # Create file with 60 products
        products_data = {
            "total_products": 60,
            "products": [
                {
                    "artikelnummer": f"210{i:06d}",
                    "data": {"bezeichnung1": f"PRODUCT {i}, 100mm"},
                    "sources": {"bezeichnung1": "edi_export"}
                }
                for i in range(60)
            ]
        }
        
        file_path = tmp_path / "batch_test.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(products_data, f)
        
        # Mock Claude to return enhanced texts
        def mock_create(**kwargs):
            # Extract batch from request
            content = kwargs["messages"][0]["content"]
            batch_count = content.count("210")  # Count products in batch
            
            # Return enhanced batch
            mock_batch = [
                {"artikelnummer": f"210{i:06d}", "bezeichnung1": f"Product {i} (100 mm)"}
                for i in range(batch_count)
            ]
            
            response = Mock()
            response.content = [Mock(text=json.dumps(mock_batch))]
            return response
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create = Mock(side_effect=mock_create)
            mock_get_client.return_value = mock_client
            
            result = await enhance_product_texts(file_path, batch_size=20)
            
            # Verify batching: 60 products / 20 per batch = 3 API calls
            assert mock_client.messages.create.call_count == 3
            assert result.total_products == 60
    
    @pytest.mark.asyncio
    async def test_quality_check_rejects_hallucination(self, temp_products_file):
        """Test quality check prevents hallucinations (TEXT-03)."""
        # Mock Claude response with MISSING measurement (hallucination)
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps([
            {
                "artikelnummer": "210100125",
                "bezeichnung1": "Beautiful CD Shipping Envelope",  # Lost measurement!
                "bezeichnung2": "Amazing product with great features"  # Lost VE!
            }
        ], ensure_ascii=False))]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await enhance_product_texts(temp_products_file, batch_size=30)
            
            # Quality check should fail - skipped_count incremented
            assert result.skipped_count > 0
            
            # Verify original text preserved (not hallucinated version)
            with open(temp_products_file, "r", encoding="utf-8") as f:
                updated_data = json.load(f)
            
            first_product = updated_data["products"][0]
            # Either enhanced field not added, or uses original text
            if "bezeichnung1_enhanced" in first_product["data"]:
                # Should use original, not hallucinated
                assert "145" in first_product["data"]["bezeichnung1_enhanced"]
    
    @pytest.mark.asyncio
    async def test_skips_products_without_bezeichnung1(self, tmp_path):
        """Test handles products missing bezeichnung1."""
        products_data = {
            "total_products": 2,
            "products": [
                {
                    "artikelnummer": "210100125",
                    "data": {},  # Missing bezeichnung1
                    "sources": {}
                },
                {
                    "artikelnummer": "210100225",
                    "data": {"bezeichnung1": "TEST PRODUCT"},
                    "sources": {"bezeichnung1": "edi_export"}
                }
            ]
        }
        
        file_path = tmp_path / "incomplete.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(products_data, f)
        
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps([
            {"artikelnummer": "210100225", "bezeichnung1": "Test Product"}
        ]))]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await enhance_product_texts(file_path)
            
            # First product skipped due to missing bezeichnung1
            assert result.skipped_count == 1
            assert result.enhanced_count == 1
    
    @pytest.mark.asyncio
    async def test_wrapper_structure_preserved(self, temp_products_file):
        """Test preserves Phase 3 wrapper structure."""
        # temp_products_file uses wrapper format
        
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps([
            {
                "artikelnummer": "210100125",
                "bezeichnung1": "Enhanced Text (145×190×25 mm)",
                "bezeichnung2": "Enhanced Description. VE 4×25 St."
            }
        ], ensure_ascii=False))]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            await enhance_product_texts(temp_products_file)
            
            # Verify wrapper structure preserved
            with open(temp_products_file, "r", encoding="utf-8") as f:
                updated_data = json.load(f)
            
            assert "total_products" in updated_data
            assert "products" in updated_data
            assert "merge_timestamp" in updated_data
    
    @pytest.mark.asyncio
    async def test_source_tracking(self, temp_products_file):
        """Test source tracking for enhanced fields."""
        mock_response = Mock()
        # Mock needs to return ALL 3 products from fixture to match batch
        # AND preserve all critical terms (measurements, colors, codes)
        mock_response.content = [Mock(text=json.dumps([
            {
                "artikelnummer": "210100125",
                "bezeichnung1": "Enhanced CD Tasche (145x190x25mm)",
                "bezeichnung2": "Enhanced, braun, VE 4x25 St."  # Must include "braun"!
            },
            {
                "artikelnummer": "210100225",
                "bezeichnung1": "Enhanced DVD Tasche (150x250x50mm)",
                "bezeichnung2": "Enhanced, weiß, VE 4x25 St."
            },
            {
                "artikelnummer": "210100325",
                "bezeichnung1": "Enhanced Box (305x220x100mm)"
            }
        ]))]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            await enhance_product_texts(temp_products_file)
            
            with open(temp_products_file, "r", encoding="utf-8") as f:
                updated_data = json.load(f)
            
            first_product = updated_data["products"][0]
            assert first_product["sources"]["bezeichnung1_enhanced"] == "llm_enhancement"
            # Only check bezeichnung2_enhanced if product actually has bezeichnung2
            if first_product["data"].get("bezeichnung2"):
                assert first_product["sources"]["bezeichnung2_enhanced"] == "llm_enhancement"


class TestBatchSizeOptimization:
    """Test batch size configuration (TEXT-04)."""
    
    @pytest.mark.asyncio
    async def test_configurable_batch_size(self, tmp_path):
        """Test batch_size parameter works correctly."""
        # Create 100 products
        products_data = {
            "total_products": 100,
            "products": [
                {"artikelnummer": f"210{i:06d}", "data": {"bezeichnung1": "TEST"}, "sources": {}}
                for i in range(100)
            ]
        }
        
        file_path = tmp_path / "large.json"
        with open(file_path, "w") as f:
            json.dump(products_data, f)
        
        mock_response = Mock()
        mock_response.content = [Mock(text="[]")]  # Empty enhanced batch
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            await enhance_product_texts(file_path, batch_size=20)
            
            # 100 products / 20 per batch = 5 API calls
            assert mock_client.messages.create.call_count == 5
    
    @pytest.mark.asyncio
    async def test_default_batch_size_30(self, tmp_path):
        """Test default batch size is 30."""
        products_data = {
            "total_products": 90,
            "products": [
                {"artikelnummer": f"210{i:06d}", "data": {"bezeichnung1": "TEST"}, "sources": {}}
                for i in range(90)
            ]
        }
        
        file_path = tmp_path / "medium.json"
        with open(file_path, "w") as f:
            json.dump(products_data, f)
        
        mock_response = Mock()
        mock_response.content = [Mock(text="[]")]
        
        with patch("app.services.text_enhancement.get_anthropic_client") as mock_get_client:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            # Don't specify batch_size - should default to 30
            await enhance_product_texts(file_path)
            
            # 90 products / 30 per batch = 3 API calls
            assert mock_client.messages.create.call_count == 3
