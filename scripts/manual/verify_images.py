#!/usr/bin/env python3
"""Verify image linking results."""
import json
from pathlib import Path

merged_path = Path("uploads/manual_test_001/merged_products.json")
with open(merged_path) as f:
    data = json.load(f)

# Find first product with images
print("=== Product WITH images ===")
for p in data['products']:
    if p['data'].get('images') and len(p['data']['images']) > 0:
        print(f"Artikelnummer: {p['artikelnummer']}")
        print(f"Number of images: {len(p['data']['images'])}")
        print(f"First image: {p['data']['images'][0]['path']}")
        print(f"Source tracking: {p['sources'].get('images', 'MISSING')}")
        if len(p['data']['images']) > 1:
            print(f"Multiple images: ✓ ({len(p['data']['images'])} images)")
        break

print("\n=== Product WITHOUT images (should have empty array) ===")
for p in data['products']:
    if 'images' in p['data'] and len(p['data']['images']) == 0:
        print(f"Artikelnummer: {p['artikelnummer']}")
        print(f"Images field: {p['data']['images']}")
        print(f"Source tracking: {p['sources'].get('images', 'MISSING')}")
        break

print("\n=== Statistics ===")
print(f"Total products: {data['total_products']}")
with_images = sum(1 for p in data['products'] if p['data'].get('images'))
without_images = sum(1 for p in data['products'] if 'images' in p['data'] and len(p['data']['images']) == 0)
print(f"Products with images array: {with_images}")
print(f"Products with empty images array: {without_images}")
