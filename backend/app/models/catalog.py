"""
Catalog generation models.
Phase 7: Professional HTML Catalog Output
"""
from pydantic import BaseModel


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
