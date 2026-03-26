"""
CSV Analysis Service using Anthropic Claude.
CONTEXT D-01: Direct API calls, no frameworks
CONTEXT D-09: Tool Use with JSON Schema
CONTEXT D-13 to D-17: Confidence scoring and user confirmation
"""
from pathlib import Path
from anthropic import Anthropic, RateLimitError, APITimeoutError, AnthropicError
import time
from typing import Tuple

from app.core.config import settings
from app.models.csv_analysis import ColumnMapping, CSVAnalysisResult
from app.services.csv_sampling import sample_csv_for_llm


# System prompt with German terminology (RESEARCH §Common Pitfalls #3)
SYSTEM_PROMPT = """You are a German product CSV analyzer.

Identify the meaning of each column based on header names and sample data.

Common German product fields:
- Artikelnummer, Art-Nr, ArtNr, Art.Nr. → article_number (JOIN KEY)
- Bezeichnung1, Produktname → product_name
- Bezeichnung2, Beschreibung → product_description
- Preis, Price → price
- VE, Verpackungseinheit → packaging_unit
- PE, Paletteneinheit → pallet_unit
- Farbe → color
- Material → material
- EAN, EAN-Nummer → ean
- Gewicht, Weight → weight
- Innenmaß, Außenmaß → inner_dimension, outer_dimension
- Füllhöhe → fill_height

Confidence guidelines:
- 0.9-1.0: Obvious from name AND sample data clearly matches pattern
- 0.7-0.9: Name suggests meaning, sample data mostly consistent
- 0.5-0.7: Ambiguous name, inferring from sample data patterns
- 0.0-0.5: Cannot determine meaning confidently

**CRITICAL:** Mark exactly ONE column as is_join_key: true (the unique product identifier, usually Artikelnummer).

Be conservative with confidence — better to ask user than mismap data.
"""


def get_anthropic_client() -> Anthropic:
    """Get configured Anthropic client."""
    return Anthropic(api_key=settings.anthropic_api_key)


def validate_join_key_detection(result: CSVAnalysisResult) -> Tuple[bool, str]:
    """
    Ensure exactly ONE column is marked as join key.
    CONTEXT D-20: Validation requirement.
    """
    join_key_count = sum(1 for m in result.mappings if m.is_join_key)
    
    if join_key_count == 0:
        return False, "No join key detected. Artikelnummer column missing?"
    elif join_key_count > 1:
        join_keys = [m.csv_column for m in result.mappings if m.is_join_key]
        return False, f"Multiple join keys detected: {join_keys}. Only one expected."
    else:
        join_key = next(m for m in result.mappings if m.is_join_key)
        return True, f"Join key detected: {join_key.csv_column}"


def analyze_csv_structure(
    csv_path: Path,
    upload_id: str,
    anthropic_client: Anthropic,
    max_retries: int = 3
) -> CSVAnalysisResult:
    """
    Analyze CSV structure using Claude with Tool Use.
    
    CONTEXT D-02/D-03: Uses Claude 3.5 Haiku primarily
    CONTEXT D-05/D-06: Samples header + 5-10 rows
    CONTEXT D-09: Tool Use (structured JSON via tool schema)
    
    Args:
        csv_path: Path to UTF-8 CSV file
        upload_id: Upload session ID for tracking
        anthropic_client: Configured Anthropic client
        max_retries: Max retry attempts for rate limits
    
    Returns:
        CSVAnalysisResult with validated column mappings
        
    Raises:
        ValueError: If join-key validation fails
        RuntimeError: If Claude API call fails after retries
    """
    # Step 1: Sample CSV (CONTEXT D-05/D-06)
    csv_sample = sample_csv_for_llm(csv_path, max_rows=10)
    
    # Step 2: Prepare user prompt
    user_prompt = f"""Analyze this German product CSV:

{csv_sample}

Identify what each column represents and map to product fields.
Provide confidence scores and mark the unique article identifier as join key.
"""
    
    # Step 3: Prepare tool definition from Pydantic schema
    tools = [{
        "name": "report_csv_analysis",
        "description": "Report the analysis of CSV column meanings",
        "input_schema": CSVAnalysisResult.model_json_schema()
    }]
    
    # Step 4: Call Claude with retry logic (RESEARCH §Error Handling)
    for attempt in range(max_retries):
        try:
            response = anthropic_client.messages.create(
                model=settings.anthropic_model_primary,  # Claude 3.5 Haiku (CONTEXT D-02)
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice={"type": "tool", "name": "report_csv_analysis"},
                temperature=0.0  # Deterministic for consistency
            )
            
            # Step 5: Extract tool_use block
            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None
            )
            if not tool_use:
                raise ValueError("Claude did not return a tool_use block")
            
            result = CSVAnalysisResult.model_validate(tool_use.input)
            
            # Step 6: Validate join-key detection (CONTEXT D-20)
            is_valid, message = validate_join_key_detection(result)
            if not is_valid:
                raise ValueError(f"Join-key validation failed: {message}")
            
            return result
            
        except RateLimitError:
            # Rate limit hit → exponential backoff (RESEARCH §Architecture Patterns #5)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
                continue
            raise RuntimeError("Claude rate limit exceeded after retries")
            
        except APITimeoutError:
            # Timeout → retry
            if attempt < max_retries - 1:
                continue
            raise RuntimeError("Claude API timeout after retries")
            
        except AnthropicError as e:
            # Other API errors → don't retry, fail fast
            raise RuntimeError(f"Anthropic API error: {str(e)}")
