"""
LLM Client - Abstraction layer for OpenAI, Anthropic, and Gemini APIs
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"


class LLMClient:
    """Unified client for LLM operations"""
    
    def __init__(self):
        """Initialize LLM clients"""
        logger.info(f"🔧 Initializing LLM clients...")
        logger.info(f"🔑 GEMINI_AVAILABLE: {GEMINI_AVAILABLE}")
        logger.info(f"🔑 Gemini API key present: {bool(settings.gemini_api_key)}")
        logger.info(f"🔑 Gemini model: {settings.gemini_model}")
        
        self.openai_client = None
        if OPENAI_AVAILABLE and settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("✅ OpenAI client initialized")
        
        self.anthropic_client = None
        if ANTHROPIC_AVAILABLE and settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("✅ Anthropic client initialized")
        
        self.gemini_client = None
        self.gemini_model_name = None
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                # Remove 'models/' prefix if present
                self.gemini_model_name = settings.gemini_model.replace('models/', '')
                self.gemini_client = genai.GenerativeModel(self.gemini_model_name)
                logger.info(f"✅ Gemini client initialized with model: {self.gemini_model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
        else:
            logger.warning(f"⚠️ Gemini not initialized - Available: {GEMINI_AVAILABLE}, Key: {bool(settings.gemini_api_key)}")
        
        self.groq_client = None
        if GROQ_AVAILABLE and hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            self.groq_client = AsyncGroq(api_key=settings.groq_api_key)
            logger.info("✅ Groq client initialized")
        
        self.default_provider = settings.default_llm_provider
        logger.info(f"✅ LLM Client initialized with provider: {self.default_provider}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Get chat completion from LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: 'openai' or 'anthropic' (defaults to configured provider)
            model: Specific model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated text response
        """
        provider = provider or self.default_provider
        temperature = temperature or settings.llm_temperature
        max_tokens = max_tokens or settings.llm_max_tokens
        
        try:
            if provider == LLMProvider.OPENAI:
                return await self._openai_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.ANTHROPIC:
                return await self._anthropic_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.GEMINI:
                return await self._gemini_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.GROQ or provider == "groq":
                return await self._groq_completion(
                    messages, model, temperature, max_tokens, **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"LLM completion failed: {str(e)}")
            raise
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Get completion from OpenAI"""
        model = model or settings.openai_model
        
        logger.info(f"🤖 OpenAI request: {model}")
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        content = response.choices[0].message.content
        logger.info(f"✅ OpenAI response received ({len(content)} chars)")
        
        return content
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Get completion from Anthropic"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        model = model or settings.anthropic_model
        
        # Anthropic requires system message separately
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        logger.info(f"🤖 Anthropic request: {model}")
        
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=user_messages,
            **kwargs
        )
        
        content = response.content[0].text
        logger.info(f"✅ Anthropic response received ({len(content)} chars)")
        
        return content
    
    async def _gemini_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Get completion from Google Gemini"""
        if not self.gemini_client:
            raise ValueError("Gemini API key not configured")
        
        logger.info(f"🤖 Gemini request: {settings.gemini_model}")
        
        # Separate system and user messages
        system_instr = None
        user_prompts = []
        for msg in messages:
            if msg["role"] == "system" and msg["content"].strip():
                system_instr = msg["content"]
            elif msg["role"] == "user":
                user_prompts.append(msg["content"])
        
        full_user_prompt = "\n".join(user_prompts)
        logger.info(f"🤖 Gemini: system={len(system_instr or '')} chars, user={len(full_user_prompt)} chars")
        
        # Create model - only add system_instruction if not empty
        if system_instr and len(system_instr.strip()) > 0:
            model_with_system = genai.GenerativeModel(
                self.gemini_model_name,
                system_instruction=system_instr
            )
        else:
            # No system instruction - minimal prompt
            model_with_system = genai.GenerativeModel(self.gemini_model_name)
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        response = await asyncio.to_thread(
            model_with_system.generate_content,
            full_user_prompt,
            generation_config=generation_config
        )
        
        # Check if response was blocked
        if not response.candidates:
            raise ValueError("Gemini response was blocked. No candidates returned.")
        
        candidate = response.candidates[0]
        
        # Check finish reason
        if candidate.finish_reason not in [1, 0]:  # 1 = STOP (success), 0 = UNSPECIFIED
            finish_reasons = {
                2: "SAFETY - Content was blocked by safety filters",
                3: "RECITATION - Content was blocked due to recitation",
                4: "OTHER - Other reason",
                5: "MAX_TOKENS - Maximum token limit reached"
            }
            reason = finish_reasons.get(candidate.finish_reason, f"Unknown reason: {candidate.finish_reason}")
            raise ValueError(f"Gemini generation failed: {reason}")
        
        # Extract text from response
        if not candidate.content.parts:
            raise ValueError("No content parts in Gemini response")
        
        content = candidate.content.parts[0].text
        logger.info(f"✅ Gemini response received ({len(content)} chars)")
        
        return content
    
    async def _groq_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Get completion from Groq"""
        if not self.groq_client:
            raise ValueError("Groq API key not configured")
        
        model = model or getattr(settings, 'groq_model', 'llama-3.3-70b-versatile')
        
        logger.info(f"🤖 Groq request: {model}")
        
        response = await self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        content = response.choices[0].message.content
        logger.info(f"✅ Groq response received ({len(content)} chars)")
        
        return content
    
    async def structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Convenience method for structured system + user prompts
        
        Args:
            system_prompt: System message defining behavior
            user_prompt: User message with the actual request
            provider: LLM provider to use
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages, provider=provider, **kwargs)
    
    async def load_prompt_file(self, filepath: str) -> str:
        """
        Load a prompt template from file
        
        Args:
            filepath: Path to prompt file
            
        Returns:
            str: Prompt content
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"📄 Loaded prompt from {filepath}")
            return content
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Error loading prompt file: {str(e)}")
            raise


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    
    if _llm_client is None:
        _llm_client = LLMClient()
    
    return _llm_client
