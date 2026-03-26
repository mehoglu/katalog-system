"""
Text enhancement API endpoint.
Exposes Phase 5 LLM text enhancement functionality via REST API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from app.services.text_enhancement import enhance_product_texts
from app.core.config import settings

router = APIRouter(prefix="/api/texts", tags=["texts"])


class EnhanceRequest(BaseModel):
    """Request to enhance product texts."""
    upload_id: str  # Upload ID containing merged_products.json
    batch_size: int = 30  # Optional, defaults to 30


class EnhanceResponse(BaseModel):
    """Response with text enhancement statistics."""
    success: bool
    total_products: int
    enhanced_count: int
    skipped_count: int
    processing_time: float


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_texts(request: EnhanceRequest):
    """
    Enhance German product texts using LLM.
    
    Improves Bezeichnung1 and Bezeichnung2 for readability and professionalism
    while preserving technical terms and measurements.
    Implements TEXT-01 through TEXT-04 requirements.
    
    Args:
        request: EnhanceRequest with upload_id and optional batch_size
        
    Returns:
        EnhanceResponse with enhancement statistics
        
    Raises:
        HTTPException 404: If merged_products.json not found
    """
    # Construct path to merged_products.json
    upload_dir = Path(settings.upload_dir) / request.upload_id
    merged_products_path = upload_dir / "merged_products.json"
    
    # Validate file exists
    if not merged_products_path.exists():
        raise HTTPException(
            status_code=404,
            detail="merged_products.json not found"
        )
    
    # Perform enhancement
    result = await enhance_product_texts(
        merged_products_path,
        batch_size=request.batch_size
    )
    
    return EnhanceResponse(
        success=True,
        total_products=result.total_products,
        enhanced_count=result.enhanced_count,
        skipped_count=result.skipped_count,
        processing_time=result.processing_time
    )
