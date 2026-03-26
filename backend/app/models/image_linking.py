"""
Image linking result models.
Tracks statistics from linking images to products via artikelnummer matching.
"""
from pydantic import BaseModel, Field


class ImageLinkResult(BaseModel):
    """
    Result of image linking operation.
    
    Tracks statistics from link_images_to_products():
    - How many products were processed
    - How many received images
    - How many had no image matches
    - How many image mappings went unused
    """
    total_products: int = Field(..., ge=0, description="Total products processed")
    products_with_images: int = Field(..., ge=0, description="Products that received images")
    products_without_images: int = Field(..., ge=0, description="Products with empty images array")
    unused_image_mappings: int = Field(..., ge=0, description="Images in manual_image_mapping.json not matched to any product")
