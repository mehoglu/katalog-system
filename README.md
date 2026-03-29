# Katalog Generator

Automatisches System zur Generierung von Produkt-Katalogen aus CSV-Daten und Produktbildern.

## Features

✅ **CSV Upload & Merge**: EDI und Preislisten-Daten zusammenführen
✅ **Bildverlinkung**: Automatische Zuordnung von Produktbildern
✅ **HTML-Katalog**: Professionelle, moderne HTML-Seiten für jedes Produkt
✅ **PDF-Export**: PDF-Generierung mit Playwright (kein WeasyPrint!)
✅ **Review UI**: Daten prüfen und korrigieren
✅ **Batch-Verarbeitung**: Alle 464 Produkte automatisch

## Projekt-Struktur

```
.
├── backend/           # FastAPI Backend
│   ├── app/
│   │   ├── api/      # API Endpoints
│   │   ├── services/ # Business Logic
│   │   └── models/   # Pydantic Models
│   └── Dockerfile
├── frontend/          # Static HTML/CSS/JS
│   ├── review.html   # Daten-Review UI
│   ├── css/
│   └── js/
├── uploads/           # Daten und generierte Kataloge
│   └── complete_run_001/
│       ├── merged_products.json
│       ├── catalog/          # HTML Katalog
│       └── catalog_pdf/      # PDF Exports
├── assets/            # CSV-Dateien und Bilder
└── scripts/           # Hilfsskripte

```

## Schnellstart

### 1. Backend starten
```bash
docker-compose up backend
```

Backend läuft auf: http://localhost:8000

### 2. Frontend starten
```bash
python3 -m http.server 8080
```

Frontend läuft auf: http://localhost:8080

### 3. Review-Seite öffnen
http://localhost:8080/frontend/review.html

### 4. Katalog ansehen
http://localhost:8080/uploads/complete_run_001/catalog/index.html

## Dependencies

**Backend:**
- FastAPI - Web Framework
- Playwright - PDF Generation (Chromium)
- Pandas/Polars - CSV Processing
- Jinja2 - Template Rendering

**Frontend:**
- Vanilla JavaScript (kein Framework)
- Modern CSS mit Gradients

## PDF Export

PDFs werden mit **Playwright** (Chromium) generiert - keine komplexen System-Dependencies!

**In der index.html:**
1. Produkte auswählen (Checkboxen)
2. "📄 Auswahl als PDF" oder "📚 Alle als PDF"
3. PDFs landen in `/uploads/complete_run_001/catalog_pdf/`

## Nützliche Skripte

**In `scripts/manual/`:**
- `enhance_descriptions.py` - Batch-Verbesserung von Produktbeschreibungen
- `manual_merge.py` - Manueller CSV-Merge falls API nicht verfügbar
- `run_complete_pipeline.py` - Komplette Pipeline ausführen

**Verwendung:**
```bash
cd scripts/manual
python enhance_descriptions.py  # Beschreibungen verbessern
python manual_merge.py          # Daten manuell mergen
```

## Status

✅ **Produktiv**: 464 Produkte erfolgreich verarbeitet
✅ **PDF Export**: Funktioniert mit Playwright
✅ **HTML Katalog**: Modern Clean Design
✅ **Daten-Qualität**: ~94% der Beschreibungen verbessert

## Hinweise

- **Backup**: `merged_products_backup_20260327_154347.json` (912 KB)
- **Upload-ID**: `complete_run_001` ist die aktuelle Session
- **Bilder**: Liegen in `assets/bilder/`
