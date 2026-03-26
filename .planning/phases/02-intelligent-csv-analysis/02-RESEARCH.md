# Phase 2 Research: Intelligent CSV Analysis

**Phase:** 02-intelligent-csv-analysis  
**Research Date:** 26. März 2026  
**Confidence Level:** HIGH (OpenAI APIs, Structured Outputs), MEDIUM (CSV sampling strategies)

---

## User Constraints

**CRITICAL: These are LOCKED decisions from CONTEXT.md. Plans MUST honor these.**

### LLM Integration (Locked)
- **Direct OpenAI API calls** — No frameworks (no LangChain)
- **GPT-4o-mini** as primary model ($0.15/1M input tokens)
- **GPT-4o** as fallback for complex cases
- Self-built retry-logic and rate-limiting

### CSV Context (Locked)
- **Header + 5-10 sample rows** as LLM input (~500-1000 tokens)
- Intelligent sampling: first 5 + random 5 from middle/end for large CSVs
- No full statistical pre-processing in Phase 2

### Output Format (Locked)
- **OpenAI Structured Outputs** with JSON Schema (strict validation)
- Schema: `{mappings: [{csv_column, product_field, confidence, is_join_key, reasoning}]}`
- No Function Calling (avoids multiple roundtrips)

### Confidence Handling (Locked)
- LLM returns confidence score 0.0-1.0 per mapping
- UI thresholds: >0.9 green (auto-accept), 0.7-0.9 yellow (review), <0.7 red (confirmation required)
- User must confirm <0.7 mappings

### Join-Key Detection (Locked)
- Artikelnummer detection integrated in main analysis
- `is_join_key: boolean` field in schema
- Exactly ONE column per CSV must be `is_join_key: true`

### Agent's Discretion
- Prompt engineering details
- Token limit management
- Error handling specifics
- Caching strategy (optional v2)
- UI layout

---

## Standard Stack

**PRIMARY:**
```python
anthropic==0.25.0+        # Official Anthropic Python SDK (2026 current)
pydantic==2.6.0+          # Data validation, JSON schema generation
polars==0.20.10           # CSV reading (already in Phase 1)
```

**EXISTING (from Phase 1):**
```python
fastapi==0.110.0+         # Backend API
pydantic-settings==2.2.0+ # Config management
```

**Rationale:**
- `anthropic` SDK has native Tool Use support (since Claude 3)
- `pydantic` v2 defines tool schemas for Claude
- `polars` already proven for CSV processing in Phase 1

---

## Architecture Patterns

### 1. Claude Tool Use Pattern (2024+)

**HIGH CONFIDENCE** — This is the current standard as of late 2024/2026.

```python
from anthropic import Anthropic
from pydantic import BaseModel

class ColumnMapping(BaseModel):
    csv_column: str
    product_field: str
    confidence: float  # 0.0-1.0
    is_join_key: bool
    reasoning: str

class CSVAnalysisResult(BaseModel):
    mappings: list[ColumnMapping]

client = Anthropic(api_key=settings.anthropic_api_key)

# Define tool for structured output
tools = [{
    "name": "analyze_csv_columns",
    "description": "Analyze CSV columns and return structured mappings",
    "input_schema": CSVAnalysisResult.model_json_schema()
}]

response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=4096,
    tools=tools,
    tool_choice={"type": "tool", "name": "analyze_csv_columns"},
    messages=[{
        "role": "user",
        "content": f"Analyze this CSV:\n\n{csv_sample}"
    }],
    system=system_prompt
)

# Extract tool use result
tool_use = next(block for block in response.content if block.type == "tool_use")
result = CSVAnalysisResult.model_validate(tool_use.input)
```

**Key features:**
- Tool Use forces structured JSON output
- Pydantic schema → Claude tool definition
- Single call returns all mappings
- Guaranteed valid output matching schema

### 2. CSV Sampling Strategy

**MEDIUM CONFIDENCE** — Based on common practices, not official OpenAI guidance.

