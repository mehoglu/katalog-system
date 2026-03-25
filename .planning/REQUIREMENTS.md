# Requirements: Katalog

**Defined:** 25. März 2026
**Core Value:** Das System muss neue CSV-Strukturen ohne manuelle Konfiguration verstehen und alle verfügbaren Produktinformationen korrekt über die Artikelnummer zusammenführen können.

## v1 Requirements

Requirements für das Initial Release. Jedes Requirement wird auf Roadmap-Phasen gemappt.

### Data Import

- [ ] **IMPORT-01**: Benutzer kann CSV-Dateien über Web-Interface hochladen
- [ ] **IMPORT-02**: System erkennt automatisch Encoding (Windows-1252, UTF-8) und konvertiert korrekt
- [ ] **IMPORT-03**: Benutzer kann Bilder-Ordner hochladen oder angeben
- [ ] **IMPORT-04**: System validiert CSV-Struktur und zeigt Fehler an

### CSV Analysis

- [ ] **CSV-01**: System analysiert CSV-Strukturen automatisch mit LLM und erkennt Spalten-Bedeutungen (Artikelnummer, Bezeichnung1, Bezeichnung2, Preis, etc.)
- [ ] **CSV-02**: System identifiziert Artikelnummer als Join-Key in beiden CSV-Dateien
- [ ] **CSV-03**: System erstellt Mapping-Vorschlag für alle erkannten Felder

### Data Fusion

- [ ] **FUSION-01**: System führt beide CSV-Dateien über Artikelnummer zusammen
- [ ] **FUSION-02**: System löst Konflikte mit Priorit ät (EDI Export > Preisliste bei Bezeichnungen)
- [ ] **FUSION-03**: System behandelt fehlende Daten als leere Felder (keine Fehler)
- [ ] **FUSION-04**: System normalisiert Produktfelder in einheitliche Struktur

### Text Enhancement

- [ ] **TEXT-01**: System verbessert Produktbezeichnung (Bezeichnung1) sprachlich mit LLM auf Deutsch
- [ ] **TEXT-02**: System formuliert Kurzbeschreibung (Bezeichnung2) ansprechender und lesbarer um
- [ ] **TEXT-03**: System behält Fachterminologie bei und verhindert Halluzinationen
- [ ] **TEXT-04**: System verarbeitet Text-Enhancement in Batches (20-50 Produkte) für Kosten-Optimierung

### Image Linking

- [ ] **IMAGE-01**: System ordnet Bilder automatisch über Artikelnummer zu
- [ ] **IMAGE-02**: System unterstützt mehrere Bilder pro Produkt
- [ ] **IMAGE-03**: System verwendet Fuzzy Matching (case-insensitive, verschiedene Datei-Endungen)
- [ ] **IMAGE-04**: Produkte ohne Bilder werden mit leerem Bildbereich dargestellt

### Data Review & Correction

- [ ] **REVIEW-01**: System zeigt tabellarische Übersicht aller gemappten Produktdaten
- [ ] **REVIEW-02**: Benutzer kann Mapping-Ergebnisse inline in Tabelle bearbeiten
- [ ] **REVIEW-03**: Benutzer kann korrigierte Daten zur Neu-Generierung verwenden
- [ ] **REVIEW-04**: System zeigt an, welche Felder von welcher Quelle stammen

### HTML Generation

- [ ] **HTML-01**: System generiert moderne HTML-Datei pro Produkt mit allen verfügbaren Informationen
- [ ] **HTML-02**: System generiert Gesamt-Katalog mit allen Produkten
- [ ] **HTML-03**: HTML verwendet Contemporary Web UI Design (clean, modern)
- [ ] **HTML-04**: Layout ist A4 Hochformat (210 × 297 mm) für späteren PDF-Export optimiert
- [ ] **HTML-05**: System zeigt alle Produktfelder, die verfügbar sind (Artikelnr, Name, Beschreibung, Maße, Farbe, Material, VE, EAN, Gewicht, Preis, Abnahmemengen)
- [ ] **HTML-06**: System bettet Bilder ein oder verlinkt sie korrekt

### System Quality

