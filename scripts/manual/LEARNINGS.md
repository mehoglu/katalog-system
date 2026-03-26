# Erkenntnisse aus dem manuellen Testlauf

## Kontext
Dieser Testlauf hat wichtige Einsichten gebracht, die möglicherweise ins automatische System einfließen können. Die folgenden Punkte wurden **vorsichtig analysiert** und mit dem bestehenden System abgeglichen.

---

## 🔍 Analyse: Automatisches System vs. Manueller Test

### 1. ✅ **Bereits Gelöst im Automatischen System**

Diese Erkenntnisse sind **bereits implementiert** und brauchen keine Änderung:

#### a. Mehrere Bilder pro Produkt
- **Manuell:** Prefix-Matching (`210100125` findet `210100125A.jpg`, `210100125AA.jpg`)
- **Automatisch:** `image_linking.py` unterstützt Array von Bildern (`images: []`)
- **Status:** ✅ Bereits implementiert

#### b. Artikelnummer als Join-Key
- **Manuell:** Artikelnummer ist der zentrale Identifier
- **Automatisch:** `validate_join_key_detection()` erzwingt exakt einen Join-Key
- **Status:** ✅ Bereits implementiert

#### c. Case-Insensitive Matching
- **Manuell:** Artikelnummer-Normalisierung (trim, lowercase)
- **Automatisch:** `normalize_artikelnummer()` in `image_linking.py`
- **Status:** ✅ Bereits implementiert

---

## 💡 **Potenzielle Verbesserungen** (Vorsichtige Vorschläge)

### 2. 🟡 **Dimension-Spalten: Mehrdeutigkeit erkennen**

**Problem:**
- EDI CSV hat drei Dimensionsspalten-Typen:
  - `USER_AA*` = Außenmaße (Verpackung)
  - `USER_AI*` = Innenmaße (Produkt) ← **KORREKT**
  - `USER_AF*` = Fertige Abmessungen
- Manuell mussten wir durch Vergleich mit Produktbeschreibungen herausfinden, dass `USER_AI*` stimmt
- Das automatische System würde vermutlich alle drei als "dimensions" erkennen → mehrdeutig

**Erkenntnis:**
- LLM könnte **automatisch Plausibilität prüfen**, indem es Dimensionen in Produktbezeichnung sucht:
  - Bezeichnung: "145x190x25mm"
  - USER_AA: 20.3×2.8×15.8 cm ❌ Passt nicht
  - USER_AI: 14.5×2.5×19.0 cm ✅ Passt (145mm = 14.5cm)

**Vorsichtiger Vorschlag:**
```python
# In csv_analysis.py erweitern:

def verify_dimension_columns_with_descriptions(
    df: pd.DataFrame,
    dimension_columns: List[str],
    description_column: str
) -> Dict[str, float]:
    """
    Prüft welche Dimensionsspalte am besten zu den Maßangaben
    in der Produktbeschreibung passt.
    
    Returns: {column_name: confidence_score}
    """
    # Sample 5-10 products
    # Extract dimensions from description (regex: \d+x\d+x\d+mm)
    # Compare with each dimension column set
    # Return confidence scores
    pass
```

**Risiko:** 
- Könnte false positives geben bei inkonsistenten Beschreibungen
- Nur anwenden wenn > 1 Dimensionsspalten-Set erkannt wurde

---

### 3. 🟡 **Staffelpreise: Array-Struktur erkennen**

**Problem:**
- Preisliste hat `ABMENGE0`, `PREIS0`, `ABMENGE1`, `PREIS1`, ..., `ABMENGE9`, `PREIS9`
- Dies sind **Price Tiers**, nicht separate Felder
- Aktuelles System würde vermutlich 20 separate Spalten erkennen

**Erkenntnis:**
- Spalten mit Pattern `NAME{digit}` sollten als **Array erkannt** werden
- Manuell haben wir das als zwei Arrays strukturiert:
  ```json
  {
    "abnahmemenge": [100, 500, 3600, 7200],
    "preis_nach_menge": [0.284, 0.200, 0.197, 0.184]
  }
  ```

**Vorsichtiger Vorschlag:**
```python
# In csv_analysis.py ergänzen:

ARRAY_COLUMN_PATTERNS = [
    {
        "pattern": r"^(PREIS|PRICE)(\d+)$",
        "group": "price_tiers",
        "type": "numeric_array"
    },
    {
        "pattern": r"^(ABMENGE|MENGE|QUANTITY)(\d+)$",
        "group": "quantity_tiers",
        "type": "numeric_array"
    }
]

def detect_array_columns(headers: List[str]) -> Dict[str, List[str]]:
    """
    Erkennt Spalten die als Array zusammengehören.
    
    Returns: {
        "price_tiers": ["PREIS0", "PREIS1", ...],
        "quantity_tiers": ["ABMENGE0", "ABMENGE1", ...]
    }
    """
    pass
```

