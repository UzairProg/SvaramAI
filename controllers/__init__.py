"""Controllers package initialization"""

from .chandas_controller import get_chandas_controller, ChandasController
from .shloka_controller import get_shloka_controller, ShlokaController
from .tagline_controller import get_tagline_controller, TaglineController
from .meaning_controller import get_meaning_controller, MeaningController
from .knowledgebase_controller import get_knowledgebase_controller, KnowledgeBaseController
from .voice_controller import get_voice_controller, VoiceController
from .chatbot_controller import get_chatbot_controller, ChatbotController

__all__ = [
    'get_chandas_controller',
    'ChandasController',
    'get_shloka_controller',
    'ShlokaController',
    'get_tagline_controller',
    'TaglineController',
    'get_meaning_controller',
    'MeaningController',
    'get_knowledgebase_controller',
    'KnowledgeBaseController',
    'get_voice_controller',
    'VoiceController',
    'get_chatbot_controller',
    'ChatbotController'
]
