"""
CSV validation service
CONTEXT D-11: Erweiterte Prüfung (Struktur + Inhalt)
CONTEXT D-12: Early-exit Performance-Strategie
"""
from pathlib import Path
import polars as pl
from typing import Optional

from app.models.validation import ValidationError, ValidationResult, ErrorSeverity

def validate_csv_structure(
    csv_path: Path,
    upload_id: str,
    encoding: str = "utf8"  # Polars expects "utf8" not "utf-8"
) -> ValidationResult:
    """
    Validiert CSV-Struktur und Inhalt (CONTEXT D-11)
    
    Phase 1 validation:
    - CSV parsable (basic structure)
    - Encoding correct (Umlaute vorhanden)
    - Has rows and columns
    - Basic duplicate check (Artikelnummer)
    
    Deferred to Phase 2:
    - Column semantics (which column is Artikelnummer)
    - Article number format validation
    - Cross-CSV duplicate detection
    - Data completeness checks
    
    Args:
        csv_path: Path to CSV file (already UTF-8 converted)
        upload_id: Upload session ID
        encoding: File encoding (should be "utf8" for Polars after conversion)
        
    Returns:
        ValidationResult with errors/warnings
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []
    stats = {}
    
    # CONTEXT D-12: Early-exit - stop at first critical error
    try:
        # Try to parse CSV with Polars (lazy evaluation)
        # Note: Use read_csv (eager) first to detect delimiter, then scan_csv for lazy ops
        df = pl.read_csv(
            csv_path,
            encoding=encoding,
            separator=None,  # Auto-detect delimiter (comma, semicolon, tab, etc.)
            ignore_errors=False,  # Fail on parse errors
            truncate_ragged_lines=True  # Handle rows with varying column counts (common in real CSVs)
        )
        
        # Check 1: Empty file?
        try:
            row_count = len(df)  # Already eager, no need for .collect()
        except Exception as e:
            errors.append(ValidationError(
                severity=ErrorSeverity.CRITICAL,
                file=csv_path.name,
                line=None,
                column=None,
                message=f"Failed to parse CSV: {str(e)}",
                suggestion="Check file format and encoding"
            ))
            return ValidationResult(
                upload_id=upload_id,
                file=csv_path.name,
                status="errors",
                errors=errors,
                stats={}
            )
        
        if row_count == 0:
            errors.append(ValidationError(
                severity=ErrorSeverity.CRITICAL,
                file=csv_path.name,
                line=None,
                column=None,
                message="CSV file is empty",
                suggestion="Upload a file with product data"
            ))
            return ValidationResult(
                upload_id=upload_id,
                file=csv_path.name,
                status="errors",
                errors=errors,
                stats={"rows": 0}
            )
        
        # Check 2: Has columns?
        columns = df.columns
        stats["rows"] = row_count
        stats["columns"] = len(columns)
        
        if len(columns) == 0:
            errors.append(ValidationError(
                severity=ErrorSeverity.CRITICAL,
                file=csv_path.name,
                line=1,
                column=None,
                message="No columns detected in CSV",
                suggestion="Ensure first row contains column headers"
            ))
            return ValidationResult(
                upload_id=upload_id,
                file=csv_path.name,
                status="errors",
                errors=errors,
                stats=stats
            )
        
        # Check 3: Look for Artikelnummer column (extended check - CONTEXT D-11)
        # Note: Column semantic detection is Phase 2, but basic check here
        artikelnummer_cols = [col for col in columns if 'artikelnummer' in col.lower() or 'artikel-nr' in col.lower()]
        
        if not artikelnummer_cols:
            warnings.append(ValidationError(
                severity=ErrorSeverity.WARNING,  # WARNING not CRITICAL (CONTEXT D-10)
                file=csv_path.name,
                line=1,
                column=None,
                message="No 'Artikelnummer' column found",
                suggestion="Phase 2 will detect column semantics - you can proceed"
            ))
        else:
            # Check 4: Duplicate article numbers? (limited sample for performance)
            artikelnummer_col = artikelnummer_cols[0]
            stats["artikelnummer_column"] = artikelnummer_col
            
            # CONTEXT D-12: Early-exit - only check first 500 rows for duplicates
            sample_df = df.select(artikelnummer_col).head(500)  # Already eager
            
            duplicated = sample_df.filter(pl.col(artikelnummer_col).is_duplicated())
            if len(duplicated) > 0:
                first_dup = duplicated.row(0)[0]
                warnings.append(ValidationError(
                    severity=ErrorSeverity.WARNING,
                    file=csv_path.name,
                    line=None,  # Would need full scan to find exact line
                    column=artikelnummer_col,
                    message=f"Duplicate article numbers found (first: {first_dup})",
                    suggestion="Review data in table interface (Phase 6)"
                ))
        
        # Check 5: Validate German umlauts present (encoding check)
        # Sample first 100 rows to look for German characters
        sample_text = df.head(100).to_pandas().to_string()  # Already eager
        has_german_chars = any(char in sample_text for char in ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü'])
        
        if not has_german_chars:
            warnings.append(ValidationError(
                severity=ErrorSeverity.WARNING,
                file=csv_path.name,
                line=None,
                column=None,
                message="No German umlauts detected - encoding may be incorrect",
                suggestion="Verify product names display correctly in UI"
            ))
        
        # Determine status
        if errors:
            status = "errors"
        elif warnings:
            status = "warnings"
        else:
            status = "valid"
        
        return ValidationResult(
            upload_id=upload_id,
            file=csv_path.name,
            status=status,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        errors.append(ValidationError(
            severity=ErrorSeverity.CRITICAL,
            file=csv_path.name,
            line=None,
            column=None,
            message=f"Validation failed: {str(e)}",
            suggestion="Check file format"
        ))
        return ValidationResult(
            upload_id=upload_id,
            file=csv_path.name,
            status="errors",
            errors=errors,
            stats=stats
        )
