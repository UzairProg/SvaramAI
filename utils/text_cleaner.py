"""
Text cleaning utilities for Sanskrit processing
"""

import re


def remove_diacritics(text: str) -> str:
    """
    Remove diacritical marks from romanized Sanskrit
    
    Args:
        text: Romanized Sanskrit text with diacritics
        
    Returns:
        Text without diacritics
    """
    replacements = {
        'ā': 'a', 'ī': 'i', 'ū': 'u',
        'ṛ': 'r', 'ṝ': 'r', 'ḷ': 'l', 'ḹ': 'l',
        'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n',
        'ṭ': 't', 'ḍ': 'd',
        'ś': 's', 'ṣ': 's',
        'ṃ': 'm', 'ḥ': 'h',
        'Ā': 'A', 'Ī': 'I', 'Ū': 'U',
        'Ṛ': 'R', 'Ṝ': 'R', 'Ḷ': 'L', 'Ḹ': 'L',
        'Ṅ': 'N', 'Ñ': 'N', 'Ṇ': 'N',
        'Ṭ': 'T', 'Ḍ': 'D',
        'Ś': 'S', 'Ṣ': 'S',
        'Ṃ': 'M', 'Ḥ': 'H'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def clean_devanagari(text: str) -> str:
    """
    Clean Devanagari text by removing extra spaces and normalizing
    
    Args:
        text: Devanagari text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove spaces around danda (।) and double danda (॥)
    text = re.sub(r'\s*।\s*', '।', text)
    text = re.sub(r'\s*॥\s*', '॥', text)
    
    # Trim
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Trim each line
    text = '\n'.join(line.strip() for line in text.split('\n'))
    
    return text.strip()


def extract_devanagari(text: str) -> str:
    """
    Extract only Devanagari characters from text
    
    Args:
        text: Mixed text
        
    Returns:
        Only Devanagari characters
    """
    # Devanagari Unicode range: 0900-097F
    devanagari_pattern = r'[\u0900-\u097F\s।॥]+'
    matches = re.findall(devanagari_pattern, text)
    return ''.join(matches).strip()


def split_verses(text: str) -> list:
    """
    Split text into individual verses using danda markers
    
    Args:
        text: Sanskrit text with multiple verses
        
    Returns:
        List of individual verses
    """
    # Split on double danda
    verses = re.split(r'॥', text)
    
    # Clean each verse
    verses = [clean_devanagari(v) for v in verses if v.strip()]
    
    return verses


def is_devanagari(text: str) -> bool:
    """
    Check if text contains Devanagari script
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains Devanagari characters
    """
    devanagari_pattern = r'[\u0900-\u097F]'
    return bool(re.search(devanagari_pattern, text))


def count_syllables_approximate(text: str) -> int:
    """
    Approximate syllable count for Devanagari text
    
    Args:
        text: Devanagari text
        
    Returns:
        Approximate syllable count
    """
    # Remove spaces and punctuation
    text = re.sub(r'[\s।॥]', '', text)
    
    # Count vowel marks and independent vowels as syllables
    # This is a rough approximation
    vowels = 'अआइईउऊऋॠऌॡएऐओऔ'
    vowel_marks = 'ािीुूृॄॢॣेैोौ'
    
    count = 0
    for char in text:
        if char in vowels or char in vowel_marks:
            count += 1
    
    # Each consonant without explicit vowel has implicit 'a'
    consonants = 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'
    for char in text:
        if char in consonants:
            # Check if next char is a vowel mark or virama
            count += 1
    
    return count


def romanize_basic(devanagari_text: str) -> str:
    """
    Basic romanization of Devanagari (IAST-like)
    
    Args:
        devanagari_text: Devanagari text
        
    Returns:
        Romanized text
    """
    romanization = {
        'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī',
        'उ': 'u', 'ऊ': 'ū', 'ऋ': 'ṛ', 'ॠ': 'ṝ',
        'ऌ': 'ḷ', 'ॡ': 'ḹ', 'ए': 'e', 'ऐ': 'ai',
        'ओ': 'o', 'औ': 'au',
        'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'ṅa',
        'च': 'ca', 'छ': 'cha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'ña',
        'ट': 'ṭa', 'ठ': 'ṭha', 'ड': 'ḍa', 'ढ': 'ḍha', 'ण': 'ṇa',
        'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
        'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
        'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
        'श': 'śa', 'ष': 'ṣa', 'स': 'sa', 'ह': 'ha',
        'ं': 'ṃ', 'ः': 'ḥ', '्': '', '॥': '||', '।': '|'
    }
    
    result = []
    for char in devanagari_text:
        if char in romanization:
            result.append(romanization[char])
        else:
            result.append(char)
    
    return ''.join(result)
