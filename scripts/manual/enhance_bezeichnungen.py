#!/usr/bin/env python3
"""
Enhance product Bezeichnung1 with rule-based improvements
"""
import json
import re
from pathlib import Path

def enhance_bezeichnung(text):
    """
    Improve product description formatting for natural readability
    - Title case for words (except abbreviations)
    - Natural phrasing ("in der Größe", "mit", etc.)
    - Measurements in parentheses
    - Better punctuation formatting
    """
    if not text or not isinstance(text, str):
        return text
    
    # Preserve original for comparison
    original = text.strip()
    enhanced = original
    
    # Common abbreviations that should stay uppercase
    abbreviations = {
        'CD', 'DVD', 'PC', 'USB', 'LED', 'LCD', 'HD', 'UV', 'PE', 'PP', 
        'PVC', 'EVA', 'ABS', 'DIN', 'ISO', 'EU', 'VE', 'ST', 'KG', 'CM',
        'MM', 'M', 'L', 'XL', 'XXL', 'SK', 'KLS', 'WS', 'TL', 'EAN', 'A3',
        'A4', 'A5', 'A6', 'B4', 'C4', 'C5', 'C6', 'DL'
    }
    
    # Step 1: Normalize measurements first (before case changes)
    # Match 3D measurements: 145x190x-25mm or 145x190x25mm
    enhanced = re.sub(r'(\d+)\s*x\s*(\d+)\s*x\s*-?\s*(\d+)\s*mm\b', r'\1×\2×\3mm', enhanced, flags=re.IGNORECASE)
    # Match 2D measurements: 375x495mm (must not already have 3 dimensions)
    enhanced = re.sub(r'(\d+)\s*x\s*(\d+)\s*mm\b', r'\1×\2mm', enhanced, flags=re.IGNORECASE)
    
    # Remove trailing comma/punctuation
    enhanced = re.sub(r'[,;\s]+$', '', enhanced)
    
    # Step 2: Extract and format size patterns
    # Pattern: "PRODUKTNAME GRÖSSE, MAßE" where GRÖSSE is last word before comma
    # Example: "VERSANDTASCHE AUS WELLPAPPE CD, 145x190mm"
    
    # Check if there's a comma with measurements after it
    if ',' in enhanced and re.search(r'[\d×x-]+mm', enhanced):
        parts = enhanced.split(',')
        if len(parts) >= 2:
            # Get product part and measurements part
            product_part = parts[0].strip()
            measurements_part = parts[1].strip()
            
            # Extract measurements (just the numbers and mm)
            measurements_match = re.search(r'([\d×x-]+\s*mm)', measurements_part, re.IGNORECASE)
            if measurements_match:
                measurements = measurements_match.group(1).strip()
                
                # Check if product part ends with a size indicator (CD, DVD, A3, A4, etc.)
                product_words = product_part.split()
                if len(product_words) >= 2:
                    last_word = product_words[-1].strip().upper()
                    
                    # Common size indicators
                    size_indicators = {'CD', 'DVD', 'A3', 'A4', 'A5', 'A6', 'B4', 'C4', 'C5', 'C6', 'DL', 'A4+', 'A3+'}
                    
                    if last_word in size_indicators or (len(last_word) <= 4 and last_word[0].isalpha()):
                        # Extract size from end of product name
                        size = last_word
                        product_name = ' '.join(product_words[:-1])
                        
                        # Get rest of text after measurements
                        rest = ','.join(parts[2:]).strip() if len(parts) > 2 else ''
                        rest = re.sub(r'^[,;\s]+', '', rest)
                        
                        # Rebuild with natural phrasing
                        enhanced = f"{product_name} in der Größe {size} ({measurements})"
                        
                        if rest and rest not in [',', '.', ';', ')']:
                            enhanced = f"{enhanced}, {rest}"
    
    # Step 3: Apply title case while preserving abbreviations
    words = []
    current_word = ''
    
    for char in enhanced:
        if char.isalnum() or char in ['ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß']:
            current_word += char
        else:
            if current_word:
                words.append(current_word)
                current_word = ''
            words.append(char)
    
    if current_word:
        words.append(current_word)
    
    # Process each word
    result = []
    prev_was_space = True
    
    for i, word in enumerate(words):
        if not word.strip():
            result.append(word)
            prev_was_space = True
            continue
        
        # Check if it's alphanumeric
        if not any(c.isalpha() for c in word):
            result.append(word)
            prev_was_space = False
            continue
        
        word_upper = word.upper()
        word_lower = word.lower()
        
        # Keep abbreviations uppercase
        if word_upper in abbreviations:
            result.append(word_upper)
        # Keep if all uppercase and length <= 4 (likely abbreviation)
        elif word.isupper() and len(word) <= 4 and word_lower not in ['aus', 'mit', 'und', 'der', 'die', 'das', 'für', 'von']:
            result.append(word)
        # Lowercase for articles and prepositions (but capitalize if first word)
        elif word_lower in ['aus', 'mit', 'und', 'der', 'die', 'das', 'für', 'von', 'in', 'an', 'auf', 'bei', 'zu', 'vor', 'nach', 'über', 'unter', 'oder']:
            if prev_was_space and len(result) == 0:  # First word
                result.append(word.capitalize())
            else:
                result.append(word_lower)
        # Title case for regular words
        else:
            result.append(word.capitalize())
        
        prev_was_space = False
    
    enhanced = ''.join(result)
    
    # Step 4: Clean up spacing and punctuation
    enhanced = re.sub(r'\s+([,;.!?)\]])', r'\1', enhanced)  # Space before punctuation
    enhanced = re.sub(r'([\(])\s+', r'\1', enhanced)  # Space after opening bracket
    enhanced = re.sub(r'([,;])\s*', r'\1 ', enhanced)  # Space after comma/semicolon
    
    # Step 5: Normalize specific patterns
    enhanced = re.sub(r'(\d+)mm\b', r'\1 mm', enhanced)  # Space before mm
    enhanced = re.sub(r'(\d+)cm\b', r'\1 cm', enhanced)  # Space before cm
    
    # Step 6: Fix common patterns
    enhanced = re.sub(r'\s+', ' ', enhanced)  # Normalize whitespace
    enhanced = enhanced.strip()
    
    # Remove trailing comma if exists
    enhanced = re.sub(r'[,;\s]+$', '', enhanced)
    
    return enhanced

