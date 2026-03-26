"""
CSV Analysis API endpoints.
CONTEXT D-14: Returns confidence scores with color indicators
Requirements: CSV-02 (auto-detect join key), CSV-03 (mapping proposal)
"""
from fastapi import APIRouter, HTTPException, Depends
from anthropic import Anthropic

from app.core.config import settings
from app.services.csv_analysis import analyze_csv_structure, get_anthropic_client

router = APIRouter()


@router.post("/analyze/csv/{upload_id}")
async def analyze_uploaded_csv(
    upload_id: str,
    anthropic_client: Anthropic = Depends(get_anthropic_client)
):
    """
    Analyze uploaded CSV structure with LLM.
    
    Requirement CSV-01: System analyzes CSV structures automatically
    Requirement CSV-02: Detects article number column as join key
    Requirement CSV-03: Creates mapping proposal
    
    Args:
        upload_id: Upload session ID from Phase 1
        anthropic_client: Injected Anthropic client
    
    Returns:
        {
            "upload_id": str,
            "csv_file": str,
            "mappings": [...],
            "join_key": str,
            "low_confidence_count": int,
            "requires_confirmation": bool
        }
        
    Raises:
        404: Upload session not found
        422: Analysis validation failed
        500: Claude API error
    """
    # Find CSV from Phase 1 upload
    upload_dir = settings.upload_dir / upload_id
    if not upload_dir.exists():
        raise HTTPException(404, detail="Upload session not found")
    
    csv_files = list(upload_dir.glob("*.csv"))
    if not csv_files:
        raise HTTPException(404, detail="No CSV found for upload_id")
    
    csv_path = csv_files[0]
    
    try:
        # Analyze with LLM
        result = analyze_csv_structure(csv_path, upload_id, anthropic_client)
        
        # Extract join key (CONTEXT D-18: integrated in analysis)
        join_key = next(m.csv_column for m in result.mappings if m.is_join_key)
        
        # Count low-confidence mappings (CONTEXT D-14: <0.7 threshold)
        low_conf_count = sum(1 for m in result.mappings if m.confidence < 0.7)
        
        return {
            "upload_id": upload_id,
            "csv_file": csv_path.name,
            "mappings": [m.dict() for m in result.mappings],
            "join_key": join_key,
            "low_confidence_count": low_conf_count,
            "requires_confirmation": low_conf_count > 0  # CONTEXT D-15
        }
        
    except ValueError as e:
        # Join-key validation or sampling errors
        raise HTTPException(422, detail=str(e))
    except RuntimeError as e:
        # Claude API errors
        raise HTTPException(500, detail=str(e))
