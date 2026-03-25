# Phase 1 Research: Backend Foundation & Data Import

**Phase:** 01 - Backend Foundation & Data Import
**Researched:** 25. März 2026
**Confidence:** HIGH (foundation patterns well-established)

## Executive Summary

Phase 1 establishes upload infrastructure for CSV files and images with robust encoding handling and validation. This foundation phase addresses **Critical Pitfall #3** (German encoding corruption) and sets up cost tracking, state persistence, and validation patterns that all subsequent LLM-based phases depend on.

The phase uses **FastAPI** for async file handling, **charset-normalizer** for encoding detection (2026 standard, faster than chardet), **Polars** for CSV validation (10-100x faster than pandas for 500+ products), and **React + TypeScript** for the upload UI with drag-and-drop. No LLM integration yet — keeps Phase 1 deterministic and fast.

**Key Decision:** User chose **warning-based validation** (non-blocking) with corrections deferred to Phase 6 table interface. This enables fast iteration — upload → see warnings → proceed to merge/enhancement → fix data in table later if needed.

## Research Questions Answered

### Q1: How to reliably detect and handle German character encoding?

**Answer:** Server-side detection with `charset-normalizer` (Python) + Windows-1252 fallback.

**Why charset-normalizer over chardet:**
- 10-100x faster than chardet (written in Rust-backed normalizer)
- Better accuracy on German text (tuned for European encodings)
- Active maintenance (chardet development stagnant since 2020)
- Drop-in replacement with same API

**Detection strategy:**
```python
from charset_normalizer import from_bytes

# Read raw bytes
with open(csv_path, 'rb') as f:
    raw_data = f.read()

# Detect encoding with confidence threshold
results = from_bytes(raw_data)
best_match = results.best()

if best_match and best_match.encoding_confidence > 0.7:
    detected_encoding = best_match.encoding
else:
    # Fallback to Windows-1252 (German Excel default)
    detected_encoding = "windows-1252"

# Decode with detected encoding
text = raw_data.decode(detected_encoding, errors='replace')
```

**User decision (from CONTEXT.md D-19):** Show encoding confirmation dialog — don't auto-fix silently. Gives control when detection uncertain.

**Validation:** Check for German umlauts (ä,ö,ü,ß) in sample to confirm correct decoding. If umlauts appear as mojibake (MÃ¼), encoding detection failed.

**Research sources:**
- charset-normalizer docs: https://github.com/Ousret/charset_normalizer
- Python CSV encoding guide: https://peps.python.org/pep-0597/

### Q2: What validation should run in Phase 1 vs deferred to Phase 2+?

**Answer:** Phase 1 validates **structure and integrity**, Phase 2+ validates **semantics**.

**Phase 1 validation (this phase):**
- CSV is parsable (valid CSV syntax, not corrupted)
- File encoding detected and converted correctly
- Basic structure present (has rows, has columns)
- No duplicate article numbers within a single CSV
- Required file types correct (CSVs are CSVs, images are images)

**Deferred to Phase 2:**
- Column semantics (which column is Artikelnummer vs Preis)
- Article number format validation (D80950 pattern)
- Cross-CSV duplicate detection
- Data completeness (missing prices, descriptions)

**User decision (from CONTEXT.md D-10, D-11):** Non-blocking warnings with extended validation. Validation shows issues but doesn't stop workflow — user proceeds to merge/enhancement, fixes data in Phase 6 table interface.

**Early-exit strategy (from CONTEXT.md D-12):** Validation stops at first critical error for fast feedback, but continues through warnings.

### Q3: How to handle multi-file uploads (CSVs + image folders)?

**Answer:** Two-step upload workflow with FastAPI streaming + background tasks.

**Step 1: CSV Upload**
```python
from fastapi import UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
import polars as pl

@app.post("/api/upload/csv")
async def upload_csv(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Create timestamped upload session
    upload_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    upload_dir = Path(f"uploads/{upload_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Stream file to disk (avoids loading full CSV into memory)
    csv_path = upload_dir / file.filename
    async with open(csv_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            await f.write(chunk)
    
    # Background: validate encoding + structure
    background_tasks.add_task(validate_csv, csv_path)
    
    return {"upload_id": upload_id, "filename": file.filename}
```

