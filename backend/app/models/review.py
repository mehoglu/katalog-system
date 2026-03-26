"""
Review API models for product data review and correction.
Phase 6: Data Review & Correction
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class ProductReview(BaseModel):
    """
    Single product for review display.
    Includes all data fields plus source tracking for UI display.
    """
    artikelnummer: str
    data: Dict[str, Any]  # All product fields (including _enhanced fields)
    sources: Dict[str, Optional[str]]  # Field -> source mapping
    # Sources can be: "edi_export", "preisliste", "llm_enhancement", "image_linking", "manual_edit"


class ReviewListResponse(BaseModel):
    """
    Response model for GET /api/review/{upload_id}
    Returns all products with metadata.
    """
    total_products: int
    upload_id: str
    products: List[ProductReview]


class UpdateFieldRequest(BaseModel):
    """
    Request model for PATCH /api/review/{upload_id}/product
    Updates a single field for a specific product.
    """
    artikelnummer: str
    field_name: str  # e.g., "bezeichnung1", "preis", "hoehe_cm"
    field_value: Any  # New value for the field


class UpdateFieldResponse(BaseModel):
    """
    Response model for field update.
    Returns the updated product.
    """
    success: bool
    product: ProductReview
    message: str = "Field updated successfully"
