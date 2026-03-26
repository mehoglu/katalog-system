#!/usr/bin/env python3
"""
Manuelle Bild-Zuordnung für CSV-Artikel
Erstellt JSON-Mapping: Artikelnummer -> Bilder
"""
import json
import re
from pathlib import Path
from collections import defaultdict

# Pfade
bilder_dir = Path("/Users/mhueseyino001/Documents/Dev/Katalog New/assets/bilder")
output_file = Path("/Users/mhueseyino001/Documents/Dev/Katalog New/.planning/manual_image_mapping.json")

# Pattern: Artikelnummer (9 Ziffern) + optionaler Suffix + Dateierweiterung
# Beispiele: 210100125A.jpg, 210100125.jpg, 211101010.tif
pattern = re.compile(r'^(\d{9})([A-Z]*)\.(.+)$', re.IGNORECASE)

# Mapping: Artikelnummer -> Liste von Bildern
image_mapping = defaultdict(list)

# Alle Dateien im Bilder-Verzeichnis durchgehen
for img_file in bilder_dir.iterdir():
    if not img_file.is_file():
        continue
    
    match = pattern.match(img_file.name)
    if match:
        artikelnummer = match.group(1)  # z.B. "210100125"
        suffix = match.group(2)          # z.B. "A", "AA", "E", "G", oder ""
        extension = match.group(3)       # z.B. "jpg", "tif", "png"
        
        # Bild-Info speichern
        image_info = {
            "filename": img_file.name,
            "suffix": suffix if suffix else "main",
            "extension": extension.lower(),
            "path": f"assets/bilder/{img_file.name}"
        }
        
        # Bestimme Bildtyp basierend auf Suffix
        if suffix == "A":
            image_info["type"] = "front"
        elif suffix == "AA":
            image_info["type"] = "detail"
        elif suffix == "E":
            image_info["type"] = "single"
        elif suffix == "G":
            image_info["type"] = "group"
        elif not suffix:
            image_info["type"] = "main"
        else:
            image_info["type"] = "other"
        
        image_mapping[artikelnummer].append(image_info)

# Sortiere Bilder pro Artikel nach Suffix-Priorität: main, A, AA, E, G, other
suffix_priority = {"main": 0, "A": 1, "AA": 2, "E": 3, "G": 4, "other": 5}
for artikelnummer in image_mapping:
    image_mapping[artikelnummer].sort(
        key=lambda x: suffix_priority.get(x["suffix"], 99)
    )

# Statistiken
total_products_with_images = len(image_mapping)
total_images = sum(len(imgs) for imgs in image_mapping.values())

# JSON erstellen
result = {
    "created_at": "2026-03-26T14:30:00",
    "source": "manual_mapping",
    "statistics": {
        "total_products_with_images": total_products_with_images,
        "total_images": total_images,
        "products_with_1_image": sum(1 for imgs in image_mapping.values() if len(imgs) == 1),
        "products_with_2_images": sum(1 for imgs in image_mapping.values() if len(imgs) == 2),
        "products_with_3_images": sum(1 for imgs in image_mapping.values() if len(imgs) == 3),
        "products_with_4+_images": sum(1 for imgs in image_mapping.values() if len(imgs) >= 4)
    },
    "image_types": {
        "main": "Hauptbild ohne Suffix",
        "A": "Frontansicht",
        "AA": "Detailansicht",
        "E": "Einzelbild",
        "G": "Gruppenbild"
    },
    "mappings": dict(image_mapping)
}

# JSON schreiben
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"✓ Bild-Mapping erstellt: {output_file}")
print(f"✓ {total_products_with_images} Produkte mit insgesamt {total_images} Bildern")
print(f"✓ Durchschnitt: {total_images / total_products_with_images:.1f} Bilder pro Produkt")
