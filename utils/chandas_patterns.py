"""
Chandas pattern detection without LLM - pure algorithmic approach.
"""
import re
from typing import Dict, List, Tuple, Any


# Syllable patterns for common meters
CHANDAS_PATTERNS = {
    "Anushtup": {
        "syllables_per_line": 8,
        "total_syllables": 32,
        "pattern": None,  # Flexible pattern
        "description": "Most common meter in Sanskrit poetry, 8 syllables per quarter"
    },
    "Indravajra": {
        "syllables_per_line": 11,
        "total_syllables": 44,
        "pattern": "GGLGGLLGLLG",
        "description": "11 syllables per quarter with specific pattern"
    },
    "Upendravajra": {
        "syllables_per_line": 11,
        "total_syllables": 44,
        "pattern": "LGLGGLLGLLG",
        "description": "11 syllables per quarter, variant of Indravajra"
    },
    "Vasantatilaka": {
        "syllables_per_line": 14,
        "total_syllables": 56,
        "pattern": "GGLGLLGLGLGLLG",
        "description": "14 syllables per quarter, spring-like rhythm"
    },
    "Malini": {
        "syllables_per_line": 15,
        "total_syllables": 60,
        "pattern": "LLGLLGGLGGLGLLG",
        "description": "15 syllables per quarter"
    },
    "Shardula-vikridita": {
        "syllables_per_line": 19,
        "total_syllables": 76,
        "pattern": "GGGGLGGLLGLLLGLLG",
        "description": "19 syllables per quarter, complex meter"
    }
}


def split_into_syllables(text: str) -> List[str]:
    """Split Sanskrit text into syllables with improved handling."""
    # Remove punctuation, newlines, and normalize
    text = re.sub(r'[।॥\n\r\s]+', '', text)
    
    syllables = []
    i = 0
    
    while i < len(text):
        syllable = text[i]
        i += 1
        
        # Handle dependent vowel signs
        while i < len(text) and text[i] in 'ािीुूृॄेैोौंः':
            syllable += text[i]
            i += 1
        
        # Handle halant/virama (्) and following consonant cluster
        while i < len(text) and text[i] == '्':
            syllable += text[i]
            i += 1
            if i < len(text) and text[i] not in 'ािीुूृॄेैोौंः।॥':
                syllable += text[i]
                i += 1
        
        if syllable:  # Only add non-empty syllables
            syllables.append(syllable)
    
    return syllables


def classify_syllable(syllable: str, is_line_end: bool = False) -> str:
    """
    Classify syllable as Laghu (L) or Guru (G).
    
    Rules:
    - Laghu: short vowel + single consonant
    - Guru: long vowel OR short vowel + conjunct OR end of line
    """
    if is_line_end:
        return "G"
    
    # Long vowels
    long_vowels = ['आ', 'ई', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ', 'ा', 'ी', 'ू', 'े', 'ै', 'ो', 'ौ']
    for v in long_vowels:
        if v in syllable:
            return "G"
    
    # Conjunct consonants (halant present)
    if '्' in syllable:
        return "G"
    
    # Anusvara or Visarga
    if 'ं' in syllable or 'ः' in syllable:
        return "G"
    
    # Default: Laghu for short vowels
    return "L"


def detect_chandas(text: str) -> Dict[str, Any]:
    """
    Detect chandas from Sanskrit text using pattern matching.
    
    Returns:
        Dict with chandas_name, syllable_breakdown, pattern, explanation, confidence
    """
    # Split into syllables
    syllables = split_into_syllables(text)
    total_syllables = len(syllables)
    
    # Classify each syllable
    syllable_breakdown = []
    pattern_str = ""
    
    for i, syl in enumerate(syllables):
        is_end = (i == len(syllables) - 1)
        classification = classify_syllable(syl, is_end)
        pattern_str += classification
        
        syllable_breakdown.append({
            "syllable": syl,
            "type": classification.lower(),
            "position": i + 1
        })
    
    # Match against known patterns
    best_match = None
    best_confidence = 0.0
    
    for chandas_name, info in CHANDAS_PATTERNS.items():
        # Check syllable count
        if info["total_syllables"] == total_syllables:
            if info["pattern"] is None:
                # Anushtup - flexible pattern
                best_match = chandas_name
                best_confidence = 0.85
                break
            elif info["pattern"] in pattern_str or pattern_str in info["pattern"]:
                # Pattern matches
                best_match = chandas_name
                best_confidence = 0.95
                break
    
    # Special handling for partial verses or Anushtup
    if best_match is None:
        # Check if it's a quarter of Anushtup (8 syllables)
        if total_syllables == 8:
            best_match = "Anushtup (single quarter detected)"
            best_confidence = 0.75
            explanation = "8 syllables detected - appears to be one quarter of Anushtup meter"
        # Check if multiple of 8 (likely Anushtup)
        elif total_syllables % 8 == 0:
            quarters = total_syllables // 8
            best_match = f"Anushtup ({quarters}/4 quarters)"
            best_confidence = 0.70
            explanation = f"{total_syllables} syllables ({quarters} quarters of 8) - Anushtup pattern"
        # Other cases
        else:
            syllables_per_line = total_syllables // 4 if total_syllables % 4 == 0 else 0
            if syllables_per_line > 0:
                best_match = f"Unknown ({syllables_per_line} syl/quarter)"
                best_confidence = 0.5
                explanation = f"{total_syllables} total syllables, {syllables_per_line} per quarter"
            else:
                best_match = "Unknown"
                best_confidence = 0.3
                explanation = f"Detected {total_syllables} syllables - no standard pattern match"
    else:
        explanation = CHANDAS_PATTERNS.get(best_match, {}).get(
            "description",
            f"Detected {total_syllables} total syllables"
        )
    
    return {
        "chandas_name": best_match,
        "syllable_breakdown": syllable_breakdown,
        "laghu_guru_pattern": pattern_str,
        "explanation": explanation,
        "confidence": best_confidence
    }
