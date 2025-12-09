"""
Routes for Sanskrit Meaning Engine API
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models import MeaningRequest, MeaningResponse
from controllers import get_meaning_controller, MeaningController

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/meaning/extract", response_model=MeaningResponse)
async def extract_meaning(
    request: MeaningRequest,
    controller: MeaningController = Depends(get_meaning_controller)
):
    """
    Extract meaning and translation from Sanskrit verses
    
    This endpoint provides comprehensive translation and analysis of Sanskrit text.
    
    Parameters:
    - **verse**: Sanskrit verse or text to translate
    - **include_word_meanings**: Include word-by-word breakdown (default: true)
    - **include_context**: Include historical/cultural context (default: true)
    
    Returns:
    - Complete English translation
    - Word-by-word meanings dictionary
    - Historical and cultural context
    - Grammatical notes
    """
    try:
        result = await controller.extract_meaning(request)
        return result
    except Exception as e:
        logger.error(f"Meaning extraction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract meaning: {str(e)}"
        )