def enhance_all_products(upload_id='complete_run_001'):
    """Enhance all product descriptions"""
    json_path = Path(f'uploads/{upload_id}/merged_products.json')
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return
    
    # Load data
    with open(json_path) as f:
        data = json.load(f)
    
    print(f"{'='*70}")
    print(f"TEXT ENHANCEMENT - Bezeichnung 1")
    print(f"{'='*70}")
    print(f"Produkte: {len(data['products'])}")
    print()
    
    # Enhance each product
    enhanced_count = 0
    unchanged_count = 0
    
    for product in data['products']:
        original = product['data'].get('bezeichnung1', '')
        enhanced = enhance_bezeichnung(original)
        
        product['data']['bezeichnung1_enhanced'] = enhanced
        
        if enhanced != original:
            enhanced_count += 1
        else:
            unchanged_count += 1
        
        # Mark source for new field
        if 'sources' not in product:
            product['sources'] = {}
        product['sources']['bezeichnung1_enhanced'] = 'text_enhancement'
    
    # Save updated data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Enhancement complete!")
    print(f"  Verbessert: {enhanced_count}")
    print(f"  Unverändert: {unchanged_count}")
    print()
    
    # Show examples
    print("Beispiele (erste 5):")
    for product in data['products'][:5]:
        orig = product['data'].get('bezeichnung1', '')[:60]
        enh = product['data'].get('bezeichnung1_enhanced', '')[:60]
        if orig != enh:
            print(f"  Original:    {orig}")
            print(f"  Verbessert:  {enh}")
            print()
    
    print(f"{'='*70}")
    print(f"Gespeichert: {json_path}")
    print(f"{'='*70}")

if __name__ == "__main__":
    enhance_all_products()
