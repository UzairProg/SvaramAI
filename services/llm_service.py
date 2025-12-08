"""
LLM service for enhanced chandas analysis
"""
import logging
import os
from typing import Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based Sanskrit analysis"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    async def analyze_with_metre(self, verse: str, metre_info: Dict[str, Any]) -> str:
        """
        Use LLM to provide enhanced analysis based on detected metre
        
        Args:
            verse: Sanskrit verse text
            metre_info: Dictionary containing metre detection results
            
        Returns:
            LLM analysis and commentary
        """
        try:
            metre_name = metre_info.get("metre", "Unknown")
            scheme = metre_info.get("scheme", "")
            laghu_guru = metre_info.get("laghu_guru_pattern", "")
            confidence = metre_info.get("confidence", 0.0)
            
            system_message = (
                "You are a Sanskrit prosody (Chandas Shastra) expert. "
                "Analyze the given verse using the detected metre information. "
                "Provide insights about correctness, beauty, and any variations."
            )
            
            user_message = (
                f"Verse:\n{verse}\n\n"
                f"Detected Metre: {metre_name}\n"
                f"Scheme: {scheme}\n"
                f"Laghu-Guru Pattern: {laghu_guru}\n"
                f"Confidence: {confidence}\n\n"
                "Please analyze:\n"
                "1. Is this metre identification correct?\n"
                "2. Does the verse follow the rules of this chandas?\n"
                "3. Any notable features or variations?\n"
                "4. Brief explanation of this chandas type."
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis = response.choices[0].message.content
            logger.info("LLM analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            return f"LLM analysis unavailable: {str(e)}"
