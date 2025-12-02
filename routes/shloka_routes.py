"""
Routes for Shloka Generator API
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models import ShlokaGenerateRequest, ShlokaGenerateResponse
from controllers import get_shloka_controller, ShlokaController

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/shloka/generate", response_model=ShlokaGenerateResponse)
async def generate_shloka(
    request: ShlokaGenerateRequest,
    controller: ShlokaController = Depends(get_shloka_controller)
):
    """
    Generate a Sanskrit shloka based on theme and parameters
    
    This endpoint creates authentic Sanskrit verses using AI.
    
    Parameters:
    - **theme**: Main subject or topic for the shloka
    - **deity**: (Optional) Deity name for devotional verses
    - **mood**: Emotional tone (devotional, philosophical, heroic, etc.)
    - **style**: Literary style (classical, modern, vedic, puranic)
    - **meter**: (Optional) Specific chandas to use
    
    Returns:
    - Generated Sanskrit shloka
    - Meter information
    - English meaning
    - Syllable pattern
    """
    try:
        result = await controller.generate_shloka(request)
        return result
    except Exception as e:
        logger.error(f"Shloka generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate shloka: {str(e)}"
        )
