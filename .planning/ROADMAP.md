# Roadmap: Katalog

**Project:** Katalog — LLM-based Product Catalog System  
**Core Value:** System must understand new CSV structures without manual configuration and merge product data correctly via article number  
**Version:** v1.0  
**Created:** 25. März 2026  
**Granularity:** Standard (5-8 phases)

## Phases

- [x] **Phase 1: Backend Foundation & Data Import** - Upload infrastructure with encoding handling and validation
- [ ] **Phase 2: Intelligent CSV Analysis** - Auto-detect column semantics via LLM agent
- [ ] **Phase 3: Multi-Source Data Fusion** - Merge CSVs via article number with conflict resolution
- [ ] **Phase 4: Automatic Image Linking** - Match images to products via article number patterns
- [ ] **Phase 5: German Text Enhancement** - Improve product descriptions with LLM batching
- [ ] **Phase 6: Data Review & Correction** - Table interface for verifying and editing mappings
- [ ] **Phase 7: Professional HTML Catalog Output** - Generate print-ready A4 HTML catalogs

## Phase Details

### Phase 1: Backend Foundation & Data Import
**Goal**: User can upload CSVs and images, system handles encoding correctly and validates data structure  
**Depends on**: Nothing (foundation phase)  
**Requirements**: IMPORT-01, IMPORT-02, IMPORT-03, IMPORT-04, SYS-03, SYS-04  
**Success Criteria** (what must be TRUE):
  1. User can upload CSV files via web interface and see file names confirmed
  2. System displays German product names with correct umlauts (ä, ö, ü, ß) from uploaded CSVs
  3. User can upload image folder and see count of images detected
  4. System shows validation errors with specific line numbers when CSV structure is invalid  
**Plans**: 2 plans  

Plans:
- [x] 01-01-PLAN.md — Backend upload API with FastAPI (✅ Complete - commit bfeae6c)
- [x] 01-02-PLAN.md — Encoding detection + CSV validation (✅ Complete - commit b435ea1)

**UI hint**: yes

### Phase 2: Intelligent CSV Analysis
**Goal**: System automatically understands CSV structure and identifies column meanings without manual configuration  
**Depends on**: Phase 1 (needs file upload and encoding handling)  
**Requirements**: CSV-01, CSV-02, CSV-03  
**Success Criteria** (what must be TRUE):
  1. User uploads unknown CSV structure and system identifies column meanings (Artikelnummer, Bezeichnung, Preis)
  2. System detects article number column automatically as join key across both CSVs
  3. User sees mapping proposal showing which CSV columns map to which product fields
  4. System processes CSV analysis within 30 seconds for 500+ products  
**Plans**: 5 plans in 4 waves

Plans:
- [x] 02-01-PLAN.md — OpenAI Integration Setup (Wave 1)
- [x] 02-02-PLAN.md — CSV Sampling Service (Wave 1)
- [x] 02-03-PLAN.md — LLM CSV Analysis Service (Wave 2)
- [x] 02-04-PLAN.md — FastAPI Analysis Endpoint (Wave 3)
- [x] 02-05-PLAN.md — CSV Analysis Tests + Manual Verification (Wave 4)

### Phase 3: Multi-Source Data Fusion
**Goal**: System merges product data from multiple CSVs correctly via article number  
**Depends on**: Phase 2 (needs column semantics from analysis)  
**Requirements**: FUSION-01, FUSION-02, FUSION-03, FUSION-04  
**Success Criteria** (what must be TRUE):
  1. User sees merged product dataset combining information from both CSVs
  2. System resolves conflicting data using priority rules (EDI Export takes precedence over Preisliste)
  3. Products with missing data (price, dimensions) display with empty fields instead of errors
  4. User can verify that all products from both CSVs are included in merged result  
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — CSV Merge Service with Polars
- [ ] 03-02-PLAN.md — FastAPI Merge Endpoint + Storage
- [ ] 03-03-PLAN.md — Integration Tests

### Phase 4: Automatic Image Linking
**Goal**: System associates product images with correct articles automatically  
**Depends on**: Phase 3 (needs merged product data with article numbers)  
**Requirements**: IMAGE-01, IMAGE-02, IMAGE-03, IMAGE-04  
**Success Criteria** (what must be TRUE):
  1. User sees which images matched to which article numbers
  2. System finds multiple images per product when available
  3. System matches images case-insensitively (D80950.jpg = d80950.JPG)
  4. Products without matching images show placeholder instead of breaking  
