#!/usr/bin/env python3
"""
Manual merge with correct column mapping
Creates merged_products.json with standardized names
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import glob

# Standardized column mapping
EDI_MAPPING = {
    "Artikelnummer": "artikelnummer",
    "Bezeichnung1": "bezeichnung1",
    "Bezeichnung2": "bezeichnung2",
    "USER_AILaenge": "breite_cm",  # Changed from USER_AABreite - using Innenmaße (AI)
    "USER_AIHoehe": "hoehe_cm",    # Changed from USER_AAHoehe - using Innenmaße (AI)
    "USER_AIBreite": "tiefe_cm",   # Changed from USER_AATiefe - using Innenmaße (AI)
    "Gewicht": "gewicht_kg",
    "USER_MatZusammensetzung": "material",
    "USER_Farbe": "farbe",
    "Verkaufsmengeneinheit": "verkaufseinheit",
    "EANNummer": "ean"
}

PREIS_MAPPING = {
    "HAN": "artikelnummer",
    "BEZEICHNUNG": "bezeichnung_preis",
    "EINHEIT": "einheit",
    "WAEHRUNG": "waehrung"
}

def load_and_map_edi():
    """Load EDI CSV and map columns to standard names"""
    print("Loading EDI Export...")
    df = pd.read_csv("assets/EDI Export Artikeldaten.csv", sep=";", encoding="utf-8")
    
    # Select and rename columns  
    mapped_df = df[list(EDI_MAPPING.keys())].copy()
    mapped_df.rename(columns=EDI_MAPPING, inplace=True)
    
    # Clean artikelnummer
    mapped_df['artikelnummer'] = mapped_df['artikelnummer'].astype(str).str.strip()
    
    print(f"  Loaded {len(mapped_df)} products from EDI")
    print(f"  Columns: {list(mapped_df.columns)}")
    return mapped_df

def load_and_map_preis():
    """Load Preisliste CSV and extract staffelpreise (price tiers)"""
    print("Loading Preisliste...")
    df = pd.read_csv("assets/preisliste_D80950__cs_pa.csv", encoding="utf-8")
    
    # Extract basic columns
    mapped_df = df[['HAN', 'BEZEICHNUNG', 'EINHEIT', 'WAEHRUNG']].copy()
    mapped_df.rename(columns={
        'HAN': 'artikelnummer',
        'BEZEICHNUNG': 'bezeichnung_preis',
        'EINHEIT': 'einheit',
        'WAEHRUNG': 'waehrung'
    }, inplace=True)
    
    # Extract all price tiers (ABMENGE0/PREIS0, ABMENGE1/PREIS1, ...)
    mapped_df['abnahmemenge'] = None
    mapped_df['preis_nach_menge'] = None
    mapped_df['abnahmemenge'] = mapped_df['abnahmemenge'].astype('object')
    mapped_df['preis_nach_menge'] = mapped_df['preis_nach_menge'].astype('object')
    
    for idx, row in df.iterrows():
        mengen = []
        preise = []
        
        # Check up to 10 price tiers
        for i in range(10):
            menge_col = f'ABMENGE{i}'
            preis_col = f'PREIS{i}'
            
            if menge_col in df.columns and preis_col in df.columns:
                menge = row[menge_col]
                preis = row[preis_col]
                
                # Only add if both values exist and are valid
                if pd.notna(menge) and pd.notna(preis) and preis > 0:
                    mengen.append(int(menge))
                    preise.append(float(preis))
        
        if mengen:  # Only set if we found any tiers
            mapped_df.at[idx, 'abnahmemenge'] = mengen
            mapped_df.at[idx, 'preis_nach_menge'] = preise
    
    # Clean artikelnummer
    mapped_df['artikelnummer'] = mapped_df['artikelnummer'].astype(str).str.strip()
    
    print(f"  Loaded {len(mapped_df)} products from Preisliste")
    print(f"  Columns: {list(mapped_df.columns)}")
    return mapped_df

def link_images(merged_df):
    """Link images to products based on artikelnummer (with prefix matching)"""
    print("Linking images...")
    
    # Find all images - only browser-compatible formats
    browser_formats = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.WEBP']
    image_files = []
    for pattern in browser_formats:
        image_files.extend(glob.glob(f"assets/bilder/{pattern}"))
    
    # Build prefix index: map artikelnummer prefix to all matching images
    # Example: "210100125" -> ["210100125A.jpg", "210100125AA.jpg", "210100125E.jpg"]
    from collections import defaultdict
    import re
    
    prefix_map = defaultdict(list)
    for img_path in image_files:
        stem = Path(img_path).stem
        # Extract leading digits (artikelnummer prefix)
        match = re.match(r'^(\d+)', stem)
        if match:
            prefix = match.group(1)
            prefix_map[prefix].append(img_path)
    
    print(f"  Found {len(image_files)} browser-compatible images")
    print(f"  Grouped into {len(prefix_map)} unique product prefixes")
    print(f"  (Filtered out .tif files - not browser-compatible)")
    
    # Initialize bild_paths column as object type to hold lists
    merged_df['bild_paths'] = None
    merged_df['bild_paths'] = merged_df['bild_paths'].astype('object')
    
    # Link images using prefix matching
    linked_count = 0
    total_images_linked = 0
    multi_image_count = 0
    
    for idx, row in merged_df.iterrows():
        art_nr = str(row['artikelnummer']).strip()
        
        # Find all images that start with this artikelnummer
        if art_nr in prefix_map:
            images = prefix_map[art_nr]
            merged_df.at[idx, 'bild_paths'] = images
            linked_count += 1
            total_images_linked += len(images)
            if len(images) > 1:
                multi_image_count += 1
    
    print(f"  Linked {total_images_linked} images to {linked_count} products")
    print(f"  Products with multiple images: {multi_image_count}")
    return merged_df

def merge_data():
    """Merge EDI and Preisliste data"""
    edi_df = load_and_map_edi()
    preis_df = load_and_map_preis()
    
    print("\nMerging data...")
    # Merge on artikelnummer
    merged = edi_df.merge(
        preis_df,
        on='artikelnummer',
        how='left',
        suffixes=('', '_preis')
    )
    
    print(f"  Total products: {len(merged)}")
    # Check how many products have price tier data
    has_price = merged['preis_nach_menge'].apply(lambda x: x is not None and isinstance(x, list) and len(x) > 0).sum()
    print(f"  With price tiers: {has_price}")
    print(f"  Missing price tiers: {len(merged) - has_price}")
    
    # Link images
    merged = link_images(merged)
    
    return merged

def create_merged_products_json(merged_df, output_dir):
    """Create merged_products.json in Phase 3 format"""
    print("\nCreating merged_products.json...")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    products = []
    for _, row in merged_df.iterrows():
        # Convert row to dict and handle NaN
        data = {}
        sources = {}
        
        for col in merged_df.columns:
            val = row[col]
            # Handle different value types
            if col == 'bild_paths':
                # Special handling for image paths
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    data[col] = []
                    sources[col] = None
                elif isinstance(val, list):
                    data[col] = val
                    sources[col] = "image_linking"
                else:
                    # Shouldn't happen, but handle gracefully
                    data[col] = []
                    sources[col] = None
            elif col in ['abnahmemenge', 'preis_nach_menge']:
                # Special handling for price tier arrays
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    data[col] = []
                    sources[col] = None
                elif isinstance(val, list):
                    data[col] = val
                    sources[col] = "preisliste"
                else:
                    data[col] = []
                    sources[col] = None
            elif isinstance(val, list):
                # Other lists
                data[col] = val
                sources[col] = "preisliste" if col in PREIS_MAPPING.values() else "edi_export"
            elif pd.isna(val):
                # NaN values
                data[col] = None
                sources[col] = None
            else:
                # Regular values - convert to JSON-serializable types
                if isinstance(val, (int, np.integer)):
                    data[col] = int(val)
                elif isinstance(val, (float, np.floating)):
                    data[col] = float(val)
                elif isinstance(val, bool):
                    data[col] = bool(val)
                else:
                    data[col] = str(val)
                
                # Determine source
                if col in EDI_MAPPING.values():
                    sources[col] = "edi_export"
                elif col in PREIS_MAPPING.values() or col in ['abnahmemenge', 'preis_nach_menge']:
                    sources[col] = "preisliste"
                else:
                    sources[col] = None
        
        products.append({
            "artikelnummer": str(row['artikelnummer']),
            "data": data,
            "sources": sources
        })
    
    # Count products with price tiers
    has_price = merged_df['preis_nach_menge'].apply(lambda x: x is not None and isinstance(x, list) and len(x) > 0).sum()
    
    result = {
        "total_products": int(len(products)),
        "edi_only": 0,  # All from EDI
        "matched": int(has_price),
        "merge_timestamp": datetime.now().isoformat(),
        "products": products
    }
    
    output_file = output_dir / "merged_products.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved to: {output_file}")
    print(f"  Total products: {result['total_products']}")
    print(f"  Matched (with price): {result['matched']}")
    
    # Sample output
    print("\nSample product:")
    sample = products[0]
    print(f"  Artikel-Nr: {sample['artikelnummer']}")
    print(f"  Bezeichnung1: {sample['data'].get('bezeichnung1', 'N/A')}")
    print(f"  Breite: {sample['data'].get('breite_cm', 'N/A')} cm")
    print(f"  Höhe: {sample['data'].get('hoehe_cm', 'N/A')} cm")
    print(f"  Preis: {sample['data'].get('preis', 'N/A')}")
    print(f"  Bilder: {len(sample['data'].get('bild_paths', []))}")

def main():
    print("=" * 60)
    print("MANUAL MERGE WITH CORRECT COLUMN MAPPING")
    print("=" * 60)
    
    merged_df = merge_data()
    create_merged_products_json(merged_df, "uploads/complete_run_001")
    
    print("\n" + "=" * 60)
    print("✓ MERGE COMPLETE!")
    print("=" * 60)
    print("\nReview UI: http://localhost:8080/review.html?upload_id=complete_run_001")
    print()

if __name__ == "__main__":
    main()
