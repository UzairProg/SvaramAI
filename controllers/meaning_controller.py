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
        self.kids_system_prompt = self._load_kids_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load meaning extraction system prompt for default mode"""
        try:
            with open("prompts/meaning_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are an expert Sanskrit scholar and translator.
Your task is to provide accurate translations and detailed word-by-word meanings.

Provide:
- Complete English translation
- Word-by-word breakdown with meanings
- Historical and cultural context
- Grammatical notes (case, gender, etc.)

Return response as JSON with:
- translation: Complete English translation
- word_meanings: Dictionary of word -> meaning
- context: Historical/cultural context
- notes: Grammatical and interpretive notes"""
    
    def _load_kids_system_prompt(self) -> str:
        """Load kid-friendly system prompt"""
        try:
            with open("prompts/meaning_kids.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are a friendly teacher explaining Sanskrit to children (ages 8-12).

Your goal is to make Sanskrit fun, simple, and relatable!

Guidelines:
- Use SIMPLE everyday words (avoid technical terms like "nominative case", "sandhi")
- Use FUN COMPARISONS kids understand (like sharing toys, playing games, family relationships)
- Make it ENGAGING and interesting
- Explain concepts through STORIES or examples from daily life
- Keep sentences SHORT and easy to understand
- Use emojis sparingly to make it fun 🌟

Return response as JSON with:
- translation: Simple English translation with everyday words
- word_meanings: Dictionary explaining each word like talking to a child
- context: Fun story or relatable explanation about where this verse comes from
- notes: Simple tips to remember or understand the verse better"""
    
    async def extract_meaning(self, request: MeaningRequest) -> MeaningResponse:
        """
        Extract meaning and translation from Sanskrit verse
        
        Args:
            request: Meaning extraction request
            
        Returns:
            MeaningResponse with translation and analysis
        """
        try:
            logger.info(f"📖 Extracting meaning for verse (section: {request.section_name})")
            
            # Select system prompt based on section_name
            system_prompt = self.kids_system_prompt if request.section_name == "kids" else self.system_prompt
            
            # Get grammar context if needed (simplified for kids mode)
            context = ""
            if request.include_context:
                context = await self._get_grammar_context(is_kids_mode=(request.section_name == "kids"))
            
            # Build user prompt (adjust language for kids mode)
            if request.section_name == "kids":
                user_prompt = f"""Help me understand this Sanskrit verse in a fun, simple way:

Verse: {request.verse}

{"Tell me what each word means in simple language." if request.include_word_meanings else ""}
{"Tell me a fun story or explain where this verse comes from." if request.include_context else ""}

Remember: Explain like I'm 8 years old! Use simple words and fun examples.

Provide:
1. Simple English translation (use everyday words)
2. What each word means (if requested) - explain like teaching a kid
3. Fun story or context (if requested) - make it interesting!
4. Simple tips to remember or understand this verse

Return as JSON with fields: translation, word_meanings (dict), context, notes"""
            else:
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

Return as JSON with fields: translation, word_meanings (dict), context, notes"""
            
            # Get LLM response
            response_text = await self.llm_client.structured_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3 if request.section_name == "default" else 0.5  # Higher temp for creative kids explanations
            )
            
            # Parse response
            result = self._parse_llm_response(response_text)
            
            logger.info(f"✅ Translation completed ({request.section_name} mode)")
            
            return MeaningResponse(**result)
            
        except Exception as e:
            logger.error(f"Meaning extraction failed: {str(e)}")
            raise
    
    async def _get_grammar_context(self, is_kids_mode: bool = False) -> str:
        """Get grammar rules context"""
        try:
            if is_kids_mode:
                return """
Simple Sanskrit Tips:
- Words can change their endings based on how they're used
- Some words join together to make new combined words (like "rain" + "bow" = "rainbow")
- Sanskrit has special sounds and letters
"""
            else:
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
            data.setdefault("notes", "")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "translation": "Unable to translate",
                "word_meanings": {},
                "context": "",
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
