"""
Catalog generation API endpoints.
Phase 7: Professional HTML Catalog Output
Phase 8: PDF Export Implementation
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.core.config import settings
from app.services.catalog_generator import generate_catalog
from app.services.pdf_generator import generate_pdfs
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


@router.post("/generate-pdf", response_model=List[GeneratePDFResponse])
async def generate_pdf_catalog(request: GeneratePDFRequest):
    """
    Generate PDF catalog from existing HTML files.
    
    Modes:
    - "individual": Generate separate PDF for each product
    - "complete": Generate single PDF with all products
    - "both": Generate both individual and complete PDFs
    
    Args:
        request: GeneratePDFRequest with upload_id and mode
        
    Returns:
        List of GeneratePDFResponse with generation statistics
        
    Raises:
        HTTPException 404: HTML catalog not found
        HTTPException 400: Invalid mode
        HTTPException 500: PDF generation failed
    """
    try:
        results = await generate_pdfs(
            upload_id=request.upload_id,
            mode=request.mode,
            upload_dir=settings.upload_dir
        )
        
        return [
            GeneratePDFResponse(
                success=True,
                total_products=result.total_products,
                files_generated=result.files_generated,
                output_path=result.output_path,
                mode=result.mode
            )
            for result in results
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
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
