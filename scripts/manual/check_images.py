import json

with open('uploads/complete_run_001/merged_products.json', 'r') as f:
    data = json.load(f)

products_with_images = [p for p in data['products'] if p['data'].get('bild_paths') and isinstance(p['data']['bild_paths'], list) and len(p['data']['bild_paths']) > 0]

print(f"Total products: {len(data['products'])}")
print(f"Products with images: {len(products_with_images)}")

if products_with_images:
    sample = products_with_images[0]
    print(f"\nSample product with images:")
    print(f"  Artikel-Nr: {sample['artikelnummer']}")
    print(f"  bild_paths type: {type(sample['data']['bild_paths'])}")
    print(f"  bild_paths: {sample['data']['bild_paths'][:2]}")
    print(f"  Image count: {len(sample['data']['bild_paths'])}")
else:
    print("\n⚠️  No products with images found!")
    print("\nChecking first product bild_paths value:")
    first = data['products'][0]
    print(f"  bild_paths: {first['data'].get('bild_paths')}")
    print(f"  type: {type(first['data'].get('bild_paths'))}")
