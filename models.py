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


class IdentificationStep(BaseModel):
    """A step in the chandas identification process"""
    step_number: int = Field(..., description="Step sequence number")
    step_name: str = Field(..., description="Name of this step")
    description: str = Field(..., description="What happens in this step")
    result: str = Field(..., description="Result of this step")


class ChandasIdentifyResponse(BaseModel):
    """Response model for chandas identification"""
    chandas_name: str = Field(..., description="Identified meter name")
    syllable_breakdown: List[SyllableInfo] = Field(..., description="Syllable-wise breakdown")
    laghu_guru_pattern: str = Field(..., description="Pattern representation (L/G or |/S)")
    explanation: str = Field(..., description="Detailed explanation of the meter")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    identification_process: List[IdentificationStep] = Field(default_factory=list, description="Step-by-step mathematical process of how chandas was identified")
    
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
                "confidence": 0.95,
                "identification_process": [
                    {
                        "step_number": 1,
                        "step_name": "Text Preprocessing",
                        "description": "Remove punctuation and normalize text",
                        "result": "Cleaned text ready for syllable extraction"
                    },
                    {
                        "step_number": 2,
                        "step_name": "Syllable Segmentation",
                        "description": "Split text into syllables using Devanagari script rules",
                        "result": "32 syllables detected"
                    },
                    {
                        "step_number": 3,
                        "step_name": "Laghu-Guru Classification",
                        "description": "Classify each syllable as Laghu (short) or Guru (long) based on vowel length and conjunct consonants",
                        "result": "Pattern: LGGLGGLG LGGLGGLG LGGLGGLG LGGLGGLG"
                    },
                    {
                        "step_number": 4,
                        "step_name": "Pattern Matching",
                        "description": "Match against known chandas patterns in database",
                        "result": "Matched: Anushtup (32 syllables, 8 per quarter)"
                    },
                    {
                        "step_number": 5,
                        "step_name": "Confidence Calculation",
                        "description": "Calculate confidence based on pattern match quality",
                        "result": "Confidence: 0.95 (Exact match)"
                    }
                ]
            }
        }


# ==================== SHLOKA ANALYZE MODELS ====================

class ShlokaAnalyzeRequest(BaseModel):
    """Request model for shloka analysis"""
    verse: str = Field(..., description="Sanskrit verse text to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "verse": "वसुदेवसुतं देवं कंसचाणूरमर्दनम्"
            }
        }


class ShlokaAnalyzeResponse(BaseModel):
    """Response model for shloka analysis"""
    metre: str = Field(..., description="Identified metre name")
    scheme: str = Field(..., description="Metrical scheme")
    laghu_guru_pattern: str = Field(..., description="Laghu-Guru pattern (L/G notation)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for detection")
    syllable_count: List[int] = Field(default_factory=list, description="Syllable count per quarter")
    gana_pattern: str = Field(default="", description="Gana pattern")
    detected: bool = Field(..., description="Whether metre was successfully detected")
    llm_output: Optional[Dict[str, Any]] = Field(default=None, description="LLM-based analysis and commentary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metre": "Anushtup",
                "scheme": "8-8-8-8",
                "laghu_guru_pattern": "LGGLGGLG LGGLGGLG LGGLGGLG LGGLGGLG",
                "confidence": 0.95,
                "syllable_count": [8, 8, 8, 8],
                "gana_pattern": "ma-ya-ra-ta",
                "detected": True,
                "llm_output": {
                    "explanation": "This verse follows the Anushtup metre...",
                    "commentary": "A well-structured verse in classical Sanskrit meter"
                }
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
    unique_facts: str = Field(default="", description="Interesting and unique facts about the shloka")
    unknown_facts: str = Field(default="", description="Lesser-known or obscure facts")
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
                "unique_facts": "This definition appears in three Taittiriya texts and forms the basis of Advaita Vedanta philosophy",
                "unknown_facts": "Some scholars believe this formulation influenced Buddhist epistemology",
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

class VoiceAnalyzeRequest(BaseModel):
    """Request for voice karaoke analysis"""
    reference_shloka: Optional[str] = Field(None, description="Expected shloka (optional, will auto-detect if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reference_shloka": "वसुदेवसुतं देवं कंसचाणूरमर्दनम्"
            }
        }


class PronunciationError(BaseModel):
    """A pronunciation error detail"""
    position: int = Field(..., description="Position in verse (word index)")
    expected: str = Field(..., description="Expected pronunciation")
    actual: str = Field(..., description="Actual pronunciation")
    error_type: str = Field(..., description="Type of error: syllable_mismatch, word_wrong, meter_deviation")
    severity: str = Field(..., description="Error severity: minor, moderate, major")
    note: str = Field(..., description="Detailed explanation")


