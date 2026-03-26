"""
Unit tests for image linking service.
Tests normalize_artikelnummer() and link_images_to_products() functions.
Validates IMAGE-01 through IMAGE-04 requirements.
"""
import pytest
import json
import tempfile
from pathlib import Path

from app.services.image_linking import link_images_to_products, normalize_artikelnummer


class TestNormalizeArtikelnummer:
    """Tests for normalize_artikelnummer() helper function."""
    
    def test_normalize_artikelnummer_strips_whitespace(self):
        """Test whitespace stripping (RESEARCH Pitfall 2)."""
        result = normalize_artikelnummer("  210100125  ")
        assert result == "210100125"
    
    def test_normalize_artikelnummer_lowercase(self):
        """Test case conversion (IMAGE-03 requirement)."""
        result = normalize_artikelnummer("D80950")
        assert result == "d80950"
    
    def test_normalize_artikelnummer_combined(self):
        """Test both whitespace + case normalization."""
        result = normalize_artikelnummer("  D80950  ")
        assert result == "d80950"


class TestLinkImagesToProducts:
    """Tests for link_images_to_products() main function."""
    
    def test_link_images_basic_match(self):
        """Test basic image matching (IMAGE-01)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temp merged_products.json with 1 product
            merged_data = [
                {
                    "artikelnummer": "210100125",
                    "data": {"bezeichnung1": "Test Product"},
                    "sources": {"bezeichnung1": "edi_export"}
                }
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # Create temp manual_image_mapping.json with 1 mapping
            image_mapping = {
                "mappings": {
                    "210100125": [
                        {
                            "filename": "210100125A.jpg",
                            "suffix": "A",
                            "extension": "jpg",
                            "path": "assets/bilder/210100125A.jpg",
                            "type": "front"
                        }
                    ]
                }
            }
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call link_images_to_products()
            result = link_images_to_products(merged_path, mapping_path)
            
            # Assert: product has 1 image
            with open(merged_path) as f:
                products = json.load(f)
            assert len(products[0]["data"]["images"]) == 1
            assert products[0]["data"]["images"][0]["filename"] == "210100125A.jpg"
            
            # Assert: source tracking added
            assert products[0]["sources"]["images"] == "image_mapping"
            
            # Assert: statistics correct
            assert result.total_products == 1
            assert result.products_with_images == 1
            assert result.products_without_images == 0
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching (IMAGE-03)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Product has uppercase artikelnummer
            merged_data = [
                {
                    "artikelnummer": "D80950",
                    "data": {},
                    "sources": {}
                }
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # Mapping has lowercase key
            image_mapping = {
                "mappings": {
                    "d80950": [
                        {
                            "filename": "d80950.jpg",
                            "suffix": "main",
                            "path": "assets/bilder/d80950.jpg",
                            "type": "main"
                        }
                    ]
                }
            }
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call and verify match despite case difference
            result = link_images_to_products(merged_path, mapping_path)
            
            with open(merged_path) as f:
                products = json.load(f)
            assert len(products[0]["data"]["images"]) == 1
            assert products[0]["data"]["images"][0]["filename"] == "d80950.jpg"
    
    def test_empty_array_for_missing_images(self):
        """Test empty array for products without matches (IMAGE-04)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Product with no matching images
            merged_data = [
                {
                    "artikelnummer": "999999999",
                    "data": {},
                    "sources": {}
                }
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # Empty mappings
            image_mapping = {"mappings": {}}
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call and verify empty array (not missing field)
            result = link_images_to_products(merged_path, mapping_path)
            
            with open(merged_path) as f:
                products = json.load(f)
            assert "images" in products[0]["data"]
            assert products[0]["data"]["images"] == []
            assert products[0]["sources"]["images"] is None
            
            # Assert: statistics correct
            assert result.products_without_images == 1
    
    def test_multiple_images_preserved(self):
        """Test multiple images per product (IMAGE-02)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            merged_data = [
                {
                    "artikelnummer": "210100125",
                    "data": {},
                    "sources": {}
                }
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # Mapping with 4 images (A, AA, E, G suffixes)
            image_mapping = {
                "mappings": {
                    "210100125": [
                        {"filename": "210100125A.jpg", "suffix": "A", "type": "front", "path": "assets/bilder/210100125A.jpg"},
                        {"filename": "210100125AA.jpg", "suffix": "AA", "type": "detail", "path": "assets/bilder/210100125AA.jpg"},
                        {"filename": "210100125E.jpg", "suffix": "E", "type": "single", "path": "assets/bilder/210100125E.jpg"},
                        {"filename": "210100125G.jpg", "suffix": "G", "type": "group", "path": "assets/bilder/210100125G.jpg"}
                    ]
                }
            }
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call and verify all 4 images preserved
            result = link_images_to_products(merged_path, mapping_path)
            
            with open(merged_path) as f:
                products = json.load(f)
            assert len(products[0]["data"]["images"]) == 4
            
            # Verify all suffixes present
            suffixes = {img["suffix"] for img in products[0]["data"]["images"]}
            assert suffixes == {"A", "AA", "E", "G"}
    
    def test_statistics_accuracy(self):
        """Test ImageLinkResult statistics (RESEARCH V-05)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 3 products, 2 have matches, 1 does not
            merged_data = [
                {"artikelnummer": "210100125", "data": {}, "sources": {}},
                {"artikelnummer": "210100225", "data": {}, "sources": {}},
                {"artikelnummer": "999999999", "data": {}, "sources": {}}
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # Mappings for first 2 products only
            image_mapping = {
                "mappings": {
                    "210100125": [{"filename": "210100125.jpg", "path": "assets/bilder/210100125.jpg", "type": "main"}],
                    "210100225": [{"filename": "210100225.jpg", "path": "assets/bilder/210100225.jpg", "type": "main"}]
                }
            }
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call and verify statistics
            result = link_images_to_products(merged_path, mapping_path)
            
            assert result.total_products == 3
            assert result.products_with_images == 2
            assert result.products_without_images == 1
            assert result.unused_image_mappings == 0  # All mappings used
    
    def test_unused_mappings_count(self):
        """Test unused image mappings count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 3 products
            merged_data = [
                {"artikelnummer": "210100125", "data": {}, "sources": {}},
                {"artikelnummer": "210100225", "data": {}, "sources": {}},
                {"artikelnummer": "210100325", "data": {}, "sources": {}}
            ]
            merged_path = Path(tmpdir) / "merged_products.json"
            with open(merged_path, "w") as f:
                json.dump(merged_data, f)
            
            # 5 mappings, 3 match products, 2 unused
            image_mapping = {
                "mappings": {
                    "210100125": [{"filename": "210100125.jpg", "path": "assets/bilder/210100125.jpg", "type": "main"}],
                    "210100225": [{"filename": "210100225.jpg", "path": "assets/bilder/210100225.jpg", "type": "main"}],
                    "210100325": [{"filename": "210100325.jpg", "path": "assets/bilder/210100325.jpg", "type": "main"}],
                    "999999998": [{"filename": "999999998.jpg", "path": "assets/bilder/999999998.jpg", "type": "main"}],
                    "999999997": [{"filename": "999999997.jpg", "path": "assets/bilder/999999997.jpg", "type": "main"}]
                }
            }
            mapping_path = Path(tmpdir) / "manual_image_mapping.json"
            with open(mapping_path, "w") as f:
                json.dump(image_mapping, f)
            
            # Call and verify unused count
            result = link_images_to_products(merged_path, mapping_path)
            
            assert result.unused_image_mappings == 2
