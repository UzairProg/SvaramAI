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
    Supports both standard explanations and kid-friendly simplified versions.
    
    Parameters:
    - **verse**: Sanskrit verse or text to translate
    - **include_word_meanings**: Include word-by-word breakdown (default: true)
    - **include_context**: Include historical/cultural context (default: true)
    - **section_name**: Explanation style:
        - `default`: Standard scholarly translation with technical terms
        - `kids`: Simplified child-friendly explanations (ages 8-12) with relatable examples
    
    Returns:
    - Complete English translation (simplified for kids mode)
    - Word-by-word meanings dictionary (kid-friendly in kids mode)
    - Historical and cultural context (fun stories in kids mode)
    - Grammatical notes (simple tips in kids mode)
    
    Example (Kids Mode):
    ```json
    {
      "verse": "सत्यम् ज्ञानम्",
      "section_name": "kids"
    }
    ```
    
    Returns fun, relatable explanations like "truth is like when you tell your parents what really happened!"
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