**Step 2: Image Folder Upload**
```python
@app.post("/api/upload/images/{upload_id}")
async def upload_images(
    upload_id: str,
    files: list[UploadFile]
):
    upload_dir = Path(f"uploads/{upload_id}")
    images_dir = upload_dir / "bilder"
    images_dir.mkdir(exist_ok=True)
    
    # Stream images in parallel (FastAPI handles concurrency)
    for image in files:
        image_path = images_dir / image.filename
        async with open(image_path, 'wb') as f:
            while chunk := await image.read(16384):  # 16KB chunks
                await f.write(chunk)
    
    return {"count": len(files), "path": str(images_dir)}
```

**User decision (from CONTEXT.md D-06):** Separate upload steps (CSVs first, then images) for clearer error handling per file type.

**Progress tracking:** WebSocket or SSE (Server-Sent Events) for real-time progress:
```python
from fastapi import WebSocket

@app.websocket("/ws/upload/{upload_id}")
async def upload_progress(websocket: WebSocket, upload_id: str):
    await websocket.accept()
    # Send progress updates as files process
    await websocket.send_json({"status": "processing", "progress": 0.5})
```

**User decision (from CONTEXT.md D-07, D-08):** Detailed progress (filename, size, time) + cancellation support.

### Q4: How to structure validation errors for line-specific feedback?

**Answer:** Structured error objects with Pydantic + line number tracking.

**Error schema:**
```python
from pydantic import BaseModel
from enum import Enum

class ErrorSeverity(str, Enum):
    CRITICAL = "critical"  # Blocks processing
    WARNING = "warning"    # Can proceed
    INFO = "info"          # FYI only

class ValidationError(BaseModel):
    severity: ErrorSeverity
    file: str
    line: int | None  # None for file-level errors
    column: str | None
    message: str
    suggestion: str | None  # Actionable fix
    
class ValidationResult(BaseModel):
    upload_id: str
    file: str
    status: str  # "valid", "warnings", "errors"
    errors: list[ValidationError]
    stats: dict  # rows, columns, encoding detected
```

**Example validation implementation:**
```python
import polars as pl

def validate_csv_structure(csv_path: Path) -> ValidationResult:
    errors = []
    
    try:
        # Polars lazy read (doesn't load full CSV into memory)
        df = pl.scan_csv(csv_path, encoding="utf-8-lossy")
        
        # Check for empty file
        row_count = df.select(pl.count()).collect().item()
        if row_count == 0:
            errors.append(ValidationError(
                severity=ErrorSeverity.CRITICAL,
                file=csv_path.name,
                line=None,
                column=None,
                message="CSV file is empty",
                suggestion="Upload a file with product data"
            ))
            return ValidationResult(errors=errors, status="errors")
        
        # Check for duplicate article numbers (limited scan)
        # Only check first occurrence for early-exit
        df_checked = df.select("Artikelnummer").head(500).collect()
        duplicates = df_checked.filter(pl.col("Artikelnummer").is_duplicated())
        
        if len(duplicates) > 0:
            first_dup = duplicates.row(0)[0]
            errors.append(ValidationError(
                severity=ErrorSeverity.WARNING,
                file=csv_path.name,
                line=None,  # Line tracking requires full scan
                column="Artikelnummer",
                message=f"Duplicate article number found: {first_dup}",
                suggestion="Review in table interface (Phase 6)"
            ))
        
        return ValidationResult(
            errors=errors,
            status="warnings" if errors else "valid",
            stats={"rows": row_count, "columns": len(df.columns)}
        )
        
    except Exception as e:
        errors.append(ValidationError(
            severity=ErrorSeverity.CRITICAL,
            file=csv_path.name,
            line=None,
            column=None,
            message=f"CSV parsing failed: {str(e)}",
            suggestion="Check file encoding and format"
        ))
        return ValidationResult(errors=errors, status="errors")
```

**User decisions (from CONTEXT.md):**
- D-13: Combined layout (inline indicators + detail panel)
- D-14: Line-specific errors when possible
- D-15: Dedicated error panel (persistent, scrollable)
- D-16: Action buttons per error (Upload neu, Ignorieren, Bearbeiten)

