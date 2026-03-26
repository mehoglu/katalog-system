"""
Encoding detection and conversion service
Addresses Critical Pitfall #3: German encoding corruption
"""
from pathlib import Path
from charset_normalizer import from_bytes
from dataclasses import dataclass
from typing import Optional

@dataclass
class EncodingResult:
    """Ergebnis der Encoding-Erkennung"""
    detected_encoding: str
    confidence: float
    is_fallback: bool  # True wenn Fallback zu Windows-1252
    needs_confirmation: bool  # True wenn confidence < 70%

def detect_encoding(file_path: Path) -> EncodingResult:
    """
    Erkennt CSV-Encoding automatisch
    
    CONTEXT D-17: Server-seitige Erkennung
    CONTEXT D-18: charset-normalizer statt chardet
    CONTEXT D-20: Windows-1252 Fallback für deutsche CSVs
    
    Args:
        file_path: Pfad zur CSV-Datei
        
    Returns:
        EncodingResult mit detected_encoding und confidence
    """
    # Read raw bytes
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    # Detect encoding with charset-normalizer
    results = from_bytes(raw_data)
    best_match = results.best()
    
    if best_match and best_match.encoding:
        confidence = float(best_match.coherence)  # charset_normalizer uses coherence (0-1)
        detected = best_match.encoding
        
        # RESEARCH: High confidence threshold for German text
        if confidence > 0.7:
            return EncodingResult(
                detected_encoding=detected,
                confidence=confidence,
                is_fallback=False,
                needs_confirmation=False
            )
        else:
            # Low confidence - needs user confirmation (CONTEXT D-19)
            return EncodingResult(
                detected_encoding=detected,
                confidence=confidence,
                is_fallback=False,
                needs_confirmation=True
            )
    
    # Detection failed - fallback to Windows-1252 (CONTEXT D-20)
    return EncodingResult(
        detected_encoding="windows-1252",
        confidence=0.0,
        is_fallback=True,
        needs_confirmation=True  # Always confirm fallback
    )

def convert_to_utf8(
    input_path: Path,
    output_path: Path,
    source_encoding: str
) -> tuple[bool, Optional[str]]:
    """
    Konvertiert CSV von source_encoding nach UTF-8
    
    Args:
        input_path: Original CSV
        output_path: UTF-8 konvertierte Datei
        source_encoding: Quell-Encoding (z.B. "windows-1252")
        
    Returns:
        (success: bool, error_message: Optional[str])
    """
    try:
        # Read with source encoding
        with open(input_path, 'r', encoding=source_encoding, errors='replace') as f:
            content = f.read()
        
        # Write as UTF-8
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Validate umlauts (RESEARCH: check for common German characters)
        if validate_german_umlauts(output_path):
            return True, None
        else:
            return False, "Conversion produced mojibake - umlauts corrupted"
            
    except UnicodeDecodeError as e:
        return False, f"Failed to decode with {source_encoding}: {str(e)}"
    except Exception as e:
        return False, f"Conversion error: {str(e)}"

def validate_german_umlauts(file_path: Path, sample_lines: int = 10) -> bool:
    """
    Prüft ob deutsche Umlaute korrekt sind (kein Mojibake)
    
    Args:
        file_path: UTF-8 Datei zum Prüfen
        sample_lines: Anzahl Zeilen zum Samplen
        
    Returns:
        True wenn Umlaute korrekt, False bei Mojibake
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = ''.join([f.readline() for _ in range(sample_lines)])
        
        # Check for mojibake patterns that indicate wrong encoding
        mojibake_patterns = [
            'Ã¤',  # ä encoded as Windows-1252 read as UTF-8
            'Ã¶',  # ö
            'Ã¼',  # ü
            'ÃŸ',  # ß
            'Ã\x84',  # Ä
            'Ã\x96',  # Ö
            'Ã\x9c',  # Ü
        ]
        
        for pattern in mojibake_patterns:
            if pattern in sample:
                return False  # Mojibake detected
        
        return True  # Looks good
        
    except Exception:
        return False  # If we can't read, assume bad encoding
