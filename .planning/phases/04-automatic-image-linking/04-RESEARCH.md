# Phase 4: Automatic Image Linking - Research

**Created:** 2026-03-26  
**Phase:** 04-automatic-image-linking  
**Purpose:** Research how to implement automatic image matching and linking to products

---

## User Constraints

**No CONTEXT.md exists for this phase.** All implementation decisions are at the agent's discretion, guided by requirements IMAGE-01 through IMAGE-04 and project conventions from Phases 1-3.

## Standard Stack

**Core Libraries (Already in Project):**
- **Python 3.11+** - Runtime
- **Pydantic 2.6+** - Data modeling and validation
- **FastAPI 0.110.0** - REST API framework
- **Pathlib** - File path operations (built-in)

**No new dependencies required.** Image linking is pure data mapping - read JSON, match by artikelnummer, write enhanced JSON.

**Confidence:** HIGH (all libraries already integrated in Phases 1-3)

## Architecture Patterns

### Pattern 1: Service Layer for Image Matching

Follow Phase 3 pattern: `backend/app/services/image_linking.py`

```python
def link_images_to_products(
    merged_products_path: Path,
    image_mapping_path: Path
) -> ImageLinkResult:
    """
    Match images from manual_image_mapping.json to products in merged_products.json.
    
    Algorithm:
    1. Load merged_products.json (array of MergedProduct)
    2. Load manual_image_mapping.json (dict mapping artikelnummer -> images)
    3. For each product, lookup images by artikelnummer (case-insensitive)
    4. Add images array to product.data
    5. Add 'image_mapping' to product.sources for image fields
    6. Save enhanced merged_products.json
    7. Return statistics (total products, with images, without images)
    """
```

**Confidence:** HIGH (matches existing service patterns from csv_merge.py, csv_sampling.py)

### Pattern 2: Extend MergedProduct Model

Add images field to product data dictionary:

```python
# In product.data after image linking:
{
    "artikelnummer": "210100125",
    "data": {
        ...existing fields...,
        "images": [
            {
                "filename": "210100125A.jpg",
                "suffix": "A",
                "path": "assets/bilder/210100125A.jpg",
                "type": "front"
            },
            {
                "filename": "210100125AA.jpg",
                "suffix": "AA",
                "path": "assets/bilder/210100125AA.jpg",
                "type": "detail"
            }
        ]
    },
    "sources": {
        ...existing sources...,
        "images": "image_mapping"  # New source type
    }
}
```

**DO NOT modify MergedProduct Pydantic class** - `data` is `Dict[str, Any]` so it already supports images array.

**Confidence:** HIGH (aligns with Phase 3 D-12 source tracking pattern)

### Pattern 3: Case-Insensitive Artikelnummer Matching (IMAGE-03)

```python
# Create case-insensitive lookup index
image_index = {
    artikelnummer.lower(): images 
    for artikelnummer, images in manual_mapping["mappings"].items()
}

# Match during iteration
for product in merged_products:
    product_id = product["artikelnummer"].lower()
    matched_images = image_index.get(product_id, [])
```

**Why:** Requirement IMAGE-03 demands fuzzy matching. Case sensitivity in filenames was flagged in Phase 2 manual analysis.

**Confidence:** HIGH (standard Python dict pattern)

### Pattern 4: Multiple Images Per Product (IMAGE-02)

**Priority order for image display (recommended):**
1. Main (no suffix) - primary product image
2. A (front) - front view
3. AA (detail) - detail view
4. E (single) - isolated product
5. G (group) - group shot

Store images as ordered array preserving manual_image_mapping.json structure. Let Phase 7 (HTML generation) or Phase 6 (Review UI) decide display priority.

**Confidence:** HIGH (array structure supports multiple images naturally)

### Pattern 5: Empty Images Array for Missing Matches (IMAGE-04)

```python
matched_images = image_index.get(product_id, [])
product.data["images"] = matched_images  # Empty [] if no match
```

**Never omit the images field** - always include it (even as empty array).  
Phase 7 HTML generator can check `if product.data.get("images")` and render placeholder.

**Confidence:** HIGH (explicit empty array better than missing field)

## Don't Hand-Roll

### ❌ Don't: Image File Discovery/Scanning

**Manual image mapping already complete in Phase 2.**  
File: `.planning/manual_image_mapping.json`

Contains:
- 545 products with images
- 954 total images
- Complete path, suffix, type metadata

