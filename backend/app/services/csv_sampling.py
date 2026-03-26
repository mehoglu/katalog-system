"""
CSV sampling service for LLM context extraction.
CONTEXT D-05: Header + 5-10 sample rows per CSV
CONTEXT D-06: Intelligent sampling for large CSVs
"""
from pathlib import Path
import polars as pl


def detect_delimiter(csv_path: Path, encoding: str = "utf8") -> str:
    """
    Detect CSV delimiter by checking first line.
    Common delimiters: comma, semicolon, tab, pipe
    """
    with open(csv_path, 'r', encoding=encoding) as f:
        first_line = f.readline()
    
    # Count occurrences of common delimiters
    delimiters = {
        ',': first_line.count(','),
        ';': first_line.count(';'),
        '\t': first_line.count('\t'),
        '|': first_line.count('|')
    }
    
    # Return delimiter with highest count (default to comma if all zero)
    detected = max(delimiters, key=delimiters.get)
    return detected if delimiters[detected] > 0 else ','


def sample_csv_for_llm(csv_path: Path, max_rows: int = 10) -> str:
    """
    Extract representative CSV sample for LLM analysis.
    
    Strategy (CONTEXT D-06):
    - Small CSV (<=max_rows): Use all rows
    - Large CSV (>max_rows): First 5 rows + random 5 from rest
    
    Args:
        csv_path: Path to UTF-8 CSV file (guaranteed by Phase 1)
        max_rows: Maximum rows to include in sample
    
    Returns:
        Semicolon-delimited CSV string with header + sample rows
        
    Raises:
        ValueError: If CSV is empty or unreadable
    """
    # Read CSV lazily (memory-efficient for large files)
    # Phase 1 guarantees UTF-8 encoding, so encoding="utf8" is safe
    try:
        delimiter = detect_delimiter(csv_path, encoding="utf8")
        df = pl.read_csv(
            csv_path, 
            encoding="utf8", 
            separator=delimiter,
            truncate_ragged_lines=True,
            n_rows=1000
        )
    except Exception as e:
        raise ValueError(f"Cannot read CSV: {e}")
    
    if len(df) == 0:
        raise ValueError("CSV is empty")
    
    total_rows = len(df)
    
    if total_rows <= max_rows:
        # Small CSV: use all rows
        sample_df = df
    else:
        # Large CSV: intelligent sampling (CONTEXT D-06)
        # First 5 rows (typical patterns)
        first_half = df.head(5)
        
        # Random 5 from remaining (edge cases, variety)
        remaining = df.tail(total_rows - 5)
        random_half = remaining.sample(n=min(5, len(remaining)), seed=42)
        
        sample_df = pl.concat([first_half, random_half])
    
    # Convert to semicolon-delimited string (German CSV standard)
    # This is the format LLM will see
    return sample_df.write_csv(separator=";")
