"""
Meaning Controller - Business logic for Sanskrit translation and meaning extraction
"""

import logging
import json
from typing import Dict, Any

from models import MeaningRequest, MeaningResponse
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MeaningController:
    """Controller for Sanskrit meaning extraction"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load meaning extraction system prompt"""
        try:
            with open("prompts/meaning_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are an expert Sanskrit scholar and translator.
Your task is to provide accurate translations, detailed word-by-word meanings, and interesting facts.

Provide:
- Complete English translation
- Word-by-word breakdown with meanings
- Historical and cultural context
- Grammatical notes (case, gender, etc.)
- Interesting and unique facts about the shloka
- Lesser-known or obscure facts

Return response as JSON with:
- translation: Complete English translation
- word_meanings: Dictionary of word -> meaning
- context: Historical/cultural context
- unique_facts: Interesting facts about the shloka
- unknown_facts: Lesser-known or obscure facts
- notes: Grammatical and interpretive notes"""
    
    async def extract_meaning(self, request: MeaningRequest) -> MeaningResponse:
        """
        Extract meaning and translation from Sanskrit verse
        
        Args:
            request: Meaning extraction request
            
        Returns:
            MeaningResponse with translation and analysis
        """
        try:
            logger.info(f"📖 Extracting meaning for verse")
            
            # Get grammar context if needed
            context = ""
            if request.include_context:
                context = await self._get_grammar_context()
            
            # Build user prompt
            user_prompt = f"""Translate and analyze this Sanskrit verse:

Verse: {request.verse}

{"Include word-by-word meanings." if request.include_word_meanings else ""}
{"Include historical and cultural context." if request.include_context else ""}

Grammar reference:
{context}

Provide:
1. Complete accurate English translation
2. Word-by-word breakdown (if requested)
3. Historical/cultural context (if requested)
4. Grammatical notes (case, sandhi, compounds, etc.)
5. Interesting and unique facts - what makes this shloka special
6. Unknown/obscure facts - rare interpretations, hidden meanings, scholarly insights

Return as JSON with fields: translation, word_meanings (dict), context, unique_facts, unknown_facts, notes"""
            
            # Get LLM response
            response_text = await self.llm_client.structured_completion(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.3  # Lower temperature for accuracy
            )
            
            # Parse response
            result = self._parse_llm_response(response_text)
            
            logger.info(f"✅ Translation completed")
            
            return MeaningResponse(**result)
            
        except Exception as e:
            logger.error(f"Meaning extraction failed: {str(e)}")
            raise
    
    async def _get_grammar_context(self) -> str:
        """Get grammar rules context"""
        try:
            return """
Sanskrit Grammar Reference:
- Nominal cases: 8 cases (vibhakti) - nominative to locative
- Sandhi rules: Vowel and consonant combination rules
- Samasa: Compound formations (tatpurusha, bahuvrihi, etc.)
- Verb forms: Present, past, future tenses with various moods

Common patterns:
- -म् (-m) ending: Neuter nominative/accusative singular
- -ः (-ḥ) ending: Masculine nominative singular
- -ा (-ā) ending: Feminine nominative singular
"""
        except Exception as e:
            logger.warning(f"Failed to get grammar context: {str(e)}")
            return ""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to extract structured data"""
        try:
            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            data = json.loads(json_str)
            
            # Set defaults
            data.setdefault("translation", "")
            data.setdefault("word_meanings", {})
            data.setdefault("context", "")
            data.setdefault("unique_facts", "")
            data.setdefault("unknown_facts", "")
            data.setdefault("notes", "")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "translation": "Unable to translate",
                "word_meanings": {},
                "context": "",
                "unique_facts": "",
                "unknown_facts": "",
                "notes": "Translation failed"
            }


# Singleton instance
_meaning_controller: MeaningController = None


def get_meaning_controller() -> MeaningController:
    """Get or create meaning controller singleton"""
    global _meaning_controller
    
    if _meaning_controller is None:
        _meaning_controller = MeaningController()
    
    return _meaning_controller
