# Phase 2: Intelligent CSV Analysis - Context

**Gathered:** 26. März 2026
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers LLM-based automatic CSV structure analysis: The system analyzes uploaded CSV files and automatically identifies what each column means (Artikelnummer, Bezeichnung, Preis, dimensions, etc.) without manual configuration. The detected mappings are presented to the user as proposals with confidence scores.

**What's in scope:**
- LLM integration with OpenAI API (GPT-4o-mini primary, GPT-4o fallback)
- CSV column semantic analysis (header + sample rows)
- Structured mapping output (JSON schema with confidence scores)
- Join-key identification (Artikelnummer as primary key)
- User confirmation flow for low-confidence mappings
- Mapping proposal UI display

**What's NOT in scope:**
- Data merging across CSVs → Phase 3
- Text enhancement/improvement → Phase 5
- Image matching → Phase 4
- Mapping persistence/learning → v2 (LEARN-01, LEARN-02)

</domain>

<decisions>
## Implementation Decisions

### LLM Integration-Architektur

- **D-01:** Direkte Anthropic API-Aufrufe ohne Framework (keine LangChain) - volle Kontrolle, minimale Dependencies, transparente Prompt-Verwaltung
- **D-02:** Claude 3.5 Haiku als primary model für Standard-Analysen (günstig, schnell, $0.25/1M input tokens)
- **D-03:** Claude 3.5 Sonnet als fallback für komplexe/mehrdeutige Fälle (höhere Qualität, $3/1M input tokens)
- **D-04:** Selbst gebaute Retry-Logic und Rate-Limiting (kein Framework-Overhead)

### Prompt-Design & Kontext

- **D-05:** Header + 5-10 Beispielzeilen pro CSV als LLM-Input (~500-1000 tokens pro Analyse)
- **D-06:** Intelligentes Sampling: Bei >1000 Zeilen → erste 5 + zufällige 5 aus Mitte/Ende (repräsentative Stichprobe)
- **D-07:** Beispielzeilen enthalten echte Produktdaten für Pattern-Erkennung durch LLM
- **D-08:** Kein vollständiges statistisches Pre-Processing (unique counts, min/max) - zu komplex für Phase 2

### Mapping-Ausgabeformat

- **D-09:** Claude Tool Use für strukturierte JSON-Outputs (native seit Claude 3, garantiert valides Schema)
- **D-10:** Schema-Struktur: `{"mappings": [{"csv_column": str, "product_field": str, "confidence": float, "is_join_key": bool, "reasoning": str}]}`
- **D-11:** Tool Use mit Single-Call Pattern (alle Mappings in einem Aufruf)
- **D-12:** Kein natürlicher Text mit Parsing (fehleranfällig, nicht robust)

### Confidence & Unsicherheit

- **D-13:** LLM gibt Confidence-Score (0.0-1.0) für jedes Mapping zurück
- **D-14:** UI zeigt Confidence visuell: >0.9 grün (auto-accept), 0.7-0.9 gelb (review suggested), <0.7 rot (confirmation required)
- **D-15:** User muss bei Confidence <0.7 explizit bestätigen oder korrigieren
- **D-16:** Keine automatischen Fallback-Regeln - bei Unsicherheit lieber User fragen als falsch mappen
- **D-17:** Unbekannte/unmappbare Spalten werden als "unknown" markiert, können in Phase 6 Review-Tabelle manuell zugeordnet werden

### Join-Key-Erkennung (Artikelnummer)

- **D-18:** Artikelnummer-Erkennung integriert in Haupt-Analyse (kein separater LLM-Call)
- **D-19:** JSON Schema enthält explizites `is_join_key: boolean` Feld pro Mapping
- **D-20:** Genau EINE Spalte pro CSV muss `is_join_key: true` haben (Validierung)
- **D-21:** Kein regelbasiertes Pre-Matching - LLM entscheidet basierend auf Daten, nicht nur Header-Namen
- **D-22:** Bei mehreren potenziellen Join-Keys (edge case): LLM wählt besten basierend auf Eindeutigkeit der Werte

