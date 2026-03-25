# Phase 1: Backend Foundation & Data Import - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 1-Backend Foundation & Data Import
**Areas discussed:** Dateispeicher-Strategie, Upload-UX-Muster, Validierungs-Timing, Fehleranzeige-Ansatz, Encoding-Erkennungs-Strategie

---

## Dateispeicher-Strategie

### Frage 1: Sollen hochgeladene CSV- und Bild-Dateien nach der Katalog-Generierung aufbewahrt werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Temporär (nach Verarbeitung löschen) | Spart Speicherplatz, keine Neu-Verarbeitung möglich | ✓ |
| Persistent (Originale behalten) | Ermöglicht Neu-Generierung, benötigt mehr Speicher | |
| Hybrid (CSVs behalten, Bilder löschen) | Kompromiss - wichtige Daten behalten, Bilder referenzieren | |

**User's choice:** Temporär (nach Verarbeitung löschen)
**Notes:** Fokus auf Speichereffizienz, keine Re-Processing-Anforderung

### Frage 2: Wo sollen die Dateien gespeichert werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Lokales Dateisystem | Einfach, keine externe Abhängigkeit, begrenzt auf Server-Festplatte | ✓ |
| Cloud Storage (S3/Azure Blob) | Skalierbar, höhere Komplexität und Kosten | |
| Du entscheidest | Agent wählt basierend auf Single-User-Anforderung | |

**User's choice:** Lokales Dateisystem
**Notes:** Single-User-System, keine Cloud-Kosten oder Komplexität nötig

### Frage 3: Wie sollen Upload-Sessions organisiert werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Pro Upload ein Zeitstempel-Ordner | uploads/2026-03-25_143022/ - klare Trennung, einfaches Löschen | ✓ |
| Flache Struktur mit UUID-Namen | uploads/abc123_produkte.csv - einfacher, schwerer zu navigieren | |
| Ordner pro Katalog-Projekt | projects/fruehjahr-2026/ - wenn mehrere Kataloge parallel | |

**User's choice:** Pro Upload ein Zeitstempel-Ordner
**Notes:** Klare zeitliche Organisation, einfache manuelle Bereinigung

### Frage 4: Sollen alte Uploads automatisch gelöscht werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, nach 30 Tagen | Automatisches Aufräumen, verhindert Speicher-Overflow | |
| Nein, manuelles Löschen | Volle Kontrolle, Benutzer entscheidet wann | ✓ |
| Du entscheidest | Agent implementiert sinnvolles Default | |

**User's choice:** Nein, manuelles Löschen
**Notes:** Benutzer behält volle Kontrolle über Dateiverwaltung

---

## Upload-UX-Muster

### Frage 1: Wie sollen Benutzer Dateien hochladen?

| Option | Description | Selected |
|--------|-------------|----------|
| Drag-and-Drop | Modern, intuitiv - Standard für 2026 | ✓ |
| Dateiauswahl-Button | Traditionell, zuverlässiger auf allen Geräten | |
| Beides kombiniert | Maximale Flexibilität, etwas mehr UI-Code | |

**User's choice:** Drag-and-Drop
**Notes:** Moderne UX bevorzugt

### Frage 2: Wie strukturiert ist der Upload-Prozess?

| Option | Description | Selected |
|--------|-------------|----------|
| Alles auf einmal (CSVs + Bilder) | Schneller, aber bei Fehler alles nochmal hochladen | |
| Getrennte Schritte (erst CSVs, dann Bilder) | Schrittweise, klarere Fehlerbehandlung pro Typ | ✓ |
| Beliebige Reihenfolge | Flexibel - Benutzer entscheidet Reihenfolge | |

**User's choice:** Getrennte Schritte (erst CSVs, dann Bilder)
**Notes:** Separation of Concerns - klarere Fehlerbehandlung

### Frage 3: Wie detailliert soll der Upload-Fortschritt angezeigt werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Prozentanzeige | Einfach, ausreichend für lokale Uploads | |
| Detaillierte Fortschrittsanzeige | Detailliert - Dateiname, Größe, verbleibende Zeit | ✓ |
| Nur Lade-Spinner | Minimalistisch - nur Spinner | |

**User's choice:** Detaillierte Fortschrittsanzeige
**Notes:** Maximale Transparenz für Benutzer

### Frage 4: Soll Upload abgebrochen werden können?

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, mit Abbruch-Button | Gibt Kontrolle zurück bei großen Uploads | ✓ |
| Nein, Upload muss durchlaufen | Einfacher, aber Benutzer muss warten | |
| Du entscheidest | Agent entscheidet basierend auf Upload-Größe | |

**User's choice:** Ja, mit Abbruch-Button
**Notes:** Benutzer-Kontrolle bei 500+ Produkten wichtig

---

## Validierungs-Timing

### Frage 1: Wann soll CSV-Struktur validiert werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Sofort beim Upload (fail fast) | Schnelles Feedback, stoppt bei erstem Problem | ✓ |
| Nach allen Uploads | Alle Dateien erst hochladen, dann prüfen | |
| Zweistufig (Struktur + Inhalt) | Nur Struktur sofort, Inhalt später | |

**User's choice:** Sofort beim Upload (fail fast)
**Notes:** Schnelles Feedback bevorzugt

### Frage 2: Wie streng soll Validierung sein?

| Option | Description | Selected |
|--------|-------------|----------|
| Blockierend (stoppt Workflow) | Streng - verhindert Weiterarbeiten bei Problemen | |
| Warnungen (kann fortfahren) | Flexibel - Benutzer kann ignorieren und fortfahren | ✓ |
| Hybrid (blockierend + Warnungen) | Kritische Fehler blockieren, Warnungen erlauben weitermachen | |

**User's choice:** Warnungen (kann fortfahren) - mit Freitext
**Notes:** *"warnungen kann fortfahren und später in der tabellen ansicht soll ich die möglichkeit haben zu verbessern"* — Benutzer möchte Workflow nicht unterbrechen, Korrekturen in Phase 6 (Tabellen-Ansicht) durchführen

### Frage 3: Wie umfassend soll Phase-1-Validierung prüfen?

| Option | Description | Selected |
|--------|-------------|----------|
| Basis (Struktur + Encoding) | Nur CSV parsbar, Spalten vorhanden | |
| Erweitert (+ Inhalt) | Auch Artikelnummer-Spalte erkannt, Duplicate-Check | ✓ |
| Du entscheidest | Agent wählt Phase-1-sinnvolles Level | |

**User's choice:** Erweitert (+ Inhalt)
**Notes:** Artikelnummer-Erkennung bereits in Phase 1 gewünscht

### Frage 4: Wie soll Validierung mit großen CSVs umgehen?

| Option | Description | Selected |
|--------|-------------|----------|
| Komplette Datei prüfen | Langsam, aber alle Fehler auf einmal sichtbar | |
| Early-Exit (stoppen bei erstem Fehler) | Schnell, aber nur erste Fehler gezeigt | ✓ |
| Sample-basiert | Mittelweg - erste 100 Zeilen vollständig | |

**User's choice:** Early-Exit (stoppen bei erstem Fehler)
**Notes:** Performance-Fokus für schnelles Feedback

---

## Fehleranzeige-Ansatz

### Frage 1: Wo sollen Validierungs-Fehler/-Warnungen angezeigt werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline-Fehler pro Datei | Direktes Feedback pro Datei, weniger scrolling | |
| Separate Fehler-Zusammenfassung | Zentraler Überblick, besser für Batch-Fehler | |
| Kombiniert (inline + Detail) | Beides - inline Indikator + Detail-Panel | ✓ |

**User's choice:** Kombiniert (inline + Detail)
**Notes:** Best of both worlds - Übersicht + Details

### Frage 2: Wie detailliert sollen Fehler lokalisiert werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Zeilenspezifisch (z.B. Zeile 42) | Präzise, hilft bei Korrektur in Excel vor Neuupload | ✓ |
| Datei-Ebene nur | Einfacher, weniger hilfreich für große CSVs | |
| Du entscheidest | Agent zeigt Level basierend auf Fehlertyp | |

**User's choice:** Zeilenspezifisch (z.B. Zeile 42)
**Notes:** Präzise Lokalisierung für effektive Fehlerkorrektur

### Frage 3: Welches UI-Pattern für Fehleranzeige?

| Option | Description | Selected |
|--------|-------------|----------|
| Toast-Benachrichtigungen | Unaufdringlich, verschwinden automatisch | |
| Modal-Dialogs | Erfordert Benutzer-Bestätigung, blockiert Interaktion | |
| Dediziertes Fehler-Panel | Persistent sichtbar, scrollbar bei vielen Fehlern | ✓ |

**User's choice:** Dediziertes Fehler-Panel
**Notes:** Persistent für Review, scrollbar bei vielen Warnungen

### Frage 4: Sollen Fehler mit Aktions-Buttons versehen sein?

| Option | Description | Selected |
|--------|-------------|----------|
| Fehler mit Actions (Upload neu, Ignorieren, Bearbeiten) | Klare Handlungsoptionen direkt bei Fehler | ✓ |
| Nur Fehlertext | Nur Anzeige, Benutzer muss selbst wissen was zu tun | |
| Du entscheidest | Agent wählt sinnvolle Standard-Actions | |

**User's choice:** Fehler mit Actions (Upload neu, Ignorieren, Bearbeiten)
**Notes:** Direkter Workflow ohne Navigation

---

## Encoding-Erkennungs-Strategie

### Frage 1: Wo soll Encoding erkannt werden?

| Option | Description | Selected |
|--------|-------------|----------|
| Server-seitig (Backend) | Zuverlässiger, richtige Werkzeuge (chardet/charset-normalizer) | ✓ |
| Client-seitig (Browser) | Schneller, aber Browser-API limitiert | |
| Beides (Client-Vorabcheck + Server-Bestätigung) | Doppelte Absicherung, höherer Aufwand | |

**User's choice:** Server-seitig (Backend)
**Notes:** Zuverlässigkeit vor Geschwindigkeit, richtige Tools nutzen

### Frage 2: Welches Tool zur Encoding-Erkennung?

| Option | Description | Selected |
|--------|-------------|----------|
| charset-normalizer (empfohlen 2026) | Modern, aktiv gewartet, schneller als chardet | ✓ |
| chardet | Klassiker, etwas langsamer aber bewährt | |
| Built-in detection | Python Standard Library, weniger zuverlässig | |
| Du entscheidest | Agent wählt beste Library | |

**User's choice:** charset-normalizer (empfohlen 2026)
**Notes:** Moderne Library bevorzugt

### Frage 3: Soll Benutzer erkanntes Encoding bestätigen?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-Fix ohne Nachfrage | Schnell, aber falsche Erkennung nicht korrigierbar | |
| Benutzer-Bestätigung zeigen | Sicher, gibt Kontrolle - besonders bei unsicherer Erkennung | ✓ |
| Nur bei niedriger Confidence fragen | Nur bei Unsicherheit fragen, sonst automatisch | |

**User's choice:** Benutzer-Bestätigung zeigen
**Notes:** Kontrolle und Transparenz gewünscht

### Frage 4: Was bei unsicherer Erkennung?

| Option | Description | Selected |
|--------|-------------|----------|
| Windows-1252 als Default | Sicherste Annahme für deutsche CSVs (Excel-Export) | ✓ |
| UTF-8 als Default | Moderne Annahme, riskant bei alten Excel-Exporten | |
| Benutzer fragen | Benutzer muss Encoding manuell wählen | |
| Du entscheidest | Agent wählt sinnvollen Fallback | |

**User's choice:** Windows-1252 als Default
**Notes:** Typisch für deutsche Excel-CSV-Exporte

---

## Agent's Discretion

- Genaue Validierungs-Regeln über "CSV parsbar" hinaus in Phase 1
- Timeout-Werte für Upload und Progress-Updates
- UI-Texte und Icons für Fehler-Panel
- Logging-Granularität

## Deferred Ideas

Keine — Diskussion blieb innerhalb des Phase-1-Scope. Keine neuen Features vorgeschlagen.
