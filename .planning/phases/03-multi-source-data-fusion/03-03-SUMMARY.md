---
phase: 03-multi-source-data-fusion
plan: 03
subsystem: testing
tags: [pytest, integration-tests, fastapi-testclient]

# Dependency graph
requires:
  - phase: 03-01
    provides: merge_csv_data service
  - phase: 03-02
    provides: POST /api/merge/csv endpoint
provides:
  - Integration test suite for merge endpoint
  - API contract validation
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [fastapi-testclient-integration-tests, monkeypatch-settings-mocking]

key-files:
  created: [backend/tests/test_merge_endpoint.py]
  modified: []

key-decisions:
  - "Mock settings.upload_dir with monkeypatch for test isolation"
  - "Use TestClient for synchronous API testing"
  - "Construct absolute paths from mocked upload_dir for file verification"

patterns-established:
  - "Pattern 1: Integration test fixtures - create realistic test CSVs with proper delimiters and edge cases"
  - "Pattern 2: Settings mocking - use monkeypatch to redirect upload_dir to tmp_path"
  - "Pattern 3: Path resolution - construct absolute paths from settings for file assertions"

requirements-completed: []

# Metrics
duration: 10min
completed: 2026-03-26
---

# Phase 3 Plan 03: Integration Tests — Complete

**FastAPI TestClient-based integration tests validate full merge workflow from API call to JSON file creation.**

## Performance

- **Duration:** 10 minutes
- **Started:** 2026-03-26T16:15:00Z
- **Completed:** 2026-03-26T16:25:00Z
- **Tasks:** 2 completed
- **Files modified:** 1 created

## Accomplishments
- Created 4 integration tests covering full API workflow
- Tested successful merge with matched and unmatched products
- Validated error handling for invalid upload IDs
- Verified field-specific conflict resolution via API
- Confirmed source tracking accuracy in JSON output
- All tests pass in < 0.1 seconds

## Task Commits

Both tasks committed together:

1. **Tasks 1-2: Create Integration Test Fixtures + Tests** - `5070509` (test)

## Files Created/Modified
- `backend/tests/test_merge_endpoint.py` - 4 integration tests for merge endpoint

## Decisions Made

**Path Resolution Strategy:** Initially used `Path(response["merge_file"])` which failed because the HTTP response returns a relative path. Fixed by constructing absolute paths from `settings.upload_dir` which was mocked via monkeypatch.

**Settings Mocking:** Used pytest monkeypatch to override `settings.upload_dir` instead of environment variables. More direct and reliable for test isolation.

**Test Data:** Reused same test CSV fixtures as unit tests (test_csv_merge.py) for consistency. Same 3 EDI products, 2 Preisliste matches, validates same scenarios at API level.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Incorrect path resolution in tests**
- **Found during:** Task 2 (Test Successful Merge Flow)
- **Issue:** Tests used `Path(response["merge_file"])` which treated relative API response path as absolute, causing FileNotFoundError
- **Fix:** Changed to `settings.upload_dir / mock_uploads["edi_id"] / "merged_products.json"` to construct absolute path from mocked settings
- **Files modified:** backend/tests/test_merge_endpoint.py
- **Verification:** pytest tests/test_merge_endpoint.py passed (4/4 green)
- **Committed in:** 5070509 (included with test file)

## Next Phase Readiness

**Phase 3 Complete - Ready for Phase 4 (Image Linking):**
- ✓ Full merge workflow validated end-to-end
- ✓ JSON file format verified (data + sources structure)
- ✓ merged_products.json persisted in upload directory
- ✓ Source tracking accurate for Review UI (Phase 6)

**Phase 5 (Text Enhancement) Prerequisites:**
- ✓ Merged product data accessible via JSON
- ✓ Text fields (bezeichnung1, bezeichnung2) readable

## Verification Status

All must-haves from PLAN.md verified:
- ✓ Integration tests validate full merge flow via API (Test Client calls endpoint)
- ✓ Edge cases tested (missing uploads via test_merge_invalid_upload_id)
- ✓ JSON output structure validated (test_merge_endpoint_success checks structure)
- ✓ Source tracking accuracy verified (test_source_tracking_accuracy)

All key-links verified:
- ✓ test_merge_endpoint.py uses TestClient from fastapi.testclient

## Test Coverage

4 integration tests:
1. **test_merge_endpoint_success**: Happy path with matched/unmatched products
2. **test_merge_invalid_upload_id**: 404 error handling
3. **test_conflict_resolution_priority**: Field-specific rules (D-05, D-06)
4. **test_source_tracking_accuracy**: Source attribution completeness (D-14)

Coverage: API contract, JSON persistence, error handling, merge logic via HTTP.
