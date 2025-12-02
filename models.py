"""
Pydantic models for all API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


# ==================== CHANDAS IDENTIFIER MODELS ====================

class ChandasIdentifyRequest(BaseModel):
    """Request model for chandas identification"""
    shloka: str = Field(..., description="Sanskrit shloka text to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "shloka": "वसुदेवसुतं देवं कंसचाणूरमर्दनम्"
            }
        }


class SyllableInfo(BaseModel):
    """Information about a syllable"""
    syllable: str
    type: str  # "laghu" or "guru"
    position: int


class ChandasIdentifyResponse(BaseModel):
    """Response model for chandas identification"""
    chandas_name: str = Field(..., description="Identified meter name")
    syllable_breakdown: List[SyllableInfo] = Field(..., description="Syllable-wise breakdown")
    laghu_guru_pattern: str = Field(..., description="Pattern representation (L/G or |/S)")
    explanation: str = Field(..., description="Detailed explanation of the meter")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chandas_name": "Anushtup",
                "syllable_breakdown": [
                    {"syllable": "va", "type": "laghu", "position": 1},
                    {"syllable": "su", "type": "laghu", "position": 2}
                ],
                "laghu_guru_pattern": "LGGLGGLG",
                "explanation": "This is Anushtup meter with 8 syllables per quarter",
                "confidence": 0.95
            }
        }


# ==================== SHLOKA GENERATOR MODELS ====================

class MoodEnum(str, Enum):
    """Mood options for shloka generation"""
    devotional = "devotional"
    philosophical = "philosophical"
    heroic = "heroic"
    romantic = "romantic"
    peaceful = "peaceful"
    energetic = "energetic"


class StyleEnum(str, Enum):
    """Style options for shloka generation"""
    classical = "classical"
    modern = "modern"
    vedic = "vedic"
    puranic = "puranic"


class ShlokaGenerateRequest(BaseModel):
    """Request model for shloka generation"""
    theme: str = Field(..., description="Main theme or subject")
    deity: Optional[str] = Field(None, description="Deity name if devotional")
    mood: MoodEnum = Field(MoodEnum.devotional, description="Emotional tone")
    style: StyleEnum = Field(StyleEnum.classical, description="Literary style")
    meter: Optional[str] = Field(None, description="Specific chandas to use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "theme": "Krishna's divine play",
                "deity": "Krishna",
                "mood": "devotional",
                "style": "classical",
                "meter": "Anushtup"
            }
        }


class ShlokaGenerateResponse(BaseModel):
    """Response model for shloka generation"""
    shloka: str = Field(..., description="Generated Sanskrit shloka")
    meter: str = Field(..., description="Meter used")
    meaning: str = Field(..., description="English translation and explanation")
    pattern: str = Field(..., description="Laghu-Guru pattern")
    
    class Config:
        json_schema_extra = {
            "example": {
                "shloka": "वसुदेवसुतं देवं कंसचाणूरमर्दनम्।\nदेवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम्॥",
                "meter": "Anushtup",
                "meaning": "I bow to Krishna, son of Vasudeva, destroyer of Kamsa and Chanura, supreme joy of Devaki, teacher of the world.",
                "pattern": "LGGLGGLG LGGLGGLG"
            }
        }


# ==================== TAGLINE GENERATOR MODELS ====================

class ToneEnum(str, Enum):
    """Tone options for taglines"""
    professional = "professional"
    inspiring = "inspiring"
    traditional = "traditional"
    modern = "modern"
    spiritual = "spiritual"
    powerful = "powerful"


class TaglineGenerateRequest(BaseModel):
    """Request model for Sanskrit tagline generation"""
    industry: str = Field(..., description="Industry or domain")
    company_name: str = Field(..., description="Company or brand name")
    vision: str = Field(..., description="Company vision or mission")
    values: List[str] = Field(..., description="Core values")
    tone: ToneEnum = Field(ToneEnum.professional, description="Desired tone")
    
    class Config:
        json_schema_extra = {
            "example": {
                "industry": "Technology",
                "company_name": "TechVeda",
                "vision": "Empowering digital transformation",
                "values": ["innovation", "excellence", "integrity"],
                "tone": "professional"
            }
        }


class TaglineVariant(BaseModel):
    """A tagline variant"""
    tagline: str
    translation: str
    context: str


class TaglineGenerateResponse(BaseModel):
    """Response model for tagline generation"""
    tagline: str = Field(..., description="Primary Sanskrit tagline")
    english_translation: str = Field(..., description="English translation")
    meaning: str = Field(..., description="Detailed meaning and context")
    variants: List[TaglineVariant] = Field(..., description="Alternative versions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tagline": "ज्ञानं शक्तिः प्रौद्योगिक्या",
                "english_translation": "Knowledge is power through technology",
                "meaning": "Combining ancient wisdom with modern technology",
                "variants": [
                    {
                        "tagline": "नवीनता परम्परायाः",
                        "translation": "Innovation from tradition",
                        "context": "Emphasizes traditional roots"
                    }
                ]
            }
        }


# ==================== MEANING ENGINE MODELS ====================

class MeaningRequest(BaseModel):
    """Request model for Sanskrit meaning extraction"""
    verse: str = Field(..., description="Sanskrit verse or text")
    include_word_meanings: bool = Field(True, description="Include word-by-word breakdown")
    include_context: bool = Field(True, description="Include historical/cultural context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "verse": "सत्यं ज्ञानमनन्तं ब्रह्म",
                "include_word_meanings": True,
                "include_context": True
            }
        }


class MeaningResponse(BaseModel):
    """Response model for meaning extraction"""
    translation: str = Field(..., description="Complete English translation")
    word_meanings: Dict[str, str] = Field(..., description="Word-by-word meanings")
    context: str = Field(..., description="Historical and cultural context")
    notes: str = Field(..., description="Additional grammatical or interpretive notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "translation": "Truth, Knowledge, Infinite is Brahman",
                "word_meanings": {
                    "सत्यम्": "truth, reality",
                    "ज्ञानम्": "knowledge, wisdom",
                    "अनन्तम्": "infinite, endless",
                    "ब्रह्म": "Brahman, the absolute"
                },
                "context": "From Taittiriya Upanishad, defining the nature of Brahman",
                "notes": "All three words are in neuter gender, nominative case"
            }
        }


# ==================== KNOWLEDGE BASE MODELS ====================

class CollectionEnum(str, Enum):
    """Available collections in knowledge base"""
    chandas_patterns = "chandas_patterns"
    example_shlokas = "example_shlokas"
    grammar_rules = "grammar_rules"
    branding_vocab = "branding_vocab"


class DocumentAddRequest(BaseModel):
    """Request to add document to knowledge base"""
    collection: CollectionEnum = Field(..., description="Target collection")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "collection": "chandas_patterns",
                "content": "Anushtup: 8 syllables per quarter, 32 total. Pattern: flexible with 5th syllable laghu",
                "metadata": {
                    "name": "Anushtup",
                    "category": "sama-vritta",
                    "syllables": 32
                }
            }
        }


class DocumentSearchRequest(BaseModel):
    """Request to search documents"""
    collection: CollectionEnum = Field(..., description="Collection to search")
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "collection": "chandas_patterns",
                "query": "meters with 8 syllables",
                "limit": 5
            }
        }


class SearchResult(BaseModel):
    """A single search result"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class DocumentSearchResponse(BaseModel):
    """Response from document search"""
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "id": "doc_001",
                        "content": "Anushtup meter description",
                        "metadata": {"name": "Anushtup"},
                        "score": 0.95
                    }
                ],
                "total": 1
            }
        }


