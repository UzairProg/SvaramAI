"""
Sanskrit syllable splitter and pattern analyzer
"""

import re
from typing import List, Tuple


class SanskritSplitter:
    """Split Sanskrit text into syllables and analyze patterns"""
    
    def __init__(self):
        """Initialize splitter with Sanskrit phonetic rules"""
        # Devanagari vowels (independent)
        self.vowels = set('अआइईउऊऋॠऌॡएऐओऔ')
        
        # Devanagari consonants
        self.consonants = set('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        
        # Vowel marks (dependent)
        self.vowel_marks = set('ािीुूृॄॢॣेैोौ')
        
        # Special marks
        self.anusvara = 'ं'
        self.visarga = 'ः'
        self.virama = '्'
        
        # Long vowels (Guru by nature)
        self.long_vowels = set('आईऊॠॡऐऔ')
        self.long_vowel_marks = set('ािीूृॄॢॣेैोौ')
    
    def split_syllables(self, text: str) -> List[str]:
        """
        Split Devanagari text into syllables
        
        Args:
            text: Devanagari Sanskrit text
            
        Returns:
            List of syllables
        """
        # Remove punctuation and spaces
        text = re.sub(r'[\s।॥]', '', text)
        
        syllables = []
        i = 0
        
        while i < len(text):
            syllable = ""
            
            # Start with vowel or consonant
            if text[i] in self.vowels:
                syllable = text[i]
                i += 1
            elif text[i] in self.consonants:
                syllable = text[i]
                i += 1
                
                # Add virama and following consonants (conjunct)
                while i < len(text) and text[i] == self.virama:
                    syllable += text[i]
                    i += 1
                    if i < len(text) and text[i] in self.consonants:
                        syllable += text[i]
                        i += 1
                
                # Add vowel mark if present
                if i < len(text) and text[i] in self.vowel_marks:
                    syllable += text[i]
                    i += 1
            else:
                # Skip unknown characters
                i += 1
                continue
            
            # Add anusvara or visarga if present
            if i < len(text) and text[i] in (self.anusvara, self.visarga):
                syllable += text[i]
                i += 1
            
            if syllable:
                syllables.append(syllable)
        
        return syllables
    
    def is_guru(self, syllable: str) -> bool:
        """
        Determine if a syllable is Guru (heavy)
        
        A syllable is Guru if:
        1. It has a long vowel
        2. It has anusvara or visarga
        3. It has conjunct consonants
        
        Args:
            syllable: Single syllable
            
        Returns:
            True if Guru, False if Laghu
        """
        # Check for long vowels
        if any(v in syllable for v in self.long_vowels):
            return True
        
        if any(v in syllable for v in self.long_vowel_marks):
            return True
        
        # Check for anusvara or visarga
        if self.anusvara in syllable or self.visarga in syllable:
            return True
        
        # Check for conjunct consonants (virama present)
        if self.virama in syllable:
            return True
        
        return False
    
    def get_pattern(self, text: str) -> str:
        """
        Get Laghu-Guru pattern for text
        
        Args:
            text: Devanagari Sanskrit text
            
        Returns:
            Pattern string (L for Laghu, G for Guru)
        """
        syllables = self.split_syllables(text)
        pattern = []
        
        for syllable in syllables:
            if self.is_guru(syllable):
                pattern.append('G')
            else:
                pattern.append('L')
        
        return ''.join(pattern)
    
    def get_syllable_info(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Get detailed syllable information
        
        Args:
            text: Devanagari Sanskrit text
            
        Returns:
            List of tuples: (syllable, type, position)
        """
        syllables = self.split_syllables(text)
        info = []
        
        for idx, syllable in enumerate(syllables, start=1):
            syllable_type = "guru" if self.is_guru(syllable) else "laghu"
            info.append((syllable, syllable_type, idx))
        
        return info
    
    def identify_meter_from_pattern(self, pattern: str) -> Tuple[str, float]:
        """
        Identify chandas from Laghu-Guru pattern
        
        Args:
            pattern: L/G pattern string
            
        Returns:
            Tuple of (meter_name, confidence)
        """
        pattern_len = len(pattern)
        
        # Common meter patterns
        meters = {
            "Anushtup": {
                "syllables": 32,
                "per_quarter": 8,
                "pattern": None,  # Flexible
                "rule": "5th syllable should be Laghu"
            },
            "Indravajra": {
                "syllables": 44,
                "per_quarter": 11,
                "pattern": "GGLGGLLGLLG",
                "rule": "Fixed pattern"
            },
            "Upendravajra": {
                "syllables": 44,
                "per_quarter": 11,
                "pattern": "LGLGGLLGLLG",
                "rule": "Fixed pattern"
            },
            "Vasantatilaka": {
                "syllables": 56,
                "per_quarter": 14,
                "pattern": "GGLGLLGLGLGLLG",
                "rule": "Fixed pattern"
            },
            "Malini": {
                "syllables": 60,
                "per_quarter": 15,
                "pattern": "LLGLLGGLGGLGLLG",
                "rule": "Fixed pattern"
            }
        }
        
        # Check for matches
        for meter_name, meter_info in meters.items():
            if pattern_len == meter_info["syllables"]:
                if meter_info["pattern"]:
                    # Check if pattern matches (repeated per quarter)
                    quarter_pattern = meter_info["pattern"]
                    expected_pattern = quarter_pattern * 4
                    
                    if pattern == expected_pattern:
                        return (meter_name, 1.0)
                    
                    # Check partial match
                    matches = sum(1 for a, b in zip(pattern, expected_pattern) if a == b)
                    confidence = matches / len(expected_pattern)
                    
                    if confidence > 0.8:
                        return (meter_name, confidence)
                else:
                    # Anushtup - check 5th syllable rule
                    if pattern_len == 32:
                        # Split into quarters
                        quarters = [pattern[i:i+8] for i in range(0, 32, 8)]
                        fifth_laghu_count = sum(1 for q in quarters if len(q) > 4 and q[4] == 'L')
                        
                        if fifth_laghu_count >= 3:
                            return ("Anushtup", 0.9)
                        else:
                            return ("Anushtup", 0.6)
        
        return ("Unknown", 0.0)


# Singleton instance
_splitter = None


def get_splitter() -> SanskritSplitter:
    """Get or create splitter singleton"""
    global _splitter
    if _splitter is None:
        _splitter = SanskritSplitter()
    return _splitter
