#!/usr/bin/env python3
"""
Complete catalog generation pipeline
Runs all phases: Upload -> Analysis -> Merge -> Image Linking -> Text Enhancement
"""
import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"
UPLOAD_ID = "complete_run_001"

def upload_files():
    """Phase 1: Upload CSV files"""
    print("=" * 60)
    print("PHASE 1: Uploading CSV files...")
    print("=" * 60)
    
    files = [
        ("files", open("assets/EDI Export Artikeldaten.csv", "rb")),
        ("files", open("assets/preisliste_D80950__cs_pa.csv", "rb"))
    ]
    
    response = requests.post(
        f"{API_BASE}/api/upload",
        files=files,
        data={"upload_id": UPLOAD_ID}
    )
    
    print(f"Upload Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✓ Files uploaded: {response.json()}")
    else:
        print(f"✗ Upload failed: {response.text}")
        return False
    return True

def analyze_csvs():
    """Phase 2: Analyze CSV structure with LLM"""
    print("\n" + "=" * 60)
    print("PHASE 2: Analyzing CSV structures...")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/api/analyze",
        json={"upload_id": UPLOAD_ID}
    )
    
    print(f"Analysis Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Analysis complete")
        print(f"  CSV 1: {result.get('csv1_analysis', {}).get('detected_join_key', 'N/A')}")
        print(f"  CSV 2: {result.get('csv2_analysis', {}).get('detected_join_key', 'N/A')}")
        
        # Save analysis for inspection
        with open(f"uploads/{UPLOAD_ID}/analysis_result.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Saved to: uploads/{UPLOAD_ID}/analysis_result.json")
    else:
        print(f"✗ Analysis failed: {response.text}")
        return False
    return True

def merge_data():
    """Phase 3: Merge CSV data"""
    print("\n" + "=" * 60)
    print("PHASE 3: Merging CSV data...")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/api/merge",
        json={"upload_id": UPLOAD_ID}
    )
    
    print(f"Merge Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Merge complete")
        print(f"  Total products: {result.get('total_products', 0)}")
        print(f"  Matched (both CSVs): {result.get('matched', 0)}")
        print(f"  EDI only: {result.get('edi_only', 0)}")
    else:
        print(f"✗ Merge failed: {response.text}")
        return False
    return True

def link_images():
    """Phase 4: Link product images"""
    print("\n" + "=" * 60)
    print("PHASE 4: Linking product images...")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/api/images/link",
        json={
            "upload_id": UPLOAD_ID,
            "image_dir": "assets/bilder"
        }
    )
    
    print(f"Image Linking Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Image linking complete")
        print(f"  Total images: {result.get('total_images', 0)}")
        print(f"  Linked products: {result.get('linked_products', 0)}")
        print(f"  Unlinked products: {result.get('unlinked_products', 0)}")
    else:
        print(f"✗ Image linking failed: {response.text}")
        return False
    return True

def enhance_texts():
    """Phase 5: Enhance product texts with LLM"""
    print("\n" + "=" * 60)
    print("PHASE 5: Enhancing product texts (optional)...")
    print("=" * 60)
    print("⚠️  Skipping text enhancement (requires Anthropic API key)")
    print("   You can run it manually later if needed:")
    print(f"   POST {API_BASE}/api/texts/enhance")
    print(f'   {{"upload_id": "{UPLOAD_ID}", "batch_size": 30}}')
    return True

def main():
    print("\n" + "=" * 60)
    print("CATALOG GENERATION PIPELINE")
    print("=" * 60)
    print(f"Upload ID: {UPLOAD_ID}")
    print(f"API: {API_BASE}")
    print()
    
    # Run pipeline
    if not upload_files():
        return
    
    time.sleep(1)
    
    if not analyze_csvs():
        return
    
    time.sleep(1)
    
    if not merge_data():
        return
    
    time.sleep(1)
    
    if not link_images():
        return
    
    time.sleep(1)
    
    enhance_texts()
    
    print("\n" + "=" * 60)
    print("✓ PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"\nReview UI: http://localhost:8080/review.html?upload_id={UPLOAD_ID}")
    print(f"\nGenerate catalog:")
    print(f"  curl -X POST {API_BASE}/api/catalog/generate \\")
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"upload_id": "{UPLOAD_ID}"}}\'')
    print()

if __name__ == "__main__":
    main()
