#!/usr/bin/env python3
"""
Analyze how images match to products
"""
import json
import glob
from pathlib import Path
from collections import defaultdict
import re

# Load product data
with open('uploads/complete_run_001/merged_products.json') as f:
    data = json.load(f)
    products = {p['artikelnummer']: p for p in data['products']}

# Get all browser-compatible images
image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.WEBP']
all_images = []
for ext in image_extensions:
    all_images.extend(glob.glob(f'assets/bilder/{ext}'))

print(f"{'='*70}")
print(f"BILDANALYSE")
print(f"{'='*70}")
print(f"Produkte in CSV: {len(products)}")
print(f"Bilder gefunden: {len(all_images)}")
print()

# Group images by their numeric prefix
image_by_prefix = defaultdict(list)
for img_path in all_images:
    stem = Path(img_path).stem
    # Extract leading digits
    match = re.match(r'^(\d+)', stem)
    if match:
        prefix = match.group(1)
        image_by_prefix[prefix].append(img_path)

# Analyze matches
exact_matches = 0
prefix_matches = 0
no_matches = 0
multi_image_products = 0

product_image_map = {}

for art_nr, product in products.items():
    art_nr_str = str(art_nr).strip()
    
    # Try exact match first
    if art_nr_str in image_by_prefix:
        images = image_by_prefix[art_nr_str]
        exact_matches += 1
        if len(images) > 1:
            multi_image_products += 1
        product_image_map[art_nr_str] = images
    else:
        no_matches += 1

print(f"Matching-Ergebnisse:")
print(f"  Exakte Übereinstimmungen: {exact_matches} Produkte")
print(f"  Produkte mit mehreren Bildern: {multi_image_products}")
print(f"  Keine Übereinstimmung: {no_matches} Produkte")
print()

# Show examples of multi-image products
print("Beispiele - Produkte mit mehreren Bildern:")
count = 0
for art_nr, images in sorted(product_image_map.items()):
    if len(images) > 1 and count < 10:
        print(f"  {art_nr}: {len(images)} Bilder")
        for img in images:
            print(f"    - {Path(img).name}")
        count += 1

print()
print(f"{'='*70}")
print(f"EMPFEHLUNG:")
print(f"Verwende PREFIX-MATCHING statt EXACT-MATCHING")
print(f"→ Artikelnummer '210100125' findet alle Bilder die mit '210100125' beginnen")
print(f"{'='*70}")