**Risiko:**
- Niedrig - Pattern ist sehr spezifisch
- Nur als optionaler Hinweis an den User ("Diese Spalten könnten zusammengehören")

---

### 4. 🟡 **Bild-Format-Validierung**

**Problem:**
- 78 TIF-Dateien im Ordner, aber Browser unterstützen TIF nicht
- Manuell mussten wir 72 TIF → JPG konvertieren
- Aktuelles System würde TIF-Dateien vermutlich als gültig akzeptieren

**Erkenntnis:**
- **Browser-kompatible Formate**: JPG, PNG, GIF, WebP, SVG
- **Nicht unterstützt**: TIF, BMP, RAW

**Vorsichtiger Vorschlag:**
```python
# In image_linking.py ergänzen:

BROWSER_COMPATIBLE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

def validate_image_format(image_path: Path) -> Tuple[bool, str]:
    """
    Prüft ob Bildformat browser-kompatibel ist.
    
    Returns: (is_valid, message)
    """
    suffix = image_path.suffix.lower()
    if suffix in BROWSER_COMPATIBLE_FORMATS:
        return True, "OK"
    else:
        return False, f"Format {suffix} nicht browser-kompatibel. Konvertierung nötig."
```

**Integration:**
- Nicht blockieren, nur warnen
- Im Upload-Step: "⚠️ 78 TIF-Dateien gefunden - bitte zu JPG konvertieren"
- Optional: Automatische Konvertierung anbieten

**Risiko:**
- Niedrig - reine Validierung, kein Breaking Change

---

### 5. 🟢 **Text-Enhancement: regelbasierte Fallback-Patterns**

**Problem:**
- LLM Text-Enhancement ist generisch
- Manuell haben wir **sehr spezifische Patterns** gefunden, die immer funktionieren:
  - `sk` → `selbstklebend` (100% Trefferquote in diesem Domain)
  - `m.` → `mit`
  - `VE` → `Verpackungseinheit:`
  - `St.` → `Stück`
  - `geb.` → `gebündelt`

**Erkenntnis:**
- Diese Patterns sind **domain-spezifisch** (Verpackungsindustrie)
- LLM macht das auch, aber inkonsistent
- Regelbasierte Post-Processing könnte Konsistenz erhöhen

**Vorsichtiger Vorschlag:**
```python
# In text_enhancement.py ergänzen:

DOMAIN_SPECIFIC_REPLACEMENTS = {
    "packaging": {  # Verpackungsindustrie
        r'\bsk\b': 'selbstklebend',
        r'\bm\.\s*': 'mit ',
        r'\bVE\b': 'Verpackungseinheit',
        r'\bSt\.\b': 'Stück',
        r'\bgeb\.\b': 'gebündelt',
    },
    # Weitere Domains könnten hinzugefügt werden
}

def apply_domain_post_processing(
    text: str,
    domain: str = "packaging"
) -> str:
    """
    Wendet domain-spezifische regelbasierte Verbesserungen an
    NACH dem LLM-Enhancement (als Konsistenz-Layer).
    """
    if domain not in DOMAIN_SPECIFIC_REPLACEMENTS:
        return text
    
    enhanced = text
    for pattern, replacement in DOMAIN_SPECIFIC_REPLACEMENTS[domain].items():
        enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
    
    return enhanced
```

**Integration:**
- Als **optionaler Post-Processing-Step** nach LLM
- Nur anwenden wenn User explizit Domain angibt
- Nicht das LLM ersetzen, nur ergänzen

**Risiko:**
- Niedrig - reine Ergänzung, kein Breaking Change
- Domain-Patterns könnten in anderen Kontexten falsch sein (z.B. "SK" = Slowakei)

---

### 6. 🟡 **Prefix-Matching für Bilder**

**Problem:**
- Aktuelles System macht vermutlich **exakt matching**: `210100125` = `210100125.jpg`
- Realität: `210100125` hat `210100125A.jpg, 210100125AA.jpg, 210100125E.jpg`
- Manuell: 67 → 322 Produkte mit Bildern durch Prefix-Matching

**Erkenntnis:**
- **Prefix-Matching** ist bei Produktbildern sehr häufig:
  - Hauptbild: `{ARTNR}A.jpg`
  - Detailbilder: `{ARTNR}AA.jpg`, `{ARTNR}B.jpg`, etc.
- Sollte **Standard-Strategie** sein, nicht nur Fallback

