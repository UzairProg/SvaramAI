"""
Tagline Controller - Business logic for Sanskrit branding taglines
"""

import logging
import json
from typing import Dict, Any, List

from models import TaglineGenerateRequest, TaglineGenerateResponse, TaglineVariant
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaglineController:
    """Controller for Sanskrit tagline generation"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load tagline system prompt"""
        try:
            with open("prompts/tagline_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are an expert in Sanskrit language and corporate branding.
Your task is to create impactful Sanskrit taglines for modern businesses.

Create taglines that:
- Capture the company's essence and values
- Use authentic Sanskrit vocabulary
- Are memorable and pronounceable
- Work well in branding context
- Convey professionalism

Return response as JSON with:
- tagline: Primary Sanskrit tagline
- english_translation: Direct translation
- meaning: Detailed explanation
- variants: Array of alternative versions"""
    
    async def generate_tagline(self, request: TaglineGenerateRequest) -> TaglineGenerateResponse:
        """
        Generate Sanskrit tagline for branding
        
        Args:
            request: Tagline generation request
            
        Returns:
            TaglineGenerateResponse with tagline and variants
        """
        try:
            logger.info(f"🎯 Generating tagline for {request.company_name}")
            
            # Get branding vocabulary context
            context = await self._get_branding_context(request)
            
            # Build user prompt
            user_prompt = f"""Create a Sanskrit tagline for this company:

Company Name: {request.company_name}
Industry: {request.industry}
Vision: {request.vision}
Core Values: {', '.join(request.values)}
Desired Tone: {request.tone}

Branding vocabulary context:
{context}

Requirements:
1. Create 1 primary tagline and 3 alternative variants
2. Keep it concise (3-7 words ideal)
3. Ensure proper Sanskrit grammar
4. Make it memorable and impactful
5. Align with company values and vision
6. Provide translations and context for each

Return as JSON with fields: tagline, english_translation, meaning, variants (array of objects with tagline, translation, context)"""
            
            # Get LLM response
            response_text = await self.llm_client.structured_completion(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.85  # High creativity for branding
            )
            
            # Parse response
            result = self._parse_llm_response(response_text)
            
            logger.info(f"✅ Generated tagline: {result['tagline']}")
            
            return TaglineGenerateResponse(**result)
            
        except Exception as e:
            logger.error(f"Tagline generation failed: {str(e)}")
            raise
    
    async def _get_branding_context(self, request: TaglineGenerateRequest) -> str:
        """Get relevant branding vocabulary"""
        try:
            # Industry-specific Sanskrit terms
            industry_vocab = {
                "technology": """
Sanskrit terms for technology/innovation:
- प्रौद्योगिकी (praudyogikī) - technology
- नवीनता (navīnatā) - innovation
- ज्ञानम् (jñānam) - knowledge
- विकासः (vikāsaḥ) - development
- सृजनम् (sṛjanam) - creation
""",
                "education": """
Sanskrit terms for education:
- विद्या (vidyā) - knowledge/education
- शिक्षा (śikṣā) - teaching
- ज्ञानम् (jñānam) - wisdom
- गुरु (guru) - teacher
- प्रज्ञा (prajñā) - intelligence
""",
                "healthcare": """
Sanskrit terms for healthcare:
- आरोग्यम् (ārogyam) - health
- चिकित्सा (cikitsā) - treatment
- आयुः (āyuḥ) - life
- सेवा (sevā) - service
- कल्याणम् (kalyāṇam) - well-being
"""
            }
            
            # Get relevant vocabulary or use general
            industry_key = request.industry.lower()
            for key in industry_vocab:
                if key in industry_key:
                    return industry_vocab[key]
            
            # Default general business terms
            return """
General Sanskrit business terms:
- उत्कर्षः (utkarṣaḥ) - excellence
- नेतृत्वम् (netṛtvam) - leadership
- विश्वासः (viśvāsaḥ) - trust
- सत्यम् (satyam) - truth
- धर्मः (dharmaḥ) - righteousness/duty
"""
            
        except Exception as e:
            logger.warning(f"Failed to get branding context: {str(e)}")
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
            
            # Ensure variants is list of TaglineVariant
            if "variants" in data and isinstance(data["variants"], list):
                data["variants"] = [
                    TaglineVariant(**v) if isinstance(v, dict) else v
                    for v in data["variants"]
                ]
            
            # Set defaults
            data.setdefault("tagline", "ज्ञानं शक्तिः")
            data.setdefault("english_translation", "Knowledge is power")
            data.setdefault("meaning", "")
            data.setdefault("variants", [])
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "tagline": "सत्यं विजयते",
                "english_translation": "Truth prevails",
                "meaning": "Classic Sanskrit phrase",
                "variants": []
            }


# Singleton instance
_tagline_controller: TaglineController = None


def get_tagline_controller() -> TaglineController:
    """Get or create tagline controller singleton"""
    global _tagline_controller
    
    if _tagline_controller is None:
        _tagline_controller = TaglineController()
    
    return _tagline_controller
