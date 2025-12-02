"""
RAG Client - Qdrant vector database operations
"""

import logging
from typing import List, Dict, Any, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not installed - using dummy embeddings")


class RAGClient:
    """Client for Qdrant vector database operations"""
    
    def __init__(self):
        """Initialize Qdrant client and embedding model"""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
                https=settings.qdrant_use_https
            )
            
            logger.info(f"✅ Qdrant client initialized: {settings.qdrant_host}:{settings.qdrant_port}")
            
            # Initialize local embedding model
            self.embedding_model = None
            self.vector_size = 384
            
            if EMBEDDINGS_AVAILABLE:
                try:
                    # Use lightweight multilingual model (supports Sanskrit)
                    # This runs locally, no API key needed!
                    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
                    logger.info(f"📥 Loading embedding model: {model_name}...")
                    self.embedding_model = SentenceTransformer(model_name)
                    self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
                    logger.info(f"✅ Embedding model loaded locally (dim: {self.vector_size})")
                except Exception as e:
                    logger.error(f"❌ Failed to load embedding model: {str(e)}")
                    logger.warning("⚠️ Falling back to dummy embeddings")
            else:
                logger.warning("⚠️ Install sentence-transformers: pip install sentence-transformers")
            
            # Initialize collections
            self._initialize_collections()
            
        except Exception as e:
            logger.warning(f"⚠️ Qdrant not available: {str(e)} - Knowledge base features will be limited")
            self.client = None
    
    def _initialize_collections(self):
        """Create collections if they don't exist"""
        if not self.client:
            logger.warning("⚠️ Qdrant client not available, skipping collection initialization")
            return
            
        collections = [
            settings.chandas_collection,
            settings.shlokas_collection,
            settings.grammar_collection,
            settings.branding_collection
        ]
        
        # Use the actual vector size from embedding model
        vector_size = self.vector_size
        
        for collection_name in collections:
            try:
                if self.client.collection_exists(collection_name):
                    # Check if vector size matches
                    collection_info = self.client.get_collection(collection_name)
                    existing_size = collection_info.config.params.vectors.size
                    
                    if existing_size != vector_size:
                        logger.warning(f"⚠️ Collection {collection_name} has wrong vector size ({existing_size} vs {vector_size})")
                        logger.info(f"🔄 Recreating collection {collection_name} with correct size...")
                        self.client.delete_collection(collection_name)
                        self.client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(
                                size=vector_size,
                                distance=Distance.COSINE
                            )
                        )
                        logger.info(f"✅ Recreated collection: {collection_name}")
                    else:
                        logger.info(f"📦 Collection exists: {collection_name}")
                else:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"📦 Created collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not create collection {collection_name}: {str(e)}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using local model
        
        Args:
            text: Input text
            
        Returns:
            List[float]: Embedding vector
        """
        if self.embedding_model:
            try:
                logger.info(f"🧠 Encoding text: '{text[:100]}...'")
                # Generate embedding locally (no API calls!)
                embedding = self.embedding_model.encode(text, convert_to_tensor=False)
                embedding_list = embedding.tolist()
                logger.info(f"✅ Generated {len(embedding_list)}-dim embedding")
                return embedding_list
            except Exception as e:
                logger.error(f"❌ Failed to generate embedding: {str(e)}", exc_info=True)
                return [0.0] * self.vector_size
        else:
            # No model - use dummy (search won't work well)
            logger.warning("⚠️ No embedding model loaded - using dummy vector!")
            return [0.0] * self.vector_size
    
    async def add_document(
        self,
        collection: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Add a document to the knowledge base
        
        Args:
            collection: Collection name
            content: Document content
            metadata: Document metadata
            embedding: Pre-computed embedding vector (if None, will use dummy vector)
            
        Returns:
            str: Document ID
        """
        try:
            # Convert enum to string if needed
            collection_name = str(collection.value) if hasattr(collection, 'value') else str(collection)
            
            doc_id = str(uuid.uuid4())
            
            # Generate embedding from content
            if embedding is None:
                logger.info(f"🔨 Generating embedding for content ({len(content)} chars)...")
                embedding = self._generate_embedding(content)
                logger.debug(f"Generated embedding: {len(embedding)} dimensions")
            
            vector = embedding
            
            point = PointStruct(
                id=doc_id,
                vector=vector,
                payload={
                    "content": content,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"✅ Added document to {collection_name}: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise
    
    async def search_documents(
        self,
        collection: str,
        query_text: str = None,
        query_embedding: List[float] = None,
        limit: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            collection: Collection name
            query_text: Query text (will be embedded)
            query_embedding: Pre-computed query vector (optional)
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Convert enum to string if needed
            collection_name = str(collection.value) if hasattr(collection, 'value') else str(collection)
            
            # Generate embedding from query text if not provided
            if query_embedding is None and query_text:
                logger.info(f"🔍 Generating embedding for query: {query_text[:50]}...")
                query_embedding = self._generate_embedding(query_text)
                logger.debug(f"Query embedding: {len(query_embedding)} dimensions")
            elif query_embedding is None:
                raise ValueError("Either query_text or query_embedding must be provided")
            
            # Check collection stats first
            collection_info = self.client.get_collection(collection_name)
            points_count = collection_info.points_count
            logger.info(f"📊 Collection {collection_name} has {points_count} points")
            
            if points_count == 0:
                logger.warning(f"⚠️ Collection {collection_name} is empty - add documents first!")
                return []
            
            logger.info(f"🔎 Executing search with limit={limit}, threshold={score_threshold}")
            
            results = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            ).points
            
            logger.info(f"📝 Qdrant search completed. Results type: {type(results)}, Length: {len(results)}")
            
            if not results:
                logger.warning(f"⚠️ No results found. This might mean:")
                logger.warning(f"   - Documents were added with dummy embeddings (all zeros)")
                logger.warning(f"   - Query embedding doesn't match document embeddings")
                logger.warning(f"   - score_threshold ({score_threshold}) is too high")
            
            documents = []
            for idx, result in enumerate(results):
                logger.info(f"Result {idx+1}: ID={result.id}, Score={result.score}")
                doc = {
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k != "content"}
                }
                documents.append(doc)
            
            logger.info(f"🔍 Returning {len(documents)} documents from {collection_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def update_document(
        self,
        collection: str,
        document_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Update an existing document
        
        Args:
            collection: Collection name
            document_id: Document ID to update
            content: New content (optional)
            metadata: New metadata (optional)
            embedding: New embedding vector (optional)
            
        Returns:
            bool: Success status
        """
        try:
            # Get existing document
            existing = self.client.retrieve(
                collection_name=collection,
                ids=[document_id]
            )
            
            if not existing:
                logger.warning(f"Document not found: {document_id}")
                return False
            
            # Update payload
            payload = existing[0].payload.copy()
            
            if content is not None:
                payload["content"] = content
            
            if metadata is not None:
                payload.update(metadata)
            
            # Update vector
            vector = embedding or existing[0].vector
            
            point = PointStruct(
                id=document_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=collection,
                points=[point]
            )
            
            logger.info(f"✅ Updated document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
            raise
    
    async def delete_document(
        self,
        collection: str,
        document_id: str
    ) -> bool:
        """
        Delete a document
        
        Args:
            collection: Collection name
            document_id: Document ID to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=[document_id]
                )
            )
            
            logger.info(f"🗑️ Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            raise
    
    async def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        Get information about a collection
        
        Args:
            collection: Collection name
            
        Returns:
            Collection information
        """
        try:
            info = self.client.get_collection(collection_name=collection)
            return {
                "name": collection,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            raise


# Singleton instance
_rag_client: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """Get or create RAG client singleton"""
    global _rag_client
    
    if _rag_client is None:
        _rag_client = RAGClient()
    
    return _rag_client