```python
import polars as pl

def sample_csv_for_llm(csv_path: Path, max_rows: int = 10) -> str:
    """
    Extract header + representative sample rows for LLM context.
    
    Returns formatted string: "Column1;Column2;...\nRow1...\nRow2..."
    """
    df = pl.read_csv(csv_path, n_rows=1000)  # Read first 1000 for sampling
    
    total_rows = len(df)
    
    if total_rows <= max_rows:
        # Small CSV: use all rows
        sample_df = df
    else:
        # Large CSV: intelligent sampling
        # First 5 rows (typical data patterns)
        first_5 = df.head(5)
        
        # Random 5 from remaining (handle edge cases, variety)
        remaining = df.tail(total_rows - 5)
        random_5 = remaining.sample(n=min(5, len(remaining)), seed=42)
        
        sample_df = pl.concat([first_5, random_5])
    
    # Convert to semicolon-delimited string (German CSV standard)
    return sample_df.write_csv(separator=";")
```

**Rationale:**
- First rows often have typical patterns
- Random middle/end rows catch data variety and edge cases
- Seed=42 ensures reproducibility for debugging
- Semicolon delimiter matches German CSV exports

### 3. Model Selection Strategy

**HIGH CONFIDENCE** — Based on Anthropic pricing and capabilities.

```python
def get_model_for_csv_analysis(
    column_count: int,
    sample_row_count: int,
    has_previous_failure: bool = False
) -> str:
    """
    Select appropriate Claude model based on complexity.
    
    Claude 3.5 Haiku: $0.25/1M input, $1.25/1M output (fast, cost-effective)
    Claude 3.5 Sonnet: $3/1M input, $15/1M output (highest quality)
    """
    # Cost estimate per analysis
    est_tokens = (column_count * 20) + (sample_row_count * 50)
    
    # Decision logic
    if has_previous_failure:
        # Previous analysis was ambiguous → upgrade to Sonnet
        return "claude-3-5-sonnet-20241022"
    elif column_count > 20 or est_tokens > 2000:
        # Complex CSV → use Sonnet for better reasoning
        return "claude-3-5-sonnet-20241022"
    else:
        # Standard case → Haiku is sufficient
        return "claude-3-5-haiku-20241022"
```

**Cost estimates (500 products, 8 columns, 10 sample rows):**
- Claude 3.5 Haiku: ~$0.01-0.02 per CSV analysis
- Claude 3.5 Sonnet: ~$0.15-0.25 per CSV analysis

**When to upgrade to Sonnet:**
- Many columns (>20) or ambiguous headers
- Previous Haiku analysis had low confidence (<0.7)
- Complex domain-specific terminology

### 4. Confidence Score Calibration

**MEDIUM CONFIDENCE** — Pattern from LLM output interpretation.

```python
def interpret_confidence(score: float, reasoning: str) -> tuple[str, str]:
    """
    Translate LLM confidence score to UI status.
    
    Returns: (status_color, user_action)
    """
    if score >= 0.9:
        return ("green", "auto_accept")
    elif score >= 0.7:
        return ("yellow", "review_suggested")
    else:
        return ("red", "confirmation_required")

# Prompt engineering for calibrated confidence
SYSTEM_PROMPT = """
You are a CSV column analyzer. Rate your confidence honestly:

0.9-1.0: Column meaning is obvious from name AND sample data clearly matches
0.7-0.9: Column name suggests meaning, sample data mostly consistent
0.5-0.7: Ambiguous column name, inferring from sample data patterns
0.0-0.5: Cannot determine meaning confidently

Be conservative - better to ask user than mismap.
"""
```

**Calibration tips:**
- Instruct LLM to be conservative (avoids false confidence)
- Provide examples in prompt of different confidence levels
- Monitor actual accuracy vs reported confidence over time

### 5. Error Handling & Retry Logic

**HIGH CONFIDENCE** — Standard resilience patterns for OpenAI APIs.

```python
import time
from openai import OpenAIError, RateLimitError, APITimeoutError

def analyze_csv_with_retry(
    csv_sample: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> CSVAnalysisResult:
    """
    Resilient CSV analysis with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            response = client.beta.chat.completions.parse(
                model=get_model_for_csv_analysis(...),
                messages=[...],
                response_format=CSVAnalysisResult,
                timeout=30.0  # 30 second timeout
            )
            return response.choices[0].message.parsed
            
        except RateLimitError as e:
            # Hit rate limit → exponential backoff
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)
                continue
            raise
            
        except APITimeoutError:
            # Timeout → retry with longer timeout
            if attempt < max_retries - 1:
                continue
            raise
            
        except OpenAIError as e:
            # Other API errors → don't retry, fail fast
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI API error: {str(e)}"
            )
```

