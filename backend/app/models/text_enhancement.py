"""
Text enhancement models for Phase 5.

Pydantic models for LLM-based German text enhancement results.
"""
from pydantic import BaseModel, Field
from typing import Optional


class EnhancementResult(BaseModel):
    """Result of text enhancement operation."""
    
    total_products: int = Field(..., ge=0, description="Total products processed")
    enhanced_count: int = Field(..., ge=0, description="Successfully enhanced products")
    skipped_count: int = Field(..., ge=0, description="Products skipped due to errors")
    processing_time: float = Field(..., ge=0.0, description="Total processing time in seconds")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "total_products": 464,
                "enhanced_count": 460,
                "skipped_count": 4,
                "processing_time": 185.3
            }
        }


class EnhancedProduct(BaseModel):
    """Internal model for single product enhancement (used during processing)."""
    
    artikelnummer: str = Field(..., description="Product article number")
    bezeichnung1_original: str = Field(..., description="Original product name")
    bezeichnung1_enhanced: str = Field(..., description="Enhanced product name")
    bezeichnung2_original: Optional[str] = Field(None, description="Original description")
    bezeichnung2_enhanced: Optional[str] = Field(None, description="Enhanced description")
    quality_check: bool = Field(..., description="Whether preservation validation passed")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "artikelnummer": "210100125",
                "bezeichnung1_original": "VERSANDTASCHE AUS WELLPAPPE CD, 145x190x-25mm",
                "bezeichnung1_enhanced": "Versandtasche aus Wellpappe für CDs (145×190×25 mm)",
                "bezeichnung2_original": "sk m. Aufreißfaden, braun, var. Höhe, VE 4x25 St.",
                "bezeichnung2_enhanced": "Selbstklebend mit Aufreißfaden, braun, variable Höhe. Verpackungseinheit: 4×25 Stück.",
                "quality_check": True
            }
        }