**Use this file directly.** Do NOT re-scan `assets/bilder/` directory.

**Reason:** Manual analysis captured naming patterns, handled edge cases, documented image types. Re-scanning would duplicate work and risk missing manual corrections.

**Confidence:** HIGH (manual mapping is canonical source)

### ❌ Don't: Image Validation/Existence Checking

**Assume image files exist if in manual_image_mapping.json.**

Phase 2 created mapping from actual filesystem scan. If files were moved/deleted since then, Phase 6 (Review UI) will surface the issue during user verification.

**Don't add file existence checks in Phase 4** - slows processing, adds I/O, doesn't prevent issues (files could be deleted after check).

**Confidence:** MEDIUM (tradeoff: performance vs validation)

### ❌ Don't: Image Format Conversion or Processing

**Phase 4 is pure linking (metadata only).**

Store paths/filenames exactly as they appear in manual_image_mapping.json:
- Keep `.jpg`, `.tif`, `.png` extensions as-is
- Keep relative paths (`assets/bilder/...`)
- No resizing, format conversion, thumbnail generation

Phase 7 (HTML generation) handles image rendering.

**Confidence:** HIGH (out of scope for Phase 4 requirements)

## Common Pitfalls

### Pitfall 1: Mismatch Between CSV Products and Image Mappings

**Problem:** 464 products in EDI CSV vs 545 products with images in manual mapping.

**Why:** Image folder contains products not in the current EDI Export CSV.

**Impact COUNT 9:**  
- **Affects requirement:** IMAGE-01 ✓  
- **Symptom:** Some mappings unused, some products missing images  
- **Detection:** Count `len(products_with_images)` vs `len(products_in_csv)`  
- **Validation:** Check both counts in ImageLinkResult  
- **If occurs:** Normal - not all products have images, not all images map to CSV products  
- **User action:** Phase 6 Review UI shows which products lack images  
- **Agent Prevention:** Return statistics showing matched vs unmatched on both sides  
- **Test:** Unit test with products missing from mapping, images without matching product  
- **How validated:** Integration test verifies counts match expected (test_image_linking.py)

**Solution:** Accept this mismatch as expected. Return statistics:
```python
class ImageLinkResult:
    total_products: int
    products_with_images: int
    products_without_images: int
    unused_image_mappings: int  # Images in mapping.json not in CSV
```

**Confidence:** HIGH (observed in Phase 2 manual summary: 117% coverage = more images than products)

### Pitfall 2: Artikelnummer Normalization Inconsistency

**Problem:** CSV has `210100125`, filename is `210100125A.jpg`, but manual mapping key might be `210100125 ` (trailing space) or `  210100125` (leading space).

**Impact COUNT 8:**  
- **Affects requirement:** IMAGE-03 ✓  
- **Symptom:** Case-insensitive lookup fails due to whitespace  
- **Detection:** Products expected to have images but images array is empty  
- **Validation:** Compare `len(products_with_images)` to Phase 2 stats (545 expected)  
- **If occurs:** Mismatch count lower than expected  
- **User action:** Phase 6 Review UI surfaces products with missing expected images  
- **Agent Prevention:** Strip whitespace + lowercase normalization in matching logic  
- **Test:** Unit test with whitespace-padded artikelnummer in test data  
- **How validated:** Integration test with realistic data edge cases

**Solution:** Normalize before matching:
```python
def normalize_artikelnummer(art_nr: str) -> str:
    return art_nr.strip().lower()

# Build index
image_index = {
    normalize_artikelnummer(art_nr): images
    for art_nr, images in manual_mapping["mappings"].items()
}

# Match
normalized_id = normalize_artikelnummer(product["artikelnummer"])
matched_images = image_index.get(normalized_id, [])
```

**Confidence:** HIGH (defensive programming for string matching)

### Pitfall 3: Mutating Original merged_products.json Without Backup

**Problem:** Image linking adds `images` field to merged_products.json. If Phase 4 runs multiple times (testing, corrections), original pre-image-linking state is lost.

**Impact COUNT 6:**  
- **Affects requirement:** N/A (development workflow)  
- **Symptom:** Can't revert to pre-Phase-4 state  
- **Detection:** Only one merged_products.json exists, no backup  
- **Validation:** Check for backup file before overwriting  
- **If occurs:** Loss of intermediate state between phases  
- **User action:** Re-run Phase 3 to regenerate base merged_products.json  
- **Agent Prevention:** Don't create backup - merged_products.json is already derived (can regenerate from CSV merge)  
- **Test:** N/A (operational concern, not functional requirement)  
- **How validated:** Documentation in PLAN.md clarifies regeneration path

