"""
Image linking API endpoint.
Exposes Phase 4 image linking functionality via REST API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageLinkRequest(BaseModel):
    """Request to link images to merged products."""
    upload_id: str  # EDI upload ID containing merged_products.json


class ImageLinkResponse(BaseModel):
    """Response with image linking statistics."""
    success: bool
    total_products: int
    products_with_images: int
    products_without_images: int
    unused_image_mappings: int


@router.post("/link", response_model=ImageLinkResponse)
def link_images(request: ImageLinkRequest):
    """
    Link images from manual_image_mapping.json to merged products.
    
    Enhances merged_products.json with images array per product.
    Implements IMAGE-01 through IMAGE-04 requirements.
    
    Args:
        request: ImageLinkRequest with upload_id
        
    Returns:
        ImageLinkResponse with linking statistics
        
    Raises:
        HTTPException 404: If merged_products.json or manual_image_mapping.json not found
    """
    from app.services.image_linking import link_images_to_products
    from app.config import settings
    
    # Construct paths
    upload_dir = Path(settings.upload_dir) / request.upload_id
    merged_products_path = upload_dir / "merged_products.json"
    image_mapping_path = Path(".planning/manual_image_mapping.json")
    
    # Validate paths exist
    if not merged_products_path.exists():
        raise HTTPException(404, "merged_products.json not found")
    if not image_mapping_path.exists():
        raise HTTPException(404, "manual_image_mapping.json not found")
    
    # Perform linking
    result = link_images_to_products(merged_products_path, image_mapping_path)
    
    return ImageLinkResponse(
        success=True,
        total_products=result.total_products,
        products_with_images=result.products_with_images,
        products_without_images=result.products_without_images,
        unused_image_mappings=result.unused_image_mappings
    )
