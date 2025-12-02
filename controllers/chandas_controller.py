"""
Chandas Controller - Business logic for prosody identification
"""

import logging
import re
from typing import Dict, Any
import json

from models import ChandasIdentifyRequest, ChandasIdentifyResponse, SyllableInfo
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings
from utils.chandas_patterns import detect_chandas

logger = logging.getLogger(__name__)
settings = get_settings()


class ChandasController:
    """Controller for chandas identification operations"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load chandas system prompt"""
        try:
            with open("prompts/chandas_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback system prompt
            return """You are an expert in Sanskrit prosody. Analyze syllable patterns (Laghu=short, Guru=long) to identify the meter. Return JSON: chandas_name, syllable_breakdown (array), laghu_guru_pattern, explanation, confidence."""
    
    async def identify_chandas(self, request: ChandasIdentifyRequest) -> ChandasIdentifyResponse:
        """
        Identify chandas from Sanskrit shloka with automatic fallback to pattern-based detection
        
        Args:
            request: Chandas identification request
            
        Returns:
            ChandasIdentifyResponse with identified meter
        """
        try:
            logger.info(f"Identifying chandas for shloka")
            
            # Try LLM first with proper prompt
            try:
                logger.info(">> Attempting Groq API for chandas identification...")
                
                # Use system prompt for better results
                messages = [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this Sanskrit shloka and identify its meter:\n\n{request.shloka}\n\nReturn ONLY valid JSON with the required fields."
                    }
                ]
                
                response_text = await self.llm_client.chat_completion(
                    messages=messages,
                    provider="groq",
                    temperature=0.3
                )
                
                # Parse LLM response
                result = self._parse_llm_response(response_text)
                logger.info(f">> GROQ SUCCESS - {result['chandas_name']} (conf: {result.get('confidence', 'N/A')})")
                
            except Exception as llm_error:
                # Groq failed - use algorithmic fallback
                logger.warning(f">> GROQ FAILED: {str(llm_error)[:100]}")
                logger.info(">> Using pattern-based fallback algorithm...")
                result = detect_chandas(request.shloka)
                logger.info(f">> FALLBACK identified: {result['chandas_name']} (conf: {result['confidence']})")
            
            return ChandasIdentifyResponse(**result)
            
        except Exception as e:
            logger.error(f"Chandas identification failed: {str(e)}")
            raise
    
    async def _get_chandas_context(self) -> str:
        """Get relevant context from knowledge base"""
        try:
            # In production, you'd search with actual embeddings
            # For now, return basic context
            context = """
Common Sanskrit Meters:
1. Anushtup: 32 syllables (8 per quarter), most common in epics
2. Indravajra: 44 syllables (11 per quarter), pattern: GGLGGLLGLLG
3. Upendravajra: 44 syllables, pattern: LGLGGLLGLLG
4. Vasantatilaka: 56 syllables (14 per quarter)
5. Malini: 60 syllables (15 per quarter)
6. Shardula-vikridita: 76 syllables (19 per quarter)

Laghu (L): Short syllable - single mÄtrÄ
Guru (G): Long syllable - two mÄtrÄs
"""
            return context
        except Exception as e:
            logger.warning(f"Failed to get context: {str(e)}")
            return ""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to extract structured data"""
        try:
            # Try to extract JSON from various formats
            json_str = response_text.strip()
            
            # Remove markdown code blocks
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Find JSON object in text (look for { ... })
            if not json_str.startswith("{"):
                import re
                json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            data = json.loads(json_str)
            
            # Ensure syllable_breakdown is list of SyllableInfo
            if "syllable_breakdown" in data and data["syllable_breakdown"]:
                data["syllable_breakdown"] = [
                    SyllableInfo(**item) if isinstance(item, dict) else item
                    for item in data["syllable_breakdown"]
                ]
            
            # Set defaults if missing
            data.setdefault("chandas_name", "Unknown")
            data.setdefault("laghu_guru_pattern", "")
            data.setdefault("explanation", "")
            data.setdefault("confidence", 0.5)
            data.setdefault("syllable_breakdown", [])
            
            # If syllable_breakdown is empty, try to use fallback
            if not data["syllable_breakdown"]:
                logger.warning("LLM returned empty syllable_breakdown, using fallback")
                fallback_result = detect_chandas(response_text)
                data["syllable_breakdown"] = fallback_result.get("syllable_breakdown", [])
                data["laghu_guru_pattern"] = fallback_result.get("laghu_guru_pattern", "")
            
            return data
            
        except Exception as e:
            logger.warning(f"Failed to parse as JSON: {str(e)}, treating as plain text")
            # Extract meter name from plain text response
            meter_name = response_text.strip().split('\n')[0] if response_text else "Unknown"
            # Clean up common patterns
            for prefix in ["The meter is", "Meter:", "Chandas:", "This is"]:
                if meter_name.startswith(prefix):
                    meter_name = meter_name.replace(prefix, "").strip()
            
            return {
                "chandas_name": meter_name,
                "syllable_breakdown": [],
                "laghu_guru_pattern": "",
                "explanation": response_text,
                "confidence": 0.7
            }


# Singleton instance
_chandas_controller: ChandasController = None


def get_chandas_controller() -> ChandasController:
    """Get or create chandas controller singleton"""
    global _chandas_controller
    
    if _chandas_controller is None:
        _chandas_controller = ChandasController()
    
    return _chandas_controller

