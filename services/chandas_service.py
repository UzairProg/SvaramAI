"""
Chandas identification service with multiple fallback strategies
"""
import logging
from typing import Dict, Optional, Any
import os
import sys

logger = logging.getLogger(__name__)


class ChandasService:
    """Service for identifying Sanskrit chandas"""
    
    _chanda_instance = None
    
    @classmethod
    def _get_chanda_instance(cls):
        """Get or create singleton instance of Chandojñānam"""
        if cls._chanda_instance is None:
            try:
                # Add chanda_lib to path
                chanda_lib_path = os.path.join(os.path.dirname(__file__), '..', 'chanda_lib')
                if os.path.exists(chanda_lib_path) and chanda_lib_path not in sys.path:
                    sys.path.insert(0, chanda_lib_path)
                
                from chanda import Chanda
                data_path = os.path.join(chanda_lib_path, 'data')
                cls._chanda_instance = Chanda(data_path)
                logger.info("Chandojñānam initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Chandojñānam: {e}")
                cls._chanda_instance = False  # Mark as unavailable
        
        return cls._chanda_instance if cls._chanda_instance is not False else None
    
    @staticmethod
    def identify_metre(verse: str) -> Dict[str, Any]:
        """
        Identify the metre of a Sanskrit verse using available libraries
        
        Tries multiple strategies:
        1. Chandojñānam (local chanda_lib)
        2. stuti-chandas library
        3. Returns "Unknown" with low confidence
        
        Args:
            verse: Sanskrit verse text
            
        Returns:
            Dictionary with metre information including name, scheme, and confidence
        """
        cleaned_verse = verse.strip() if verse else ""
        
        if not cleaned_verse:
            return {
                "metre": "Unknown",
                "scheme": "",
                "laghu_guru_pattern": "",
                "confidence": 0.0,
                "syllable_count": [],
                "gana_pattern": "",
                "detected": False
            }
        
        # Try Chandojñānam first
        try:
            chanda = ChandasService._get_chanda_instance()
            
            if chanda:
                # Try identify_line for first line
                lines = cleaned_verse.split('\n')
                if lines:
                    first_line = lines[0].strip()
                    if first_line:
                        try:
                            result = chanda.identify_line(first_line)
                            
                            if result and result.get('found'):
                                chanda_list = result.get('chanda', [])
                                if chanda_list:
                                    metre_name = str(chanda_list[0])
                                    confidence = 0.85
                                    
                                    metre_info = {
                                        "metre": metre_name,
                                        "scheme": "",
                                        "laghu_guru_pattern": result.get('lg_str', ''),
                                        "confidence": confidence,
                                        "syllable_count": [],
                                        "gana_pattern": "",
                                        "detected": True
                                    }
                                    logger.info(f"Metre identified using Chandojñānam: {metre_name}")
                                    return metre_info
                        except Exception as e:
                            logger.debug(f"Chandojñānam identify_line failed: {e}")
        except Exception as e:
            logger.debug(f"Chandojñānam error: {e}")
        
        # Try stuti-chandas library as fallback
        try:
            from stuti.chandas import identify_metre
            
            result = identify_metre(cleaned_verse)
            
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
                logger.info(f"Metre identified using stuti-chandas: {metre_info['metre']}")
                return metre_info
                
        except ImportError:
            logger.debug("stuti-chandas library not installed")
        except Exception as e:
            logger.debug(f"stuti-chandas error: {e}")
        
        # Return Unknown with low confidence
        logger.warning("Could not identify metre - returning Unknown")
        return {
            "metre": "Unknown",
            "scheme": "",
            "laghu_guru_pattern": "",
            "confidence": 0.0,
            "syllable_count": [],
            "gana_pattern": "",
            "detected": False
        }
