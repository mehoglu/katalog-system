"""
Text enhancement service using Anthropic Claude.

Implements Phase 5 German text enhancement with batch processing
and technical term preservation (TEXT-01 through TEXT-04).
"""
import json
import re
import time
from pathlib import Path
from typing import Union, Dict, List, Any, Optional
from anthropic import Anthropic, AnthropicError

from app.core.config import settings
from app.models.text_enhancement import EnhancementResult


# System prompt for German text enhancement (D-01 through D-10 from CONTEXT)
ENHANCEMENT_PROMPT = """You are enhancing German product catalog texts.

Rules:
- Improve readability and professionalism
- Preserve ALL measurements (mm, kg, Stück, etc.) exactly
- Preserve ALL technical codes (VE, KLS, WS, TL, etc.)
- Expand abbreviations but keep originals in context
- Fix capitalization and punctuation
- Do NOT hallucinate or invent details not in original
- Return JSON array matching input structure exactly

Example:
Input: "VERSANDTASCHE AUS WELLPAPPE CD, 145x190x-25mm"
Output: "Versandtasche aus Wellpappe für CDs (145×190×25 mm)"

Changes: Capitalization, punctuation, readability
Preserved: All measurements, technical information
"""


def get_anthropic_client() -> Anthropic:
    """Get configured Anthropic client."""
    return Anthropic(api_key=settings.anthropic_api_key)


def extract_critical_terms(text: str) -> set:
    """
    Extract measurements and technical codes for quality checking.
    
    Implements D-07 through D-09 preservation rules from CONTEXT.
    """
    if not text:
        return set()
    
    critical_terms = set()
    
    # Measurements: numbers with units (145mm, 2.5kg, 25 Stück)
    measurements = re.findall(r'\d+[.,]?\d*\s*(?:mm|cm|m|kg|g|Stück|St\.|°C)', text, re.IGNORECASE)
    critical_terms.update(m.lower().replace(' ', '') for m in measurements)
    
    # Technical codes (VE, KLS, WS, TL, EAN, etc.)
    tech_codes = re.findall(r'\b(?:VE|KLS|WS|TL|EAN|Art\.?Nr\.?|PE|braun|weiß|schwarz)\b', text, re.IGNORECASE)
    critical_terms.update(c.lower() for c in tech_codes)
    
    # Artikelnummer references (210100125)
    art_nums = re.findall(r'\b\d{9,}\b', text)
    critical_terms.update(art_nums)
    
    return critical_terms


def quality_check_preservation(original: str, enhanced: str) -> bool:
    """
    Verify enhanced text preserves all critical terms from original.
    
    Implements D-10 from CONTEXT: quality check requirement.
    Returns True if all critical terms preserved, False otherwise.
    """
    original_terms = extract_critical_terms(original)
    enhanced_terms = extract_critical_terms(enhanced)
    
    # All original critical terms must appear in enhanced text
    missing_terms = original_terms - enhanced_terms
    
    if missing_terms:
        return False
    
    return True