**Retry strategy:**
- Exponential backoff: 1s, 2s, 4s
- Retry on: Rate limits, timeouts
- Don't retry on: Invalid API key, malformed requests, refusals
- Total max time: ~7 seconds for 3 retries

### 6. Join-Key Validation

**HIGH CONFIDENCE** — Required for Phase 3 data fusion.

```python
def validate_join_key_detection(result: CSVAnalysisResult) -> tuple[bool, str]:
    """
    Ensure exactly ONE column is marked as join key.
    """
    join_key_count = sum(1 for m in result.mappings if m.is_join_key)
    
    if join_key_count == 0:
        return False, "No join key detected. Artikelnummer column missing?"
    elif join_key_count > 1:
        join_keys = [m.csv_column for m in result.mappings if m.is_join_key]
        return False, f"Multiple join keys detected: {join_keys}. Only one expected."
    else:
        # Exactly 1 join key → valid
        join_key = next(m for m in result.mappings if m.is_join_key)
        return True, f"Join key: {join_key.csv_column}"
```

**LLM prompt guidance for join-key:**
```
Identify the column that uniquely identifies each product (article number, SKU, product ID).
Common German names: "Artikelnummer", "Art-Nr", "Art.Nr.", "Artikel-Nr.", "ArtNr"
Mark this column with is_join_key: true. Exactly ONE column should be the join key.
```

---

## Don't Hand-Roll

**NEVER build custom solutions for these problems** — use proven libraries:

| Problem | DON'T Build | USE Instead |
|---------|-------------|-------------|
| OpenAI API client | Custom HTTP requests | `openai` Python SDK (official) |
| JSON Schema validation | Manual dict validation | `pydantic` v2 models |
| CSV parsing | Custom file readers | `polars.read_csv()` (already in Phase 1) |
| Retry logic | Basic try/except | Exponential backoff with `tenacity` library (optional) or manual |
| Rate limiting | Request counting | Built-in OpenAI SDK rate limit handling + backoff |

**Why avoid custom OpenAI client:**
- SDK handles auth, retries, streaming, structured outputs automatically
- Breaking API changes handled by SDK updates
- Type hints and IDE autocomplete

**Why avoid custom JSON validation:**
- Pydantic generates OpenAI-compatible schemas automatically
- Type safety at development time
- Clear error messages for invalid data

---

## Common Pitfalls

### Pitfall 1: Token Limit Exceeded

**Problem:** CSVs with 50+ columns + 500 rows → massive context.

**Solution:**
- Limit sample to 10 rows max
- Truncate long cell values (>100 chars) in sample
- For very wide CSVs (>30 columns), consider two-pass analysis:
  1. First pass: Identify likely product-related columns only
  2. Second pass: Deep analysis of selected columns

**Detection:**
```python
if len(csv_sample) > 15000:  # ~15KB text input
    # Reduce sample size or truncate
    warning = "CSV sample too large, reducing context..."
```

### Pitfall 2: Ambiguous Column Names

**Problem:** Headers like "F1", "Spalte_A", "Desc" → LLM guesses.

**Solution:**
- Always include sample rows (header alone insufficient)
- Prompt LLM to assign LOW confidence when ambiguous
- UI forces user confirmation on <0.7 confidence

**Example:**
- Column "Desc" could be Bezeichnung1 (product name) OR Bezeichnung2 (description)
- Sample data resolves: "Müllbehälter 120L" → Bezeichnung1 (name), "Robuster Kunststoff..." → Bezeichnung2 (description)

### Pitfall 3: German-Specific Terminology

**Problem:** German product CSVs use specific terms LLM might misinterpret.

**Solution:**
Include domain glossary in system prompt:

```
German product data terminology:
- Artikelnummer: Article number (unique ID)
- Bezeichnung1: Primary product name
- Bezeichnung2: Product description/details
- VE: Verpackungseinheit (packaging unit)
- PE: Paletteneinheit (pallet unit)
- Innenmaß/Außenmaß: Inner/outer dimensions
- Füllhöhe: Fill height
```

### Pitfall 4: Confidence Over-Confidence

**Problem:** LLM always returns 0.95+ confidence (not calibrated).

**Solution:**
- Add calibration examples to system prompt
- Monitor actual accuracy vs confidence in production
- If actual accuracy << confidence, add more conservative instructions

**Monitoring:**
```python
# Track over time
actual_accuracy = correct_mappings / total_mappings
avg_confidence = sum(m.confidence for m in mappings) / len(mappings)

if avg_confidence > actual_accuracy + 0.15:
    # Over-confident → adjust prompt
    pass
```