**Vorsichtiger Vorschlag:**
```python
# In image_linking.py erweitern:

def match_images_fuzzy(
    artikelnummer: str,
    available_images: List[Path],
    strategies: List[str] = ["exact", "prefix", "fuzzy"]
) -> List[Path]:
    """
    Wendet mehrere Matching-Strategien an (in Reihenfolge).
    
    Strategies:
    - exact: artikelnummer.jpg (aktuell)
    - prefix: artikelnummer*.jpg (NEU)
    - fuzzy: Levenshtein distance < 2 (optional)
    
    Returns: Alle gefundenen Bilder (mehrere möglich)
    """
    matched = []
    
    # Strategy 1: Exact match
    if "exact" in strategies:
        exact_matches = [
            img for img in available_images 
            if img.stem == artikelnummer
        ]
        matched.extend(exact_matches)
    
    # Strategy 2: Prefix match (NEU aus manuellem Test)
    if "prefix" in strategies and not matched:
        prefix_matches = [
            img for img in available_images
            if img.stem.startswith(artikelnummer)
        ]
        matched.extend(prefix_matches)
    
    return matched
```

**Integration:**
- Default: `strategies=["exact", "prefix"]`
- User kann via Config deaktivieren: `"image_matching_strategy": "exact"`

**Risiko:**
- Mittleres Risiko: Könnte false positives geben
  - Beispiel: `2101` matched auch `21010000.jpg`
- Lösung: Nur anwenden wenn Artikelnummer >= 6 Zeichen (zu kurze IDs → zu vage)

---

## 📊 **Zusammenfassung: Empfohlene Integrationen**

| # | Feature | Risiko | Aufwand | Nutzen | Empfehlung |
|---|---------|--------|---------|--------|------------|
| 1 | ✅ Mehrere Bilder | - | - | - | Bereits implementiert |
| 2 | 🟡 Dimension-Plausibilität | Mittel | Hoch | Hoch | **JA** - als optionale Validierung |
| 3 | 🟡 Staffelpreise-Arrays | Niedrig | Mittel | Hoch | **JA** - als Hinweis an User |
| 4 | 🟡 Bild-Format-Validierung | Niedrig | Niedrig | Mittel | **JA** - als Warnung |
| 5 | 🟢 Domain-Post-Processing | Niedrig | Mittel | Mittel | **JA** - als optionaler Layer |
| 6 | 🟡 Prefix-Matching | Mittel | Mittel | Hoch | **VORSICHTIG** - nur mit Schutzmaßnahmen |

---

## 🎯 **Konkrete Nächste Schritte** (falls gewünscht)

### Phase 1: Schnelle Wins (Low Risk, High Impact)
1. **Bild-Format-Validierung** hinzufügen (~30 min)
   - Warnung bei TIF/BMP-Dateien
   - Keine Breaking Changes

2. **Array-Column-Detection** als Hinweis (~1h)
   - Erkennt `PREIS0-9` Pattern
   - Zeigt im UI: "⚠️ Diese Spalten könnten zusammengehören"
   - User entscheidet

### Phase 2: Medium Complexity (Medium Risk, High Impact)
3. **Prefix-Matching für Bilder** (~2h)
   - Mit Schutzmaßnahmen (min. 6 Zeichen)
   - Als optionale Strategie
   - Default: `["exact", "prefix"]`

4. **Domain-Post-Processing** (~2h)
   - Regelbasiertes Fallback nach LLM
   - Als optionaler Step
   - Config: `"text_enhancement_domain": "packaging"`

### Phase 3: Komplex (Higher Risk, High Impact)
5. **Dimension-Plausibilitäts-Check** (~4h)
   - LLM vergleicht Dimensionen mit Beschreibung
   - Zeigt Confidence-Score pro Spalten-Set
   - User wählt final

---

## ⚠️ **Was NICHT übernehmen**

Diese manuellen Patterns sollten **NICHT** ins automatische System:

1. ❌ **Hardcoded Column Mappings** (`EDI_MAPPING`, `PREIS_MAPPING`)
   - Grund: Automatisches System soll flexibel bleiben
   - Stattdessen: LLM erkennt Spalten dynamisch

2. ❌ **Spezifische Enhancement-Rules als Ersatz für LLM**
   - Grund: Zu starr, funktioniert nur für Verpackungsindustrie
   - Stattdessen: Als optionaler Post-Processing-Layer

3. ❌ **Manuelle TIF-Konvertierung als Standard**
   - Grund: Nicht alle Projekte brauchen das
   - Stattdessen: Warnung + Anleitung zur Konvertierung

---

## 📝 **Fazit**

Der manuelle Test hat **5 konkrete Verbesserungen** identifiziert:

1. ✅ **Schnell umsetzbar:** Bild-Format-Validierung, Array-Detection
2. ⚠️ **Mit Vorsicht:** Prefix-Matching (mit Schutzmaßnahmen)
3. 🎯 **Strategisch wertvoll:** Dimension-Plausibilität (reduziert User-Errors erheblich)
4. 🔧 **Optional aber nützlich:** Domain-Post-Processing (für Konsistenz)

**Nächster Schritt:**
Falls du diese Verbesserungen umsetzen möchtest, können wir mit **Phase 1** (Schnelle Wins) starten - das sind ~1-2 Stunden Arbeit mit minimalem Risiko.

---

**Erstellt:** 26.03.2026  
**Basis:** Manueller Testlauf mit 464 Produkten, 2 CSVs, 1055 Bildern