### Q5: What frontend patterns for drag-and-drop with detailed progress?

**Answer:** React + react-dropzone + TanStack Query for state management.

**Component stack:**
```
UploadPage
├── CSVUploadZone (react-dropzone)
│   ├── DropzoneArea (drag target)
│   ├── FileList (uploaded files)
│   └── ValidationPanel (errors/warnings)
├── ImageUploadZone (react-dropzone)
│   ├── DropzoneArea
│   ├── FolderPreview (image count)
│   └── ProgressBar (detailed)
└── ErrorPanel (shared, scrollable)
```

**Drag-and-drop implementation:**
```typescript
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';

interface UploadProgress {
  filename: string;
  bytesUploaded: number;
  totalBytes: number;
  percentage: number;
  estimatedTimeRemaining: number;
}

function CSVUploadZone() {
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/upload/csv', {
        method: 'POST',
        body: formData,
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentage = (progressEvent.loaded / progressEvent.total) * 100;
            const bytesRemaining = progressEvent.total - progressEvent.loaded;
            const bytesPerSecond = progressEvent.loaded / progressEvent.timeStamp;
            const estimatedTimeRemaining = bytesRemaining / bytesPerSecond;
            
            setProgress({
              filename: file.name,
              bytesUploaded: progressEvent.loaded,
              totalBytes: progressEvent.total,
              percentage,
              estimatedTimeRemaining
            });
          }
        }
      });
      
      return response.json();
    }
  });
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 2,  // EDI Export + Preisliste
    onDrop: (acceptedFiles) => {
      acceptedFiles.forEach(file => uploadMutation.mutate(file));
    }
  });
  
  return (
    <div {...getRootProps()} className={isDragActive ? 'drag-active' : ''}>
      <input {...getInputProps()} />
      {progress && (
        <ProgressBar
          filename={progress.filename}
          percentage={progress.percentage}
          timeRemaining={progress.estimatedTimeRemaining}
        />
      )}
    </div>
  );
}
```

**User decision (from CONTEXT.md D-05, D-07, D-08):**
- Drag-and-drop interface
- Detailed progress (filename, size, time)
- Cancellation button (AbortController)

**Libraries:**
- `react-dropzone` (27k stars, drag-drop standard)
- `@tanstack/react-query` (state management for uploads)
- `axios` or native `fetch` with AbortController for cancellation

## Recommended Stack (Phase 1 Specific)

### Backend
- **FastAPI 0.110+** — Async file uploads, streaming responses, automatic OpenAPI docs
- **Polars 0.20+** — Fast CSV validation (10-100x faster than pandas), lazy evaluation
- **charset-normalizer 3.3+** — Encoding detection (faster than chardet)
- **Pydantic 2.5+** — Validation error schemas, type safety
- **pytest + pytest-asyncio** — Testing async upload endpoints

### Frontend
- **React 18.2+** — Component architecture
- **TypeScript 5.3+** — Type safety
- **react-dropzone 14.2+** — Drag-and-drop uploads
- **@tanstack/react-query 5.17+** — Upload state management
- **shadcn/ui** or **Chakra UI** — Error panel, progress bars, action buttons
- **Tailwind CSS 3.4+** — Styling

### Infrastructure
- **Docker + Docker Compose** — Local development environment
- **Caddy or Nginx** — Static file serving for images
- **SQLite (optional)** — Persist upload session metadata (if needed)

## Critical Implementation Notes

### 1. Encoding Detection Flow

```
1. User uploads CSV
2. Backend reads raw bytes
3. charset-normalizer analyzes (< 100ms)
4. If confidence > 70%: use detected encoding
5. If confidence < 70%: show confirmation dialog with detected + fallback options
6. User confirms or selects override
7. Decode CSV with chosen encoding
8. Validate umlauts in first 10 rows
9. If mojibake detected: flag error, request re-upload or manual encoding selection
```

**User decision (from CONTEXT.md D-17, D-18, D-19, D-20):** Server-side detection, charset-normalizer, user confirmation, Windows-1252 fallback.

### 2. File Storage Structure