**Solution:** Don't back up. `merged_products.json` is derived data (regenerable from CSVs via Phase 3 merge). If user needs pre-image state, they can re-run Phase 3 merge endpoint.

**Alternative (if needed):** Create `merged_products_with_images.json` as separate output. But this complicates Phase 5 (text enhancement) - which file to read?

**Recommendation:** Overwrite merged_products.json in place. Phase 3 merge is idempotent and fast (~1 second).

**Confidence:** MEDIUM (tradeoff: simplicity vs state preservation)

### Pitfall 4: Image Path Format Assumptions

**Problem:** Assuming images are in specific directory structure or have absolute paths.

**Impact COUNT 7:**  
- **Affects requirement:** IMAGE-01 ✓  
- **Symptom:** Phase 7 HTML generation can't find images  
- **Detection:** Broken image links in generated HTML catalogs  
- **Validation:** Manual verification in Phase 6 Review UI  
- **If occurs:** Images don't display in final output  
- **User action:** Fix paths manually in Phase 6 or regenerate image mapping  
- **Agent Prevention:** Use paths exactly as stored in manual_image_mapping.json (relative, starting with `assets/bilder/`)  
- **Test:** Integration test verifies path format matches manual mapping  
- **How validated:** Phase 6 visual verification confirms images load

**Solution:** Copy paths verbatim from manual_image_mapping.json:

```python
# Direct copy from manual mapping to product data
product.data["images"] = matched_images  # Already has correct paths
```

**Reason:** Phase 2 manual mapping used actual filesystem scan. Paths are correct as-is.

**Confidence:** HIGH (trust canonical source from Phase 2)

## Validation Architecture

### V-01: Source Tracking Integrity

**What must be true:** Every product with images has `"images": "image_mapping"` in sources dict.

**How to verify:**
```python
for product in enhanced_products:
    if product.data.get("images"):
        assert product.sources.get("images") == "image_mapping", \
            f"Product {product.artikelnummer} has images but missing source tracking"
```

**Automated:** Unit test in `test_image_linking_service.py`
**Manual:** Phase 6 Review UI displays sources column (requirement REVIEW-04)

### V-02: Case-Insensitive Matching

**What must be true:** Products match images regardless of case (IMAGE-03).

**How to verify:**
```python
# Test data with mixed case
products = [{"artikelnummer": "D80950"}]
mappings = {"d80950": [{"filename": "d80950.jpg"}]}

result = link_images(products, mappings)
assert len(result.products[0].data["images"]) > 0
```

**Automated:** Unit test with case-mismatched data
**Manual:** N/A (covered by automated test)

### V-03: Empty Array for Missing Images

**What must be true:** Products without image matches have `images: []` not missing field (IMAGE-04).

**How to verify:**
```python
for product in enhanced_products:
    assert "images" in product.data, \
        f"Product {product.artikelnummer} missing images field"
```

**Automated:** Unit test with product not in image mapping
**Manual:** Phase 6 Review UI shows all products (with/without images)

### V-04: Multiple Images Per Product

**What must be true:** Products with multiple images preserve all images (IMAGE-02).

**How to verify:**
```python
# Test with known multi-image product from Phase 2 manual summary
# Example: 210100125 has 4 images (A, AA, E, G)
product = find_product("210100125", enhanced_products)
assert len(product.data["images"]) == 4
assert {"A", "AA", "E", "G"} == {img["suffix"] for img in product.data["images"]}
```

**Automated:** Integration test with Phase 2 sample data
**Manual:** Phase 6 Review UI displays image count per product

### V-05: Statistics Accuracy

**What must be true:** ImageLinkResult counts match actual product state.

**How to verify:**
```python
result = link_images(products, mappings)
actual_with_images = sum(1 for p in result.products if p.data["images"])
assert result.products_with_images == actual_with_images
```

**Automated:** Unit test recounting products after linking
**Manual:** Display statistics in API response for user validation

## Code Examples

### Example 1: Image Linking Service

