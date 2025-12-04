"""
Routes for Chandas Identifier API
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models import ChandasIdentifyRequest, ChandasIdentifyResponse
from controllers import get_chandas_controller, ChandasController

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chandas/identify", response_model=ChandasIdentifyResponse)
async def identify_chandas(
    request: ChandasIdentifyRequest,
    controller: ChandasController = Depends(get_chandas_controller)
):
    """
    Identify the chandas (meter) of a Sanskrit shloka with detailed mathematical process explanation
    
    This endpoint analyzes the syllable pattern and identifies the prosodic meter.
    
    - **shloka**: Sanskrit verse to analyze
    
    Returns detailed analysis including:
    - Chandas name
    - Syllable breakdown with Laghu/Guru classification
    - Pattern representation
    - Explanation and confidence score
    - **Step-by-step identification process**: Shows exactly how the chandas was determined through:
      1. Text preprocessing and normalization
      2. Syllable segmentation using Devanagari script rules
      3. Laghu-Guru classification based on vowel length and conjuncts
      4. Pattern matching against known chandas database
      5. Confidence calculation methodology
    """
    try:
        result = await controller.identify_chandas(request)
        return result
    except Exception as e:
        logger.error(f"Chandas identification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify chandas: {str(e)}"
        )
