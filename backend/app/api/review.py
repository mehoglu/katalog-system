"""
Review API endpoints for product data review and correction.
Phase 6: Data Review & Correction
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import tempfile
import shutil
from typing import Dict, Any

from app.core.config import settings
from app.models.review import (
    ReviewListResponse,
    ProductReview,
    UpdateFieldRequest,
    UpdateFieldResponse
)

router = APIRouter(prefix="/api/review")


@router.get("/{upload_id}", response_model=ReviewListResponse)
async def get_all_products(upload_id: str):
    """
    Get all products for review with source tracking.
    
    Args:
        upload_id: Upload session ID
        
    Returns:
        ReviewListResponse with all products and sources
        
    Raises:
        HTTPException 404: merged_products.json not found
    """
    upload_dir = Path(settings.upload_dir) / upload_id
    merged_products_path = upload_dir / "merged_products.json"
    
    if not merged_products_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"merged_products.json not found for upload_id: {upload_id}"
        )
    
    # Read merged products (Phase 3 wrapper structure)
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)
    
    # Convert to ProductReview models
    products = []
    for product in merged_data.get("products", []):
        products.append(ProductReview(
            artikelnummer=product["artikelnummer"],
            data=product["data"],
            sources=product["sources"]
        ))
    
    return ReviewListResponse(
        total_products=len(products),
        upload_id=upload_id,
        products=products
    )


@router.patch("/{upload_id}/product", response_model=UpdateFieldResponse)
async def update_product_field(upload_id: str, request: UpdateFieldRequest):
    """
    Update a single field for a specific product.
    
    Args:
        upload_id: Upload session ID
        request: Update request with artikelnummer, field_name, field_value
        
    Returns:
        UpdateFieldResponse with updated product
        
    Raises:
        HTTPException 404: File not found or product not found
    """
    upload_dir = Path(settings.upload_dir) / upload_id
    merged_products_path = upload_dir / "merged_products.json"
    
    if not merged_products_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"merged_products.json not found for upload_id: {upload_id}"
        )
    
    # Read merged products
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)
    
    # Find product by artikelnummer
    product_found = False
    updated_product = None
    
    for product in merged_data.get("products", []):
        if product["artikelnummer"] == request.artikelnummer:
            product_found = True
            
            # Update field in data object
            product["data"][request.field_name] = request.field_value
            
            # Update source to "manual_edit"
            product["sources"][request.field_name] = "manual_edit"
            
            updated_product = ProductReview(
                artikelnummer=product["artikelnummer"],
                data=product["data"],
                sources=product["sources"]
            )
            break
    
    if not product_found:
        raise HTTPException(
            status_code=404,
            detail=f"Product not found with artikelnummer: {request.artikelnummer}"
        )
    
    # Write updated JSON back to file (atomic write)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=upload_dir,
        delete=False,
        suffix=".json"
    ) as temp_file:
        json.dump(merged_data, temp_file, ensure_ascii=False, indent=2)
        temp_path = temp_file.name
    
    # Atomic replace
    shutil.move(temp_path, merged_products_path)
    
    return UpdateFieldResponse(
        success=True,
        product=updated_product,
        message=f"Field '{request.field_name}' updated successfully"
    )
