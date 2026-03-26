"""Validation error models"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ErrorSeverity(str, Enum):
    """Fehler-Schweregrad"""
    CRITICAL = "critical"  # Blockiert Processing
    WARNING = "warning"    # Kann fortfahren (CONTEXT D-10)
    INFO = "info"          # Nur FYI

class ValidationError(BaseModel):
    """
    Strukturierter Validierungsfehler
    CONTEXT D-14: Zeilenspezifische Fehler wo möglich
    """
    severity: ErrorSeverity
    file: str
    line: Optional[int] = None  # None für file-level errors
    column: Optional[str] = None
    message: str
    suggestion: Optional[str] = None  # Actionable fix (CONTEXT D-16)
    
class ValidationResult(BaseModel):
    """Ergebnis der CSV-Validierung"""
    upload_id: str
    file: str
    status: str  # "valid", "warnings", "errors"
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)  # rows, columns, encoding
