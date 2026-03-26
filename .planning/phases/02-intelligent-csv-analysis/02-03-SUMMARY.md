---
phase: 02-intelligent-csv-analysis
plan: 03
subsystem: api
tags: [anthropic, claude, llm, tool-use, german-nlp]

# Dependency graph  
requires:
  - phase: 02-01
    provides: Anthropic SDK, Pydantic models for Tool Use
  - phase: 02-02
    provides: CSV sampling function
provides:
  - Claude-based CSV column analysis function
  - Join-key validation (exactly 1 required)
  - Retry logic with exponential backoff
  - German product terminology system prompt
affects: [02-04-fastapi-endpoint, 02-05-tests]

# Tech tracking
tech-stack:
  added: []
  patterns: [Claude Tool Use for structured outputs, German domain prompting, Exponential backoff retry]

key-files:
  created:
    - backend/app/services/csv_analysis.py
  modified:
    - backend/app/services/__init__.py

key-decisions:
  - "Claude 3.5 Haiku as primary model for cost-effectiveness ($0.25/1M input)"
  - "Tool Use API for structured JSON (Pydantic schema → tool input_schema)"
  - "German product terminology glossary in system prompt (12 common fields)"
  - "Exponential backoff retry: 1s, 2s, 4s on rate limits"
  - "Join-key validation ensures exactly ONE column marked as identifier"
  - "Temperature=0.0 for deterministic, reproducible results"
  - "Fail-fast on non-retry errors (not rate limits/timeouts)"

patterns-established:
  - "Claude Tool Use: messages.create() with tools list containing Pydantic model_json_schema()"
  - "Extract tool_use block from response.content with type check"
  - "Conservative confidence guidance: 0.9-1.0 obvious, 0.7-0.9 suggested, <0.7 ask user"
  - "Self-built retry logic (no framework) with exponential backoff"

requirements-completed: [CSV-01]

# Metrics
duration: 6min
completed: 2026-03-26
---

# Phase 02-03: LLM CSV Analysis Service Summary

**Claude Tool Use integration for intelligent German CSV column detection with retry logic and join-key validation**

## Performance

- **Duration:** 6 min
- **Tasks:** 2
- **Files modified:** 1
- **Files created:** 1

## Accomplishments
- Core analysis function using Claude 3.5 Haiku with Tool Use API
- German product terminology system prompt (12 common field mappings)
- Join-key validation ensuring exactly ONE column marked as identifier
- Retry logic with exponential backoff (1s, 2s, 4s) for rate limits

## Task Commits

Each task was committed atomically:

1. **Task 1: Create LLM Analysis Service Core** - `5eefc37` (feat)
2. **Task 2: Export Analysis Service** - `e758d5d` (feat)

## Files Created/Modified
- `backend/app/services/csv_analysis.py` - Claude Tool Use integration with German terminology, retry logic, validation
- `backend/app/services/__init__.py` - Export analysis service functions

## Decisions Made
- **Claude Tool Use:** Pydantic model_json_schema() as tool input_schema - Claude validates against schema and returns structured data
- **System prompt terminology:** 12 common German product fields (Artikelnummer, Bezeichnung1/2, VE, Preis, etc.) guide column detection
- **Confidence calibration:** Explicit thresholds (0.9+ obvious, 0.7-0.9 suggested, <0.7 ask) prevent overconfident mappings  
- **Join-key validation:** Post-processing check ensures exactly 1 is_join_key=true - critical for data merging
- **Retry strategy:** 3 attempts, exponential backoff on RateLimitError/APITimeoutError - fail fast on other AnthropicErrors
- **Deterministic:** temperature=0.0 for consistent results across runs

## Deviations from Plan

None - plan executed exactly as written. All CONTEXT decisions (D-01: Anthropic API, D-02: Haiku model, D-09: Tool Use, D-20: join-key validation) followed.

## Issues Encountered

None - straightforward Claude API integration using patterns from RESEARCH.md.

## User Setup Required

**Anthropic API key required** (configured in Phase 02-01):
- Set `ANTHROPIC_API_KEY` in `backend/.env` before calling analysis functions
- Key from https://console.anthropic.com/

## Next Phase Readiness

**Ready for Wave 3 (Plan 02-04):**
- FastAPI endpoint can import `analyze_csv_structure()` and `get_anthropic_client()`
- Dependency injection pattern established for client

**Enables downstream plans:**
- 02-04: FastAPI endpoint orchestrates CSV sample → analyze → return mappings
- 02-05: Tests mock Anthropic API responses to verify analysis logic

---
*Phase: 02-intelligent-csv-analysis*
*Completed: 2026-03-26*
