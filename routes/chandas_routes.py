"""
Routes for Chandas Identifier API
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models import ChandasIdentifyRequest, ChandasIdentifyResponse, ShlokaAnalyzeRequest, ShlokaAnalyzeResponse
from controllers import get_chandas_controller, ChandasController
from services.chandas_service import ChandasService
from services.llm_service import LLMService

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


@router.post("/chandas/analyze-shloka", response_model=ShlokaAnalyzeResponse)
async def analyze_shloka(request: ShlokaAnalyzeRequest):
    """
    Analyze Sanskrit shloka for meter detection with optional LLM enhancement
    
    This endpoint identifies the metre of a Sanskrit verse and optionally provides
    LLM-based analysis and commentary.
    
    - **verse**: Sanskrit verse text to analyze
    
    Returns:
    - Detected metre name
    - Metrical scheme and patterns
    - Confidence score
    - LLM-based analysis (if available)
    """
    try:
        # Validate input
        if not request.verse or not request.verse.strip():
            raise HTTPException(status_code=422, detail="Field 'verse' is required and cannot be empty")
        
        # Step 1: Identify metre using chandas service
        chandas_service = ChandasService()
        metre_info = chandas_service.identify_metre(request.verse)
        
        # Step 2: Get LLM analysis (optional)
        llm_analysis = None
        try:
            llm_service = LLMService()
            llm_analysis = await llm_service.analyze_with_metre(request.verse, metre_info)
        except Exception as e:
            logger.debug(f"LLM analysis not available: {e}")
        
        # Step 3: Build response
        response = ShlokaAnalyzeResponse(
            metre=metre_info.get("metre", "Unknown"),
            scheme=metre_info.get("scheme", ""),
            laghu_guru_pattern=metre_info.get("laghu_guru_pattern", ""),
            confidence=metre_info.get("confidence", 0.0),
            syllable_count=metre_info.get("syllable_count", []),
            gana_pattern=metre_info.get("gana_pattern", ""),
            detected=metre_info.get("detected", False),
            llm_output=llm_analysis
        )
        
        logger.info(f"Successfully analyzed shloka: {metre_info.get('metre', 'Unknown')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shloka analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze shloka: {str(e)}"
        )

