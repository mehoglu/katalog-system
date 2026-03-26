# Phase 3: Multi-Source Data Fusion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 26. März 2026
**Phase:** 03-multi-source-data-fusion
**Areas discussed:** Merge Strategy, Conflict Resolution, Missing Data Handling, Output Format

---

## Merge Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Left Join (EDI als Basis) | Alle Produkte aus EDI Export bleiben, Preisliste ergänzt wo Artikelnummer matcht | ✓ |
| Full Outer Join (alle) | Alle Produkte aus BEIDEN CSVs, auch wenn nur in einer | |
| Inner Join (nur Überschneidung) | Nur Produkte die in BEIDEN CSVs existieren | |

**User's choice:** Left Join (EDI als Basis)
**Notes:** EDI ist "primäre Quelle" laut PROJECT.md, Preisliste ergänzt nur Preis-Informationen

---

## Conflict Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| EDI gewinnt IMMER | Bei allen Konflikten EDI Export bevorzugen | |
| Feld-spezifische Regeln | Preisliste für Preise/Mengen, EDI für Stammdaten | ✓ |
| Neuester Wert / Timestamp-basiert | Welche CSV neuer ist gewinnt | |

**User's choice:** Feld-spezifische Regeln
**Notes:** Nutzt Stärken beider Quellen optimal - Preisliste ist spezialisiert auf Preise, EDI hat bessere Stammdaten

### Feld-spezifische Details

| Option | Description | Selected |
|--------|-------------|----------|
| Nur Preis-spezifische Felder | Aus Preisliste: preis, menge1-5; Rest aus EDI | ✓ |
| Auch andere Felder aus Preisliste | Falls Preisliste Bezeichnung/Gewicht hat, auch nutzen | |

**User's choice:** Nur Preis-spezifische Felder
**Notes:** Sehr restriktiv - nur 6 Felder aus Preisliste (`preis`, `menge1`, `menge2`, `menge3`, `menge4`, `menge5`), alles andere ignorieren

---

## Produkte ohne Preis

| Option | Description | Selected |
|--------|-------------|----------|
| Produkt behalten mit null | Produkt bleibt in Liste, preis = null | ✓ |
| Produkt markieren | Flag wie has_pricing = false | |
| Produkt ausschließen | Nur Produkte mit Preis im Output | |

**User's choice:** Produkt behalten mit null
**Notes:** Vollständige Produktliste wichtiger als nur Produkte mit Preis - kann später gefiltert werden falls nötig

---

## Missing Data Handling

| Option | Description | Selected |
|--------|-------------|----------|
| null Werte | Standard JSON null für fehlende Werte | ✓ |
| Leere Strings "" | Alle fehlenden Felder als "" | |
| Typspezifisch | Text: "", Zahlen: null oder 0 | |
| Spezial-Marker "N/A" | Sichtbar in UI, nicht standard-konform | |

**User's choice:** null Werte
**Notes:** Standard-konform, klar unterscheidbar von leerem String, gut für JSON/APIs

---

## Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Unified Product Model (flach) | Alle Felder in einem Objekt, keine Quelleninfo | |
| Source-Tracking (mit Metadaten) | data + sources Objekte, zeigt Herkunft | ✓ |
| Getrennte Sections | from_edi + from_preisliste Objekte | |

**User's choice:** Source-Tracking (mit Metadaten)
**Notes:** Notwendig für REVIEW-04 - Phase 6 Review UI muss sehen können wo jeder Wert herkommt

---

## Speicherung

| Option | Description | Selected |
|--------|-------------|----------|
| JSON-Datei im Upload-Verzeichnis | uploads/{id}/merged_products.json | ✓ |
| Nur in-memory | Nicht persistent, muss neu gemerged werden | |
| In Datenbank | SQLite/Postgres | |

**User's choice:** JSON-Datei im Upload-Verzeichnis
**Notes:** Persistiert, nachvollziehbar, kann von Phase 4 und 5 gelesen und erweitert werden

---

## Agent's Discretion

- Performanz-Optimierung beim Merge (Polars vs Pandas)
- Error-Handling Details
- API-Endpoint-Design
- Validierung der Merge-Ergebnisse
- Memory-Management für >500 Produkte
