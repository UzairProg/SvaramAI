"""
Knowledge Base Controller - Business logic for RAG operations
"""

import logging
from typing import List

from models import (
    DocumentAddRequest,
    DocumentSearchRequest,
    DocumentUpdateRequest,
    DocumentDeleteRequest,
    DocumentSearchResponse,
    SearchResult,
    OperationResponse
)
from services.rag_client import get_rag_client
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KnowledgeBaseController:
    """Controller for knowledge base operations"""
    
    def __init__(self):
        self.rag_client = get_rag_client()
    
    async def add_document(self, request: DocumentAddRequest) -> OperationResponse:
        """
        Add document to knowledge base
        
        Args:
            request: Document add request
            
        Returns:
            OperationResponse with success status
        """
        try:
            logger.info(f"📝 Adding document to {request.collection}")
            logger.debug(f"Content length: {len(request.content)} chars")
            logger.debug(f"Metadata: {request.metadata}")
            
            # Add document to collection
            doc_id = await self.rag_client.add_document(
                collection=request.collection,
                content=request.content,
                metadata=request.metadata
            )
            
            logger.info(f"✅ Document added with ID: {doc_id}")
            
            return OperationResponse(
                success=True,
                message="Document added successfully",
                data={"document_id": doc_id}
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to add document: {str(e)}", exc_info=True)
            # Re-raise so the route handler can see it
            raise
    
    async def search_documents(self, request: DocumentSearchRequest) -> DocumentSearchResponse:
        """
        Search documents in knowledge base
        
        Args:
            request: Document search request
            
        Returns:
            DocumentSearchResponse with results
        """
        try:
            logger.info(f"🔍 Searching {request.collection} for: {request.query}")
            
            # Search documents (RAG client will generate embedding from query)
            results = await self.rag_client.search_documents(
                collection=request.collection,
                query_text=request.query,
                limit=request.limit
            )
            
            # Convert to SearchResult models
            search_results = [
                SearchResult(
                    id=str(r["id"]),
                    content=r["content"],
                    metadata=r["metadata"],
                    score=r["score"]
                )
                for r in results
            ]
            
            logger.info(f"✅ Found {len(search_results)} results")
            
            return DocumentSearchResponse(
                results=search_results,
                total=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
            # Still return empty but with proper logging
            return DocumentSearchResponse(
                results=[],
                total=0
            )
    
    async def update_document(self, request: DocumentUpdateRequest) -> OperationResponse:
        """
        Update existing document
        
        Args:
            request: Document update request
            
        Returns:
            OperationResponse with success status
        """
        try:
            logger.info(f"✏️ Updating document {request.document_id}")
            
            success = await self.rag_client.update_document(
                collection=request.collection,
                document_id=request.document_id,
                content=request.content,
                metadata=request.metadata
            )
            
            if success:
                logger.info(f"✅ Document updated")
                return OperationResponse(
                    success=True,
                    message="Document updated successfully",
                    data={"document_id": request.document_id}
                )
            else:
                return OperationResponse(
                    success=False,
                    message="Document not found",
                    data=None
                )
                
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return OperationResponse(
                success=False,
                message=f"Update failed: {str(e)}",
                data=None
            )
    
    async def delete_document(self, request: DocumentDeleteRequest) -> OperationResponse:
        """
        Delete document from knowledge base
        
        Args:
            request: Document delete request
            
        Returns:
            OperationResponse with success status
        """
        try:
            logger.info(f"🗑️ Deleting document {request.document_id}")
            
            success = await self.rag_client.delete_document(
                collection=request.collection,
                document_id=request.document_id
            )
            
            if success:
                logger.info(f"✅ Document deleted")
                return OperationResponse(
                    success=True,
                    message="Document deleted successfully",
                    data={"document_id": request.document_id}
                )
            else:
                return OperationResponse(
                    success=False,
                    message="Delete operation failed",
                    data=None
                )
                
        except Exception as e:
            logger.error(f"Delete failed: {str(e)}")
            return OperationResponse(
                success=False,
                message=f"Delete failed: {str(e)}",
                data=None
            )
    
    async def get_collection_stats(self, collection: str) -> OperationResponse:
        """
        Get statistics about a collection
        
        Args:
            collection: Collection name
            
        Returns:
            OperationResponse with collection stats
        """
        try:
            logger.info(f"📊 Getting stats for {collection}")
            
            info = await self.rag_client.get_collection_info(collection)
            
            return OperationResponse(
                success=True,
                message="Collection stats retrieved",
                data=info
            )
            
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return OperationResponse(
                success=False,
                message=f"Failed to get stats: {str(e)}",
                data=None
            )


# Singleton instance
_kb_controller: KnowledgeBaseController = None


def get_knowledgebase_controller() -> KnowledgeBaseController:
    """Get or create knowledge base controller singleton"""
    global _kb_controller
    
    if _kb_controller is None:
        _kb_controller = KnowledgeBaseController()
    
    return _kb_controller
