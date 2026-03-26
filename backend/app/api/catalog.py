"""
Catalog generation API endpoints.
Phase 7: Professional HTML Catalog Output
"""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.catalog_generator import generate_catalog
from app.models.catalog import GenerateCatalogRequest, GenerateCatalogResponse


router = APIRouter(prefix="/api/catalog")


@router.post("/generate", response_model=GenerateCatalogResponse)
async def generate_html_catalog(request: GenerateCatalogRequest):
    """
    Generate HTML catalog from merged product data.
    
    Args:
        request: GenerateCatalogRequest with upload_id
        
    Returns:
        GenerateCatalogResponse with generation statistics
        
    Raises:
        HTTPException 404: merged_products.json not found
        HTTPException 500: Catalog generation failed
    """
    try:
        result = await generate_catalog(
            upload_id=request.upload_id,
            upload_dir=settings.upload_dir
        )
        
        return GenerateCatalogResponse(
            success=True,
            total_products=result.total_products,
            files_generated=result.files_generated,
            output_path=result.output_path
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Catalog generation failed: {str(e)}"
        )