async def enhance_product_texts(
    merged_products_path: Union[str, Path],
    batch_size: int = 30
) -> EnhancementResult:
    """
    Enhance German product texts using LLM with batch processing.
    
    Implements TEXT-01 through TEXT-04 requirements:
    - TEXT-01: Enhances Bezeichnung1
    - TEXT-02: Enhances Bezeichnung2  
    - TEXT-03: Preserves technical terms via quality checks
    - TEXT-04: Batch processing for cost optimization
    
    Args:
        merged_products_path: Path to merged_products.json from Phase 3
        batch_size: Products per batch (default 30, range 20-50)
        
    Returns:
        EnhancementResult with processing statistics
        
    Raises:
        FileNotFoundError: If merged_products.json missing
        ValueError: If JSON structure invalid
    """
    start_time = time.time()
    
    # Load products (D-11: read merged_products.json)
    merged_products_path = Path(merged_products_path)
    if not merged_products_path.exists():
        raise FileNotFoundError(f"merged_products.json not found: {merged_products_path}")
    
    with open(merged_products_path, "r", encoding="utf-8") as f:
        merged_file = json.load(f)
    
    # Handle wrapper format from Phase 3 (same as image linking)
    if isinstance(merged_file, dict) and "products" in merged_file:
        products = merged_file["products"]
        metadata = {k: v for k, v in merged_file.items() if k != "products"}
    else:
        products = merged_file
        metadata = {}
    
    # Initialize Anthropic client
    client = get_anthropic_client()
    
    # Track statistics
    total_products = len(products)
    enhanced_count = 0
    skipped_count = 0
    
    # Process in batches (D-12: batch processing)
    for batch_start in range(0, total_products, batch_size):
        batch_end = min(batch_start + batch_size, total_products)
        batch = products[batch_start:batch_end]
        
        # Skip products without bezeichnung1 (D-14: error handling)
        valid_batch = []
        for product in batch:
            if not product.get("data", {}).get("bezeichnung1"):
                skipped_count += 1
                continue
            valid_batch.append(product)
        
        if not valid_batch:
            continue
        
        # Build batch request for Claude
        batch_input = []
        for product in valid_batch:
            batch_input.append({
                "artikelnummer": product["artikelnummer"],
                "bezeichnung1": product["data"].get("bezeichnung1", ""),
                "bezeichnung2": product["data"].get("bezeichnung2", "")
            })
        
        try:
            # Call Claude for batch enhancement
            response = client.messages.create(
                model=settings.anthropic_model_fallback,  # Use Sonnet for quality
                max_tokens=4096,
                temperature=0.3,
                system=ENHANCEMENT_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Enhance these {len(batch_input)} German product texts:\n\n{json.dumps(batch_input, ensure_ascii=False, indent=2)}\n\nReturn enhanced texts as JSON array with same structure."
                }]
            )
            
            # Extract enhanced texts from response
            response_text = response.content[0].text
            
            # Try to extract JSON from response (Claude sometimes adds markdown)
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                enhanced_batch = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire response
                enhanced_batch = json.loads(response_text)
            
            # Update products with enhanced texts and perform quality checks
            for i, enhanced_item in enumerate(enhanced_batch):
                if i >= len(valid_batch):
                    break
                
                product = valid_batch[i]
                original_b1 = product["data"].get("bezeichnung1", "")
                enhanced_b1 = enhanced_item.get("bezeichnung1", "")
                
                # Quality check for Bezeichnung1 (D-10)
                if quality_check_preservation(original_b1, enhanced_b1):
                    product["data"]["bezeichnung1_enhanced"] = enhanced_b1
                    product["sources"]["bezeichnung1_enhanced"] = "llm_enhancement"
                    enhanced_count += 1
                else:
                    # Failed quality check - keep original
                    product["data"]["bezeichnung1_enhanced"] = original_b1
                    product["sources"]["bezeichnung1_enhanced"] = None
                    skipped_count += 1
                
                # Handle Bezeichnung2 if present
                if product["data"].get("bezeichnung2") and enhanced_item.get("bezeichnung2"):
                    original_b2 = product["data"]["bezeichnung2"]
                    enhanced_b2 = enhanced_item["bezeichnung2"]
                    
                    if quality_check_preservation(original_b2, enhanced_b2):
                        product["data"]["bezeichnung2_enhanced"] = enhanced_b2
                        product["sources"]["bezeichnung2_enhanced"] = "llm_enhancement"
                    else:
                        product["data"]["bezeichnung2_enhanced"] = original_b2
                        product["sources"]["bezeichnung2_enhanced"] = None
        
        except (AnthropicError, json.JSONDecodeError) as e:
            # D-14: Continue batch on errors, log skipped products
            print(f"Error processing batch {batch_start}-{batch_end}: {e}")
            skipped_count += len(valid_batch)
            continue
    
    # Save updated products (preserve wrapper structure)
    if metadata:
        output_data = {**metadata, "products": products}
    else:
        output_data = products
    
    with open(merged_products_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    processing_time = time.time() - start_time
    
    return EnhancementResult(
        total_products=total_products,
        enhanced_count=enhanced_count,
        skipped_count=skipped_count,
        processing_time=processing_time
    )
