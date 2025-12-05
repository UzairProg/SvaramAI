"""
Chatbot Controller - Multimodal Sanskrit AI assistant
"""

import logging
import json
from typing import Dict, Any, List, Optional
import base64

from models import ChatRequest, ChatResponse, ChatMessage
from services.llm_client import get_llm_client
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatbotController:
    """Controller for Sanskrit AI chatbot operations"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.rag_client = get_rag_client()
        self.system_prompt = self._load_system_prompt()
        self.krishna_prompt = self._load_krishna_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load chatbot system prompt"""
        try:
            with open("prompts/chatbot_system.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback system prompt
            return """You are a Sanskrit AI assistant specialized in helping users with Sanskrit language processing."""
    
    def _load_krishna_prompt(self) -> str:
        """Load Krishna persona prompt"""
        try:
            with open("prompts/krishna_persona.txt", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback Krishna prompt
            return """You are Lord Krishna, sharing divine wisdom and guidance with devotees."""
    
    async def process_chat(
        self, 
        message: Optional[str],
        input_type: str,
        audio_path: Optional[str] = None,
        image_path: Optional[str] = None,
        conversation_history: List[ChatMessage] = None,
        persona: str = "default"
    ) -> ChatResponse:
        """
        Process chatbot request with text, voice, or image input
        
        Args:
            message: Text message (for text input)
            input_type: Type of input (text/voice/image)
            audio_path: Path to audio file (for voice input)
            image_path: Path to image file (for image input)
            conversation_history: Previous conversation messages
            
        Returns:
            ChatResponse with answer and context
        """
        try:
            logger.info(f"🤖 Processing chatbot request - Input type: {input_type}")
            
            # Step 1: Convert input to text
            if input_type == "text":
                user_query = message
                if not user_query or not user_query.strip():
                    raise ValueError("Message cannot be empty for text input")
            elif input_type == "voice":
                user_query = await self._transcribe_audio(audio_path)
                logger.info(f"🎤 Transcribed: {user_query}")
            elif input_type == "image":
                user_query = await self._extract_text_from_image(image_path)
                logger.info(f"🖼️ Extracted from image: {user_query}")
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            # Step 2: Decide if RAG is needed (smart routing)
            needs_rag = self._should_use_rag(user_query)
            
            if needs_rag:
                logger.info("📚 Using RAG knowledge base for context")
                rag_context = await self._get_rag_context(user_query)
            else:
                logger.info("💬 Casual chat - skipping RAG search")
                rag_context = []
            
            # Step 3: Build conversation messages
            messages = self._build_conversation(
                user_query=user_query,
                rag_context=rag_context,
                conversation_history=conversation_history or [],
                persona=persona
            )
            
            # Step 4: Get LLM response
            response_text = await self.llm_client.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.7,
                max_tokens=1000
            )
            
            # Step 5: Extract sources from RAG context
            sources = self._extract_sources(rag_context) if needs_rag else []
            
            # Step 6: Generate follow-up suggestions
            suggestions = self._generate_suggestions(user_query, response_text)
            
            logger.info(f"✅ Chatbot response generated successfully")
            
            return ChatResponse(
                response=response_text,
                input_detected=user_query,
                sources=sources,
                confidence=0.85,  # Can be enhanced with confidence scoring
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Chatbot processing failed: {str(e)}")
            raise
    
    def _should_use_rag(self, query: str) -> bool:
        """
        Determine if RAG search is needed based on query content
        
        Returns True if query is about Sanskrit-specific content that would benefit from RAG
        """
        query_lower = query.lower()
        
        # Casual greetings and general chat - no RAG needed
        casual_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'what\'s up', 'thanks', 'thank you', 'bye', 'goodbye',
            'who are you', 'what can you do', 'help me', 'what is your name'
        ]
        
        # Check if it's just a greeting
        if any(pattern in query_lower for pattern in casual_patterns):
            # But if they mention Sanskrit topics in greeting, still use RAG
            sanskrit_keywords = [
                'shloka', 'chandas', 'meter', 'verse', 'sanskrit', 'pronunciation',
                'anushtup', 'indravajra', 'meaning', 'translation', 'bhagavad',
                'ramayana', 'upanishad', 'veda', 'गीता', 'श्लोक'
            ]
            if any(keyword in query_lower for keyword in sanskrit_keywords):
                return True
            return False
        
        # Short queries without Sanskrit keywords - likely casual
        if len(query.split()) <= 3 and not any(c.isalpha() and ord(c) > 2304 for c in query):
            # Check if it has Sanskrit keywords
            sanskrit_keywords = [
                'shloka', 'chandas', 'meter', 'verse', 'sanskrit', 'pronunciation',
                'meaning', 'translation', 'anushtup'
            ]
            if not any(keyword in query_lower for keyword in sanskrit_keywords):
                return False
        
        # Questions about features/capabilities - no RAG needed
        feature_patterns = [
            'how does', 'can you', 'what features', 'what can', 'how to use',
            'how do i', 'show me how'
        ]
        if any(pattern in query_lower for pattern in feature_patterns):
            # Unless asking specifically about Sanskrit content
            if not any(word in query_lower for word in ['shloka', 'verse', 'meter', 'chandas', 'pronunciation']):
                return False
        
        # Everything else - use RAG (Sanskrit content, analysis, specific questions)
        return True
    
    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text using OpenAI Whisper"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            with open(audio_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    prompt="Sanskrit text or question about Sanskrit language"
                )
            
            return transcript.text
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            raise
    
    async def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using GPT-4 Vision"""
        try:
            import openai
            
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract any Sanskrit text or questions about Sanskrit from this image. If it contains Sanskrit verse, preserve the Devanagari script. If it's a question in English/other language, extract that. Be precise."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Image text extraction failed: {str(e)}")
            raise
    
    async def _get_rag_context(self, query: str) -> List[Dict[str, Any]]:
        """Search RAG knowledge base for relevant context"""
        try:
            # Search across all collections
            results = []
            
            # Search shlokas collection
            try:
                shloka_results = await self.rag_client.search_documents(
                    collection=settings.shlokas_collection,
                    query_text=query,
                    limit=3
                )
                results.extend(shloka_results)
            except Exception as e:
                logger.warning(f"Shloka search failed: {str(e)}")
            
            # Search chandas patterns collection
            try:
                chandas_results = await self.rag_client.search_documents(
                    collection=settings.chandas_collection,
                    query_text=query,
                    limit=2
                )
                results.extend(chandas_results)
            except Exception as e:
                logger.warning(f"Chandas search failed: {str(e)}")
            
            # Sort by score and return top results
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            return results[:5]
            
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {str(e)}")
            return []
    
    def _build_conversation(
        self,
        user_query: str,
        rag_context: List[Dict[str, Any]],
        conversation_history: List[ChatMessage],
        persona: str = "default"
    ) -> List[Dict[str, str]]:
        """Build conversation messages for LLM"""
        
        # Select system prompt based on persona
        if persona == "krishna":
            base_prompt = self.krishna_prompt
        else:
            base_prompt = self.system_prompt
        
        # Format RAG context
        if rag_context:
            context_text = "\n\n".join([
                f"Source: {r.get('metadata', {}).get('source', 'Unknown')}\n{r.get('content', '')}"
                for r in rag_context
            ])
            system_content = f"{base_prompt}\n\n**Available Context from Knowledge Base:**\n{context_text}"
        else:
            system_content = base_prompt
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user query
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        return messages
    
    def _extract_sources(self, rag_context: List[Dict[str, Any]]) -> List[str]:
        """Extract source names with page numbers from RAG context"""
        sources = []
        seen = set()
        
        for result in rag_context:
            metadata = result.get('metadata', {})
            
            # Get book/source name (clean up temp file paths)
            source_file = metadata.get('source', 'Unknown')
            
            # Extract readable book name from filename
            if '\\' in source_file or '/' in source_file:
                # It's a file path - get just the filename
                book_name = source_file.split('\\')[-1].split('/')[-1]
                # Remove .pdf extension and temp prefixes
                book_name = book_name.replace('.pdf', '').replace('tmp', '').strip('_-')
                
                # If it's still messy (like "pfn18mz1"), use a generic name
                if len(book_name) < 10 or not any(c.isalpha() for c in book_name):
                    book_name = metadata.get('title', 'Sanskrit Text')
            else:
                book_name = source_file
            
            # Get page number if available
            page_num = metadata.get('page_number') or metadata.get('page')
            
            # Format source string
            if page_num:
                source_str = f"{book_name} (Page {page_num})"
            else:
                source_str = book_name
            
            # Add unique sources only
            if source_str not in seen:
                sources.append(source_str)
                seen.add(source_str)
        
        return sources[:3]  # Return top 3 unique sources
    
    def _generate_suggestions(self, query: str, response: str) -> List[str]:
        """Generate follow-up question suggestions"""
        # Smart suggestions based on query keywords
        suggestions = []
        
        query_lower = query.lower()
        
        if "meter" in query_lower or "chandas" in query_lower:
            suggestions = [
                "Can you show me an example?",
                "How do I identify this meter?",
                "What are the rules for this chandas?"
            ]
        elif "shloka" in query_lower or "verse" in query_lower:
            suggestions = [
                "Can you analyze this shloka?",
                "What is the meter of this verse?",
                "What does this shloka mean?"
            ]
        elif "pronunciation" in query_lower or "pronounce" in query_lower:
            suggestions = [
                "Can you check my pronunciation?",
                "How should I practice?",
                "What are common mistakes?"
            ]
        elif "meaning" in query_lower or "translation" in query_lower:
            suggestions = [
                "Can you explain word-by-word?",
                "What is the cultural context?",
                "Are there other interpretations?"
            ]
        else:
            suggestions = [
                "Tell me more about Sanskrit meters",
                "How does the voice analyzer work?",
                "Can you generate a shloka?"
            ]
        
        return suggestions


# Singleton instance
_chatbot_controller: ChatbotController = None


def get_chatbot_controller() -> ChatbotController:
    """Get or create chatbot controller singleton"""
    global _chatbot_controller
    
    if _chatbot_controller is None:
        _chatbot_controller = ChatbotController()
    
    return _chatbot_controller
