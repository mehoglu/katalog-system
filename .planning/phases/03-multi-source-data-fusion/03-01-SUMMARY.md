---
phase: 03-multi-source-data-fusion
plan: 01
subsystem: api
tags: [polars, csv, merge, data-fusion, pydantic]

# Dependency graph
requires:
  - phase: 02-intelligent-csv-analysis
    provides: CSV delimiter detection, encoding handling, validation patterns
provides:
  - Merge service combining EDI Export + Preisliste CSVs via Artikel nummer
  - Field-specific conflict resolution (Preisliste for prices, EDI for master data)
  - Source tracking for every product field
  - MergedProduct and MergeResult Pydantic models
affects: [03-02-api-endpoint, 04-image-linking, 05-text-enhancement, 06-review-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [field-specific-priority-rules, source-tracking-dict, left-join-merge]

key-files:
  created: [backend/app/models/merge.py, backend/app/services/csv_merge.py, backend/tests/test_csv_merge.py, backend/app/models/__init__.py]
  modified: []

key-decisions:
  - "Use Polars left join with EDI as basis (preserves all EDI products)"
  - "Rename Preisliste columns before join to ensure _preisliste suffix"
  - "Field-specific priority: Preisliste wins for prices (preis, menge1-5), EDI wins for master data"
  - "Source tracking via parallel data/sources dicts per D-12 from CONTEXT"

patterns-established:
  - "Pattern 1: Source tracking - every product field has data value + source attribution (edi_export|preisliste|null)"
  - "Pattern 2: Field-specific conflict resolution - PREISLISTE_PRIORITY_FIELDS constant drives merge logic"
  - "Pattern 3: Column normalization - lowercase all columns before merge for case-insensitive matching"

requirements-completed: [FUSION-01, FUSION-02, FUSION-03]

# Metrics
duration: 45min
completed: 2026-03-26
---

# Phase 3 Plan 01: CSV Merge Service — Complete

**Polars-based merge service combines product data from EDI Export and Preisliste CSVs with field-specific conflict resolution and complete source tracking.**

## Performance

- **Duration:** 45 minutes
- **Started:** 2026-03-26T15:15:00Z
- **Completed:** 2026-03-26T16:00:00Z
- **Tasks:** 3 completed
- **Files modified:** 4 created

## Accomplishments
- Created MergedProduct and MergeResult Pydantic models with source tracking structure (D-12 compliance)
- Implemented merge_csv_data() with Polars left join preserving all 464 EDI products
- Field-specific priority rules: Preisliste wins for price fields (preis, menge1-5), EDI for master data
- Complete source tracking - every field shows which CSV it came from (or null if missing)
- 7 unit tests validating FUSION requirements (merge, conflicts, nulls, source tracking)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Merge Data Models** - `4b5fd40` (feat)
2. **Task 2-3: Implement CSV Merge Logic + Unit Tests** - `58af5f2` (feat)

## Files Created/Modified
- `backend/app/models/merge.py` - MergedProduct and MergeResult Pydantic models with source tracking
- `backend/app/services/csv_merge.py` - merge_csv_data() function using Polars left join
- `backend/tests/test_csv_merge.py` - 7 unit tests covering merge, conflicts, nulls, source tracking
- `backend/app/models/__init__.py` - Export new merge models

## Decisions Made

**D-01 Implementation:** Used Polars left join on artikelnummer with EDI as basis. This guarantees all 464 EDI products appear in output even if they have no price data.

**Column Renaming Strategy:** Renamed Preisliste columns with `_preisliste` suffix BEFORE join. This solved Polars join behavior where columns existing only in right table weren't getting suffixed.

**Priority Fields Constant:** Created `PREISLISTE_PRIORITY_FIELDS` set containing the 6 price fields (preis, menge1-5) per D-05 from CONTEXT. Centralized logic makes priority rules explicit and maintainable.

**Matched Count Logic:** Detect matched products by checking for ANY non-null `_preisliste` field in the joined result. More robust than checking specific fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Polars column normalization creating duplicate columns**
- **Found during:** Task 2 (Implement CSV Merge Logic)
- **Issue:** Using `df.with_columns([pl.col(col).alias(col.lower())])` added lowercase columns but kept originals, causing merge confusion
- **Fix:** Changed to direct column assignment: `df.columns = [col.lower() for col in df.columns]` to replace names instead of duplicating
- **Files modified:** backend/app/services/csv_merge.py
- **Verification:** pytest tests/test_csv_merge.py passed
- **Committed in:** 58af5f2 (part of task commit)

**2. [Rule 1 - Bug] Polars join not adding suffix to right-table-only columns**
- **Found during:** Task 2 (Implement CSV Merge Logic)
- **Issue:** When columns exist only in right table (Preisliste), Polars left join doesn't add the suffix parameter - columns appear without suffix
- **Fix:** Renamed Preisliste columns to add `_preisliste` suffix BEFORE join using `df.rename()`, ensuring all Preisliste fields are distinguishable
- **Files modified:** backend/app/services/csv_merge.py
- **Verification:** pytest tests/test_csv_merge.py::test_field_priority passed
- **Committed in:** 58af5f2 (part of task commit)

## Next Phase Readiness

**Ready for Phase 3 Plan 02 (FastAPI Endpoint + Storage):**
- ✓ merge_csv_data() function available for import
- ✓ MergeResult model provides structured response
- ✓ Source tracking format matches D-16 (merged_products.json structure)
- ✓ All FUSION requirements validated through unit tests

**Phase 4 (Image Linking) Prerequisites:**
- merged_products.json will contain artikelnummer for image matching
- Source tracking preserved for Review UI (Phase 6 requirement REVIEW-04)

## Verification Status

All must-haves from PLAN.md verified:
- ✓ System reads both CSV files with detected column mappings (delimiter detection reused)
- ✓ Products from EDI Export joined with Preisliste via Artikelnummer (left join)
- ✓ Conflicts resolved with field-specific rules (tests validate D-05, D-06)
- ✓ Missing data represented as null values (D-09, D-10 compliance)
- ✓ Source tracking shows which CSV each field came from (D-12, D-14 compliance)

All key-links verified:
- ✓ csv_merge.py imports detect_delimiter from csv_sampling.py
- ✓ Polars DataFrame operations (pl.read_csv) functioning
- ✓ MergedProduct model instantiation working

## Test Coverage

7 unit tests covering:
- Basic merge functionality (FUSION-01)
- Field-specific conflict resolution (FUSION-02, D-05, D-06)
- Missing price handling (FUSION-03, D-03, D-09)
- Source tracking completeness (D-12, D-14)
- Left join preservation (D-01, D-02)
- MergeResult structure (FUSION-04)
- Null value handling (D-09, D-10)

All tests pass in < 0.1 seconds via Docker container.
