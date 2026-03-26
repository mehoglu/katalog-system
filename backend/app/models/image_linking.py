"""
Image linking result models.
Tracks statistics from linking images to products via artikelnummer matching.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ImageFormatWarning(BaseModel):
    """Warning about non-browser-compatible image formats."""
    format: str = Field(description="File extension (e.g., '.tif', '.bmp')")
    count: int = Field(ge=0, description="Number of images with this format")
    example_files: List[str] = Field(description="First 3 example filenames")
    recommendation: str = Field(description="User-friendly recommendation")


class ImageLinkResult(BaseModel):
    """
    Result of image linking operation.
    
    Tracks statistics from link_images_to_products():
    - How many products were processed
    - How many received images
    - How many had no image matches
    - How many image mappings went unused
    - Warnings about image format compatibility (Phase 1 enhancement)
    """
    total_products: int = Field(..., ge=0, description="Total products processed")
    products_with_images: int = Field(..., ge=0, description="Products that received images")
    products_without_images: int = Field(..., ge=0, description="Products with empty images array")
    unused_image_mappings: int = Field(..., ge=0, description="Images in manual_image_mapping.json not matched to any product")
    format_warnings: Optional[List[ImageFormatWarning]] = Field(default=None, description="Warnings about browser-incompatible image formats")