- [ ] **SYS-01**: System verarbeitet 500+ Produkte in akzeptabler Zeit (< 10 Minuten)
- [ ] **SYS-02**: System cached LLM-Outputs zur Kosten-Reduzierung
- [ ] **SYS-03**: System verwendet strukturierte Prompts zur Prompt-Injection-Prävention
- [ ] **SYS-04**: System escaped HTML-Ausgabe korrekt

## v2 Requirements

Für zukünftige Releases vorgesehen. Getrackt, aber nicht im aktuellen Roadmap.

### Templates & Customization

- **TMPL-01**: Benutzer kann HTML-Template anpassen
- **TMPL-02**: System bietet mehrere Design-Vorlagen

### Learning & Optimization

- **LEARN-01**: System persistiert erkannte CSV-Mappings für zukünftige Nutzung
- **LEARN-02**: System re-analysiert bei neuen Strukturen trotz gespeicherter Mappings
- **LEARN-03**: System lernt aus Korrekturen und verbessert zukünftige Auto-Detection

### Export & Delivery

- **EXPORT-01**: System exportiert HTML direkt als PDF (Playwright-basiert)
- **EXPORT-02**: System bietet Sammel-PDF aller Produkte
- **EXPORT-03**: System bietet andere Export-Formate (Excel, JSON)

### Progress & Monitoring

- **PROG-01**: System zeigt Echtzeit-Progress für Batch-Verarbeitung
- **PROG-02**: System trackt LLM-Kosten pro Katalog-Durchlauf
- **PROG-03**: System erstellt Audit-Trail für Debugging

## Out of Scope

Explizit ausgeschlossen. Dokumentiert zur Scope-Creep-Prävention.

| Feature | Begründung |
|---------|-----------|
| Echtzeit-ERP-Synchronisation | Manueller CSV-Upload ausreichend, reduziert Komplexität |
| Multi-User-Verwaltung | Single-User-System für eine Person |
| Englische oder andere Sprachen | Ausschließlich Deutsch definiert in PROJECT.md |
| Eingebauter PDF-Engine | HTML-first Ansatz, PDF später über Playwright |
| Bild-Editing (Cropping, Resize) | System verwendet Bilder as-is aus Ordner |
| Inventory Management / EAN-Datenbank-Lookup | Nur Daten aus bereitgestellten CSVs |
| E-Commerce-Integration (Shop-Export) | Fokus auf Katalog-Generierung, kein Verkaufs-System |
| Version Control für Kataloge | Filesystem-basiert ausreichend |
| Analytics / BI auf Produktdaten | Reine Katalog-Generierung |

## Traceability

Welche Phasen welche Requirements abdecken. Wird während Roadmap-Erstellung aktualisiert.

| Requirement | Phase | Status |
|-------------|-------|--------|
| IMPORT-01 | TBD | Pending |
| IMPORT-02 | TBD | Pending |
| IMPORT-03 | TBD | Pending |
| IMPORT-04 | TBD | Pending |
| CSV-01 | TBD | Pending |
| CSV-02 | TBD | Pending |
| CSV-03 | TBD | Pending |
| FUSION-01 | TBD | Pending |
| FUSION-02 | TBD | Pending |
| FUSION-03 | TBD | Pending |
| FUSION-04 | TBD | Pending |
| TEXT-01 | TBD | Pending |
| TEXT-02 | TBD | Pending |
| TEXT-03 | TBD | Pending |
| TEXT-04 | TBD | Pending |
| IMAGE-01 | TBD | Pending |
| IMAGE-02 | TBD | Pending |
| IMAGE-03 | TBD | Pending |
| IMAGE-04 | TBD | Pending |
| REVIEW-01 | TBD | Pending |
| REVIEW-02 | TBD | Pending |
| REVIEW-03 | TBD | Pending |
| REVIEW-04 | TBD | Pending |
| HTML-01 | TBD | Pending |
| HTML-02 | TBD | Pending |
| HTML-03 | TBD | Pending |
| HTML-04 | TBD | Pending |
| HTML-05 | TBD | Pending |
| HTML-06 | TBD | Pending |
| SYS-01 | TBD | Pending |
| SYS-02 | TBD | Pending |
| SYS-03 | TBD | Pending |
| SYS-04 | TBD | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 0
- Unmapped: 34 ⚠️

---
*Requirements defined: 25. März 2026*
*Last updated: 25. März 2026 after initialization*
