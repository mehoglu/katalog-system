"""
Catalog generation models.
Phase 7: Professional HTML Catalog Output
Phase 8: PDF Export Implementation
"""
from pydantic import BaseModel, Field
from typing import Literal


class GenerateCatalogRequest(BaseModel):
    """Request model for catalog generation."""
    upload_id: str


class GenerateCatalogResponse(BaseModel):
    """Response model for catalog generation."""
    success: bool
    total_products: int
    files_generated: int
    output_path: str
    message: str = "Catalog generated successfully"


class GeneratePDFRequest(BaseModel):
    """Request model for PDF generation."""
    upload_id: str
    mode: Literal["individual", "complete", "both"] = Field(
        default="both",
        description="PDF generation mode: individual PDFs, single complete PDF, or both"
    )


class GeneratePDFResponse(BaseModel):
    """Response model for PDF generation."""
    success: bool
    total_products: int
    files_generated: int
    output_path: str
    mode: str
    message: str = "PDF generated successfully"
