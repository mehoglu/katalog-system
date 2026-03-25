# Feature Landscape

**Domain:** Intelligent Catalog & Document Generation Systems
**Researched:** 25. März 2026
**Confidence:** MEDIUM (based on training data for PIM/catalog platforms, analyzed against project requirements)

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **CSV/Excel Import** | Standard data source for product catalogs | Low | Multi-file import, drag-and-drop UI |
| **Data Validation** | Prevents corrupt output | Medium | Required fields, format checks, duplicate detection |
| **Preview Before Generation** | Users need to verify before committing | Medium | Shows sample products, layout preview |
| **Export to Common Formats** | HTML/PDF minimum for catalog use | Medium-High | A4 print-ready output |
| **Multi-Image Support** | Modern catalogs = multiple product views | Medium | Filename/SKU matching, image gallery layouts |
| **Batch Processing** | Catalogs have 100s-1000s of products | Medium | Progress tracking, cancellation support |
| **Error Reporting** | Shows what failed and why | Low-Medium | Missing data, invalid formats, failed mappings |
| **Data Mapping Interface** | Users expect to map columns to fields | Medium | Especially when auto-detection uncertain |
| **Template Customization** | Brand alignment required | High | Logo, colors, fonts, layout variations |
| **Undo/Revert Capability** | Safety net for corrections | Medium | Version history or session rollback |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI Auto-Structure Detection** | Zero-config data import | High | LLM analyzes CSV semantics, not just headers |
| **Intelligent Text Enhancement** | Converts raw data to marketing copy | High | LLM rewrites product names/descriptions |
| **Multi-Source Data Fusion** | Merge from multiple CSVs automatically | High | Conflict resolution, priority rules, join logic |
| **Learning from Corrections** | System improves over time | High | Persistent mappings, pattern recognition |
| **Inline Table Editing** | Fix data post-import without re-upload | Medium | Spreadsheet-like UI for corrections |
| **Validation Re-run** | Correct and regenerate without re-import | Low-Medium | Uses corrected data from session |
| **Smart Missing Data Handling** | Graceful degradation vs hard failure | Medium | Optional fields, conditional layouts |
| **Filename-to-Product Matching** | Auto-link images by SKU in filename | Medium | Pattern matching (SKU_01.jpg → SKU) |
| **Hybrid Auto/Manual Mapping** | AI suggests, user overrides | High | Confidence scores, review workflow |
| **Multi-Product Layouts** | Not just single-page per product | Medium | Grid layouts, comparison views, category pages |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time ERP Sync** | Over-engineering for manual workflow | Batch CSV imports on-demand |
| **Multi-user Collaboration** | Complex for single-user scenario | Single-session web UI sufficient |
| **Built-in PDF Engine** | HTML-to-PDF tools exist | HTML output, external PDF conversion |
| **Advanced Analytics/BI** | Not a data analytics tool | Focus on catalog generation quality |
| **Version Control/Branching** | Catalog drafts aren't code | Simple before/after comparison enough |
| **Multi-language Support** | German-only requirement stated | Avoid i18n complexity premature |
| **In-app Image Editing** | Not a design tool | Users prepare images externally |
| **Inventory/Stock Management** | Different domain entirely | Pure catalog generation focus |
| **E-commerce Integration** | Catalog viewing ≠ selling | Static output, no cart/checkout |
| **Custom Scripting/Plugins** | Complexity explosion | Opinionated workflow, fast to use |

## Feature Dependencies

```
CSV Import → Data Validation → Column Detection → Data Mapping
                                                    ↓
Multi-Source Fusion → Missing Data Handling → Text Enhancement
                                                    ↓
                        Preview Generation ← Template Selection
                                                    ↓
                        Batch Processing → Progress Tracking
                                                    ↓
                        Error Review → Inline Editing → Validation Re-run
                                                          ↓
                                              Final Export (HTML/PDF)
```

**Critical Path Dependencies:**
- **Data Mapping** must work before **Text Enhancement** (need field semantics)
- **Multi-Source Fusion** requires **Column Detection** from all sources first
- **Inline Editing** requires **Data Mapping** results to be persistent
- **Preview** requires **Template Selection** and at least partial data processing
- **Validation Re-run** requires **Inline Editing** infrastructure

**Parallel Capabilities:**
- Image matching can run independent of data processing
- Template customization can be developed separately from data pipeline
- Error reporting is orthogonal to main data flow

## MVP Recommendation

**Phase 1 Focus (Table Stakes Foundation):**
1. CSV Import with drag-and-drop
2. AI Auto-Structure Detection (differentiator)
3. Basic Data Validation (required fields, duplicates)
4. Simple Data Mapping UI (fallback for AI detection)
5. Single-source processing only (defer multi-source fusion)

