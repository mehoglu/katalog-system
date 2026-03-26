#!/usr/bin/env python3
"""Quick test for Phase 1 enhancements"""
import re
from collections import defaultdict

# Test 1: Array Column Detection
print("="*60)
print("TEST 1: Array Column Detection")
print("="*60)

ARRAY_COLUMN_PATTERNS = [
    {
        "pattern": r"^(PREIS|PRICE)(\d+)$",
        "group_type": "price_tiers",
    },
    {
        "pattern": r"^(ABMENGE|MENGE|QUANTITY|QTY)(\d+)$",
        "group_type": "quantity_tiers",
    }
]

headers = ['HAN', 'BEZEICHNUNG', 'PREIS0', 'PREIS1', 'PREIS2', 'PREIS3', 
           'ABMENGE0', 'ABMENGE1', 'ABMENGE2', 'WAEHRUNG']

matched_columns = set()
groups = []

for pattern_config in ARRAY_COLUMN_PATTERNS:
    pattern = pattern_config["pattern"]
    group_type = pattern_config["group_type"]
    
    matches = defaultdict(list)
    for header in headers:
        match = re.match(pattern, header, re.IGNORECASE)
        if match and header not in matched_columns:
            base_name = match.group(1)
            digit = int(match.group(2))
            matches[base_name.upper()].append((digit, header))
    
    for base_name, column_list in matches.items():
        if len(column_list) >= 2:
            column_list.sort(key=lambda x: x[0])
            columns = [col for _, col in column_list]
            print(f'✓ Detected: {base_name} → {columns}')
            print(f'  Type: {group_type}')
            groups.append(base_name)

if groups:
    print(f'\n✅ SUCCESS: {len(groups)} array groups detected')
else:
    print('\n✗ FAILED: No groups detected')

# Test 2: Image Format Validation
print("\n" + "="*60)
print("TEST 2: Image Format Validation")
print("="*60)

BROWSER_COMPATIBLE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}

test_images = [
    "product1.jpg",
    "product2.tif",
    "product3.TIF",
    "product4.png",
    "product5.bmp"
]

incompatible = []
for img in test_images:
    from pathlib import Path
    suffix = Path(img).suffix.lower()
    
    if suffix not in BROWSER_COMPATIBLE_FORMATS:
        incompatible.append(img)
        print(f'⚠️  {img} → {suffix} (not browser-compatible)')
    else:
        print(f'✓ {img} → {suffix} (OK)')

if incompatible:
    print(f'\n⚠️  WARNING: {len(incompatible)} incompatible formats found')
    print(f'   Files: {incompatible}')
    print(f'   Recommendation: Convert to JPG or PNG')
else:
    print('\n✅ All images browser-compatible')

print("\n" + "="*60)
print("Phase 1 Tests Complete!")
print("="*60)
