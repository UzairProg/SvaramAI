"""
Chandas identification service using stuti-chandas library
"""
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ChandasService:
    """Service for identifying Sanskrit chandas using stuti-chandas library"""
    
    @staticmethod
    def identify_metre(verse: str) -> Dict[str, Any]:
        """
        Identify the metre of a Sanskrit verse using stuti-chandas library
        
        Args:
            verse: Sanskrit verse text
            
        Returns:
            Dictionary with metre information including name, scheme, and confidence
        """
        try:
            from stuti.chandas import identify_metre
            
            # Clean the verse
            cleaned_verse = verse.strip()
            
            # Identify metre using stuti library
            result = identify_metre(cleaned_verse)
            
            # Extract information
            if result:
                metre_info = {
                    "metre": result.get("name", "Unknown"),
                    "scheme": result.get("pattern", ""),
                    "laghu_guru_pattern": result.get("laghu_guru", ""),
                    "confidence": result.get("confidence", 0.0),
                    "syllable_count": result.get("syllable_count", []),
                    "gana_pattern": result.get("gana", ""),
                    "detected": True
                }
                logger.info(f"Metre identified: {metre_info['metre']}")
                return metre_info
            else:
                logger.warning("Metre identification returned no result")
                return {
                    "metre": "Unknown",
                    "scheme": "",
                    "laghu_guru_pattern": "",
                    "confidence": 0.0,
                    "syllable_count": [],
                    "gana_pattern": "",
                    "detected": False
                }
                
        except ImportError:
            logger.error("stuti-chandas library not installed")
            return {
                "metre": "Error",
                "scheme": "",
                "laghu_guru_pattern": "",
                "confidence": 0.0,
                "syllable_count": [],
                "gana_pattern": "",
                "detected": False,
                "error": "stuti-chandas library not available"
            }
        except Exception as e:
            logger.error(f"Error identifying metre: {str(e)}")
            return {
                "metre": "Error",
                "scheme": "",
                "laghu_guru_pattern": "",
                "confidence": 0.0,
                "syllable_count": [],
                "gana_pattern": "",
                "detected": False,
                "error": str(e)
            }