class DocumentUpdateRequest(BaseModel):
    """Request to update a document"""
    collection: CollectionEnum = Field(..., description="Collection name")
    document_id: str = Field(..., description="Document ID to update")
    content: Optional[str] = Field(None, description="New content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")


class DocumentDeleteRequest(BaseModel):
    """Request to delete a document"""
    collection: CollectionEnum = Field(..., description="Collection name")
    document_id: str = Field(..., description="Document ID to delete")


class OperationResponse(BaseModel):
    """Generic operation response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")


# ==================== VOICE ANALYZER MODELS ====================

class VoiceAnalyzeResponse(BaseModel):
    """Response from voice karaoke analyzer"""
    transcribed: str = Field(..., description="Transcribed Sanskrit text")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Pronunciation accuracy")
    errors: List[Dict[str, str]] = Field(..., description="Identified errors")
    suggestions: str = Field(..., description="Improvement suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcribed": "वसुदेव सुतं देवं",
                "accuracy": 0.87,
                "errors": [
                    {
                        "position": "2",
                        "expected": "वसुदेव",
                        "actual": "वसुदेव",
                        "note": "Slight mispronunciation of 'dev' sound"
                    }
                ],
                "suggestions": "Focus on clear pronunciation of dental consonants"
            }
        }


# ==================== COMMON MODELS ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")
