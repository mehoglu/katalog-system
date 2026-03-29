#!/usr/bin/env python3
"""
Text Enhancement - Logik-basierte Verbesserung von Produktbezeichnungen
Verbessert Grammatik, Rechtschreibung, Lesbarkeit ohne externe API
"""
import json
import re
from pathlib import Path
from typing import Dict, Tuple


# Abkürzungen-Dictionary für deutsche Produktbeschreibungen
# Reihenfolge ist wichtig! Längere/spezifischere zuerst
ABBREVIATIONS = [
    # Spezielle Kombinationen zuerst
    (r'\bsk\s+m\.', 'selbstklebend mit'),
    (r'\bsk\b', 'selbstklebend'),
    (r'\bm\.(?=\s)', 'mit'),
    
    # Verpackung
    (r'\bSt\.', 'Stück'),
    (r'\bStck\.', 'Stück'),
    (r'\bVE\b', 'Verpackungseinheit'),
    (r'\bVPE\b', 'Verpackungseinheit'),
    
    # Materialien
    (r'\bWellp\.', 'Wellpappe'),
    
    # Eigenschaften
    (r'\bvar\.', 'variable'),
    (r'\bgr\.', 'groß'),
    (r'\bkl\.', 'klein'),
    
    # Häufige Begriffe
    (r'\binkl\.', 'inklusive'),
    (r'\bexkl\.', 'exklusive'),
    (r'\bca\.', 'circa'),
    (r'\bzB\.', 'zum Beispiel'),
    (r'\bmax\.', 'maximal'),
    (r'\bmin\.', 'minimal'),
]

# Farben und Material-Begriffe für Großschreibung
NOUNS_TO_CAPITALIZE = [
    'braun', 'weiß', 'weiss', 'schwarz', 'rot', 'blau', 'grün', 'gelb', 'grau',
    'wellpappe', 'karton', 'pappe', 'papier', 'folie', 'kunststoff',
    'versandtasche', 'versandkarton', 'faltkarton', 'schachtel', 'box',
    'aufreißfaden', 'haftklebung', 'klebeverschluss',
]

# Technische Begriffe die Großgeschrieben werden sollen
TECHNICAL_TERMS = {
    'cd': 'CD',
    'dvd': 'DVD',
    'a4': 'A4',
    'a5': 'A5',
    'a6': 'A6',
    'din': 'DIN',
}


def clean_spacing(text: str) -> str:
    """Bereinige Leerzeichen und Formatierung"""
    # Multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    # Space before punctuation
    text = re.sub(r'\s+([,;.!?])', r'\1', text)
    # Space after punctuation (if not already there)
    text = re.sub(r'([,;])(?=[^\s])', r'\1 ', text)
    # Trim
    return text.strip()


def expand_abbreviations(text: str) -> str:
    """Ersetze Abkürzungen mit ausgeschriebenen Begriffen"""
    for abbr_pattern, full_text in ABBREVIATIONS:
        text = re.sub(abbr_pattern, full_text, text, flags=re.IGNORECASE)
    return text


def fix_capitalization(text: str) -> str:
    """Korrigiere Groß- und Kleinschreibung"""
    # Erster Buchstabe groß
    if text:
        text = text[0].upper() + text[1:]
    
    # Technische Begriffe
    for term_lower, term_upper in TECHNICAL_TERMS.items():
        # Als ganzes Wort mit Wortgrenzen
        text = re.sub(rf'\b{term_lower}\b', term_upper, text, flags=re.IGNORECASE)
    
    # Substantive und häufige Begriffe
    # Teile Text in Wörter auf, behalte Satzzeichen
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Extrahiere reines Wort ohne Satzzeichen
        word_clean = re.sub(r'[^\w]', '', word)
        word_lower = word_clean.lower()
        
        # Position der Buchstaben im ursprünglichen Wort
        if not word_clean:
            result.append(word)
            continue
        
        # Bestimmte Substantive groß schreiben
        if word_lower in NOUNS_TO_CAPITALIZE:
            # Finde Position des Wortes im Original und kapitalisiere
            word_capitalized = word.replace(word_clean, word_clean.capitalize(), 1)
            result.append(word_capitalized)
        # Präpositionen, Artikel, Konjunktionen, Adjektive klein
        elif word_lower in ['aus', 'in', 'mit', 'für', 'bei', 'von', 'zu', 'an', 'auf', 
                           'der', 'die', 'das', 'dem', 'den', 'des', 'ein', 'eine',
                           'und', 'oder', 'sowie', 'aber',
                           'braun', 'weiss', 'weiß', 'schwarz', 'rot', 'blau', 'grün',
                           'variable', 'groß', 'klein']:
            # Nur klein wenn nicht am Satzanfang (i > 0)
            if i > 0:
                word_lowered = word.replace(word_clean, word_lower, 1)
                result.append(word_lowered)
            else:
                result.append(word)
        else:
            result.append(word)
    
    return ' '.join(result)


