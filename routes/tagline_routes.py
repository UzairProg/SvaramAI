"""
Routes for Sanskrit Tagline Generator API
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models import TaglineGenerateRequest, TaglineGenerateResponse
from controllers import get_tagline_controller, TaglineController

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tagline/generate", response_model=TaglineGenerateResponse)
async def generate_tagline(
    request: TaglineGenerateRequest,
    controller: TaglineController = Depends(get_tagline_controller)
):
    """
    Generate Sanskrit taglines for branding
    
    Create impactful Sanskrit taglines for modern businesses that capture
    the company's vision and values.
    
    Parameters:
    - **industry**: Business industry or domain
    - **company_name**: Company or brand name
    - **vision**: Company vision or mission statement
    - **values**: List of core values
    - **tone**: Desired tone (professional, inspiring, traditional, etc.)
    
    Returns:
    - Primary Sanskrit tagline
    - English translation
    - Detailed meaning and context
    - Alternative variants
    """
    try:
        result = await controller.generate_tagline(request)
        return result
    except Exception as e:
        logger.error(f"Tagline generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate tagline: {str(e)}"
        )
