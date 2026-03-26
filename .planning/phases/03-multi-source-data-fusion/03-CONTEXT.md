# Phase 3: Multi-Source Data Fusion - Context

**Gathered:** 26. März 2026
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers CSV merge functionality: The system combines product data from multiple CSV files (EDI Export + Preisliste) via Artikelnummer (join key), resolves conflicts using field-specific priority rules, and produces a unified product database with source tracking.

**What's in scope:**
- Merge EDI Export + Preisliste CSVs via Artikelnummer
- Field-specific conflict resolution (Preisliste for prices, EDI for master data)
- Handling missing data gracefully (null values)
- Source tracking (which field came from which CSV)
- Unified product JSON output with metadata
- Storage as merged_products.json in upload directory

**What's NOT in scope:**
- Image linking → Phase 4
- Text enhancement → Phase 5
- Manual data correction UI → Phase 6
- Multi-CSV analysis optimization → Phase 2 deferred (both CSVs analyzed separately)

</domain>

<decisions>
## Implementation Decisions

### Merge Strategy

- **D-01:** Left Join mit EDI Export als Basis - alle Produkte aus EDI bleiben erhalten, Preislisten-Daten werden hinzugefügt wo Artikelnummer matcht
- **D-02:** Produkte nur in Preisliste (nicht in EDI) werden ignoriert - EDI ist primäre Quelle laut PROJECT.md
- **D-03:** Produkte ohne Match in Preisliste behalten mit `null` für Preis-Felder - vollständige Produktliste wichtiger als nur Produkte mit Preis

### Conflict Resolution

- **D-04:** Feld-spezifische Prioritätsregeln statt pauschale "EDI gewinnt immer"
- **D-05:** Preisliste gewinnt für: `preis`, `menge1`, `menge2`, `menge3`, `menge4`, `menge5`
- **D-06:** EDI Export gewinnt für: alle anderen Felder (Bezeichnungen, Stammdaten, Maße, etc.)
- **D-07:** Felder aus Preisliste die NICHT in D-05 Liste sind werden ignoriert (z.B. wenn Preisliste auch Bezeichnung hat)
- **D-08:** Keine timestamp-basierte oder neueste-gewinnt Logik - feste Regeln für Nachvollziehbarkeit

### Missing Data Handling

- **D-09:** Fehlende Werte als `null` in JSON (nicht leere Strings oder "N/A")
- **D-10:** Keine Default-Werte für fehlende Daten - lieber `null` als 0 oder ""
- **D-11:** Typsicherheit: `null` ist valide für alle Feldtypen (Text, Zahlen, Listen)

### Output Format

- **D-12:** Source-Tracking Format mit zwei Objekten:
  ```json
  {
    "artikelnummer": "210100125",
    "data": {
      "bezeichnung1": "VERSANDTASCHE...",
      "preis": 1.50,
      "gewicht": 0.028
    },
    "sources": {
      "bezeichnung1": "edi_export",
      "preis": "preisliste",
      "gewicht": "edi_export"
    }
  }
  ```
- **D-13:** `data` Objekt: Alle Produktfelder mit tatsächlichen Werten
- **D-14:** `sources` Objekt: Für jedes Feld in `data` die Quell-CSV ("edi_export" | "preisliste" | null für fehlende Werte)
- **D-15:** Notwendig für REVIEW-04 (Phase 6 Review UI muss Quellen anzeigen können)

### Storage & Persistence

- **D-16:** Merged data als `merged_products.json` im Upload-Verzeichnis speichern
- **D-17:** Pfad: `uploads/{upload_id}/merged_products.json`
- **D-18:** JSON Array mit einem Objekt pro Produkt
- **D-19:** Datei wird von Phase 4 (Image Linking) und Phase 5 (Text Enhancement) gelesen und erweitert

### Agent's Discretion

