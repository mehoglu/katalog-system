"""
Image linking service for matching products to images via artikelnummer.
Implements Phase 4 requirements IMAGE-01 through IMAGE-04.
"""
from pathlib import Path
import json
from typing import Dict, List

from app.models.image_linking import ImageLinkResult


def normalize_artikelnummer(art_nr: str) -> str:
    """
    Normalize article number for case-insensitive matching.
    
    Handles edge cases from RESEARCH.md Pitfall 2:
    - Strips leading/trailing whitespace
    - Converts to lowercase
    
    Args:
        art_nr: Article number (may have whitespace, mixed case)
        
    Returns:
        Normalized article number (trimmed, lowercase)
        
    Examples:
        >>> normalize_artikelnummer("  D80950  ")
        'd80950'
        >>> normalize_artikelnummer("210100125")
        '210100125'
    """
    return art_nr.strip().lower()


def link_images_to_products(
    merged_products_path: Path,
    image_mapping_path: Path
) -> ImageLinkResult:
    """
    Link images from manual_image_mapping.json to products in merged_products.json.
    
    Implementation follows RESEARCH.md Pattern 1:
    - Case-insensitive artikelnummer matching (IMAGE-03)
    - Preserves multiple images per product (IMAGE-02)
    - Empty array for products without matches (IMAGE-04)
    - Complete source tracking for images field
    
    Algorithm:
    1. Load merged_products.json (list of MergedProduct dicts)
    2. Load manual_image_mapping.json (dict mapping artikelnummer -> images)
    3. Build case-insensitive lookup index
    4. For each product: match images, add to data, track source
    5. Save enhanced merged_products.json
    6. Return statistics
    
    Args:
        merged_products_path: Path to merged_products.json from Phase 3
        image_mapping_path: Path to manual_image_mapping.json from Phase 2
        
    Returns:
        ImageLinkResult with linking statistics
        
    Raises:
        FileNotFoundError: If either JSON file missing
        ValueError: If JSON structure invalid
    """
    # Load merged products
    if not merged_products_path.exists():
        raise FileNotFoundError(f"merged_products.json not found: {merged_products_path}")
    
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_file = json.load(f)
    
    # Handle both array format and wrapper object format
    if isinstance(merged_file, dict) and "products" in merged_file:
        merged_data = merged_file["products"]
        metadata = {k: v for k, v in merged_file.items() if k != "products"}
    else:
        merged_data = merged_file
        metadata = {}
    
    # Load image mapping
    if not image_mapping_path.exists():
        raise FileNotFoundError(f"manual_image_mapping.json not found: {image_mapping_path}")
    
    with open(image_mapping_path, "r", encoding="utf-8") as f:
        image_mapping = json.load(f)
    
    # Build case-insensitive lookup index
    image_index: Dict[str, List[dict]] = {
        normalize_artikelnummer(art_nr): images
        for art_nr, images in image_mapping["mappings"].items()
    }
    
    # Match images to products
    products_with_images = 0
    
    for product in merged_data:
        # Normalize product's artikelnummer for matching
        normalized_id = normalize_artikelnummer(product["artikelnummer"])
        
        # Lookup images (default to empty list if no match)
        matched_images = image_index.get(normalized_id, [])
        
        # Add images to product data (IMAGE-04: always include field, even if empty)
        product["data"]["images"] = matched_images
        
        # Add source tracking
        if matched_images:
            product["sources"]["images"] = "image_mapping"
            products_with_images += 1
        else:
            product["sources"]["images"] = None
    
    # Save enhanced merged_products.json (preserve wrapper structure if present)
    if metadata:
        output_data = {**metadata, "products": merged_data}
    else:
        output_data = merged_data
    
    with open(merged_products_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Calculate statistics
    total_products = len(merged_data)
    products_without_images = total_products - products_with_images
    
    # Count unused image mappings (images not matched to any product)
    matched_ids = {
        normalize_artikelnummer(p["artikelnummer"])
        for p in merged_data
    }
    unused_mappings = sum(
        1 for art_nr in image_index.keys()
        if art_nr not in matched_ids
    )
    
    return ImageLinkResult(
        total_products=total_products,
        products_with_images=products_with_images,
        products_without_images=products_without_images,
        unused_image_mappings=unused_mappings
    )
