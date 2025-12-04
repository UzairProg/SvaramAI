"""
Voice Karaoke Controller - Sanskrit pronunciation analysis
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from models import (
    VoiceAnalyzeRequest, 
    VoiceAnalyzeResponse,
    PronunciationError,
    AccuracyMetrics,
    IdentifiedShloka
)
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceController:
    """Controller for voice karaoke analysis operations"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load voice analysis system prompt"""
        try:
            with open("prompts/voice_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback system prompt
            return """You are an expert in Sanskrit pronunciation and prosody. Analyze transcribed Sanskrit text against reference shlokas to identify pronunciation errors, syllable mismatches, and meter deviations. Provide detailed, constructive feedback."""
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to Sanskrit text using OpenAI Whisper
        
        Args:
            audio_file_path: Path to audio file (wav, mp3, etc.)
            
        Returns:
            str: Transcribed Sanskrit text
        """
        try:
            logger.info(f"🎤 Transcribing audio file: {audio_file_path}")
            
            # Use OpenAI Whisper API for transcription
            with open(audio_file_path, 'rb') as audio_file:
                # Call OpenAI Whisper API
                if not self.llm_client.openai_client:
                    raise ValueError("OpenAI client not initialized. Check API key configuration.")
                
                transcription = await self.llm_client.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    # Note: Whisper doesn't support Sanskrit directly, so we omit language to auto-detect
                    # or use "hi" for Hindi which handles Devanagari script well
                    response_format="text",
                    prompt="Sanskrit shloka in Devanagari script"  # Hint for better transcription
                )
            
            transcribed_text = transcription if isinstance(transcription, str) else transcription.text
            logger.info(f"✅ Transcribed: {transcribed_text[:100]}...")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def identify_shloka(self, transcribed_text: str, limit: int = 3) -> Optional[IdentifiedShloka]:
        """
        Identify which shloka the user attempted to recite using RAG search
        
        Args:
            transcribed_text: Transcribed Sanskrit text
            limit: Number of top matches to consider
            
        Returns:
            IdentifiedShloka or None if no good match found
        """
        try:
            logger.info(f"🔍 Searching for matching shloka in '{settings.shlokas_collection}' collection...")
            logger.info(f"   Query text: {transcribed_text[:100]}...")
            
            # Search in shlokas collection
            try:
                search_results = await self.rag_client.search_documents(
                    collection=settings.shlokas_collection,  # Fixed: was collection_name
                    query_text=transcribed_text,
                    limit=limit
                )
                logger.info(f"   ✅ RAG search completed successfully")
            except Exception as search_error:
                logger.error(f"   ❌ RAG search failed: {str(search_error)}", exc_info=True)
                logger.warning("   Falling back to AI context due to search error")
                return await self._get_ai_shloka_context(transcribed_text)
            
            logger.info(f"   📊 RAG returned {len(search_results) if search_results else 0} results")
            
            if not search_results or len(search_results) == 0:
                logger.warning("⚠️ No matching shlokas found in knowledge base - using AI to provide context")
                return await self._get_ai_shloka_context(transcribed_text)
            
            # Get best match and log all results for debugging
            logger.info(f"📊 RAG Search Results (top {len(search_results)}):")
            for idx, result in enumerate(search_results):
                logger.info(f"  {idx+1}. Score: {result['score']:.3f} | Content: {result['content'][:80]}...")
            
            best_match = search_results[0]
            
            # Lower threshold to 0.3 to be more lenient with pronunciation variations
            if best_match['score'] < 0.3:
                logger.warning(f"Best match score too low: {best_match['score']:.3f} - using AI fallback")
                return await self._get_ai_shloka_context(transcribed_text)
            
            # Extract metadata
            metadata = best_match.get('metadata', {})
            
            # Build IdentifiedShloka with PDF reference info
            identified = IdentifiedShloka(
                text=best_match['content'],
                source=metadata.get('source', 'Unknown'),
                meter=metadata.get('meter', 'Unknown'),
                meaning=metadata.get('meaning', ''),
                confidence=best_match['score'],
                page_number=metadata.get('page_number'),
                source_file=metadata.get('source_file'),
                chunk_id=metadata.get('chunk_id')
            )
            
            logger.info(f"✅ Identified shloka: {identified.source} (confidence: {identified.confidence:.2f})")
            if identified.page_number:
                logger.info(f"   📄 Found on page {identified.page_number} of {identified.source_file}")
            
            return identified
            
        except Exception as e:
            logger.error(f"Shloka identification failed: {str(e)}", exc_info=True)
            # Always return AI context on any error
            try:
                return await self._get_ai_shloka_context(transcribed_text)
            except Exception as ai_error:
                logger.error(f"AI context also failed: {str(ai_error)}")
                # Last resort - return generic context
                return IdentifiedShloka(
                    text=transcribed_text,
                    source="General Sanskrit Verse",
                    meter="Unknown",
                    meaning="This appears to be a Sanskrit verse. Sanskrit shlokas are used for prayer, meditation, and spiritual reflection across various contexts including devotional worship, philosophical teachings, and cultural celebrations.",
                    confidence=0.5,
                    page_number=None,
                    source_file=None,
                    chunk_id=None
                )
    
    async def _get_ai_shloka_context(self, transcribed_text: str) -> Optional[IdentifiedShloka]:
        """
        Use AI to provide context about the shloka when RAG search fails
        
        Args:
            transcribed_text: Transcribed Sanskrit text
            
        Returns:
            IdentifiedShloka with AI-generated context
        """
        try:
            logger.info("🤖 Using AI to identify shloka context...")
            
            context_prompt = f"""Analyze this Sanskrit text and provide context:

TEXT:
{transcribed_text}

Please identify or provide context about this shloka:
1. If you recognize it, provide the source (e.g., "Bhagavad Gita 2.47", "Hanuman Chalisa", etc.)
2. Identify the likely meter/chandas
3. Describe the theme and mood (devotional, philosophical, peace, protection, etc.)
4. Provide English translation
5. Explain when/why this type of shloka is typically recited

Return ONLY valid JSON:
{{
    "text": "complete shloka if known, or the transcribed text",
    "source": "source name or 'General Sanskrit Verse'",
    "meter": "meter name",
    "meaning": "English translation and context about usage/mood/purpose",
    "confidence": 0.0-1.0
}}"""

            messages = [
                {"role": "system", "content": "You are a Sanskrit scholar expert. Identify shlokas and provide cultural context."},
                {"role": "user", "content": context_prompt}
            ]
            
            response_text = await self.llm_client.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.3
            )
            
            # Parse JSON response
            import json
            import re
            
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            if not json_str.startswith("{"):
                json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            data = json.loads(json_str)
            
            identified = IdentifiedShloka(
                text=data.get('text', transcribed_text),
                source=data.get('source', 'General Sanskrit Verse'),
                meter=data.get('meter', 'Unknown'),
                meaning=data.get('meaning', 'Sanskrit verse with spiritual significance'),
                confidence=data.get('confidence', 0.7),
                page_number=None,  # AI fallback - no PDF reference
                source_file=None,
                chunk_id=None
            )
            
            logger.info(f"✅ AI identified context: {identified.source}")
            return identified
            
        except Exception as e:
            logger.error(f"AI context generation failed: {str(e)}")
            # Return generic context
            return IdentifiedShloka(
                text=transcribed_text,
                source="General Sanskrit Verse",
                meter="Unknown",
                meaning="This appears to be a Sanskrit verse. Sanskrit shlokas are used for prayer, meditation, and spiritual reflection across various contexts including devotional worship, philosophical teachings, and cultural celebrations.",
                confidence=0.5,
                page_number=None,
                source_file=None,
                chunk_id=None
            )
    
    async def analyze_pronunciation(
        self, 
        transcribed_text: str,
        reference_shloka: Optional[str] = None,
        identified_shloka: Optional[IdentifiedShloka] = None
    ) -> Dict[str, Any]:
        """
        Analyze pronunciation accuracy using OpenAI
        
        Args:
            transcribed_text: User's transcribed text
            reference_shloka: Reference shloka text (if provided)
            identified_shloka: Auto-identified shloka (if found)
            
        Returns:
            Dict with analysis results
        """
        try:
            logger.info(f"📊 Analyzing pronunciation...")
            
            # Determine reference text
            reference_text = reference_shloka
            if not reference_text and identified_shloka:
                reference_text = identified_shloka.text
            
            if not reference_text:
                # No reference available - provide general feedback
                return await self._analyze_without_reference(transcribed_text)
            
            # Create detailed analysis prompt
            analysis_prompt = f"""Analyze this Sanskrit pronunciation attempt:

TRANSCRIBED TEXT (what user said):
{transcribed_text}

REFERENCE TEXT (correct shloka):
{reference_text}

Please analyze and provide:
1. Overall accuracy score (0-1)
2. Word-level accuracy score
3. Syllable-level accuracy score
4. Meter pattern accuracy score
5. Pronunciation clarity score
6. List of specific errors with:
   - Position (word index, starting from 0)
   - Expected pronunciation
   - Actual pronunciation
   - Error type (syllable_mismatch, word_wrong, meter_deviation)
   - Severity (minor, moderate, major)
   - Detailed note explaining the error
7. Personalized suggestions for improvement
8. Overall encouraging feedback

Return ONLY valid JSON with this structure:
{{
    "overall_accuracy": 0.0-1.0,
    "word_accuracy": 0.0-1.0,
    "syllable_accuracy": 0.0-1.0,
    "meter_accuracy": 0.0-1.0,
    "pronunciation_clarity": 0.0-1.0,
    "errors": [
        {{
            "position": 0,
            "expected": "word",
            "actual": "word",
            "error_type": "syllable_mismatch",
            "severity": "minor",
            "note": "explanation"
        }}
    ],
    "suggestions": "detailed suggestions",
    "overall_feedback": "encouraging feedback"
}}"""
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response_text = await self.llm_client.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            analysis = self._parse_analysis_response(response_text)
            logger.info(f"✅ Analysis complete - Overall accuracy: {analysis['overall_accuracy']:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Pronunciation analysis failed: {str(e)}")
            raise
    
    async def _analyze_without_reference(self, transcribed_text: str) -> Dict[str, Any]:
        """Analyze pronunciation without reference shloka"""
        logger.info("📊 Analyzing without reference - providing general feedback")
        
        analysis_prompt = f"""Analyze this Sanskrit recitation (no reference available):

TEXT:
{transcribed_text}

Provide general feedback on:
1. Overall pronunciation quality (0-1 score)
2. Sanskrit phonetic accuracy
3. General observations
4. Suggestions for improvement

Return ONLY valid JSON with scores and feedback."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response_text = await self.llm_client.chat_completion(
            messages=messages,
            provider="openai",
            temperature=0.3
        )
        
        # Parse response
        try:
            analysis = json.loads(response_text)
        except:
            # Fallback response
            analysis = {
                "overall_accuracy": 0.75,
                "word_accuracy": 0.75,
                "syllable_accuracy": 0.75,
                "meter_accuracy": 0.75,
                "pronunciation_clarity": 0.75,
                "errors": [],
                "suggestions": "Continue practicing Sanskrit pronunciation. Focus on dental and retroflex consonants.",
                "overall_feedback": "Good effort! Keep practicing to improve clarity."
            }
        
        return analysis
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM analysis response to extract structured data"""
        try:
            # Clean JSON from markdown
            json_str = response_text.strip()
            
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Find JSON object
            if not json_str.startswith("{"):
                import re
                json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            analysis = json.loads(json_str)
            
            # Ensure all required fields exist with defaults
            analysis.setdefault("overall_accuracy", 0.75)
            analysis.setdefault("word_accuracy", 0.75)
            analysis.setdefault("syllable_accuracy", 0.75)
            analysis.setdefault("meter_accuracy", 0.75)
            analysis.setdefault("pronunciation_clarity", 0.75)
            analysis.setdefault("errors", [])
            analysis.setdefault("suggestions", "Practice regularly to improve pronunciation.")
            analysis.setdefault("overall_feedback", "Good effort! Keep practicing.")
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to parse analysis JSON: {str(e)}")
            # Return default analysis
            return {
                "overall_accuracy": 0.75,
                "word_accuracy": 0.75,
                "syllable_accuracy": 0.75,
                "meter_accuracy": 0.75,
                "pronunciation_clarity": 0.75,
                "errors": [],
                "suggestions": "Continue practicing. Focus on clear pronunciation.",
                "overall_feedback": "Good attempt! Keep working on your Sanskrit pronunciation."
            }
    
    async def analyze_voice(
        self, 
        audio_file_path: str,
        request: VoiceAnalyzeRequest
    ) -> VoiceAnalyzeResponse:
        """
        Complete voice karaoke analysis pipeline
        
        Args:
            audio_file_path: Path to user's audio recording
            request: Analysis request with optional reference shloka
            
        Returns:
            VoiceAnalyzeResponse with complete analysis
        """
        try:
            logger.info(f"🎵 Starting voice karaoke analysis...")
            
            # Step 1: Transcribe audio to text
            transcribed_text = await self.transcribe_audio(audio_file_path)
            logger.info(f"📝 Transcribed: {transcribed_text[:100]}...")
            
            # Step 2: Identify which shloka (if reference not provided)
            identified_shloka = None
            if not request.reference_shloka:
                logger.info("🔍 No reference provided - attempting to identify shloka...")
                try:
                    identified_shloka = await self.identify_shloka(transcribed_text)
                except Exception as identify_error:
                    logger.error(f"❌ identify_shloka failed: {str(identify_error)}", exc_info=True)
                    # Force creation of generic context
                    identified_shloka = IdentifiedShloka(
                        text=transcribed_text,
                        source="General Sanskrit Verse",
                        meter="Unknown",
                        meaning="This is a Sanskrit shloka. Sanskrit verses are recited for various purposes including devotional worship, meditation, philosophical reflection, and cultural ceremonies. They carry spiritual significance and are part of India's ancient wisdom tradition.",
                        confidence=0.6,
                        page_number=None,
                        source_file=None,
                        chunk_id=None
                    )
                
                if identified_shloka:
                    logger.info(f"✅ Shloka identified: {identified_shloka.source}")
                else:
                    logger.error("❌❌ CRITICAL: identified_shloka is None even after all fallbacks!")
                    # Force non-null
                    identified_shloka = IdentifiedShloka(
                        text=transcribed_text,
                        source="Sanskrit Recitation",
                        meter="Unknown",
                        meaning="Sanskrit verse recitation",
                        confidence=0.5,
                        page_number=None,
                        source_file=None,
                        chunk_id=None
                    )
            else:
                logger.info(f"📖 Using provided reference shloka")
            
            # Step 3: Analyze pronunciation
            analysis = await self.analyze_pronunciation(
                transcribed_text=transcribed_text,
                reference_shloka=request.reference_shloka,
                identified_shloka=identified_shloka
            )
            
            # Step 4: Build response
            accuracy_metrics = AccuracyMetrics(
                overall_accuracy=analysis['overall_accuracy'],
                word_accuracy=analysis['word_accuracy'],
                syllable_accuracy=analysis['syllable_accuracy'],
                meter_accuracy=analysis['meter_accuracy'],
                pronunciation_clarity=analysis['pronunciation_clarity']
            )
            
            errors = [
                PronunciationError(**error) for error in analysis.get('errors', [])
            ]
            
            # DEBUG: Log what we're about to return
            logger.info(f"🔍 DEBUG - identified_shloka before response creation: {identified_shloka}")
            logger.info(f"🔍 DEBUG - identified_shloka type: {type(identified_shloka)}")
            if identified_shloka:
                logger.info(f"🔍 DEBUG - identified_shloka.source: {identified_shloka.source}")
            
            response = VoiceAnalyzeResponse(
                transcribed_text=transcribed_text,
                identified_shloka=identified_shloka,
                accuracy_metrics=accuracy_metrics,
                errors=errors,
                suggestions=analysis['suggestions'],
                overall_feedback=analysis['overall_feedback']
            )
            
            logger.info(f"✅ Voice analysis complete - Accuracy: {accuracy_metrics.overall_accuracy:.2%}")
            logger.info(f"🔍 DEBUG - response.identified_shloka: {response.identified_shloka}")
            
            return response
            
        except Exception as e:
            logger.error(f"Voice analysis failed: {str(e)}")
            raise


# Singleton instance
_voice_controller: Optional[VoiceController] = None


def get_voice_controller() -> VoiceController:
    """Get or create voice controller singleton"""
    global _voice_controller
    
    if _voice_controller is None:
        _voice_controller = VoiceController()
    
    return _voice_controller
