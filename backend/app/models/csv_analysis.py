"""CSV Analysis Models for LLM-based column detection"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ColumnMapping(BaseModel):
    """Single CSV column to product field mapping."""
    csv_column: str = Field(description="Original CSV column name")
    product_field: str = Field(description="Mapped product field (e.g., 'article_number', 'product_name', 'price')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    is_join_key: bool = Field(description="True if this column is the unique article identifier")
    reasoning: str = Field(description="Why this mapping was chosen")


class ArrayColumnGroup(BaseModel):
    """Group of columns that form an array (e.g., PREIS0-9)."""
    base_name: str = Field(description="Base column name without digit (e.g., 'PREIS', 'ABMENGE')")
    columns: List[str] = Field(description="Full column names in order (e.g., ['PREIS0', 'PREIS1', ...])")
    pattern_type: str = Field(description="Type of array (e.g., 'price_tiers', 'quantity_tiers')")
    recommendation: str = Field(description="User-friendly recommendation for handling")


class CSVAnalysisResult(BaseModel):
    """Complete CSV analysis result with all column mappings."""
    mappings: List[ColumnMapping]
    array_column_groups: Optional[List[ArrayColumnGroup]] = Field(default=None, description="Detected array column groups (Phase 1 enhancement)")
