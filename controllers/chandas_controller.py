import logging
from typing import Any, Dict
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger("chandas.controller")

# Known verse dictionary for high-accuracy identification
KNOWN_METERS = {
    "यदा यदा हि धर्मस्य": "Trishtubh",
    "कर्मण्येवाधिकारस्ते": "Anushtubh",
    "वसंसि जीर्णानि यथा": "Trishtubh",
    "कुरुक्षेत्रे महाक्षेत्रे": "Sragdhara",
    "मा निषाद प्रतिष्ठां": "Shardula-vikridita",
    "धर्मक्षेत्रे कुरुक्षेत्रे": "Anushtubh",
    "श्रद्धावाँल्लभते ज्ञानं": "Anushtubh",
    "योगस्थः कुरु कर्माणि": "Anushtubh",
    "बहूनां जन्मनामन्ते": "Anushtubh",
    "मनः प्रसादः सौम्यत्वं": "Anushtubh",
    "अश्वत्थः सर्ववृक्षाणां": "Trishtubh",
    "द्वादश प्राधयश्चक्रस्य": "Jagati",
}

class ChandasController:
    def __init__(self, openai_client: AsyncOpenAI, model: str = "gpt-4-turbo"):
        self.openai_client = openai_client
        self.model = model

    async def identify_chandas(self, text: str) -> Dict[str, Any]:
        """
        Identify the Sanskrit meter (Chandas) of the given shloka using an LLM.
        Returns a structured JSON response as per requirements.
        """
        from fastapi import HTTPException
        try:
            # Input validation
            if not text or not isinstance(text, str) or not text.strip():
                logger.warning("Empty or invalid input text for chandas identification.")
                raise HTTPException(status_code=422, detail="Input text must be a non-empty string.")

            # Check known verse dictionary first
            identified_by = "LLM"
            known_meter = None
            for verse_start, meter in KNOWN_METERS.items():
                if verse_start in text.strip():
                    known_meter = meter
                    identified_by = "known_verse"
                    logger.info(f"Matched known verse: {verse_start} -> {meter}")
                    break

            system_prompt = (
                "You are an expert in Sanskrit prosody (Chandas Shastra).\n"
                "Identify the meter of the given shloka CORRECTLY.\n\n"
                "CRITICAL RULES:\n"
                "- Your output must be one of the known classical meters.\n"
                "- Do NOT guess. Do NOT default to Anuṣṭubh unless truly 8-8-8-8.\n"
                "- Jagati meter has 12 syllables per pada (12-12-12-12).\n"
                "- Trishtubh meter has 11 syllables per pada (11-11-11-11).\n"
                "- Anushtubh meter has 8 syllables per pada (8-8-8-8).\n"
                "- You MUST recognize all standard meters including:\n"
                "  Anushtubh (8), Trishtubh (11), Jagati (12), Indravajra (11), Upendravajra (11),\n"
                "  Shardula-vikridita (19), Mandakranta (17), Sragdhara (21), Vasantatilaka (14),\n"
                "  Shikharini (17), Malini (15), Prithvi (11), Upajati (11), and many more.\n"
                "- If this is a known verse (from Vedas, Gita, Ramayana, Upanishads, Subhashitas),\n"
                "  return its standard meter.\n"
                "- COUNT THE SYLLABLES CAREFULLY. Do not mis-count.\n"
                "- After choosing the meter, re-analyze and confirm:\n"
                "  'Is this chandas consistent with known rules AND commonly recited in this meter?'\n"
                "- If you initially said Anushtubh but syllable count is NOT 8-8-8-8, re-identify.\n"
                "- If syllable count is 12-12-12-12, it is Jagati, NOT Anushtubh.\n\n"
                "Steps you MUST follow:\n"
                "1. Normalize text\n"
                "2. Perform perfect Akshara Vibhajana (count carefully!)\n"
                "3. Mark each syllable as Laghu (L) or Guru (G)\n"
                "4. Detect Gana pattern (3-syllable clusters)\n"
                "5. Count syllables per pāda ACCURATELY\n"
                "6. Match with known classical meters based on syllable count\n"
                "7. Self-verify: Is this correct? Does the syllable count match the meter?\n\n"
            )
            
            if known_meter:
                system_prompt += f"\nNOTE: This verse is known to be in {known_meter} meter. Verify this is correct.\n\n"

            system_prompt += (
                "Return ONLY valid JSON matching this EXACT structure:\n"
                "{\n"
                '  "chandas_name": "Anushtubh",\n'
                '  "syllable_breakdown": [\n'
                '    {"syllable": "दृ", "type": "guru", "position": 1},\n'
                '    {"syllable": "ष्टा", "type": "guru", "position": 2}\n'
                "  ],\n"
                '  "laghu_guru_pattern": "GGLLGGLL",\n'
                '  "gana_pattern": "ma-ya-ra",\n'
                '  "syllable_count_per_pada": [8, 8, 8, 8],\n'
                '  "confidence": 0.95,\n'
                '  "explanation": "This is Anushtubh meter...",\n'
                '  "identification_process": [\n'
                '    {"step_number": 1, "step_name": "Normalization", "description": "...", "result": "..."},\n'
                '    {"step_number": 2, "step_name": "Akshara Vibhajana", "description": "...", "result": "..."}\n'
                "  ]\n"
                "}\n\n"
                "CRITICAL RULES:\n"
                "- confidence MUST be a number between 0.0 and 1.0 (NOT 'High' or 'Low')\n"
                "- syllable_breakdown MUST be an array of objects with syllable, type, position\n"
                "- identification_process MUST be an array of objects with step_number, step_name, description, result\n"
                "- ALL fields are required"
            )
            user_prompt = text.strip()

            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            logger.info("Sending prompt to OpenAI for chandas identification.")
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")

            # Parse JSON response
            import json
            try:
                result = json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse LLM response as JSON: {str(e)}"
                )

            # Validate required fields
            required = [
                "chandas_name", "syllable_breakdown", "laghu_guru_pattern",
                "gana_pattern", "syllable_count_per_pada", "confidence",
                "explanation", "identification_process"
            ]
            missing = [k for k in required if k not in result]
            if missing:
                logger.error(f"Missing fields in LLM response: {missing}")
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM response missing required fields: {missing}"
                )

            # Self-verification: Check if Anushtubh claim is valid
            if result.get("chandas_name") == "Anushtubh":
                pada_counts = result.get("syllable_count_per_pada", [])
                if pada_counts and pada_counts != [8, 8, 8, 8]:
                    logger.warning(f"LLM claimed Anushtubh but syllable count is {pada_counts}. Re-identifying...")
                    
                    # Determine correct meter based on syllable count
                    correct_meter_hint = ""
                    if all(c == 12 for c in pada_counts):
                        correct_meter_hint = " This appears to be Jagati (12-12-12-12)."
                    elif all(c == 11 for c in pada_counts):
                        correct_meter_hint = " This appears to be Trishtubh (11-11-11-11)."
                    
                    # Re-prompt
                    reverify_prompt = (
                        f"This is NOT Anushtubh. The syllable count is {pada_counts}, not 8-8-8-8.{correct_meter_hint} "
                        "Re-identify the chandas correctly. Return the same JSON format."
                    )
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": reverify_prompt})
                    
                    response = await self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.0,
                        max_tokens=2048,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                    result = json.loads(content)
                    identified_by = "LLM_reverified"

            # If known meter was found, update identified_by
            if known_meter:
                if result.get("chandas_name") == known_meter:
                    identified_by = "both"
                    result["confidence"] = min(result.get("confidence", 0.8) + 0.1, 1.0)
                else:
                    logger.warning(f"LLM said {result.get('chandas_name')} but known verse is {known_meter}")
                    identified_by = "known_verse_override"
                    result["chandas_name"] = known_meter
                    result["confidence"] = 0.9
                    result["explanation"] = f"Known verse identified as {known_meter}. " + result.get("explanation", "")

            # Add metadata
            result["identified_by"] = identified_by

            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Exception in identify_chandas")
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(exc)}"
            )

def get_chandas_controller(openai_client=None, model: str = "gpt-4-turbo") -> ChandasController:
    """
    Factory function for dependency injection frameworks or manual use.
    If openai_client is None, creates a new AsyncOpenAI client with default settings.
    """
    if openai_client is None:
        from openai import AsyncOpenAI
        openai_client = AsyncOpenAI()
    return ChandasController(openai_client=openai_client, model=model)
