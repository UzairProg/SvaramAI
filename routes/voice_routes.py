"""
Voice Karaoke Routes - Sanskrit pronunciation analysis API
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from models import VoiceAnalyzeRequest, VoiceAnalyzeResponse
from controllers.voice_controller import get_voice_controller

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["Voice Karaoke"])

# Initialize controller
voice_controller = get_voice_controller()


@router.post("/analyze", response_model=VoiceAnalyzeResponse)
async def analyze_voice_pronunciation(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, m4a, etc.)"),
    reference_shloka: Optional[str] = Form(None, description="Reference shloka text (optional - will auto-detect if not provided)")
):
    """
    Analyze Sanskrit pronunciation from audio recording
    
    **Process:**
    1. Transcribes audio using OpenAI Whisper
    2. Identifies which shloka was recited (if reference not provided)
    3. Compares pronunciation against reference
    4. Provides detailed error analysis and suggestions
    
    **Supported Audio Formats:**
    - WAV, MP3, M4A, FLAC, OGG
    - Max file size: 25MB
    - Recommended: Clear audio, minimal background noise
    
    **Returns:**
    - Transcribed Sanskrit text
    - Identified shloka (source, meter, meaning)
    - Detailed accuracy metrics
    - Specific pronunciation errors
    - Personalized improvement suggestions
    """
    temp_file_path = None
    
    try:
        logger.info(f"📥 Received audio file: {audio.filename} ({audio.content_type})")
        
        # Validate file type
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm'}
        file_ext = Path(audio.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. Supported: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)
            logger.info(f"💾 Saved audio to temp file: {temp_file_path} ({len(content)} bytes)")
        
        # Clean empty string to None (FastAPI forms send empty strings)
        cleaned_reference = reference_shloka if reference_shloka and reference_shloka.strip() else None
        
        logger.info(f"🔍 Raw reference_shloka: '{reference_shloka}' | Cleaned: '{cleaned_reference}'")
        
        # Create request object
        request = VoiceAnalyzeRequest(reference_shloka=cleaned_reference)
        
        # Analyze voice
        result = await voice_controller.analyze_voice(
            audio_file_path=temp_file_path,
            request=request
        )
        
        logger.info(f"✅ Analysis complete - Accuracy: {result.accuracy_metrics.overall_accuracy:.2%}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice analysis failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"🗑️ Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported audio formats and requirements
    """
    return {
        "supported_formats": [
            {
                "extension": ".wav",
                "description": "Waveform Audio File Format (recommended)",
                "max_size_mb": 25
            },
            {
                "extension": ".mp3",
                "description": "MPEG Audio Layer 3",
                "max_size_mb": 25
            },
            {
                "extension": ".m4a",
                "description": "MPEG-4 Audio",
                "max_size_mb": 25
            },
            {
                "extension": ".flac",
                "description": "Free Lossless Audio Codec",
                "max_size_mb": 25
            },
            {
                "extension": ".ogg",
                "description": "Ogg Vorbis",
                "max_size_mb": 25
            }
        ],
        "requirements": {
            "audio_quality": "Clear audio with minimal background noise",
            "language": "Sanskrit (sa)",
            "duration": "Up to 60 seconds recommended",
            "sample_rate": "16kHz or higher recommended"
        },
        "tips": [
            "Record in a quiet environment",
            "Speak clearly and at a moderate pace",
            "Use a good quality microphone",
            "Avoid background music or noise"
        ]
    }
