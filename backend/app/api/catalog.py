"""
Catalog generation API endpoints.
Phase 7: Professional HTML Catalog Output
Phase 8: PDF Export Implementation
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.core.config import settings
from app.services.catalog_generator import generate_catalog

# PDF generator - optional import (requires Playwright)
try:
    from app.services.pdf_generator import generate_pdfs, PLAYWRIGHT_AVAILABLE
    PDF_AVAILABLE = PLAYWRIGHT_AVAILABLE
except ImportError as e:
    print(f"⚠️  PDF generation not available: {e}")
    PDF_AVAILABLE = False

from app.models.catalog import (
    GenerateCatalogRequest, 
    GenerateCatalogResponse,
    GeneratePDFRequest,
    GeneratePDFResponse
)


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


@router.post("/generate-pdf", response_model=GeneratePDFResponse)
async def generate_pdf_catalog(request: GeneratePDFRequest):
    """
    Generate PDF catalog from existing HTML files.
    
    Args:
        request: GeneratePDFRequest with upload_id, mode, and optional artikelnummern filter
        
    Returns:
        GeneratePDFResponse with generation statistics
        
    Raises:
        HTTPException 404: HTML catalog not found
        HTTPException 500: PDF generation failed
        HTTPException 503: PDF generation not available (missing system dependencies)
    """
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF generation not available. Install Playwright: pip install playwright && playwright install chromium"
        )
    
    try:
        results = await generate_pdfs(
            upload_id=request.upload_id,
            upload_dir=settings.upload_dir,
            mode=request.mode,
            artikelnummern=request.artikelnummern
        )
        
        # Get first result (for individual or complete mode) or combined stats for both
        if len(results) == 1:
            result = results[0]
            total_products = result.total_products
            pages_generated = result.files_generated
            catalog_file = result.output_path
        else:
            # Both mode: combine statistics
            total_products = sum(r.total_products for r in results)
            pages_generated = sum(r.files_generated for r in results)
            catalog_file = f"{results[0].output_path}, {results[1].output_path}"
        
        return GeneratePDFResponse(
            success=True,
            total_products=total_products,
            pages_generated=pages_generated,
            catalog_file=catalog_file
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )
