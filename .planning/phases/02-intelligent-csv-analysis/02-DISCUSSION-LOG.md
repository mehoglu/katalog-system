# Phase 2: Intelligent CSV Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 02-intelligent-csv-analysis
**Areas discussed:** LLM Integration-Architektur, LLM Provider, Prompt-Design & Kontext, Mapping-Ausgabeformat, Confidence & Unsicherheit, Join-Key-Erkennung

---

## LLM Integration-Architektur

| Option | Description | Selected |
|--------|-------------|----------|
| Direkte API-Aufrufe | Einfachster Setup, volle Kontrolle über Prompts, keine Framework-Dependencies. Du baust Retry-Logic selbst. | ✓ |
| LangChain Framework | Abstraktions-Layer für Multi-LLM, viele Built-in Tools (Memory, Chains). Heavy dependency, steile Lernkurve. | |
| Custom Agent Pipeline | Eigene Orchestrierungs-Logik mit mehreren Agenten. Flexibel aber mehr Entwicklungsaufwand. | |

**User's choice:** Option 1 - Direkte API-Aufrufe
**Notes:** User möchte Transparenz und minimale Dependencies. Kein Framework-Overhead. Retry-Logic und Rate-Limiting selbst implementieren für volle Kontrolle.

---

## LLM Provider

| Option | Description | Selected |
|--------|-------------|----------|
| OpenAI (GPT-4o / GPT-4o-mini) | GPT-4o-mini günstig ($0.15/1M), GPT-4o teurer aber bessere Qualität. Excellentes Function Calling, stabile API. | ✓ |
| Anthropic (Claude 3.5 Sonnet / Haiku) | Premium Qualität (Sonnet $3/1M), Budget (Haiku $0.25/1M). Sehr gute Reasoning-Fähigkeit. | |
| Hybrid (verschiedene je nach Task) | Kosten-optimiert, aber mehr Setup mit 2 SDKs. | |

**User's choice:** Option 1 - OpenAI
**Notes:** GPT-4o-mini für Standard-Analysen, GPT-4o als Fallback für komplexe Fälle. Kosten-Balance durch intelligentes Model-Switching.

---

## Prompt-Design & Kontext

| Option | Description | Selected |
|--------|-------------|----------|
| Nur Header | Minimal tokens (~50-100), sehr günstig. Aber LLM rät nur aus Namen. | |
| Header + 5-10 Beispielzeilen | Balance: ~500-1000 tokens, LLM sieht echte Daten. Gute Erkennungsqualität. | ✓ |
| Header + Spalten-Statistiken | Maximale Kontext-Info (Datentypen, unique values, min/max). Mehr Aufwand, mehr tokens. | |

**User's choice:** Option 2 - Header + 5-10 Beispielzeilen
**Notes:** Intelligentes Sampling bei großen CSVs: erste 5 + zufällige 5 aus Mitte/Ende. Balance zwischen Token-Kosten und Erkennungsgenauigkeit.

---

## Mapping-Ausgabeformat

| Option | Description | Selected |
|--------|-------------|----------|
| Structured Outputs (JSON Schema) | OpenAI's neuestes Feature - garantiert valides JSON. Kein Parsing nötig, type-safe. | ✓ |
| Function Calling | LLM ruft definierte Funktionen auf. Natürliches Pattern. Mehrere Roundtrips = langsamer. | |
| Natürlicher Text mit Regex-Parsing | LLM antwortet in Prosa. Fehleranfällig, fragil, nicht empfohlen 2026. | |

**User's choice:** Option 1 - Structured Outputs mit JSON Schema
**Notes:** Schema definiert: `{"mappings": [{"csv_column": str, "product_field": str, "confidence": float, "is_join_key": bool, "reasoning": str}]}`. Type-safe und zuverlässig.

---

## Confidence & Unsicherheit

| Option | Description | Selected |
|--------|-------------|----------|
| Confidence-Scores anzeigen + User entscheiden | LLM gibt Confidence (0.0-1.0), UI zeigt an, User bestätigt bei Low-Confidence. Transparente Unsicherheit. | ✓ |
| Automatische Fallback-Regeln | Bei Confidence <0.7: Spalte "Unbekannt", später manuell zuordnen. Keine Unterbrechung. | |
| Dedizierte Nachfrage pro unsicherer Spalte | System fragt sofort: "Was bedeutet 'F1'?". Sofort geklärt, aber UX-Unterbrechung. | |

**User's choice:** Option 1 - Confidence-Scores anzeigen
**Notes:** Threshold 0.7: >0.9 grün (auto-accept), 0.7-0.9 gelb (review), <0.7 rot (confirmation required). User hat volle Kontrolle bei Unsicherheit.

---

## Join-Key-Erkennung (Artikelnummer)

| Option | Description | Selected |
|--------|-------------|----------|
| In Haupt-Analyse integriert | Eine LLM-Anfrage erkennt ALLE Spalten inkl. Artikelnummer. Effizient, nur 1 API-Call. | ✓ |
| Separater LLM-Call für Artikelnummer | Extra Fokus auf kritischen Key. 2 API-Calls, teurer. | |
| Regelbasiertes Pattern-Matching + LLM Fallback | Regex nach "artikel", "art-nr" etc. Schnell bei klaren Fällen, Hybrid-Logik komplexer. | |

**User's choice:** Option 1 - In Haupt-Analyse integriert
**Notes:** JSON Schema enthält explizites `is_join_key: boolean` Feld. Validierung: Genau EINE Spalte pro CSV muss `is_join_key: true` haben. LLM entscheidet basierend auf echten Daten, nicht nur Header-Namen.

---

## Agent's Discretion

- Genaue Prompt-Formulierung und System-Message
- Token-Limits und Kontext-Window-Management
- Error-Handling bei LLM API-Ausfällen (Retry-Strategie)
- Caching-Strategie (optional in Phase 2, v2 Feature)
- UI-Layout für Mapping-Vorschlag-Anzeige
- Logging-Granularität

---

## Deferred Ideas

- **Mapping-Persistenz/Learning:** System cached Mappings für identische Strukturen (v2: LEARN-01, LEARN-02)
- **Statistik-basierter Kontext:** Vollständige Spalten-Statistiken als zusätzlicher LLM-Input (möglicherweise v2)
- **Multi-CSV Batch-Analyse:** Beide CSVs gleichzeitig in einem LLM-Call (Optimierung später)