def improve_readability(text: str) -> str:
    """Verbessere Lesbarkeit durch bessere Strukturierung"""
    # Komma vor Konjunktionen wenn fehlend
    text = re.sub(r'(\w)\s+(und|oder|sowie)\s+', r'\1, \2 ', text)
    
    # Spezialfall: Dimensionen mit negativem Wert (variable Höhe)
    # "145x190x-25mm" -> "145 x 190 x bis 25 mm"
    # Erst das Minus-Pattern ersetzen, aber mit Leerzeichen davor
    text = re.sub(r'x\s*-\s*(\d+)', r' x bis \1', text)
    
    # Dann alle anderen "x" zwischen Nummern mit Leerzeichen
    # Mehrfach anwenden für "145x190x25" -> "145 x 190 x 25"
    for _ in range(3):  # Max 3 Dimensionen
        text = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1 x \2', text)
    
    return text


def standardize_units(text: str) -> str:
    """Standardisiere Maßeinheiten-Schreibweise"""
    # mm immer ohne Leerzeichen zur Zahl: "25 mm" -> "25mm"
    text = re.sub(r'(\d+)\s*(mm|cm|m)\b', r'\1\2', text)
    
    # Bei mehrteiligen Maßangaben Leerzeichen: "145x190mm" -> "145 x 190 mm"
    text = re.sub(r'(\d+\s*x\s*\d+(?:\s*x\s*\d+)?)\s*(mm|cm)', r'\1 \2', text)
    
    return text


def enhance_description(original: str) -> Tuple[str, bool]:
    """
    Verbessere eine Produktbezeichnung
    Returns: (enhanced_text, was_improved)
    """
    if not original or not isinstance(original, str):
        return original, False
    
    enhanced = original
    
    # 1. Basis-Bereinigung
    enhanced = clean_spacing(enhanced)
    
    # 2. Abkürzungen ausschreiben
    enhanced = expand_abbreviations(enhanced)
    
    # 3. Groß-/Kleinschreibung korrigieren
    enhanced = fix_capitalization(enhanced)
    
    # 4. Lesbarkeit verbessern
    enhanced = improve_readability(enhanced)
    
    # 5. Maßeinheiten standardisieren
    enhanced = standardize_units(enhanced)
    
    # 6. Finale Bereinigung
    enhanced = clean_spacing(enhanced)
    
    # Check if actually improved
    was_improved = enhanced != original
    
    return enhanced, was_improved


def enhance_product_descriptions(upload_id: str = "complete_run_001"):
    """Verbessere alle Produktbezeichnungen in merged_products.json"""
    
    merged_path = Path(f"uploads/{upload_id}/merged_products.json")
    
    if not merged_path.exists():
        print(f"❌ Datei nicht gefunden: {merged_path}")
        return
    
    print("=" * 70)
    print("PRODUKTBEZEICHNUNGEN VERBESSERN")
    print("=" * 70)
    print(f"\n📂 Lade: {merged_path}")
    
    with open(merged_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    total = len(products)
    print(f"📊 Verarbeite {total} Produkte...\n")
    
    stats = {
        'bez1_improved': 0,
        'bez2_improved': 0,
        'unchanged': 0,
    }
    
    # Zeige erste 3 Beispiele
    examples_shown = 0
    
    for i, product in enumerate(products):
        data_obj = product.get('data', {})
        sources = product.get('sources', {})
        
        # Bezeichnung 1
        bez1_original = data_obj.get('bezeichnung1', '')
        if bez1_original:
            bez1_enhanced, improved = enhance_description(bez1_original)
            data_obj['bezeichnung1_enhanced'] = bez1_enhanced
            sources['bezeichnung1_enhanced'] = 'logic_enhancement' if improved else 'original'
            
            if improved:
                stats['bez1_improved'] += 1
                
                # Zeige erste 3 Beispiele
                if examples_shown < 3:
                    print(f"\n📝 Beispiel {examples_shown + 1}:")
                    print(f"   Original:    {bez1_original}")
                    print(f"   Verbessert:  {bez1_enhanced}")
                    examples_shown += 1
        
        # Bezeichnung 2
        bez2_original = data_obj.get('bezeichnung2', '')
        if bez2_original:
            bez2_enhanced, improved = enhance_description(bez2_original)
            data_obj['bezeichnung2_enhanced'] = bez2_enhanced
            sources['bezeichnung2_enhanced'] = 'logic_enhancement' if improved else 'original'
            
            if improved:
                stats['bez2_improved'] += 1
        
        # Progress indicator every 50 products
        if (i + 1) % 50 == 0:
            print(f"\n⏳ Fortschritt: {i + 1}/{total} Produkte verarbeitet...")
    
    print("\n" + "=" * 70)
    print("STATISTIK")
    print("=" * 70)
    print(f"✅ Bezeichnung 1 verbessert:  {stats['bez1_improved']:>4} Produkte")
    print(f"✅ Bezeichnung 2 verbessert:  {stats['bez2_improved']:>4} Produkte")
    print(f"📊 Gesamt bearbeitet:         {total:>4} Produkte")
    print(f"📈 Verbesserungsrate:         {(stats['bez1_improved']/total*100):.1f}%")
    
    # Speichern
    print(f"\n💾 Speichere zu: {merged_path}")
    with open(merged_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n✓ Fertig! Produktbezeichnungen wurden verbessert.")
    print("\nVerbesserungen umfassen:")
    print("  • Abkürzungen ausgeschrieben (m. → mit, St. → Stück)")
    print("  • Groß-/Kleinschreibung korrigiert")
    print("  • Dimensionen formatiert (145x190 → 145 x 190)")
    print("  • Lesbarkeit verbessert")
    print("  • Maßeinheiten standardisiert")


if __name__ == '__main__':
    enhance_product_descriptions()
