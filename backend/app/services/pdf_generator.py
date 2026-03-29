"""
PDF generation service - converts HTML catalogs to PDF using Playwright.
Phase 8: PDF Export Implementation

Uses Playwright (Chromium) for HTML to PDF conversion.
No system dependencies required - Chromium is downloaded automatically.
"""
from pathlib import Path
import json
from typing import List, Optional
from pydantic import BaseModel
import asyncio

# Try to import Playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("⚠️  Playwright not available. Install with: pip install playwright && playwright install chromium")
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None  # type: ignore


class PDFGenerationResult(BaseModel):
    """Result of PDF generation operation."""
    total_products: int
    files_generated: int
    output_path: str
    mode: str  # "individual" or "complete"


async def generate_individual_pdfs(
    upload_id: str, 
    upload_dir: str = "uploads",
    artikelnummern: Optional[List[str]] = None
) -> PDFGenerationResult:
    """
    Generate individual PDF for each product using Playwright.
    
    Args:
        upload_id: Upload session ID
        upload_dir: Base upload directory (default: "uploads")
        artikelnummern: Optional list of article numbers to filter (None = all products)
        
    Returns:
        PDFGenerationResult with generation statistics
        
    Raises:
        FileNotFoundError: If HTML catalog directory not found
    """
    # Setup paths
    upload_path = Path(upload_dir) / upload_id
    catalog_html_path = upload_path / "catalog"
    pdf_output_path = upload_path / "catalog_pdf"
    
    if not catalog_html_path.exists():
        raise FileNotFoundError(
            f"HTML catalog not found for upload_id: {upload_id}. "
            "Generate HTML catalog first using POST /api/catalog/generate"
        )
    
    # Create PDF output directory
    pdf_output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all product HTML files (exclude index.html)
    html_files = list(catalog_html_path.glob("*.html"))
    product_html_files = [f for f in html_files if f.name != "index.html"]
    
    # Filter by artikelnummern if provided
    if artikelnummern:
        artikel_set = set(artikelnummern)
        product_html_files = [
            f for f in product_html_files 
            if f.stem in artikel_set  # f.stem is filename without extension
        ]
    
    files_generated = 0
    
    # Use Playwright to convert HTML to PDF
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        for html_file in product_html_files:
            pdf_filename = html_file.stem + ".pdf"
            pdf_file_path = pdf_output_path / pdf_filename
            
            # Navigate to HTML file and print to PDF
            await page.goto(f"file://{html_file.absolute()}")
            await page.pdf(
                path=str(pdf_file_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "12mm",
                    "right": "12mm",
                    "bottom": "12mm",
                    "left": "12mm"
                }
            )
            
            files_generated += 1
        
        await browser.close()
    
    return PDFGenerationResult(
        total_products=len(product_html_files),
        files_generated=files_generated,
        output_path=str(pdf_output_path),
        mode="individual"
    )


async def generate_complete_pdf(upload_id: str, upload_dir: str = "uploads") -> PDFGenerationResult:
    """
    Generate single PDF file containing all products using Playwright.
    
    Args:
        upload_id: Upload session ID
        upload_dir: Base upload directory (default: "uploads")
        
    Returns:
        PDFGenerationResult with generation statistics
        
    Raises:
        FileNotFoundError: If merged_products.json or HTML catalog not found
    """
    # Setup paths
    upload_path = Path(upload_dir) / upload_id
    merged_products_path = upload_path / "merged_products.json"
    catalog_html_path = upload_path / "catalog"
    pdf_output_path = upload_path / "catalog_pdf"
    
    if not merged_products_path.exists():
        raise FileNotFoundError(f"merged_products.json not found for upload_id: {upload_id}")
    
    if not catalog_html_path.exists():
        raise FileNotFoundError(
            f"HTML catalog not found for upload_id: {upload_id}. "
            "Generate HTML catalog first using POST /api/catalog/generate"
        )
    
    # Create PDF output directory
    pdf_output_path.mkdir(parents=True, exist_ok=True)
    
    # Load product list for page ordering
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)
    
    products = merged_data.get("products", [])
    total_products = len(products)
    
    # Generate combined PDF using Playwright
    complete_pdf_path = pdf_output_path / "Katalog_Komplett.pdf"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Create a temporary combined HTML file
        combined_html = catalog_html_path / "_temp_complete.html"
        
        try:
            # Build combined HTML content
            html_parts = ['<html><head><meta charset="UTF-8"></head><body>']
            
            for product in products:
                artikelnummer = product["artikelnummer"]
                html_file = catalog_html_path / f"{artikelnummer}.html"
                
                if html_file.exists():
                    # Read HTML content and extract body
                    with open(html_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Simple extraction of body content
                        if '<body' in content and '</body>' in content:
                            body_start = content.find('<body')
                            body_start = content.find('>', body_start) + 1
                            body_end = content.find('</body>')
                            body_content = content[body_start:body_end]
                            html_parts.append(body_content)
                            html_parts.append('<div style="page-break-after: always;"></div>')
            
            html_parts.append('</body></html>')
            
            # Write combined HTML
            with open(combined_html, "w", encoding="utf-8") as f:
                f.write('\n'.join(html_parts))
            
            # Navigate to combined HTML and print to PDF
            await page.goto(f"file://{combined_html.absolute()}")
            await page.pdf(
                path=str(complete_pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "12mm",
                    "right": "12mm",
                    "bottom": "12mm",
                    "left": "12mm"
                }
            )
            
        finally:
            # Clean up temporary file
            if combined_html.exists():
                combined_html.unlink()
            await browser.close()
    
    return PDFGenerationResult(
        total_products=total_products,
        files_generated=1,  # One complete PDF file
        output_path=str(complete_pdf_path),
        mode="complete"
    )


async def generate_pdfs(
    upload_id: str, 
    mode: str = "both",
    upload_dir: str = "uploads",
    artikelnummern: Optional[List[str]] = None
) -> List[PDFGenerationResult]:
    """
    Generate PDF catalogs in specified mode using Playwright.
    
    Args:
        upload_id: Upload session ID
        mode: Generation mode - "individual", "complete", or "both"
        upload_dir: Base upload directory (default: "uploads")
        artikelnummern: Optional list of article numbers to filter (None = all products)
        
    Returns:
        List of PDFGenerationResult (one or two depending on mode)
        
    Raises:
        ValueError: If invalid mode specified
        FileNotFoundError: If required files not found
        RuntimeError: If Playwright not available
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "PDF generation not available. Install Playwright: "
            "pip install playwright && playwright install chromium"
        )
    
    if mode not in ["individual", "complete", "both"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'individual', 'complete', or 'both'")
    
    results = []
    
    if mode in ["individual", "both"]:
        individual_result = await generate_individual_pdfs(upload_id, upload_dir, artikelnummern)
        results.append(individual_result)
    
    if mode in ["complete", "both"]:
        complete_result = await generate_complete_pdf(upload_id, upload_dir)
        results.append(complete_result)
    
    return results