```python
from pathlib import Path
import json
from typing import Dict, List
from pydantic import BaseModel


class ImageLinkResult(BaseModel):
    """Result of image linking operation."""
    total_products: int
    products_with_images: int
    products_without_images: int
    unused_image_mappings: int


def normalize_artikelnummer(art_nr: str) -> str:
    """Normalize article number for matching (strip, lowercase)."""
    return art_nr.strip().lower()


def link_images_to_products(
    merged_products_path: Path,
    image_mapping_path: Path
) -> ImageLinkResult:
    """
    Link images to products via artikelnummer matching.
    
    Reads merged_products.json, matches images from manual_image_mapping.json,
    adds images array to each product, saves enhanced merged_products.json.
    """
    # Load data
    with open(merged_products_path) as f:
        merged_data = json.load(f)
    with open(image_mapping_path) as f:
        image_mapping = json.load(f)
    
    # Build case-insensitive lookup index
    image_index = {
        normalize_artikelnummer(art_nr): images
        for art_nr, images in image_mapping["mappings"].items()
    }
    
    # Match images to products
    products_with_images = 0
    for product in merged_data:
        normalized_id = normalize_artikelnummer(product["artikelnummer"])
        matched_images = image_index.get(normalized_id, [])
        
        # Add images to product data
        product["data"]["images"] = matched_images
        
        # Add source tracking
        if matched_images:
            product["sources"]["images"] = "image_mapping"
            products_with_images += 1
        else:
            product["sources"]["images"] = None
    
    # Save enhanced merged_products.json
    with open(merged_products_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    # Calculate statistics
    total_products = len(merged_data)
    products_without_images = total_products - products_with_images
    
    # Count unused mappings
    matched_ids = {
        normalize_artikelnummer(p["artikelnummer"]) 
        for p in merged_data
    }
    unused_mappings = len([
        art_nr for art_nr in image_index.keys()
        if art_nr not in matched_ids
    ])
    
    return ImageLinkResult(
        total_products=total_products,
        products_with_images=products_with_images,
        products_without_images=products_without_images,
        unused_image_mappings=unused_mappings
    )
```

**Confidence:** HIGH (complete implementation matching requirements)

### Example 2: FastAPI Endpoint

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageLinkRequest(BaseModel):
    """Request to link images to merged products."""
    upload_id: str  # EDI upload ID containing merged_products.json


class ImageLinkResponse(BaseModel):
    """Response with image linking statistics."""
    success: bool
    total_products: int
    products_with_images: int
    products_without_images: int
    unused_image_mappings: int


@router.post("/link", response_model=ImageLinkResponse)
def link_images(request: ImageLinkRequest):
    """
    Link images from manual_image_mapping.json to merged products.
    
    Enhances merged_products.json with images array per product.
    """
    from app.services.image_linking import link_images_to_products
    from app.config import settings
    
    # Construct paths
    upload_dir = Path(settings.upload_dir) / request.upload_id
    merged_products_path = upload_dir / "merged_products.json"
    image_mapping_path = Path(".planning/manual_image_mapping.json")
    
    # Validate paths exist
    if not merged_products_path.exists():
        raise HTTPException(404, "merged_products.json not found")
    if not image_mapping_path.exists():
        raise HTTPException(404, "manual_image_mapping.json not found")
    
    # Perform linking
    result = link_images_to_products(merged_products_path, image_mapping_path)
    
    return ImageLinkResponse(
        success=True,
        total_products=result.total_products,
        products_with_images=result.products_with_images,
        products_without_images=result.products_without_images,
        unused_image_mappings=result.unused_image_mappings
    )
```

**Confidence:** HIGH (follows Phase 3 API pattern)

## Discovery Summary

**Phase 4 has NO external dependencies or complex integrations.**

Entire implementation is:
1. Read JSON (manual_image_mapping.json)
2. Read JSON (merged_products.json)
3. Match via case-insensitive lookup
4. Enhance products with images array
5. Write JSON (merged_products.json)
6. Return statistics

**Estimated complexity:** LOW (compared to Phase 2 LLM integration or Phase 3 CSV merging)

**Research depth:** Level 0 - All patterns established in Phases 1-3, no new libraries needed

---

## Research Complete

**Confidence levels:**
- Architecture patterns: HIGH
- Implementation approach: HIGH  
- Pitfall identification: HIGH (learned from Phase 2 manual analysis)
- Validation strategy: HIGH

**Uncertainties:** None. Phase 4 is straightforward data mapping using established project patterns.

**Ready for planning:** YES - planner has all information needed to create task breakdown.

---

*Phase: 04-automatic-image-linking*  
*Research completed: 2026-03-26*  
*Next: Feed to gsd-planner for PLAN.md creation*
