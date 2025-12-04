"""
Routes for Chatbot API - Multimodal Sanskrit AI assistant
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import logging
import tempfile
import os
import json
from typing import Optional, List, Union

from models import ChatRequest, ChatResponse, ChatMessage, InputTypeEnum
from controllers.chatbot_controller import get_chatbot_controller, ChatbotController

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    message: Optional[str] = Form(None),
    input_type: str = Form("text"),
    conversation_history: Optional[str] = Form(None),
    audio: Union[UploadFile, str, None] = File(default=None),
    image: Union[UploadFile, str, None] = File(default=None),
    controller: ChatbotController = Depends(get_chatbot_controller)
):
    """
    Multimodal Sanskrit AI Chatbot
    
    Supports three input types:
    
    **Text Input:**
    - message: Your question or text
    - input_type: "text"
    
    **Voice Input:**
    - audio: Audio file (wav, mp3, m4a, flac, ogg)
    - input_type: "voice"
    
    **Image Input:**
    - image: Image file containing Sanskrit text or question (jpg, png)
    - input_type: "image"
    
    **Optional:**
    - conversation_history: JSON array of previous messages for context
    
    The chatbot specializes in:
    - Sanskrit chandas/meter identification
    - Shloka analysis and generation
    - Pronunciation guidance
    - Meaning and translation
    - Sanskrit grammar and knowledge
    
    Returns intelligent responses with sources, confidence, and follow-up suggestions.
    """
    try:
        # Handle empty string files (some clients send "" instead of null)
        if isinstance(audio, str) and not audio:
            audio = None
        if isinstance(image, str) and not image:
            image = None
        
        # Convert to UploadFile or None
        audio_file = audio if isinstance(audio, UploadFile) else None
        image_file = image if isinstance(image, UploadFile) else None
        
        # Validate input type
        if input_type not in ["text", "voice", "image"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input_type: {input_type}. Must be 'text', 'voice', or 'image'"
            )
        
        # Parse conversation history
        history = []
        if conversation_history:
            try:
                history_data = json.loads(conversation_history)
                history = [ChatMessage(**msg) for msg in history_data]
            except Exception as e:
                logger.warning(f"Failed to parse conversation history: {str(e)}")
        
        # Handle different input types
        audio_path = None
        image_path = None
        
        if input_type == "text":
            if not message or not message.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Message is required for text input"
                )
        
        elif input_type == "voice":
            if not audio_file:
                raise HTTPException(
                    status_code=400,
                    detail="Audio file is required for voice input"
                )
            
            # Validate audio format
            allowed_audio = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/x-m4a", "audio/flac", "audio/ogg"}
            if audio_file.content_type not in allowed_audio:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format: {audio_file.content_type}"
                )
            
            # Save audio temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as tmp:
                content = await audio_file.read()
                tmp.write(content)
                audio_path = tmp.name
            
            logger.info(f"📥 Audio file saved: {audio_file.filename} ({len(content)} bytes)")
        
        elif input_type == "image":
            if not image_file:
                raise HTTPException(
                    status_code=400,
                    detail="Image file is required for image input"
                )
            
            # Validate image format
            allowed_images = {"image/jpeg", "image/png", "image/jpg"}
            if image_file.content_type not in allowed_images:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format: {image_file.content_type}"
                )
            
            # Save image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.filename)[1]) as tmp:
                content = await image_file.read()
                tmp.write(content)
                image_path = tmp.name
            
            logger.info(f"📥 Image file saved: {image_file.filename} ({len(content)} bytes)")
        
        # Process chat request
        try:
            result = await controller.process_chat(
                message=message,
                input_type=input_type,
                audio_path=audio_path,
                image_path=image_path,
                conversation_history=history
            )
            return result
        
        except ValueError as ve:
            # Handle validation errors from controller
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )
            
        finally:
            # Cleanup temporary files
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp audio file: {str(e)}")
            
            if image_path and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp image file: {str(e)}")
    
    except HTTPException:
        raise
    except ValueError as ve:
        # Catch any ValueError that escaped the inner try-except
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Chatbot request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot processing failed: {str(e)}"
        )
