# Phase 1: Backend Foundation & Data Import - Context

**Gathered:** 25. März 2026
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the upload infrastructure: Users can upload CSV files and image folders via a web interface. The system validates CSV structure, detects and handles German character encoding correctly (Windows-1252/UTF-8), and provides detailed feedback with validation warnings. This foundation enables all downstream LLM agents to work with clean, properly-encoded data.

**What's in scope:**
- File upload UI (drag-and-drop, multi-file support)
- CSV structure validation (parsable, required columns present)
- Encoding detection and conversion for German umlauts
- Image folder upload and file counting
- Error/warning display with actionable feedback

**What's NOT in scope:**
- CSV semantic analysis (column meaning detection) → Phase 2
- Data merging across CSVs → Phase 3
- Image-to-product matching → Phase 4
- Any LLM agent integration → Phase 2+

</domain>

<decisions>
## Implementation Decisions

### Dateispeicher-Strategie

- **D-01:** Temporäre Speicherung - hochgeladene Dateien werden nach erfolgreicher Katalog-Generierung gelöscht (spart Speicherplatz, keine automatische Neu-Verarbeitung)
- **D-02:** Lokales Dateisystem als Speicherort (keine Cloud-Abhängigkeit für Single-User-System)
- **D-03:** Zeitstempel-basierte Ordner-Struktur pro Upload-Session (z.B. `uploads/2026-03-25_143022/`) für klare Trennung
- **D-04:** Manuelles Löschen durch Benutzer (kein automatisches Cleanup nach X Tagen)

### Upload-UX-Muster

- **D-05:** Drag-and-Drop Upload-Interface (moderner Standard 2026)
- **D-06:** Getrennte Upload-Schritte: erst CSVs hochladen, dann Bilder-Ordner (klarere Fehlerbehandlung pro Dateityp)
- **D-07:** Detaillierte Fortschrittsanzeige mit Dateiname, Größe und verbleibender Zeit
- **D-08:** Upload-Abbruch möglich mit dediziertem Abbruch-Button

### Validierungs-Timing

- **D-09:** Sofortige Validierung beim Upload (fail-fast Prinzip)
- **D-10:** Nicht-blockierende Warnungen - Benutzer kann trotz Validierungs-Warnungen fortfahren und Daten später in Tabellen-Ansicht (Phase 6) korrigieren
- **D-11:** Erweiterte Prüftiefe: Struktur (CSV parsbar, Encoding) + Inhalt (Artikelnummer-Spalte erkennbar, Duplikat-Check)
- **D-12:** Early-Exit Performance-Strategie - Validierung stoppt bei erstem kritischen Fehler für schnelles Feedback

### Fehleranzeige-Ansatz

- **D-13:** Kombiniertes Layout: inline Fehler-Indikatoren pro Datei + dediziertes Detail-Panel für vollständige Fehlerliste
- **D-14:** Zeilenspezifische Fehler-Lokalisierung (z.B. "Zeile 42: Fehlende Artikelnummer") für präzise Korrektur
- **D-15:** Dediziertes Fehler-Panel als UI-Pattern (persistent sichtbar, scrollbar)
- **D-16:** Aktions-Buttons bei Fehlern: "Upload neu", "Ignorieren", "Bearbeiten" für direkten Workflow

### Encoding-Erkennungs-Strategie

- **D-17:** Server-seitige Encoding-Erkennung im Backend (zuverlässiger als Browser-APIs)
- **D-18:** `charset-normalizer` Library (moderner Standard 2026, schneller als `chardet`)
- **D-19:** Benutzer-Bestätigung für erkanntes Encoding zeigen (gibt Kontrolle bei unsicherer Erkennung)
- **D-20:** Windows-1252 als Fallback-Default bei unsicherer Erkennung (typisch für deutsche Excel-CSV-Exporte)

### Agent's Discretion

- Welche spezifischen Validierungs-Regeln über "CSV parsbar" hinaus in Phase 1 implementiert werden (detaillierte Content-Validierung kommt hauptsächlich in Phase 2)
- Timeout-Werte für Upload-Abbruch und Fortschritts-Updates
- Genaue UI-Texte und Icon-Auswahl für Fehler-Panel
- Logging-Granularität für Upload- und Validierungs-Events

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Research
- `.planning/research/SUMMARY.md` — Stack decisions (FastAPI, Polars, React), encoding pitfalls, performance patterns

### Requirements
- `.planning/REQUIREMENTS.md` §Data Import (IMPORT-01 to IMPORT-04) — Specific upload and validation requirements
- `.planning/REQUIREMENTS.md` §CSV Analysis (CSV-01) — Encoding detection requirement
- `.planning/REQUIREMENTS.md` §System Quality (SYS-03, SYS-04) — HTML escaping and security

### Project Context
- `.planning/PROJECT.md` §Context — CSV file locations (`assets/`), image folder (`bilder/`), 500+ products scale

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **None yet** — This is a greenfield project (Phase 1 builds foundation)

### Established Patterns
- **Tech Stack** (from research): FastAPI backend, React+TypeScript frontend, Polars for data processing
- **Encoding Strategy** (from research): Critical pitfall #3 — German umlauts corruption addressed here before LLM agents run

### Integration Points
- Phase 1 outputs clean, validated, UTF-8 normalized CSV data and image file references that Phase 2's LLM-based CSV analyzer will consume
- Upload session metadata (timestamp folder, file list) will be used by Phase 3+ for data merging

</code_context>

<specifics>
## Specific Ideas

- **Tabellen-Ansicht für Korrekturen:** Benutzer möchte Validierungs-Warnungen nicht sofort beheben müssen, sondern später in einer Tabellen-Übersicht (Phase 6) inline bearbeiten können
- **Windows-1252 Focus:** Deutsche Excel-Exporte verwenden typischerweise Windows-1252 Encoding — dies sollte als primärer Erkennungs-Kandidat behandelt werden
- **Zweistufiger Upload:** Klare Trennung zwischen CSV-Upload (Daten) und Bilder-Upload (Assets) vereinfacht Fehlerbehandlung

</specifics>

<deferred>
## Deferred Ideas

None — Diskussion blieb innerhalb des Phase-1-Scope (Upload & Validierung). Keine neuen Features vorgeschlagen.

</deferred>

---

*Phase: 01-backend-foundation-data-import*
*Context gathered: 25. März 2026*