- Performanz-Optimierung beim Merge (Polars vs Pandas vs manuelle Iteration)
- Logging-Granularität für Merge-Operations
- Validierung der Merge-Ergebnisse (Anzahl Produkte, vollständige Felder)
- Error-Handling bei invaliden Artikelnummern oder Duplikaten
- API-Endpoint-Design (synchron vs asynchron, Response-Format)
- Memory-Management bei >500 Produkten

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Data Fusion (FUSION-01, FUSION-02, FUSION-03, FUSION-04) — Merge CSVs via article number, conflict resolution, missing data handling, unified structure

### Project Context
- `.planning/PROJECT.md` §Context — EDI Export als primäre Quelle, Preisliste für Mengen/Preise, Artikelnummer als Join-Key
- `.planning/PROJECT.md` §Key Decisions — "EDI Export hat Vorrang bei Bezeichnungen" (generalisiert zu feld-spezifischen Regeln in D-04 bis D-07)

### Phase 2 Context
- `.planning/phases/02-intelligent-csv-analysis/02-CONTEXT.md` — CSV column mappings already identified, Artikelnummer confirmed as join key
- `.planning/manual_csv_analysis.json` — EDI Export Artikeldaten analysis (33 columns, 464 products)
- `.planning/manual_image_mapping.json` — For later phases (not needed in Phase 3)

### Phase 1 Implementations
- `.planning/phases/01-backend-foundation-data-import/01-01-SUMMARY.md` — Upload session structure, FastAPI patterns
- `backend/app/api/upload.py` — Upload endpoint patterns, session creation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets from Prior Phases
- **`backend/app/api/upload.py`** — Upload session pattern (`upload_id`, timestamp folders)
- **`backend/app/services/validation.py`** — Polars CSV reading, delimiter detection
- **`backend/app/services/csv_sampling.py`** — CSV reading with auto-detected delimiter
- **`backend/app/models/upload.py`** — UploadSession model - extend with merge status

### Established Patterns
- **Polars for CSV processing** — Memory-efficient, already handles semicolon delimiter auto-detection
- **FastAPI async endpoints** — All API routes are async
- **Pydantic models** — Type-safe request/response
- **JSON file storage** — Upload sessions already use timestamp-based folders

### Integration Points
- Phase 3 receives: Two `upload_id`s (EDI + Preisliste) or paths to uploaded CSVs
- Phase 3 reads: CSV column mappings from Phase 2 analysis results (from `.planning/manual_csv_analysis.json` for now, later from API)
- Phase 3 outputs: `merged_products.json` in upload directory
- Phase 4 will: Read `merged_products.json` and add image links to each product

</code_context>

<specifics>
## Specific Ideas

- **Preisliste CSV noch nicht analysiert:** Phase 2 manual analysis hat nur EDI Export analysiert. Preisliste-Struktur muss noch geprüft werden oder Planer muss von typischer Preislisten-Struktur ausgehen (Artikelnummer + Menge1-5 + Preis)
- **Source-Tracking für Phase 6:** User will in Review UI sehen können wo jeder Wert herkommt - daher `sources` Objekt essentiell
- **Null-Werte vs leere Strings:** User explizit `null` gewählt für klare "kein Wert" Semantik
- **Nur 6 Felder aus Preisliste:** Sehr restriktive Regel - nur `preis` und `menge1-5`, alles andere ignorieren auch wenn vorhanden

</specifics>

<deferred>
## Deferred Ideas

- **Multi-CSV Batch-Merge:** Merge von mehr als 2 CSVs gleichzeitig → aktuell nur EDI + Preisliste
- **Konfigurierbarer Priority-Override:** User kann Konflikt-Regeln pro Feld anpassen → aktuell fest kodiert
- **Merge-Validation UI:** User wird nicht vorab über Merge-Konflikte informiert → erst in Phase 6 Review sichtbar
- **Inkrementelles Merge Update:** Bei neuen CSV-Uploads bestehendes Merge aktualisieren statt komplett neu → aktuell immer komplett neu mergen

</deferred>

---

*Phase: 03-multi-source-data-fusion*
*Context gathered: 26. März 2026*