```
uploads/
├── 2026-03-25_143022/          # Timestamped session (CONTEXT D-03)
│   ├── EDI_Export.csv          # Original files
│   ├── Preisliste.csv
│   ├── bilder/                 # Image folder
│   │   ├── D80950.jpg
│   │   └── D80951.png
│   └── metadata.json           # Session info (encoding, validation status)
└── 2026-03-25_150533/          # Next session
```

**User decisions (from CONTEXT.md):**
- D-01: Temporary storage (deleted after catalog generation)
- D-02: Local filesystem
- D-03: Timestamped folders per upload
- D-04: Manual deletion (no auto-cleanup)

### 3. Validation Error UI

**Inline indicator + detail panel (CONTEXT D-13):**

```
┌─────────────────────────────────────────┐
│ CSV Files Uploaded                      │
│ ┌─────────────────────────────────────┐ │
│ │ ✓ EDI_Export.csv (2.3 MB)          │ │
│ │ ⚠ Preisliste.csv (856 KB)          │ │  <- Inline warning indicator
│ └─────────────────────────────────────┘ │
│                                         │
│ ⚠ Validation Warnings (2)              │  <- Detail panel
│ ┌─────────────────────────────────────┐ │
│ │ Preisliste.csv, Line 42:            │ │  <- Line-specific (D-14)
│ │ Duplicate article number: D80950    │ │
│ │ Suggestion: Review in table         │ │
│ │ [Upload New] [Ignore] [Edit]        │ │  <- Action buttons (D-16)
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 4. Performance Targets

- **Upload 2 CSVs (5 MB total):** < 2 seconds
- **Encoding detection:** < 100ms per file
- **Structure validation:** < 1 second (Polars lazy evaluation)
- **Image folder upload (200 images, 50 MB):** < 10 seconds
- **UI responsive:** Progress updates every 100ms

## Known Limitations & Trade-offs

### Limitations
1. **No streaming validation** — Validation runs after full file upload (not during). Acceptable for CSV files < 10 MB.
2. **Line number tracking requires full scan** — Early-exit validation (D-12) means some errors won't have line numbers. Trade-off for speed.
3. **Windows-1252 fallback may be wrong** — If CSV is Latin-1 or ISO-8859-1, umlauts will still corrupt. User confirmation dialog catches this.

### Trade-offs
1. **Non-blocking warnings vs fail-fast** — User chose warnings (D-10). Pro: Fast iteration. Con: Bad data proceeds to merge. Mitigated by Phase 6 table corrections.
2. **Temporary storage vs persistent** — User chose temporary (D-01). Pro: Saves disk space. Con: Can't re-generate catalog from originals. User accepted trade-off.
3. **Manual cleanup vs auto-delete** — User chose manual (D-04). Pro: User control. Con: Disk can fill if user forgets. Document in UI.

## Dependencies & Blockers

### No blockers
Phase 1 has no dependencies (foundation phase).

### Provides to downstream phases
- Upload session structure (timestamped folders)
- Validated, UTF-8 normalized CSV files
- Image file references
- Encoding detection patterns
- Validation error schemas

**Phase 2 (CSV Analysis) depends on:**
- Clean UTF-8 CSV text from Phase 1
- Article number column identified

**Phase 3 (Data Fusion) depends on:**
- Both CSVs uploaded and validated from Phase 1

## Testing Strategy

### Unit Tests
- Encoding detection (Windows-1252, UTF-8, Latin-1 edge cases)
- CSV parsing (valid, empty, malformed)
- Validation rules (duplicates, empty rows)
- Error object construction

### Integration Tests
- Full upload flow (CSV + images)
- Multi-file upload (2 CSVs)
- Large file handling (10 MB CSV)
- WebSocket progress tracking
- Cancellation mid-upload

### Manual Tests
- German umlauts display correctly (ä→ä, not ÃŤ)
- Drag-and-drop UI works in Chrome, Firefox, Safari
- Error panel scrolls with 10+ errors
- Action buttons trigger correct flows

## Open Questions (None)

All research questions answered with high confidence. Phase 1 uses well-established patterns.

---

## RESEARCH COMPLETE

**Confidence:** HIGH
**Blockers:** None
**Ready for planning:** Yes

Phase 1 addresses Critical Pitfall #3 (encoding) and sets up foundation for all LLM-based phases. User decisions from CONTEXT.md fully integrated into recommendations above.
