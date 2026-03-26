"""
Merged product data models with source tracking.
Implements D-12 through D-15 from Phase 3 CONTEXT.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class MergedProduct(BaseModel):
    """
    Merged product with source tracking.
    
    D-12 from CONTEXT: data + sources objects
    - data: All product fields with actual values
    - sources: For each field, which CSV it came from
    """
    artikelnummer: str
    data: Dict[str, Any]  # All product fields
    sources: Dict[str, Optional[Literal["edi_export", "preisliste"]]]  # Field -> source mapping


class MergeResult(BaseModel):
    """
    Result of CSV merge operation.
    
    Tracks merge statistics and complete product list.
    """
    total_products: int
    edi_only: int  # Products only in EDI (no price data)
    matched: int  # Products in both CSVs
    merge_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    products: list[MergedProduct]
