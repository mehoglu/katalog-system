"""
CSV merge service for combining product data from multiple sources.
Implements Phase 3 decisions D-01 through D-19 from CONTEXT.md.
"""
from pathlib import Path
from typing import Union
import polars as pl
from datetime import datetime

from app.services.csv_sampling import detect_delimiter
from app.models.merge import MergedProduct, MergeResult


# Field-specific priority rules (D-05 from CONTEXT)
PREISLISTE_PRIORITY_FIELDS = {"preis", "menge1", "menge2", "menge3", "menge4", "menge5"}


def merge_csv_data(
    edi_csv_path: Union[str, Path],
    preisliste_csv_path: Union[str, Path]
) -> MergeResult:
    """
    Merge EDI Export and Preisliste CSVs via Artikelnummer.
    
    Implementation follows Phase 3 CONTEXT decisions:
    - D-01: Left join (EDI as basis)
    - D-05, D-06: Field-specific priority rules
    - D-09, D-10: Null values for missing data
    - D-12, D-14: Source tracking for every field
    
    Args:
        edi_csv_path: Path to EDI Export CSV (primary source)
        preisliste_csv_path: Path to Preisliste CSV (price data)
        
    Returns:
        MergeResult with complete product list and source tracking
        
    Raises:
        ValueError: If CSVs cannot be read or Artikelnummer column missing
    """
    edi_csv_path = Path(edi_csv_path)
    preisliste_csv_path = Path(preisliste_csv_path)
    
    # Read CSVs with delimiter detection (reuse from Phase 1)
    try:
        edi_delimiter = detect_delimiter(edi_csv_path, encoding="utf8")
        df_edi = pl.read_csv(
            edi_csv_path,
            separator=edi_delimiter,
            encoding="utf8",
            truncate_ragged_lines=True
        )
    except Exception as e:
        raise ValueError(f"Cannot read EDI CSV: {e}")
    
    try:
        preisliste_delimiter = detect_delimiter(preisliste_csv_path, encoding="utf8")
        df_preisliste = pl.read_csv(
            preisliste_csv_path,
            separator=preisliste_delimiter,
            encoding="utf8",
            truncate_ragged_lines=True
        )
    except Exception as e:
        raise ValueError(f"Cannot read Preisliste CSV: {e}")
    
    # Validate join key exists
    if "Artikelnummer" not in df_edi.columns:
        raise ValueError("EDI CSV missing 'Artikelnummer' column")
    if "Artikelnummer" not in df_preisliste.columns:
        raise ValueError("Preisliste CSV missing 'Artikelnummer' column")
    
    # Normalize column names to lowercase for consistent access
    df_edi.columns = [col.lower() for col in df_edi.columns]
    df_preisliste.columns = [col.lower() for col in df_preisliste.columns]
    
    # Rename Preisliste columns (except join key) to add suffix BEFORE join
    # This ensures we can distinguish between EDI and Preisliste fields
    preisliste_rename_map = {
        col: f"{col}_preisliste" if col != "artikelnummer" else col
        for col in df_preisliste.columns
    }
    df_preisliste = df_preisliste.rename(preisliste_rename_map)
    
    # Left join on Artikelnummer (D-01: EDI as basis)
    merged_df = df_edi.join(
        df_preisliste,
        on="artikelnummer",
        how="left"
    )
    
    # Build MergedProduct objects with source tracking
    products: list[MergedProduct] = []
    edi_only_count = 0
    matched_count = 0
    
    for row in merged_df.iter_rows(named=True):
        artikelnummer = row["artikelnummer"]
        
        # Check if this product matched in Preisliste
        # Look for ANY _preisliste suffix field with non-null value
        has_price_match = any(
            col.endswith("_preisliste") and row.get(col) is not None
            for col in merged_df.columns
        )
        
        if has_price_match:
            matched_count += 1
        else:
            edi_only_count += 1
        
        data = {}
        sources = {}
        
        # Get all field names (excluding artikelnummer and _preisliste suffixes)
        all_fields = set()
        for col in merged_df.columns:
            if col == "artikelnummer":
                continue
            if col.endswith("_preisliste"):
                # Add the base field name
                all_fields.add(col.replace("_preisliste", "").lower())
            else:
                all_fields.add(col.lower())
        
        # Process each field with source tracking
        for field_normalized in all_fields:
            # Get values from both sources
            edi_value = row.get(field_normalized)
            preisliste_field = f"{field_normalized}_preisliste"
            preisliste_value = row.get(preisliste_field)
            
            # Apply field-specific priority rules (D-05, D-06, D-07)
            if field_normalized in PREISLISTE_PRIORITY_FIELDS:
                # Preisliste wins for price fields (D-05)
                if preisliste_value is not None:
                    data[field_normalized] = preisliste_value
                    sources[field_normalized] = "preisliste"
                elif edi_value is not None:
                    # Fall back to EDI if Preisliste doesn't have it
                    data[field_normalized] = edi_value
                    sources[field_normalized] = "edi_export"
                else:
                    # Both are None
                    data[field_normalized] = None
                    sources[field_normalized] = None
            else:
                # EDI wins for all other fields (D-06, D-07)
                if edi_value is not None:
                    data[field_normalized] = edi_value
                    sources[field_normalized] = "edi_export"
                else:
                    data[field_normalized] = None
                    sources[field_normalized] = None
        
        products.append(MergedProduct(
            artikelnummer=str(artikelnummer),
            data=data,
            sources=sources
        ))
    
    return MergeResult(
        total_products=len(products),
        edi_only=edi_only_count,
        matched=matched_count,
        merge_timestamp=datetime.utcnow().isoformat(),
        products=products
    )
