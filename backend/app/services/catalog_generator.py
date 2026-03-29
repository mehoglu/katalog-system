"""
Catalog generation service - creates HTML catalogs from merged product data.
Phase 7: Professional HTML Catalog Output
"""
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel


class CatalogGenerationResult(BaseModel):
    """Result of catalog generation operation."""
    total_products: int
    files_generated: int
    output_path: str


async def generate_catalog(upload_id: str, upload_dir: str = "uploads") -> CatalogGenerationResult:
    """
    Generate HTML catalog from merged product data.
    
    Args:
        upload_id: Upload session ID
        upload_dir: Base upload directory (default: "uploads")
        
    Returns:
        CatalogGenerationResult with generation statistics
        
    Raises:
        FileNotFoundError: If merged_products.json not found
    """
    # Setup paths
    upload_path = Path(upload_dir) / upload_id
    merged_products_path = upload_path / "merged_products.json"
    catalog_output_path = upload_path / "catalog"
    
    if not merged_products_path.exists():
        raise FileNotFoundError(f"merged_products.json not found for upload_id: {upload_id}")
    
    # Create output directory
    catalog_output_path.mkdir(parents=True, exist_ok=True)
    
    # Load products
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)
    
    products = merged_data.get("products", [])
    total_products = len(products)
    
    # Setup Jinja2 environment
    template_dir = Path(__file__).parent.parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"])
    )
    
    product_template = env.get_template("product_template.html")
    index_template = env.get_template("index_template.html")
    
    # Current timestamp
    generation_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Generate individual product pages
    files_generated = 0
    for i, product in enumerate(products):
        # Log progress every 50 products
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1}/{total_products} product pages...")
        
        # Render product page
        html_content = product_template.render(
            product=product,
            generation_date=generation_date
        )
        
        # Write to file
        product_filename = f"{product['artikelnummer']}.html"
        product_file_path = catalog_output_path / product_filename
        
        with open(product_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        files_generated += 1
    
    # Generate index page
    index_html = index_template.render(
        products=products,
        total_products=total_products,
        generation_date=generation_date,
        upload_id=upload_id
    )
    
    index_file_path = catalog_output_path / "index.html"
    with open(index_file_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    
    files_generated += 1
    
    print(f"✓ Catalog generation complete: {files_generated} files generated")
    
    return CatalogGenerationResult(
        total_products=total_products,
        files_generated=files_generated,
        output_path=str(catalog_output_path)
    )


def format_price(price: str) -> str:
    """
    Format price string as EUR.
    
    Args:
        price: Price string (e.g., "89.99")
        
    Returns:
        Formatted price (e.g., "89,99 €")
    """
    if not price:
        return "N/A"
    
    try:
        # Convert dot to comma for German formatting
        price_formatted = price.replace(".", ",")
        return f"{price_formatted} €"
    except:
        return price


def get_image_path_or_placeholder(bild_paths: List[str]) -> str:
    """
    Get first image path or placeholder text.
    
    Args:
        bild_paths: List of image paths
        
    Returns:
        First image path or "Kein Bild" placeholder
    """
    if bild_paths and len(bild_paths) > 0:
        return bild_paths[0]
    return "Kein Bild"
