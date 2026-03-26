"""
Merge API endpoint for combining product data from multiple CSVs.
Implements Phase 3 FUSION-04 requirement.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
from datetime import datetime

from app.services.csv_merge import merge_csv_data
from app.models.merge import MergeResult
from app.core.config import settings

router = APIRouter()


class MergeRequest(BaseModel):
    """Request to merge two CSV uploads"""
    edi_upload_id: str
    preisliste_upload_id: str


class MergeResponse(BaseModel):
    """Response from merge operation"""
    success: bool
    merge_file: str  # Path to merged_products.json
    total_products: int
    matched: int
    edi_only: int
    timestamp: str


@router.post("/merge/csv", response_model=MergeResponse)
async def merge_csvs(request: MergeRequest):
    """
    Merge EDI Export and Preisliste CSVs via Artikelnummer.
    
    D-16, D-17, D-18 from CONTEXT: Save as merged_products.json in EDI upload dir.
    
    Args:
        request: Contains edi_upload_id and preisliste_upload_id
        
    Returns:
        MergeResponse with merge statistics and file path
        
    Raises:
        HTTPException 404: If upload directories or CSV files not found
        HTTPException 500: If merge operation fails
    """
    # Find upload directories
    edi_dir = settings.upload_dir / request.edi_upload_id
    preisliste_dir = settings.upload_dir / request.preisliste_upload_id
    
    if not edi_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"EDI upload not found: {request.edi_upload_id}"
        )
    if not preisliste_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Preisliste upload not found: {request.preisliste_upload_id}"
        )
    
    # Find CSV files (first .csv in each directory)
    edi_csv = next(edi_dir.glob("*.csv"), None)
    preisliste_csv = next(preisliste_dir.glob("*.csv"), None)
    
    if not edi_csv:
        raise HTTPException(
            status_code=404,
            detail=f"No CSV found in EDI upload: {request.edi_upload_id}"
        )
    if not preisliste_csv:
        raise HTTPException(
            status_code=404,
            detail=f"No CSV found in Preisliste upload: {request.preisliste_upload_id}"
        )
    
    # Perform merge
    try:
        result: MergeResult = merge_csv_data(edi_csv, preisliste_csv)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Merge failed: {str(e)}"
        )
    
    # Save as JSON (D-16, D-17: uploads/{upload_id}/merged_products.json)
    output_file = edi_dir / "merged_products.json"
    json_data = {
        "total_products": result.total_products,
        "matched": result.matched,
        "edi_only": result.edi_only,
        "merge_timestamp": result.merge_timestamp,
        "products": [p.dict() for p in result.products]
    }
    
    # Write JSON with proper encoding (D-18: JSON array with one object per product)
    output_file.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    return MergeResponse(
        success=True,
        merge_file=str(output_file.relative_to(settings.upload_dir.parent)),
        total_products=result.total_products,
        matched=result.matched,
        edi_only=result.edi_only,
        timestamp=result.merge_timestamp
    )
