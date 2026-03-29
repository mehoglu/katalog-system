"""
PDF generation service - converts HTML catalogs to PDF using Playwright.
Phase 8: PDF Export Implementation

Uses Playwright (Chromium) for HTML to PDF conversion.
No system dependencies required - Chromium is downloaded automatically.
"""
from pathlib import Path
import json
import re
import base64
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


def embed_images_as_base64(html_content: str, base_path: Path, image_cache: dict = None) -> str:
    """
    Convert all image src paths to base64 data URLs for reliable PDF generation.
    Uses caching to avoid re-encoding the same images.
    
    Args:
        html_content: HTML content with image paths
        base_path: Base directory path for resolving relative paths
        image_cache: Optional dictionary to cache encoded images
        
    Returns:
        HTML content with base64-encoded images
    """
    if image_cache is None:
        image_cache = {}
    
    def replace_img_src(match):
        img_tag = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
        
        if not src_match:
            return img_tag
        
        src_path = src_match.group(1)
        
        # Skip if already a data URL
        if src_path.startswith('data:'):
            return img_tag
        
        # Resolve relative path
        if src_path.startswith('../'):
            image_path = (base_path / src_path).resolve()
        else:
            image_path = Path(src_path)
        
        # Use cache key
        cache_key = str(image_path)
        
        # Check cache first
        if cache_key in image_cache:
            data_url = image_cache[cache_key]
            new_img_tag = re.sub(
                r'src=["\'][^"\']+["\']',
                f'src="{data_url}"',
                img_tag
            )
            return new_img_tag
        
        # Check if file exists
        if not image_path.exists():
            # Silently skip missing images
            return img_tag
        
        # Read image and encode as base64
        try:
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Determine MIME type from extension
            ext = image_path.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.tif': 'image/tiff',
                '.tiff': 'image/tiff',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            # Create data URL and cache it
            data_url = f'data:{mime_type};base64,{img_base64}'
            image_cache[cache_key] = data_url
            
            # Replace src with base64 data URL
            new_img_tag = re.sub(
                r'src=["\'][^"\']+["\']',
                f'src="{data_url}"',
                img_tag
            )
            
            return new_img_tag
            
        except Exception as e:
            # Silently fail and keep original tag
            return img_tag
    
    # Replace all <img> tags
    html_content = re.sub(
        r'<img[^>]+>',
        replace_img_src,
        html_content,
        flags=re.IGNORECASE
    )
    
    return html_content


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
    failed = 0
    image_cache = {}  # Cache for base64-encoded images
    
    print(f"📄 Starting individual PDF generation for {len(product_html_files)} products...")
    
    # Use Playwright to convert HTML to PDF
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        for i, html_file in enumerate(product_html_files):
            if i % 50 == 0 and i > 0:
                print(f"   Progress: {i}/{len(product_html_files)} PDFs generated...")
            
            try:
                # Read HTML and embed images as base64
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                # Embed images as base64 for reliable PDF generation with caching
                html_content_fixed = embed_images_as_base64(html_content, html_file.parent, image_cache)
                
                # Create temporary HTML file with base64 images
                temp_html = html_file.parent / f"_temp_{html_file.name}"
                with open(temp_html, "w", encoding="utf-8") as f:
                    f.write(html_content_fixed)
                
                try:
                    pdf_filename = html_file.stem + ".pdf"
                    pdf_file_path = pdf_output_path / pdf_filename
                    
                    # Navigate to temporary HTML file
                    await page.goto(f"file://{temp_html.absolute()}")
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
                finally:
                    # Clean up temporary file
                    if temp_html.exists():
                        temp_html.unlink()
                        
            except Exception as e:
                print(f"⚠️  Failed to generate PDF for {html_file.name}: {e}")
                failed += 1
                continue
        
        await browser.close()
    
    print(f"✅ Generated {files_generated} PDFs successfully, {failed} failed")
    print(f"📦 Image cache size: {len(image_cache)} unique images")
    
    return PDFGenerationResult(
        total_products=len(product_html_files),
        files_generated=files_generated,
        output_path=str(pdf_output_path),
        mode="individual"
    )


async def generate_complete_pdf(upload_id: str, upload_dir: str = "uploads") -> PDFGenerationResult:
    """
    Generate single PDF file containing all products using Playwright.
    Uses batch processing for better performance and reliability.
    
    Args:
        upload_id: Upload session ID
        upload_dir: Base upload directory (default: "uploads")
        
    Returns:
        PDFGenerationResult with generation statistics
        
    Raises:
        FileNotFoundError: If merged_products.json or HTML catalog not found
    """
    import time
    
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
    
    print(f"📄 Starting complete PDF generation for {total_products} products...")
    
    # Generate combined PDF using Playwright
    complete_pdf_path = pdf_output_path / "Katalog_Komplett.pdf"
    
    # Cache for base64-encoded images
    image_cache = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Collect all HTML file paths
        html_files_to_merge = []
        for product in products:
            artikelnummer = product["artikelnummer"]
            html_file = catalog_html_path / f"{artikelnummer}.html"
            if html_file.exists():
                html_files_to_merge.append(html_file)
        
        # Create temporary combined HTML with proper styling
        combined_html = catalog_html_path / "_temp_complete.html"
        
        try:
            print(f"📝 Processing {len(html_files_to_merge)} HTML files...")
            
            # Read first HTML to get head/style content
            with open(html_files_to_merge[0], "r", encoding="utf-8") as f:
                first_html = f.read()
            
            # Extract head content (including all styles)
            head_start = first_html.find('<head')
            head_start = first_html.find('>', head_start) + 1
            head_end = first_html.find('</head>')
            head_content = first_html[head_start:head_end]
            
            # Build combined HTML
            html_parts = [
                '<!DOCTYPE html>',
                '<html lang="de">',
                '<head>',
                head_content,
                '</head>',
                '<body>'
            ]
            
            # Process in batches for progress tracking
            batch_size = 50
            processed = 0
            
            for i, html_file in enumerate(html_files_to_merge):
                if i % batch_size == 0 and i > 0:
                    print(f"   Progress: {i}/{len(html_files_to_merge)} pages processed...")
                
                try:
                    with open(html_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Embed images as base64 with caching
                    content = embed_images_as_base64(content, html_file.parent, image_cache)
                        
                    # Extract body content
                    if '<body' in content and '</body>' in content:
                        body_start = content.find('<body')
                        body_start = content.find('>', body_start) + 1
                        body_end = content.find('</body>')
                        body_content = content[body_start:body_end]
                        
                        # Wrap in page container with page break
                        html_parts.append('<div style="page-break-after: always;">')
                        html_parts.append(body_content)
                        html_parts.append('</div>')
                        
                        processed += 1
                        
                except Exception as e:
                    print(f"⚠️  Warning: Failed to process {html_file.name}: {e}")
                    continue
            
            html_parts.append('</body>')
            html_parts.append('</html>')
            
            print(f"✅ Successfully processed {processed} pages")
            print(f"💾 Writing combined HTML...")
            
            # Write combined HTML
            with open(combined_html, "w", encoding="utf-8") as f:
                f.write('\n'.join(html_parts))
            
            print(f"📄 Generating PDF (this may take a few minutes)...")
            start_time = time.time()
            
            # Navigate to combined HTML and wait for all images to load
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
            
            elapsed = time.time() - start_time
            print(f"✅ PDF generated in {elapsed:.1f} seconds")
            
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
