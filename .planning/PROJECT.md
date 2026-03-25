# Katalog – Agentenbasiertes Produktkatalog-System

## Was das ist

Ein intelligentes, LLM-basiertes System zur automatischen Erstellung professioneller Produktkataloge. Das System analysiert selbständig CSV-Strukturen verschiedener Datenquellen, führt Produktinformationen zusammen, veredelt Texte sprachlich und generiert moderne HTML-Kataloge mit mehreren Bildern pro Produkt. Über ein Web-Interface können fehlerhafte Mappings nachträglich tabellarisch korrigiert werden.

## Core Value

Das System muss neue CSV-Strukturen ohne manuelle Konfiguration verstehen und alle verfügbaren Produktinformationen korrekt über die Artikelnummer zusammenführen können.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] System analysiert CSV-Strukturen automatisch und erkennt Spalten-Bedeutungen
- [ ] Produktdaten aus mehreren CSVs werden über Artikelnummer zusammengeführt
- [ ] Bilder werden automatisch über Artikelnummer zugeordnet (mehrere pro Produkt möglich)
- [ ] Fehlende Daten (Preis, Bild, Maße) werden als leere Felder behandelt
- [ ] Produktbezeichnungen werden sprachlich verbessert und lesbarer formuliert (Deutsch)
- [ ] System generiert moderne HTML-Dateien pro Produkt (A4 Hochformat, PDF-ready)
- [ ] System generiert Gesamt-Katalog mit allen Produkten
- [ ] Web-Interface ermöglicht Upload von CSV-Dateien und Bilder-Ordner
- [ ] Web-Interface zeigt tabellarische Übersicht der gemappten Daten zur Prüfung
- [ ] Fehlerhafte Mappings können tabellarisch bearbeitet und korrigiert werden
- [ ] Korrigierte Daten können erneut zur HTML-Generierung verwendet werden
- [ ] HTML-Ausgabe verwendet cleanes, modernes Contemporary Web UI Design
- [ ] System persistiert erkannte CSV-Mappings für zukünftige Nutzung
- [ ] System re-analysiert bei neuen CSV-Strukturen trotz gespeicherter Mappings

### Out of Scope

- PDF-Export — vorerst nur HTML, PDF-Generierung wird später hinzugefügt
- Multi-User-Verwaltung — System wird von einer Person genutzt
- Echtzeit-Synchronisation mit ERP-Systemen — manuelle CSV-Uploads ausreichend
- Englische oder andere Sprachen — ausschließlich Deutsch

## Context

**Datenquellen:**
- 2 CSV-Dateien im Ordner `assets/`:
  - `Preisliste`: Abnahmemengen (Menge1-5) und Preise
  - `EDI Export Artikeldaten`: Produktstammdaten (primäre Quelle)
- Produktbilder im Ordner `bilder/`

**Eindeutiger Schlüssel:**
Artikelnummer ist der zentrale Identifier für alle Zusammenführungen

**Priorität der Datenquellen:**
1. EDI Export (Hauptdaten, Stammdaten)
2. Preisliste (Mengen und Preise)
3. Bei Konflikten: EDI Export hat Vorrang bei Bezeichnungen

**Zu extrahierende Produktinformationen:**
- Artikelnummer
- Produktname/Bezeichnung (aus Bezeichnung1, sprachlich verbessert)
- Kurzbeschreibung (aus Bezeichnung2, ansprechender formuliert)
- Format/Maße (Innenmaß, Außenmaß, Höhe/variable Füllhöhe)
- Farbe
- Material
- Verpackungseinheit
- Verkaufseinheit/Abnahmemengen (Menge1-5)
- EAN-Nummer
- Gewicht
- Paletteneinheit
- Preis

**Katalog-Volumen:**
>500 Produkte pro Katalog-Durchlauf

**Typografie und Design:**
- Moderne, hochwertige HTML-Darstellung
- Sauber strukturiert mit klarer visueller Hierarchie
- Gut lesbare Typografie
- A4 Hochformat (210 × 297 mm) als Zielformat
- Geeignet für späteren PDF-Export

## Constraints

- **Tech Stack**: LLM-basierte Agenten (GPT-4/Claude) für CSV-Analyse und Sprachveredlung
- **Interface**: Web UI (nicht CLI-only)
- **Sprache**: Ausschließlich Deutsch für alle Ausgaben und Text-Veredlungen
- **Ordnerstruktur**: CSV-Dateien in `assets/`, Bilder in `bilder/`
- **Bildformat**: Mehrere Bilder pro Produkt möglich, Zuordnung über Artikelnummer
- **Ausgabeformat**: HTML first (PDF später), A4 Hochformat

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LLM-basierte Agenten statt regelbasierte Heuristiken | Neue CSV-Strukturen sollen autonom verstanden werden ohne manuelle Mapping-Konfiguration | — Pending |
| Web UI statt CLI | Benutzerfreundlichkeit, tabellarische Bearbeitung von Mappings, einfacher Upload | — Pending |
| Nachträgliche Korrektur statt Vorab-Review | Workflow-Effizienz: System läuft vollautomatisch durch, Korrekturen nur bei Bedarf | — Pending |
| Hybrid Mapping-Memory | System lernt aus früheren Mappings, analysiert aber trotzdem neue Strukturen erneut zur Validierung | — Pending |
| Artikelnummer als einziger Join-Key | Alle Datenquellen verwenden Artikelnummer als eindeutigen Identifier | — Pending |

## Evolution

Dieses Dokument entwickelt sich an Phasenübergängen und Meilenstein-Grenzen.

**Nach jedem Phasenübergang** (via `/gsd-transition`):
1. Requirements invalidiert? → Zu Out of Scope mit Begründung verschieben
2. Requirements validiert? → Zu Validated mit Phasenreferenz verschieben
3. Neue Requirements entstanden? → Zu Active hinzufügen
4. Decisions zu protokollieren? → Zu Key Decisions hinzufügen
5. "Was das ist" noch akkurat? → Aktualisieren falls abgedriftet

**Nach jedem Meilenstein** (via `/gsd-complete-milestone`):
1. Vollständige Überprüfung aller Abschnitte
2. Core Value Check — noch die richtige Priorität?
3. Out of Scope auditieren — Begründungen noch valide?
4. Context mit aktuellem Stand aktualisieren

---
*Last updated: 25. März 2026 after initialization*
