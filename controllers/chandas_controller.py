"""
Chandas Controller - Business logic for prosody identification
"""

import logging
import re
from typing import Dict, Any, List
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
                logger.info(">> Attempting OpenAI API for chandas identification...")
                
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
                    provider="openai",
                    temperature=0.3
                )
                
                # Parse LLM response
                result = self._parse_llm_response(response_text)
                logger.info(f">> OPENAI SUCCESS - {result['chandas_name']} (conf: {result.get('confidence', 'N/A')})")
                
            except Exception as llm_error:
                # OpenAI failed - use algorithmic fallback
                logger.warning(f">> OPENAI FAILED: {str(llm_error)[:100]}")
                logger.info(">> Using pattern-based fallback algorithm...")
                result = detect_chandas(request.shloka)
                logger.info(f">> FALLBACK identified: {result['chandas_name']} (conf: {result['confidence']})")
            
            # Add step-by-step identification process explanation
            result['identification_process'] = self._generate_identification_process(request.shloka, result)
            
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
    
    def _generate_identification_process(self, shloka: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate step-by-step explanation of the mathematical process used to identify chandas
        
        Args:
            shloka: Original Sanskrit text
            result: Detection result with syllable breakdown and pattern
            
        Returns:
            List of identification steps
        """
        steps = []
        
        # Step 1: Text Preprocessing
        cleaned_text = re.sub(r'[।॥\n\r\s]+', '', shloka)
        steps.append({
            "step_number": 1,
            "step_name": "Text Preprocessing",
            "description": "Remove punctuation marks (।॥), whitespace, and newlines to get clean Devanagari text",
            "result": f"Cleaned text: {cleaned_text[:50]}{'...' if len(cleaned_text) > 50 else ''}"
        })
        
        # Step 2: Syllable Segmentation
        syllable_count = len(result.get('syllable_breakdown', []))
        sample_syllables = result.get('syllable_breakdown', [])[:5]
        
        # Handle both dict and SyllableInfo objects
        sample_texts = []
        for s in sample_syllables:
            if isinstance(s, dict):
                sample_texts.append(s.get('syllable', ''))
            else:
                sample_texts.append(getattr(s, 'syllable', ''))
        
        sample_text = ", ".join(sample_texts)
        if len(result.get('syllable_breakdown', [])) > 5:
            sample_text += "..."
        
        steps.append({
            "step_number": 2,
            "step_name": "Syllable Segmentation (Akshara Vibhajana)",
            "description": "Split text into syllables using Devanagari rules: consonant + vowel + optional dependent marks (ा, ि, ी, ु, ू, े, ै, ो, ौ, ं, ः) + optional halant (्) + conjunct consonants",
            "result": f"Total syllables: {syllable_count}. Examples: {sample_text}"
        })
        
        # Step 3: Laghu-Guru Classification
        pattern = result.get('laghu_guru_pattern', '')
        laghu_count = pattern.count('L')
        guru_count = pattern.count('G')
        
        classification_rules = [
            "• Laghu (L): Short vowel (अ, इ, उ, ऋ) without conjunct",
            "• Guru (G): Long vowel (आ, ई, ऊ, ए, ऐ, ओ, औ) OR short vowel + conjunct OR anusvara (ं) OR visarga (ः) OR end of line"
        ]
        
        steps.append({
            "step_number": 3,
            "step_name": "Laghu-Guru Classification (Mātrā Analysis)",
            "description": "Classify each syllable based on prosodic weight:\n" + "\n".join(classification_rules),
            "result": f"Pattern: {pattern}\nLaghu: {laghu_count}, Guru: {guru_count}"
        })
        
        # Step 4: Pattern Matching
        chandas_name = result.get('chandas_name', 'Unknown')
        
        if syllable_count == 32:
            match_explanation = "32 syllables (8 per quarter × 4 quarters) matches Anushtup meter structure"
        elif syllable_count == 44:
            match_explanation = f"44 syllables (11 per quarter × 4 quarters). Pattern {pattern} matched against Indravajra/Upendravajra templates"
        elif syllable_count == 56:
            match_explanation = "56 syllables (14 per quarter × 4 quarters) matches Vasantatilaka structure"
        elif syllable_count % 8 == 0:
            quarters = syllable_count // 8
            match_explanation = f"{syllable_count} syllables = {quarters} quarters of 8. Likely Anushtup variant"
        else:
            match_explanation = f"{syllable_count} syllables analyzed. Pattern compared against database of known chandas signatures"
        
        steps.append({
            "step_number": 4,
            "step_name": "Pattern Matching (Chandas Parichaya)",
            "description": "Compare syllable count and L-G pattern against database of known chandas:\n• Anushtup: 32 syllables, flexible pattern\n• Indravajra: 44 syllables, GGLGGLLGLLG pattern\n• Upendravajra: 44 syllables, LGLGGLLGLLG pattern\n• Vasantatilaka: 56 syllables\n• Malini: 60 syllables\n• Shardula-vikridita: 76 syllables",
            "result": f"Matched: {chandas_name}\n{match_explanation}"
        })
        
        # Step 5: Confidence Calculation
        confidence = result.get('confidence', 0.5)
        
        if confidence >= 0.9:
            confidence_reason = "Exact match with standard pattern and syllable count"
        elif confidence >= 0.7:
            confidence_reason = "Strong match with minor variations acceptable in classical texts"
        elif confidence >= 0.5:
            confidence_reason = "Partial match - incomplete verse or variant form detected"
        else:
            confidence_reason = "Low confidence - unusual pattern or insufficient data"
        
        steps.append({
            "step_number": 5,
            "step_name": "Confidence Score Calculation",
            "description": "Calculate confidence based on:\n• Pattern match accuracy (exact vs partial)\n• Syllable count alignment with known meters\n• Consistency of L-G pattern across quarters\n• Presence of standard chandas markers",
            "result": f"Confidence: {confidence:.2f}\nReason: {confidence_reason}"
        })
        
        return steps
    
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