**Phase 2 Focus (Core Workflow):**
1. Multi-Source Data Fusion (merge 2+ CSVs)
2. Image filename matching
3. Preview Generation (sample products)
4. Template Selection (2-3 fixed templates)
5. Batch Processing with progress

**Phase 3 Focus (Quality & Corrections):**
1. Text Enhancement with LLM
2. Inline Table Editing
3. Error Review UI
4. Validation Re-run
5. HTML Export (A4 print-ready)

**Defer to Post-MVP:**
- Template Customization (complex, use fixed templates initially)
- Learning from Corrections (requires usage history)
- Advanced Multi-Product Layouts (single-page-per-product sufficient initially)
- PDF Export (HTML first, delegate to external tools)

## Complexity Analysis

**High-Risk Features (need careful planning):**
- **AI Auto-Structure Detection** — LLM prompt engineering, semantic analysis, edge cases
- **Multi-Source Data Fusion** — Conflict resolution logic, merge strategies, performance
- **Text Enhancement** — Quality control, hallucination prevention, German language tuning
- **Template Customization** — CSS/layout complexity, preview accuracy, user flexibility

**Medium-Risk Features:**
- **Inline Table Editing** — State management, validation on edit, UI responsiveness
- **Batch Processing** — Memory management for 500+ products, progress tracking
- **Preview Generation** — Representative sampling, accurate rendering

**Low-Risk Features:**
- **CSV Import** — Standard libraries exist
- **Error Reporting** — Logging and display patterns
- **Image Matching** — Regex/glob patterns

## Feature Interactions

**Synergies:**
- **AI Detection + Learning from Corrections** → System gets smarter over time
- **Multi-Source Fusion + Missing Data Handling** → Graceful merges even with incomplete data
- **Inline Editing + Validation Re-run** → Fast correction loop without re-import
- **Preview + Template Selection** → Users see exactly what they'll get

**Conflicts to Manage:**
- **Auto-Detection vs Manual Mapping** — When to show mapping UI? How to override?
- **Text Enhancement vs User Edits** — Which takes precedence? Re-enhance after edit?
- **Batch Progress vs Preview** — Can't preview all 500 products, sample strategy?
- **Learning Persistence vs Re-Analysis** — When to trust old mappings vs re-detect?

## Competitive Context

**PIM Systems (Akeneo, Pimcore):**
- Expect: Multi-channel output, DAM integration, workflow management
- Overkill for this use case (catalog generation only)

**Catalog Automation (InDesign Scripts, Catalog Machine):**
- Expect: Template-driven layouts, design control, print production
- Lack: AI-powered intelligence, zero-config data handling

**Document Automation (DocRaptor, Documotor):**
- Expect: Template engines, API-driven generation, multi-format export
- Lack: Data integration, semantic understanding of product data

**This System's Niche:**
- **Zero-config data understanding** (AI detection)
- **Multi-source fusion** (not just single CSV)
- **Correction workflow** (edit post-import)
- **German B2B catalogs** (specific market)

## Edge Cases to Consider

1. **Ambiguous CSV Columns** — "Menge" could be quantity or measure, "Preis" might be with/without VAT
2. **Duplicate Products** — Same SKU in different CSVs with conflicting data
3. **Missing Critical Data** — Product without name, without SKU, without any images
4. **Large Image Sets** — 10+ images per product, performance implications
5. **Special Characters** — German umlauts (ä, ö, ü, ß), special symbols in product names
6. **Numeric Formats** — European formats (1.234,56) vs US formats (1,234.56)
7. **Multi-line Descriptions** — Line breaks in CSV cells, formatting preservation
8. **Orphaned Images** — Images in folder with no matching SKU
9. **SKU Format Variations** — Leading zeros, hyphens, spaces ("123" vs "0123" vs "1-23")
10. **Batch Size Limits** — Memory constraints with 1000+ products, pagination strategy

## Sources

**Training Data Sources:**
- PIM system feature comparisons (Akeneo, Pimcore, Salsify)
- Catalog automation tools (InDesign automation, Catalog Machine)
- Document generation platforms (DocRaptor, Documotor, Pandadoc)
- ETL/data integration best practices
- Product catalog industry standards

**Confidence Note:**
This research is based on training data about established platforms in adjacent spaces (PIM, document automation, data integration). Unable to verify with current web sources (Brave API unavailable). Recommendations are extrapolated from known patterns in these domains and aligned with the specific requirements in PROJECT.md.

**Recommend validating:**
- Current state-of-the-art in AI-powered catalog generation (2026)
- Latest German B2B catalog publishing practices
- Modern web-to-print capabilities and constraints
