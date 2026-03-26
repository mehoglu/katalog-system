#!/usr/bin/env python3
"""
Enhance Bezeichnung2 with semantic improvements
Expands abbreviations and improves readability
"""
import json
import re
from pathlib import Path

def enhance_bezeichnung2(text):
    """
    Improve Bezeichnung2 formatting for better readability
    - Expand common abbreviations
    - Better structure and punctuation
    - Clearer packaging information
    """
    if not text or not isinstance(text, str):
        return text
    
    # Preserve original
    original = text.strip()
    enhanced = original
    
    # Remove trailing whitespace and noise
    enhanced = re.sub(r'\s+', ' ', enhanced)
    enhanced = enhanced.strip()
    
    # Step 1: Expand common abbreviations
    replacements = {
        # Verschlussarten
        r'\bsk\b': 'selbstklebend',
        r'\bSK\b': 'Selbstklebend',
        
        # Präpositionen und Konjunktionen
        r'\bm\.\s*': 'mit ',
        r'\bu\.\s*': 'und ',
        
        # Mengenangaben
        r'\bSt\.\s*': 'Stück ',
        r'\bSt\b': 'Stück',
        r'\bgeb\.\s*': 'gebündelt ',
        r'\bgeb\b': 'gebündelt',
        
        # Maßeinheiten
        r'\bmm\b': 'mm',
        r'\bcm\b': 'cm',
        
        # Sonstiges
        r'\bvar\.\s*': 'variable ',
        r'\bVE\s+': 'Verpackungseinheit: ',
        r'\bAM:\s*': 'Außenmaße: ',
    }
    
    for pattern, replacement in replacements.items():
        enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
    
    # Step 2: Normalize "x" to "×" in measurements
    enhanced = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1×\2', enhanced)
    
    # Step 3: Improve "4x25 St." → "4 × 25 Stück"
    enhanced = re.sub(r'(\d+)×(\d+)\s*Stück', r'\1 × \2 Stück', enhanced)
    
    # Step 4: Capitalize first letter
    if enhanced:
        enhanced = enhanced[0].upper() + enhanced[1:]
    
    # Step 5: Clean up multiple spaces
    enhanced = re.sub(r'\s+', ' ', enhanced)
    
    # Step 6: Fix punctuation spacing
    enhanced = re.sub(r'\s+,', ',', enhanced)
    enhanced = re.sub(r',(?!\s)', ', ', enhanced)
    
    # Step 7: Remove trailing comma
    enhanced = enhanced.rstrip(',. ')
    
    # Step 8: Specific phrase improvements
    # "zu 25 St geb" → "gebündelt zu 25 Stück"
    enhanced = re.sub(
        r'zu\s+(\d+)\s+Stück\s+gebündelt',
        r'gebündelt zu \1 Stück',
        enhanced
    )
    
    # ", zu 10 gebündelt" → ", gebündelt zu 10 Stück"
    enhanced = re.sub(
        r',\s*zu\s+(\d+)\s+gebündelt',
        r', gebündelt zu \1 Stück',
        enhanced
    )
    
    # "10 Stück geb." → "gebündelt zu 10 Stück"
    enhanced = re.sub(
        r'(\d+)\s+Stück\s+gebündelt',
        r'gebündelt zu \1 Stück',
        enhanced
    )
    
    # Step 9: Normalize color names (capitalize)
    colors = ['braun', 'weiß', 'gelb', 'grün', 'blau', 'rot', 'schwarz']
    for color in colors:
        # Only capitalize if at start or after comma
        enhanced = re.sub(
            rf'(^|,\s*){color}\b',
            lambda m: m.group(1) + color.capitalize(),
            enhanced
        )
    
    return enhanced

def enhance_all_bezeichnung2(upload_id='complete_run_001'):
    """Enhance all Bezeichnung2 fields"""
    json_path = Path(f'uploads/{upload_id}/merged_products.json')
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return
    
    # Load data
    with open(json_path) as f:
        data = json.load(f)
    
    print(f"{'='*70}")
    print(f"TEXT ENHANCEMENT - Bezeichnung 2")
    print(f"{'='*70}")
    print(f"Produkte: {len(data['products'])}")
    print()
    
    # Enhance each product
    enhanced_count = 0
    unchanged_count = 0
    empty_count = 0
    
    for product in data['products']:
        original = product['data'].get('bezeichnung2', '')
        
        if not original or original.strip() == '':
            empty_count += 1
            product['data']['bezeichnung2_enhanced'] = ''
            if 'sources' not in product:
                product['sources'] = {}
            product['sources']['bezeichnung2_enhanced'] = None
            continue
        
        enhanced = enhance_bezeichnung2(original)
        
        product['data']['bezeichnung2_enhanced'] = enhanced
        
        if enhanced != original:
            enhanced_count += 1
        else:
            unchanged_count += 1
        
        # Mark source for new field
        if 'sources' not in product:
            product['sources'] = {}
        product['sources']['bezeichnung2_enhanced'] = 'text_enhancement'
    
    # Save updated data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Enhancement complete!")
    print(f"  Verbessert: {enhanced_count}")
    print(f"  Unverändert: {unchanged_count}")
    print(f"  Leer: {empty_count}")
    print()
    
    # Show examples
    print("Beispiele (erste 10 mit Änderungen):")
    count = 0
    for product in data['products']:
        orig = product['data'].get('bezeichnung2', '')
        enh = product['data'].get('bezeichnung2_enhanced', '')
        
        if orig and enh and orig != enh and count < 10:
            print(f"\n  Original:    {orig[:65]}")
            print(f"  Verbessert:  {enh[:65]}")
            count += 1
    
    print()
    print(f"{'='*70}")
    print(f"Gespeichert: {json_path}")
    print(f"{'='*70}")

if __name__ == "__main__":
    enhance_all_bezeichnung2()