class AccuracyMetrics(BaseModel):
    """Detailed accuracy metrics"""
    overall_accuracy: float = Field(..., ge=0.0, le=1.0, description="Overall accuracy score")
    word_accuracy: float = Field(..., ge=0.0, le=1.0, description="Word-level accuracy")
    syllable_accuracy: float = Field(..., ge=0.0, le=1.0, description="Syllable-level accuracy")
    meter_accuracy: float = Field(..., ge=0.0, le=1.0, description="Meter pattern accuracy")
    pronunciation_clarity: float = Field(..., ge=0.0, le=1.0, description="Overall pronunciation clarity")


class IdentifiedShloka(BaseModel):
    """Information about the identified shloka"""
    text: str = Field(..., description="Complete shloka text")
    source: str = Field(..., description="Source text (e.g., Bhagavad Gita 2.47)")
    meter: str = Field(..., description="Meter name")
    meaning: str = Field(..., description="English translation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Matching confidence")
    page_number: Optional[int] = Field(None, description="Page number in source PDF (if available)")
    source_file: Optional[str] = Field(None, description="Source PDF filename (if from uploaded document)")
    chunk_id: Optional[int] = Field(None, description="Chunk ID in RAG database")


class VoiceAnalyzeResponse(BaseModel):
    """Response from voice karaoke analyzer"""
    transcribed_text: str = Field(..., description="Transcribed Sanskrit text from audio")
    identified_shloka: Optional[IdentifiedShloka] = Field(None, description="Identified shloka details")
    accuracy_metrics: AccuracyMetrics = Field(..., description="Detailed accuracy metrics")
    errors: List[PronunciationError] = Field(default_factory=list, description="Identified pronunciation errors")
    suggestions: str = Field(..., description="Personalized improvement suggestions")
    overall_feedback: str = Field(..., description="Overall performance feedback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcribed_text": "वसुदेव सुतं देवं कंसचाणूरमर्दनम्",
                "identified_shloka": {
                    "text": "वसुदेवसुतं देवं कंसचाणूरमर्दनम्।\nदेवकीपरमानन्दं कृष्णं वन्दे जगद्गुरुम्॥",
                    "source": "Krishna Stotram",
                    "meter": "Anushtup",
                    "meaning": "I bow to Krishna, son of Vasudeva, destroyer of Kamsa and Chanura, supreme joy of Devaki, teacher of the world.",
                    "confidence": 0.92
                },
                "accuracy_metrics": {
                    "overall_accuracy": 0.87,
                    "word_accuracy": 0.90,
                    "syllable_accuracy": 0.85,
                    "meter_accuracy": 0.88,
                    "pronunciation_clarity": 0.84
                },
                "errors": [
                    {
                        "position": 1,
                        "expected": "वसुदेवसुतं",
                        "actual": "वसुदेव सुतं",
                        "error_type": "syllable_mismatch",
                        "severity": "minor",
                        "note": "Added extra space between compound words"
                    }
                ],
                "suggestions": "Focus on connecting compound words smoothly. Practice the 'dev' sound with proper dental pronunciation.",
                "overall_feedback": "Good attempt! Your pronunciation is 87% accurate. Main areas for improvement: compound word joining and dental consonant clarity."
            }
        }


# ==================== CHATBOT MODELS ====================

class InputTypeEnum(str, Enum):
    """Input type for chatbot"""
    text = "text"
    voice = "voice"
    image = "image"


class PersonaEnum(str, Enum):
    """AI persona options"""
    default = "default"
    krishna = "krishna"


class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: Optional[float] = Field(None, description="Unix timestamp")


class ChatRequest(BaseModel):
    """Request model for chatbot"""
    message: Optional[str] = Field(None, description="Text message (required if input_type=text)")
    input_type: InputTypeEnum = Field(InputTypeEnum.text, description="Type of input")
    persona: PersonaEnum = Field(PersonaEnum.default, description="AI persona to use")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Previous conversation context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is Anushtup meter?",
                "input_type": "text",
                "persona": "default",
                "conversation_history": []
            }
        }


class ChatResponse(BaseModel):
    """Response model from chatbot"""
    response: str = Field(..., description="Chatbot response text")
    input_detected: str = Field(..., description="Detected/transcribed input from user")
    sources: List[str] = Field(default_factory=list, description="Knowledge base sources used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up question suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Anushtup is the most common Sanskrit meter, consisting of 32 syllables divided into 4 quarters of 8 syllables each. It's widely used in epics like Mahabharata and Ramayana.",
                "input_detected": "What is Anushtup meter?",
                "sources": ["Chandas Knowledge Base", "Example Shlokas"],
                "confidence": 0.95,
                "suggestions": [
                    "How do I identify Anushtup meter?",
                    "What are other common Sanskrit meters?",
                    "Can you show me an example of Anushtup?"
                ]
            }
        }


# ==================== COMMON MODELS ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")