### Agent's Discretion

- Genaue Prompt-Formulierung und System-Message für LLM
- Token-Limits und Kontext-Window-Management
- Error-Handling bei LLM API-Ausfällen (Retry-Strategie, Backoff)
- Caching-Strategie für identische CSV-Strukturen (v2 Feature, optional in Phase 2)
- UI-Layout für Mapping-Vorschlag-Anzeige (Design-Details)
- Logging-Granularität für LLM-Requests und Responses

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §CSV Analysis (CSV-01, CSV-02, CSV-03) — LLM-based column recognition, join-key detection, mapping proposals

### Project Context
- `.planning/PROJECT.md` §Context — CSV file locations, 500+ products scale, Artikelnummer as unique identifier, data source priorities (EDI Export > Preisliste)

### Prior Phase Context
- `.planning/phases/01-backend-foundation-data-import/01-CONTEXT.md` — Upload infrastructure, UTF-8 normalization already done, Polars for CSV processing
- `.planning/phases/01-backend-foundation-data-import/01-01-SUMMARY.md` — FastAPI backend patterns, upload session structure (timestamp folders)
- `.planning/phases/01-backend-foundation-data-import/01-02-SUMMARY.md` — Encoding detection already handled, CSV validation patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets from Phase 1
- **`backend/app/api/upload.py`** — Upload endpoints, session creation pattern (`create_upload_session()`)
- **`backend/app/models/upload.py`** — UploadSession, CSVUploadResponse models (extend for analysis results)
- **`backend/app/services/validation.py`** — Polars CSV reading pattern (`pl.scan_csv()`) - reuse for sample extraction
- **`backend/app/core/config.py`** — Pydantic settings pattern - add OpenAI API key

### Established Patterns
- **FastAPI async endpoints** — All endpoints use async/await
- **Pydantic models** — Type-safe request/response models
- **Polars for CSV** — Memory-efficient lazy evaluation with `scan_csv()`
- **Error wrapping** — HTTPException with status codes for API errors
- **UTF-8 normalized CSVs** — All CSVs guaranteed UTF-8 after Phase 1, no encoding issues

### Integration Points
- Phase 2 receives: `upload_id` (from Phase 1 upload session), CSV file path (already validated and UTF-8)
- Phase 2 outputs: Mapping JSON (column → product field), confidence scores, join-key identification
- Phase 3 will consume: Mapping results to merge CSVs using identified join-key

</code_context>

<specifics>
## Specific Ideas

- **Confidence-Threshold 0.7:** User explizit nach diesem Schwellenwert fragen - basiert auf Balance zwischen Auto-Accept und manuellem Review
- **GPT-4o-mini zuerst:** Kosten-Optimierung durch günstigeres Modell für Standard-Fälle, GPT-4o nur bei Bedarf
- **Kein LangChain:** User möchte volle Kontrolle und Transparenz, keine Framework-"Magic"
- **5-10 Beispielzeilen:** Nicht zu wenig (nur Header reicht nicht), nicht zu viel (Token-Verschwendung bei 500+ Produkten)

</specifics>

<deferred>
## Deferred Ideas

- **Mapping-Persistenz:** System lernt aus früheren Mappings und cached Ergebnisse für identische Strukturen → v2 (LEARN-01, LEARN-02)
- **Statistik-basierter Kontext:** Vollständige Spalten-Statistiken (unique counts, min/max, data types) als zusätzlicher LLM-Input → möglicherweise v2, Phase 2 startet mit Header + Samples
- **Multi-CSV Batch-Analyse:** Beide CSVs gleichzeitig analysieren in einem LLM-Call → Phase 2 analysiert CSVs einzeln, Optimierung ggf. später

</deferred>

---

*Phase: 02-intelligent-csv-analysis*
*Context gathered: 26. März 2026*