**Plans**: 2 plans in 2 waves

Plans:
- [x] 04-01-PLAN.md — Image Linking Service + Models (Wave 1)
- [x] 04-02-PLAN.md — API Endpoint + Integration Tests (Wave 2)

### Phase 5: German Text Enhancement
**Goal**: System improves product texts to be more readable and professional in German  
**Depends on**: Phase 3 (needs merged product data for text fields)  
**Requirements**: TEXT-01, TEXT-02, TEXT-03, TEXT-04  
**Success Criteria** (what must be TRUE):
  1. User sees enhanced product names (Bezeichnung1) that are more readable than raw CSV data
  2. User sees improved descriptions (Bezeichnung2) that are more engaging and grammatically polished
  3. System preserves technical terminology and measurements (does not hallucinate)
  4. System processes 500 products in under 10 minutes with batch optimization  
**Plans**: 2 plans in 2 waves

Plans:
- [x] 05-01-PLAN.md — Text enhancement service with LLM batching (Wave 1, autonomous)
- [x] 05-02-PLAN.md — API endpoint + performance verification (Wave 2, has checkpoint)

### Phase 6: Data Review & Correction
**Goal**: User can review all mapped data in table format and correct errors before generating catalogs  
**Depends on**: Phase 3, Phase 4, Phase 5 (needs complete merged/enhanced data)  
**Requirements**: REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04  
**Success Criteria** (what must be TRUE):
  1. User sees complete table with all products and all mapped fields
  2. User can edit any cell inline and see changes saved immediately
  3. User can identify which data came from which CSV source
  4. User can trigger catalog regeneration using corrected data  
**Plans**: 2 plans in 2 waves

Plans:
- [x] 06-01-PLAN.md — Review API (GET all products, PATCH single field) (Wave 1, autonomous)
- [x] 06-02-PLAN.md — Review UI table with inline editing (Wave 2, has checkpoint)

**UI hint**: yes

### Phase 7: Professional HTML Catalog Output
**Goal**: System generates print-ready HTML catalogs with modern design  
**Depends on**: Phase 4, Phase 5, Phase 6 (needs images, enhanced text, and corrected data)  
**Requirements**: HTML-01, HTML-02, HTML-03, HTML-04, HTML-05, HTML-06, SYS-01, SYS-02  
**Success Criteria** (what must be TRUE):
  1. User receives individual HTML file for each product with all available information
  2. User receives master catalog HTML with all products indexed
  3. Generated HTML displays correctly in A4 format (210×297mm) for PDF export
  4. HTML uses clean, modern design with proper typography and visual hierarchy
  5. All product fields (name, description, dimensions, price, images) appear correctly in catalog  
**Plans**: 1 plan

Plans:
- [ ] 07-01-PLAN.md — HTML catalog generation (templates + API + tests) (Wave 1, has checkpoint)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Foundation & Data Import | 0/0 | Not started | - |
| 2. Intelligent CSV Analysis | 0/0 | Not started | - |
| 3. Multi-Source Data Fusion | 0/0 | Not started | - |
| 4. Automatic Image Linking | 0/0 | Not started | - |
| 5. German Text Enhancement | 0/0 | Not started | - |
| 6. Data Review & Correction | 0/0 | Not started | - |
| 7. Professional HTML Catalog Output | 0/0 | Not started | - |

## Research Notes

Phase 1 addresses **critical pitfall #3** from research: German encoding corruption (umlaut hell). Encoding detection must work before any LLM agents process text.

Phase 2 establishes LLM integration patterns and addresses **pitfall #1** (cost spiral) and **pitfall #2** (token overflow) with batch processing architecture.

Phase 5 text enhancement uses batch processing (20-50 products per call) to avoid cost spiral. Research estimates €2.26 per 500-product run with Claude 3.5 Sonnet.

Phase 7 must validate PDF rendering early (research **pitfall #5**) — design HTML for print from start.

---
*Roadmap created: 25. März 2026*  
*Coverage: 34/34 v1 requirements mapped ✓*