### Pitfall 5: Missing Join-Key Detection

**Problem:** Both CSVs analyzed, but column names differ ("Artikelnummer" vs "Art-Nr").

**Solution:**
- Normalize join-key in prompt: "Identify article number column regardless of exact spelling"
- Phase 3 (Data Fusion) should handle fuzzy join-key matching
- Validation: Warn if join-key detection confidence <0.8

### Pitfall 6: Cost Explosion

**Problem:** Analyzing 500 CSVs with GPT-4o → $$$.

**Solution:**
- Default to GPT-4o-mini ($0.15/1M vs $2.50/1M)
- Only upgrade to GPT-4o on retry or complexity trigger
- Batch multiple CSVs if structure identical (v2 optimization)

**Cost estimates:**
- 2 CSVs per analysis × 1000 tokens avg = 2000 tokens
- GPT-4o-mini: $0.0003 per analysis
- For 100 analyses: $0.03 total (negligible)

---

## Code Examples

### Complete Analysis Flow

```python
from pathlib import Path
from anthropic import Anthropic
from pydantic import BaseModel, Field
from typing import List
import polars as pl

# === Models ===

class ColumnMapping(BaseModel):
    csv_column: str = Field(description="Original CSV column name")
    product_field: str = Field(description="Mapped product field (e.g., 'article_number', 'name', 'price')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    is_join_key: bool = Field(description="True if this column is the unique article identifier")
    reasoning: str = Field(description="Why this mapping was chosen")

class CSVAnalysisResult(BaseModel):
    mappings: List[ColumnMapping]

# === CSV Sampling ===

def sample_csv_for_llm(csv_path: Path, max_rows: int = 10) -> str:
    """Extract representative sample for LLM analysis."""
    df = pl.read_csv(csv_path, n_rows=1000)
    
    if len(df) <= max_rows:
        sample = df
    else:
        first_half = df.head(5)
        random_half = df.tail(len(df) - 5).sample(n=5, seed=42)
        sample = pl.concat([first_half, random_half])
    
    return sample.write_csv(separator=";")

# === Analysis ===

SYSTEM_PROMPT = """You are a German product CSV analyzer. 

Identify the meaning of each column based on header names and sample data.

Common German product fields:
- Artikelnummer, Art-Nr, ArtNr → article_number (JOIN KEY)
- Bezeichnung1, Produktname → product_name
- Bezeichnung2, Beschreibung → product_description
- Preis, Price → price
- VE, Verpackungseinheit → packaging_unit
- Farbe → color
- Material → material
- EAN, EAN-Nummer → ean

Confidence guidelines:
- 0.9-1.0: Obvious from name AND data matches
- 0.7-0.9: Name suggests meaning, data mostly consistent
- 0.5-0.7: Ambiguous name, inferring from data
- 0.0-0.5: Cannot determine confidently

Mark exactly ONE column as is_join_key: true (the unique product identifier).
"""

def analyze_csv_structure(
    upload_id: str,
    csv_path: Path,
    client: Anthropic
) -> CSVAnalysisResult:
    """
    Analyze CSV structure with Claude.
    
    Returns: CSVAnalysisResult with column mappings
    """
    # Step 1: Sample CSV
    csv_sample = sample_csv_for_llm(csv_path)
    
    # Step 2: Prepare prompt
    user_prompt = f"""Analyze this German product CSV:

{csv_sample}

Identify what each column represents and map to product fields.
"""
    
    # Step 3: Prepare tool definition from Pydantic schema
    tools = [{
        "name": "analyze_csv_columns",
        "description": "Report the analysis of CSV column meanings",
        "input_schema": CSVAnalysisResult.model_json_schema()
    }]
    
    # Step 4: Call Claude with Tool Use
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        tools=tools,
        tool_choice={"type": "tool", "name": "analyze_csv_columns"},
        temperature=0.0  # Deterministic for consistency
    )
    
    # Step 5: Extract tool_use block and parse result
    tool_use = next(
        (block for block in response.content if block.type == "tool_use"),
        None
    )
    if not tool_use:
        raise ValueError("Claude did not return a tool_use block")
    
    result = CSVAnalysisResult.model_validate(tool_use.input)
    
    # Step 6: Validate join-key detection
    is_valid, message = validate_join_key_detection(result)
    if not is_valid:
        raise ValueError(f"Join-key validation failed: {message}")
    
    return result
```

