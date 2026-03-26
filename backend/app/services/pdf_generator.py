"""
PDF generation service - converts HTML catalogs to PDF.
Phase 8: PDF Export Implementation
"""
from pathlib import Path
import json
from typing import List, Optional
from weasyprint import HTML, CSS
from pydantic import BaseModel


class PDFGenerationResult(BaseModel):
    """Result of PDF generation operation."""
    total_products: int
    files_generated: int
    output_path: str
    mode: str  # "individual" or "complete"


async def generate_individual_pdfs(upload_id: str, upload_dir: str = "uploads") -> PDFGenerationResult:
    """
    Generate individual PDF file for each product from existing HTML files.
    
    Args:
        upload_id: Upload session ID
        upload_dir: Base upload directory (default: "uploads")
        
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
    
    files_generated = 0
    
    # Convert each HTML to PDF
    for html_file in product_html_files:
        pdf_filename = html_file.stem + ".pdf"
        pdf_file_path = pdf_output_path / pdf_filename
        
        # Convert HTML to PDF using WeasyPrint
        HTML(filename=str(html_file)).write_pdf(
            target=str(pdf_file_path),
            optimize_size=('fonts', 'images')  # Optimize file size
        )
        
        files_generated += 1
    
    return PDFGenerationResult(
        total_products=len(product_html_files),
        files_generated=files_generated,
        output_path=str(pdf_output_path),
        mode="individual"
    )


async def generate_complete_pdf(upload_id: str, upload_dir: str = "uploads") -> PDFGenerationResult:
    """
    Generate single PDF file containing all products.
    
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
    
    # Collect all HTML files in order
    html_documents = []
    
    for product in products:
        artikelnummer = product["artikelnummer"]
        html_file = catalog_html_path / f"{artikelnummer}.html"
        
        if html_file.exists():
            html_documents.append(HTML(filename=str(html_file)))
    
    # Generate combined PDF
    complete_pdf_path = pdf_output_path / "Katalog_Komplett.pdf"
    
    # Render all documents and combine into single PDF
    all_pages = []
    for html_doc in html_documents:
        document = html_doc.render()
        all_pages.extend(document.pages)
    
    # Write combined PDF
    if all_pages:
        all_pages[0].document.copy(all_pages).write_pdf(
            target=str(complete_pdf_path),
            optimize_size=('fonts', 'images')
        )
    
    return PDFGenerationResult(
        total_products=total_products,
        files_generated=1,  # One complete PDF file
        output_path=str(complete_pdf_path),
        mode="complete"
    )


async def generate_pdfs(
    upload_id: str, 
    mode: str = "both",
    upload_dir: str = "uploads"
) -> List[PDFGenerationResult]:
    """
    Generate PDF catalogs in specified mode.
    
    Args:
        upload_id: Upload session ID
        mode: Generation mode - "individual", "complete", or "both"
        upload_dir: Base upload directory (default: "uploads")
        
    Returns:
        List of PDFGenerationResult (one or two depending on mode)
        
    Raises:
        ValueError: If invalid mode specified
        FileNotFoundError: If required files not found
    """
    if mode not in ["individual", "complete", "both"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'individual', 'complete', or 'both'")
    
    results = []
    
    if mode in ["individual", "both"]:
        individual_result = await generate_individual_pdfs(upload_id, upload_dir)
        results.append(individual_result)
    
    if mode in ["complete", "both"]:
        complete_result = await generate_complete_pdf(upload_id, upload_dir)
        results.append(complete_result)
    
    return results
