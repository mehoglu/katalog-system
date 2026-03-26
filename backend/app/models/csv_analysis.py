"""CSV Analysis Models for LLM-based column detection"""
from pydantic import BaseModel, Field
from typing import List


class ColumnMapping(BaseModel):
    """Single CSV column to product field mapping."""
    csv_column: str = Field(description="Original CSV column name")
    product_field: str = Field(description="Mapped product field (e.g., 'article_number', 'product_name', 'price')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    is_join_key: bool = Field(description="True if this column is the unique article identifier")
    reasoning: str = Field(description="Why this mapping was chosen")


class CSVAnalysisResult(BaseModel):
    """Complete CSV analysis result with all column mappings."""
    mappings: List[ColumnMapping]