### FastAPI Endpoint Integration

```python
from fastapi import APIRouter, HTTPException, Depends
from anthropic import Anthropic

router = APIRouter()

def get_anthropic_client() -> Anthropic:
    """Dependency for Anthropic client."""
    return Anthropic(api_key=settings.anthropic_api_key)

@router.post("/analyze/csv/{upload_id}")
async def analyze_uploaded_csv(
    upload_id: str,
    anthropic_client: Anthropic = Depends(get_anthropic_client)
):
    """
    Analyze uploaded CSV structure.
    
    Returns: {
        "upload_id": str,
        "mappings": [...],
        "join_key": str,
        "low_confidence_count": int
    }
    """
    # Find CSV from Phase 1 upload
    upload_dir = settings.upload_dir / upload_id
    csv_files = list(upload_dir.glob("*.csv"))
    
    if not csv_files:
        raise HTTPException(404, "No CSV found for upload_id")
    
    csv_path = csv_files[0]
    
    try:
        # Analyze with Claude
        result = analyze_csv_structure(upload_id, csv_path, anthropic_client)
        
        # Prepare response
        join_key = next(m.csv_column for m in result.mappings if m.is_join_key)
        low_conf_count = sum(1 for m in result.mappings if m.confidence < 0.7)
        
        return {
            "upload_id": upload_id,
            "mappings": [m.dict() for m in result.mappings],
            "join_key": join_key,
            "low_confidence_count": low_conf_count,
            "requires_confirmation": low_conf_count > 0
        }
        
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
```

---

## Performance Targets

**From ROADMAP Success Criteria:** System processes CSV analysis within 30 seconds for 500+ products.

**Breakdown:**
- CSV sampling: <1 second (Polars is fast)
- Claude API call: 3-10 seconds (depends on token count, model)
- Response parsing: <1 second (Pydantic validation)
- **Total per CSV:** 5-12 seconds

**For 2 CSVs (Preisliste + EDI Export):** 10-24 seconds → ✅ Meets <30s target

**Optimization opportunities (if needed):**
- Parallel analysis of both CSVs (if independent)
- Reduce sample size for very large CSVs
- Cache results for identical structures (v2)

---

## Integration Points

### Phase 1 Dependencies (REQUIRED)

Phase 2 consumes Phase 1 outputs:
- **Upload session directory:** `.planning/uploads/{upload_id}/`
- **UTF-8 normalized CSVs:** Already validated and encoded correctly
- **Upload metadata:** `CSVUploadResponse` from Phase 1

### Phase 3 Requirements (OUTPUT)

Phase 2 produces for Phase 3 (Data Fusion):
- **Mapping JSON:** Column → Product field mappings for each CSV
- **Join-key identification:** Which column is Artikelnummer in each CSV
- **Confidence scores:** For validation and user review

**Data structure Phase 3 expects:**
```json
{
  "upload_id": "2026-03-26_143022",
  "csv_file": "EDI Export Artikeldaten.csv",
  "mappings": [
    {
      "csv_column": "Artikelnummer",
      "product_field": "article_number",
      "confidence": 0.98,
      "is_join_key": true
    },
    {
      "csv_column": "Bezeichnung1",
      "product_field": "product_name",
      "confidence": 0.95,
      "is_join_key": false
    }
  ]
}
```

### UI Requirements

Phase 2 must provide data for UI display:
- **Mapping table:** CSV column → Product field → Confidence → Actions
- **Confidence indicators:** Color-coded (green/yellow/red)
- **Edit capability:** User can override low-confidence mappings
- **Confirmation flow:** <0.7 confidence requires user click

---

## Validation Architecture

### Unit Tests

```python
# tests/test_csv_analysis.py

def test_sample_csv_small():
    """Small CSVs use all rows."""
    # Create test CSV with 5 rows
    # Assert sample contains all 5

def test_sample_csv_large():
    """Large CSVs use first 5 + random 5."""
    # Create test CSV with 500 rows
    # Assert sample has exactly 10 rows
    # Assert includes first row and last segment

def test_join_key_validation_none():
    """No join key detected → validation fails."""
    result = CSVAnalysisResult(mappings=[
        ColumnMapping(..., is_join_key=False)
    ])
    valid, msg = validate_join_key_detection(result)
    assert not valid
    assert "No join key" in msg

def test_join_key_validation_multiple():
    """Multiple join keys → validation fails."""
    result = CSVAnalysisResult(mappings=[
        ColumnMapping(..., is_join_key=True),
        ColumnMapping(..., is_join_key=True)
    ])
    valid, msg = validate_join_key_detection(result)
    assert not valid
    assert "Multiple" in msg

def test_confidence_thresholds():
    """Confidence interpretation matches UI requirements."""
    assert interpret_confidence(0.95, "")[0] == "green"
    assert interpret_confidence(0.8, "")[0] == "yellow"
    assert interpret_confidence(0.6, "")[0] == "red"
```

