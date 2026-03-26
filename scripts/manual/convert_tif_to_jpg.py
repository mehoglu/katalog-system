#!/usr/bin/env python3
"""
Convert TIF/TIFF images to JPG for browser compatibility
"""
import glob
from pathlib import Path
from PIL import Image

def convert_tif_to_jpg():
    """Convert all .tif files to .jpg"""
    tif_files = glob.glob("assets/bilder/*.tif") + glob.glob("assets/bilder/*.TIF")
    
    print(f"Found {len(tif_files)} TIF files to convert")
    
    converted = 0
    errors = 0
    
    for tif_path in tif_files:
        try:
            # Open TIF image
            img = Image.open(tif_path)
            
            # Convert to RGB if necessary (TIF can have different modes)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Create JPG path (same name, different extension)
            jpg_path = Path(tif_path).with_suffix('.jpg')
            
            # Save as JPG with good quality
            img.save(jpg_path, 'JPEG', quality=85, optimize=True)
            
            converted += 1
            if converted % 10 == 0:
                print(f"  Converted {converted}/{len(tif_files)}...")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ Error converting {tif_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✓ Conversion complete!")
    print(f"  Converted: {converted}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}")

if __name__ == "__main__":
    convert_tif_to_jpg()
