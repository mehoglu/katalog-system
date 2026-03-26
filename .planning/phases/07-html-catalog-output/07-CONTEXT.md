# Phase 07: Professional HTML Catalog Output - Context

**Gathered:** 26. März 2026
**Status:** Ready for planning
**Source:** Fast-track to completion

## Phase Boundary

Generate print-ready HTML catalogs from corrected product data. Create individual product pages and a master catalog index. Design for A4 print format (210×297mm) with modern, professional styling.

## What We're Building

### Individual Product Pages
- One HTML file per product (464 files)
- Product name, description (original + enhanced), images
- Dimensions, weight, price
- Professional layout optimized for A4 print
- File naming: `{artikelnummer}.html`

### Master Catalog Index
- Single HTML file listing all products
- Sortable/searchable product list
- Links to individual product pages
- Overview statistics
- Print-optimized layout

### HTML Catalog Generator API
- POST /api/catalog/generate endpoint
- Reads merged_products.json
- Generates HTML files in output directory
- Returns generation statistics

## Implementation Decisions

### Design (Locked)
- A4 format: 210×297mm (CSS @page)
- Modern, clean typography
- Good contrast for readability
- Professional product layout
- Images prominently displayed
- Print-friendly (no backgrounds, clean borders)

### Backend (Locked)
- FastAPI endpoint for generation
- Jinja2 templates for HTML rendering
- Write to `uploads/{upload_id}/catalog/` directory
- Return ZIP file for download (optional)

### Templates (Locked)
- `product_template.html` - Individual product page
- `index_template.html` - Master catalog index
- CSS embedded in HTML for portability

### the agent's Discretion
- Exact layout and spacing
- Color scheme (keep professional, print-friendly)
- Section ordering within product page
- Index sorting/grouping strategy

## Canonical References

**Must read before planning:**
- `backend/app/models/merge.py` - MergedProduct structure
- `backend/app/api/review.py` - Pattern for reading merged_products.json
- Prior phase SUMMARYs for data structure

## Specific Ideas

- Use CSS Grid for product page layout
- Display images in gallery format
- Show enhanced text prominently (if available)
- Include generation timestamp
- Highlight source of each field (optional)
- Make catalog self-contained (all CSS inline)

## Deferred Ideas

- PDF generation (use browser print-to-PDF for v1)
- Custom branding/logo
- Interactive JavaScript features
- Multi-language support
- Batch ZIP download of all catalogs

These are v2 enhancements - not needed for v1.

---

*Phase: 07-html-catalog-output*
*Context gathered: 26. März 2026*
