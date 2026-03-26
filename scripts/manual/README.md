# Manuelle Skripte & Einmalige Durchführungen

Dieser Ordner enthält alle manuellen Analyse- und Enhancement-Skripte, die während der Projekt-Entwicklung verwendet wurden.

## ✅ Bereits Durchgeführt (Einmalig)

### Daten-Verarbeitung
- **`manual_merge.py`** - Manuelles Merge von EDI Export & Preisliste CSV
  - Korrekte Spalten-Mappings (USER_AI* Innenmaße)
  - Prefix-Matching für Bilder (322/464 Produkte)
  - Staffelpreise-Extraktion (ABMENGE0-9, PREIS0-9)
  - **Status:** ✅ Durchgeführt
  - **Ausgabe:** `uploads/complete_run_001/merged_products.json`

### Text-Enhancement
- **`enhance_bezeichnungen.py`** - Bezeichnung1 Verbesserung
  - Natürliche Phrasierung: "in der Größe", Maßeinheiten
  - Title Case mit Ausnahmen (aus, mit, der, und)
  - **Status:** ✅ 461/464 verbessert (99.4%)

- **`enhance_bezeichnung2.py`** - Bezeichnung2 Verbesserung
  - Abkürzungen expandiert: sk→selbstklebend, m.→mit, VE→Verpackungseinheit
  - Phrase-Normalisierung: "zu 25 St geb" → "gebündelt zu 25 Stück"
  - **Status:** ✅ 449/464 verbessert (96.8%)

### Bild-Verarbeitung
- **`convert_tif_to_jpg.py`** - TIF zu JPG Konvertierung
  - **Status:** ✅ 72/78 erfolgreich konvertiert (6 beschädigt)

- **`check_images.py`** - Bildformat-Prüfung
  - Browser-kompatible Formate identifizieren

- **`verify_images.py`** - Bildverknüpfungs-Verifikation
  - Statistiken über Bildverknüpfungen

- **`analyze_image_matching.py`** - Prefix-Matching Analyse
  - Analyse der Bildnamen-Muster

### Analysen
- **`analyze_dimensions.py`** - Dimensionsspalten-Analyse
  - Entdeckte korrekte Spalten: USER_AI* (Innenmaße) statt USER_AA* (Außenmaße)
  - **Status:** ✅ Analyse abgeschlossen, Spalten korrigiert

### Pipeline
- **`run_complete_pipeline.py`** - Komplette Daten-Pipeline
  - Könnte für Re-Run nützlich sein (z.B. bei neuen CSV-Daten)
  - Führt alle Schritte automatisch aus

---

## 📊 Ergebnisse (Stand: 26.03.2026)

- **464 Produkte** vollständig verarbeitet
- **322 Produkte** mit Bildern (607 Bilder gesamt)
- **461 Bezeichnung1** verbessert (99.4%)
- **449 Bezeichnung2** verbessert (96.8%)
- **Dimensionen** korrigiert (USER_AI* Innenmaße)
- **Staffelpreise** extrahiert (3-4 Tiers pro Produkt)

## 🔄 Bei Bedarf Wiederverwenden

Falls neue CSV-Daten kommen oder Änderungen nötig sind:
1. `run_complete_pipeline.py` - Komplette Verarbeitung
2. `manual_merge.py` - Nur Merge-Schritt
3. `enhance_*.py` - Nur Text-Enhancement

**Hinweis:** Diese Skripte sind bereits ausgeführt. Die Ergebnisse sind im Hauptprojekt integriert.
