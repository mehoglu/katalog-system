"""
Tests for PDF generation service and API endpoints.
Phase 8: PDF Export Implementation
"""
import pytest
from pathlib import Path
import json
from app.services.pdf_generator import (
    generate_individual_pdfs,
    generate_complete_pdf,
    generate_pdfs
)


@pytest.fixture
def test_upload_with_html(tmp_path):
    """Create test upload directory with HTML catalog."""
    upload_id = "test_pdf_001"
    upload_dir = tmp_path / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json
    products = {
        "products": [
            {
                "artikelnummer": "TEST001",
                "data": {
                    "artikelnummer": "TEST001",
                    "bezeichnung1": "Test Product 1",
                    "bezeichnung1_enhanced": "Enhanced Test Product 1"
                },
                "sources": {}
            },
            {
                "artikelnummer": "TEST002",
                "data": {
                    "artikelnummer": "TEST002",
                    "bezeichnung1": "Test Product 2",
                    "bezeichnung1_enhanced": "Enhanced Test Product 2"
                },
                "sources": {}
            }
        ]
    }
    
    with open(upload_dir / "merged_products.json", "w") as f:
        json.dump(products, f)
    
    # Create catalog directory with HTML files
    catalog_dir = upload_dir / "catalog"
    catalog_dir.mkdir()
    
    # Simple HTML template for testing
    html_template = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>{artikelnummer} - Test</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{ font-family: Arial, sans-serif; padding: 20mm; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>{bezeichnung1}</h1>
    <p>Artikel-Nr: {artikelnummer}</p>
    <p>Enhanced: {bezeichnung1_enhanced}</p>
</body>
</html>"""
    
    # Create HTML files for each product
    for product in products["products"]:
        data = product["data"]
        html_content = html_template.format(
            artikelnummer=data["artikelnummer"],
            bezeichnung1=data["bezeichnung1"],
            bezeichnung1_enhanced=data["bezeichnung1_enhanced"]
        )
        
        html_file = catalog_dir / f"{data['artikelnummer']}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    # Create index.html
    with open(catalog_dir / "index.html", "w") as f:
        f.write("<html><body><h1>Index</h1></body></html>")
    
    return tmp_path, upload_id


@pytest.mark.asyncio
async def test_generate_individual_pdfs_success(test_upload_with_html):
    """Test individual PDF generation creates PDF for each product."""
    upload_dir, upload_id = test_upload_with_html
    
    result = await generate_individual_pdfs(upload_id, str(upload_dir))
    
    assert result.total_products == 2
    assert result.files_generated == 2
    assert result.mode == "individual"
    
    # Check PDFs were created
    pdf_dir = Path(result.output_path)
    assert pdf_dir.exists()
    assert (pdf_dir / "TEST001.pdf").exists()
    assert (pdf_dir / "TEST002.pdf").exists()
    
    # Verify PDF file size (should be > 0)
    assert (pdf_dir / "TEST001.pdf").stat().st_size > 0
    assert (pdf_dir / "TEST002.pdf").stat().st_size > 0


@pytest.mark.asyncio
async def test_generate_complete_pdf_success(test_upload_with_html):
    """Test complete PDF generation creates single combined PDF."""
    upload_dir, upload_id = test_upload_with_html
    
    result = await generate_complete_pdf(upload_id, str(upload_dir))
    
    assert result.total_products == 2
    assert result.files_generated == 1
    assert result.mode == "complete"
    
    # Check complete PDF was created
    pdf_path = Path(result.output_path)
    assert pdf_path.exists()
    assert pdf_path.name == "Katalog_Komplett.pdf"
    assert pdf_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_generate_pdfs_both_mode(test_upload_with_html):
    """Test generating both individual and complete PDFs."""
    upload_dir, upload_id = test_upload_with_html
    
    results = await generate_pdfs(upload_id, mode="both", upload_dir=str(upload_dir))
    
    assert len(results) == 2
    
    # Check individual result
    individual_result = next(r for r in results if r.mode == "individual")
    assert individual_result.files_generated == 2
    
    # Check complete result
    complete_result = next(r for r in results if r.mode == "complete")
    assert complete_result.files_generated == 1


@pytest.mark.asyncio
async def test_generate_pdfs_invalid_mode(test_upload_with_html):
    """Test error handling for invalid mode."""
    upload_dir, upload_id = test_upload_with_html
    
    with pytest.raises(ValueError, match="Invalid mode"):
        await generate_pdfs(upload_id, mode="invalid", upload_dir=str(upload_dir))


@pytest.mark.asyncio
async def test_generate_pdfs_missing_html_catalog(tmp_path):
    """Test error handling when HTML catalog directory missing."""
    upload_id = "missing_html"
    upload_dir = tmp_path / upload_id
    upload_dir.mkdir()
    
    # Create merged_products.json but no catalog directory
    products = {"products": []}
    with open(upload_dir / "merged_products.json", "w") as f:
        json.dump(products, f)
    
    with pytest.raises(FileNotFoundError, match="HTML catalog not found"):
        await generate_individual_pdfs(upload_id, str(tmp_path))


@pytest.mark.asyncio
async def test_pdf_optimization(test_upload_with_html):
    """Test PDF file size optimization is applied."""
    upload_dir, upload_id = test_upload_with_html
    
    result = await generate_individual_pdfs(upload_id, str(upload_dir))
    
    # PDFs should be created with optimization
    # (exact size depends on content, but should be reasonable)
    pdf_dir = Path(result.output_path)
    pdf_size = (pdf_dir / "TEST001.pdf").stat().st_size
    
    # Should be less than 100 KB for simple test HTML
    assert pdf_size < 100_000  # 100 KB
