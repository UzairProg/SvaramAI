"""
Shloka Controller - Business logic for shloka generation
"""

import logging
import json
from typing import Dict, Any

from models import ShlokaGenerateRequest, ShlokaGenerateResponse
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ShlokaController:
    """Controller for shloka generation operations"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load shloka generation system prompt"""
        try:
            with open("prompts/shloka_generate.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are an expert Sanskrit poet and scholar.
Your task is to compose beautiful, grammatically correct Sanskrit shlokas.

Generate high-quality Sanskrit verses that:
- Follow proper chandas (meter) rules
- Use appropriate vocabulary and style
- Convey the requested theme and mood
- Are authentic and meaningful

Return response as JSON with:
- shloka: The complete Sanskrit verse
- meter: The chandas used
- meaning: English translation and explanation
- pattern: Laghu-Guru pattern"""
    
    async def generate_shloka(self, request: ShlokaGenerateRequest) -> ShlokaGenerateResponse:
        """
        Generate Sanskrit shloka based on parameters
        
        Args:
            request: Shloka generation request
            
        Returns:
            ShlokaGenerateResponse with generated shloka
        """
        try:
            logger.info(f"✍️ Generating shloka - Theme: {request.theme}")
            
            # Get example shlokas for context
            context = await self._get_shloka_examples(request)
            
            # Build user prompt
            user_prompt = f"""Generate a Sanskrit shloka with the following parameters:

Theme: {request.theme}
Deity: {request.deity or 'N/A'}
Mood: {request.mood}
Style: {request.style}
Preferred Meter: {request.meter or 'Choose appropriate meter'}

Context - Example shlokas in similar style:
{context}

Requirements:
1. Create an authentic Sanskrit verse
2. Follow proper meter rules
3. Capture the requested theme and mood
4. Ensure grammatical correctness
5. Provide English translation
6. Include syllable pattern

Return as JSON with fields: shloka, meter, meaning, pattern"""
            
            # Get LLM response
            response_text = await self.llm_client.structured_completion(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.8  # Higher temperature for creativity
            )
            
            # Parse response
            result = self._parse_llm_response(response_text)
            
            logger.info(f"✅ Generated shloka in {result['meter']} meter")
            
            return ShlokaGenerateResponse(**result)
            
        except Exception as e:
            logger.error(f"Shloka generation failed: {str(e)}")
            raise
    
    async def _get_shloka_examples(self, request: ShlokaGenerateRequest) -> str:
        """Get example shlokas from knowledge base"""
        try:
            # Return relevant examples based on style and mood
            examples = {
                "devotional": """Example (Krishna devotion):
वसुदेवसुतं देवं कंसचाणूरमर्दनम्।
देवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम्॥

I bow to Krishna, son of Vasudeva, destroyer of Kamsa and Chanura,
supreme joy of Devaki, teacher of the world.""",
                
                "philosophical": """Example (Bhagavad Gita style):
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥

You have right to action alone, never to its fruits.
Do not be motivated by fruits of action, nor attach to inaction.""",
                
                "heroic": """Example (Heroic):
पराक्रमो वीरवरस्य शौर्यं
महाबलं संयुगे दर्शयित्वा।

Displaying valor and great strength,
The hero's prowess shines in battle."""
            }
            
            mood_key = request.mood.value if hasattr(request.mood, 'value') else str(request.mood)
            return examples.get(mood_key, examples["devotional"])
            
        except Exception as e:
            logger.warning(f"Failed to get examples: {str(e)}")
            return ""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to extract structured data"""
        try:
            # Extract JSON from response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            data = json.loads(json_str)
            
            # Set defaults
            data.setdefault("shloka", "")
            data.setdefault("meter", "Anushtup")
            data.setdefault("meaning", "")
            data.setdefault("pattern", "")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "shloka": "Error generating shloka",
                "meter": "Unknown",
                "meaning": "Unable to generate",
                "pattern": ""
            }


# Singleton instance
_shloka_controller: ShlokaController = None


def get_shloka_controller() -> ShlokaController:
    """Get or create shloka controller singleton"""
    global _shloka_controller
    
    if _shloka_controller is None:
        _shloka_controller = ShlokaController()
    
    return _shloka_controller
