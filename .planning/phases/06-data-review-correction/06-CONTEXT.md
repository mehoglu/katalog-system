# Phase 06: Data Review & Correction - Context

**Gathered:** 26. März 2026
**Status:** Ready for planning
**Source:** Fast-track to completion

## Phase Boundary

Build a review UI (table interface) where users can see all products with all mapped data, edit any cell inline, identify data sources, and save corrections. This is the quality control gate before final catalog generation.

## What We're Building

### Data Review Table
- Display all 464 products in an editable table
- Show all fields: Artikelnummer, Bezeichnung1, Bezeichnung2, dimensions, price, images, etc.
- Display both original and enhanced text fields
- Show which CSV each value came from (source tracking)
- Client-side filtering and sorting

### Inline Editing
- Click any cell to edit
- Save changes immediately to backend
- Update merged_products.json
- No page reload required

### Source Traceability
- Display data provenance (EDI Export vs Preisliste)
- Highlight enhanced fields (from LLM Phase 5)
- Show image match status (from Phase 4)

### Catalog Trigger
- Button to regenerate catalog with corrected data
- Routes to Phase 7 (HTML Catalog Output)

## Implementation Decisions

### Backend API (Locked)
- GET /api/review/{upload_id} — Returns all products with sources
- PATCH /api/review/{upload_id}/product/{artikelnummer} — Update single field
- Backend reads from merged_products.json (Phase 3 output)
- Preserves Phase 3 wrapper structure with sources

### Frontend UI (Locked)
- HTML/JS table with editable cells
- Use existing simple stack (no React/Vue - keep it simple)
- Responsive table (horizontal scroll if needed)
- Filter/sort with vanilla JS
- Save on blur for edited cells

### Data Model (Locked)
- Use existing merged_products.json structure
- Sources object shows provenance per field
- Enhanced fields have _enhanced suffix (e.g., bezeichnung1_enhanced)
- Image paths from Phase 4 image_linking

### the agent's Discretion
- Table styling (use modern CSS, clean design)
- Edit UI pattern (contenteditable, input field, etc.)
- Error handling for failed saves
- Loading states

## Canonical References

**Must read before planning:**
- `backend/app/models/merge.py` — MergedProduct structure
- `backend/app/models/text_enhancement.py` — Enhanced text model
- `backend/app/models/image_linking.py` — Image linking model
- `backend/app/api/merge.py` — Existing merge endpoint pattern
- Prior phase SUMMARYs for data structure understanding

## Specific Ideas

- Table should be wide - horizontal scroll acceptable
- Show image thumbnails in table
- Highlight edited cells (visual feedback)
- Auto-save on blur (don't need explicit save button per row)
- Consider pagination if 464 rows is too much (optional)

## Deferred Ideas

- Batch edit operations (select multiple, edit all)
- Export to Excel
- Undo/redo
- Real-time collaboration (multi-user editing)
- Advanced filtering (date ranges, regex)

These are v2 features - not needed for v1 catalog generation.

---

*Phase: 06-data-review-correction*
*Context gathered: 26. März 2026*