### Integration Tests

```python
# tests/test_analyze_endpoint.py

@pytest.mark.asyncio
async def test_analyze_csv_endpoint_success(test_client, mock_openai):
    """Successful CSV analysis returns mappings."""
    # Upload CSV in Phase 1
    # Call /analyze/csv/{upload_id}
    # Assert 200 response
    # Assert mappings present
    # Assert join_key identified

@pytest.mark.asyncio
async def test_analyze_csv_endpoint_no_join_key(test_client, mock_openai):
    """Analysis fails if no join key detected."""
    # Mock OpenAI to return result with no join key
    # Call endpoint
    # Assert 422 error

@pytest.mark.asyncio
async def test_analyze_csv_endpoint_low_confidence(test_client, mock_openai):
    """Low confidence mappings flagged for user."""
    # Mock confidence <0.7 for some columns
    # Call endpoint
    # Assert requires_confirmation=true
    # Assert low_confidence_count > 0
```

### Manual Verification

**Test Cases (use actual asset files):**

1. **EDI Export Artikeldaten.csv:**
   - Headers: Artikelnummer, Bezeichnung1, Bezeichnung2, Farbe, Material, etc.
   - Expected: Artikelnummer = join_key, confidence >0.9 for most columns

2. **Preisliste.csv:**
   - Headers: Art-Nr, Menge1-5, Preis1-5, etc.
   - Expected: Art-Nr = join_key, quantity/price columns correctly identified

3. **Ambiguous CSV:**
   - Headers: F1, F2, F3, Desc, Val
   - Expected: Low confidence scores, requires user confirmation

**Acceptance Criteria:**
- Both real CSVs analyzed in <30 seconds total
- Artikelnummer/Art-Nr correctly identified as join-key in both
- No false confidence (if ambiguous, confidence <0.7)

---

## Research Confidence Summary

| Topic | Confidence | Basis |
|-------|-----------|-------|
| OpenAI Structured Outputs | HIGH | Official API feature, documented |
| Pydantic JSON Schema | HIGH | Official integration with OpenAI SDK |
| GPT-4o-mini vs GPT-4o | HIGH | Public pricing, capabilities documented |
| CSV Sampling Strategy | MEDIUM | Common practice, not official guidance |
| Confidence Calibration | MEDIUM | Pattern-based, needs validation |
| German CSV Terminology | HIGH | Domain knowledge, actual asset files |
| Cost Estimates | MEDIUM | Based on current pricing, subject to change |

---

## Next Steps for Planning

**Planner should create plans addressing:**

1. **Plan 01: OpenAI Integration Setup**
   - Add `openai` SDK to requirements.txt
   - Create Pydantic models for CSVAnalysisResult
   - Add OPENAI_API_KEY to config
   - Create OpenAI client dependency

2. **Plan 02: CSV Sampling Service**
   - Implement `sample_csv_for_llm()` function
   - Reuse Polars from Phase 1
   - Add intelligent sampling logic

3. **Plan 03: LLM Analysis Service**
   - Create `analyze_csv_structure()` function
   - Implement system prompt with German terminology
   - Add retry logic with exponential backoff
   - Join-key validation

4. **Plan 04: FastAPI Analysis Endpoint**
   - POST `/api/analyze/csv/{upload_id}`
   - Integrate with Phase 1 upload sessions
   - Return mapping results with confidence scores

5. **Plan 05: Tests**
   - Unit tests for sampling, validation
   - Integration tests for analysis endpoint
   - Manual verification with actual asset CSVs

**Wave structure suggestion:**
- Wave 1: Plan 01 (setup), Plan 02 (sampling)
- Wave 2: Plan 03 (analysis service)
- Wave 3: Plan 04 (API endpoint)
- Wave 4: Plan 05 (tests)

---

*Research complete. Ready for planning.*
