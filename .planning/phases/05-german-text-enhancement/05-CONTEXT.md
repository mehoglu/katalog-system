# Phase 5: German Text Enhancement - Context

**Gathered:** 2026-03-26  
**Status:** Ready for planning  
**Source:** Direct planning (builds on Phase 2 OpenAI patterns)

<domain>
## Phase Boundary

Phase 5 enhances German product texts (Bezeichnung1 and Bezeichnung2) using LLM to improve readability and professionalism while preserving technical accuracy.

**Inputs:** merged_products.json from Phase 3 with raw CSV text  
**Outputs:** enhanced_products.json with improved German texts  
**Core Constraint:** No hallucination — preserve all measurements, technical terms, and factual data

</domain>

<decisions>
## Implementation Decisions

### Text Enhancement Strategy
- **D-01:** Enhance two fields: Bezeichnung1 (product name) and Bezeichnung2 (description)
- **D-02:** Use OpenAI GPT-4 (already integrated in Phase 2)
- **D-03:** Process in batches of 20-50 products for cost optimization (TEXT-04)
- **D-04:** System prompt emphasizes: improve readability, preserve technical terms, no hallucination
- **D-05:** Enhanced texts stored in `data.bezeichnung1_enhanced` and `data.bezeichnung2_enhanced`
- **D-06:** Source tracking: `sources.bezeichnung1_enhanced = "llm_enhancement"`

### Preservation Rules
- **D-07:** Preserve ALL measurements (mm, kg, Stück, etc.)
- **D-08:** Preserve ALL technical codes (VE, WS, KLS, TL, etc.)
- **D-09:** Preserve ALL artikelnummer references
- **D-10:** Verify enhanced text contains all critical terms from original

### Batch Processing
- **D-11:** Read merged_products.json, process in chunks of 30 products
- **D-12:** Single API call per batch with structured JSON response
- **D-13:** Progress tracking: show "Enhanced 30/464 products..."
- **D-14:** Error handling: skip problematic products, log, continue batch

### Performance Target
- **D-15:** Complete 500 products in under 10 minutes (TEXT-04 success criteria)
- **D-16:** Use async/parallel batch processing if needed

### the agent's Discretion
- Exact batch size (20-50 range acceptable)
- Prompt engineering specifics (as long as preservation rules met)
- Whether to use GPT-4 or GPT-3.5-turbo (cost vs quality tradeoff)
- Progress display format
- Whether to create API endpoint or CLI script

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Text Enhancement (TEXT-01, TEXT-02, TEXT-03, TEXT-04) — LLM enhancement, readability, preservation, batch processing

### Project Context
- `.planning/PROJECT.md` §Core Value — System must handle German text with umlauts correctly
- `.planning/ROADMAP.md` Phase 5 — Success criteria and dependencies

### Phase 2 OpenAI Integration
- `.planning/phases/02-intelligent-csv-analysis/02-01-SUMMARY.md` — OpenAI setup pattern (API key, client initialization)
- `backend/app/services/csv_analysis.py` — Existing OpenAI usage pattern to follow

### Phase 3 Data Structure
- `.planning/phases/03-multi-source-data-fusion/03-CONTEXT.md` — merged_products.json structure
- `backend/app/models/merge.py` — MergedProduct model (extend for enhanced fields)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`backend/app/services/csv_analysis.py`** — OpenAI client already configured, prompt patterns
- **`backend/app/models/merge.py`** — MergedProduct model to extend
- **`merged_products.json`** — Input data with Bezeichnung1 and Bezeichnung2 fields

### Established Patterns
- OpenAI API key in settings.openai_api_key
- Async service functions with error handling
- JSON file read/write for product data
- Source tracking in `sources` object

### Integration Points
- Phase 5 reads: merged_products.json (Phase 3 output)
- Phase 5 writes: enhanced_products.json OR updates merged_products.json in-place
- Phase 6 will: Display enhanced texts in review UI

</code_context>

<specifics>
## Specific Ideas

**Example original text:**
```
Bezeichnung1: "VERSANDTASCHE AUS WELLPAPPE CD, 145x190x-25mm"
Bezeichnung2: "sk m. Aufreißfaden, braun, var. Höhe, VE 4x25 St."
```

**Example enhanced text:**
```
Bezeichnung1_enhanced: "Versandtasche aus Wellpappe für CDs (145×190×25 mm)"
Bezeichnung2_enhanced: "Selbstklebend mit Aufreißfaden, braun, variable Höhe. Verpackungseinheit: 4×25 Stück."
```

**What changed:** Capitalization, punctuation, readability  
**What stayed:** All measurements, technical abbreviations expanded with originals preserved

</specifics>

<deferred>
## Deferred Ideas

- **Multi-language support:** Only German in this phase
- **User-editable prompts:** Fixed system prompt for consistency
- **A/B testing enhancement quality:** Single enhancement approach
- **Manual approval per product:** Batch automation only, review happens in Phase 6

</deferred>

---

*Phase: 05-german-text-enhancement*  
*Context gathered: 2026-03-26*
