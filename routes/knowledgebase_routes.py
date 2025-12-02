"""
Routes for Knowledge Base (RAG) API
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import Optional
import logging
import tempfile
import os

from models import (
    DocumentAddRequest,
    DocumentSearchRequest,
    DocumentUpdateRequest,
    DocumentDeleteRequest,
    DocumentSearchResponse,
    OperationResponse,
    CollectionEnum
)
from controllers import get_knowledgebase_controller, KnowledgeBaseController
from services.pdf_loader import get_pdf_loader

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/kb/document", response_model=OperationResponse)
async def add_document(
    request: DocumentAddRequest,
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Add a document to the knowledge base
    
    Parameters:
    - **collection**: Target collection (chandas_patterns, example_shlokas, etc.)
    - **content**: Document content/text
    - **metadata**: Additional metadata as key-value pairs
    
    Returns:
    - Success status and document ID
    """
    try:
        result = await controller.add_document(request)
        return result
    except Exception as e:
        logger.error(f"Failed to add document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document: {str(e)}"
        )


@router.post("/kb/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Search documents in the knowledge base
    
    Parameters:
    - **collection**: Collection to search in
    - **query**: Search query text
    - **limit**: Maximum number of results (default: 5, max: 50)
    
    Returns:
    - List of matching documents with scores
    - Total count
    """
    try:
        result = await controller.search_documents(request)
        return result
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.put("/kb/document", response_model=OperationResponse)
async def update_document(
    request: DocumentUpdateRequest,
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Update an existing document
    
    Parameters:
    - **collection**: Collection name
    - **document_id**: ID of document to update
    - **content**: New content (optional)
    - **metadata**: New metadata (optional)
    
    Returns:
    - Success status
    """
    try:
        result = await controller.update_document(request)
        return result
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/kb/document", response_model=OperationResponse)
async def delete_document(
    request: DocumentDeleteRequest,
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Delete a document from the knowledge base
    
    Parameters:
    - **collection**: Collection name
    - **document_id**: ID of document to delete
    
    Returns:
    - Success status
    """
    try:
        result = await controller.delete_document(request)
        return result
    except Exception as e:
        logger.error(f"Delete failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}"
        )


@router.get("/kb/collection/{collection}/stats", response_model=OperationResponse)
async def get_collection_stats(
    collection: CollectionEnum,
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Get statistics about a collection
    
    Parameters:
    - **collection**: Collection name
    
    Returns:
    - Collection statistics (document count, status, etc.)
    """
    try:
        result = await controller.get_collection_stats(collection)
        return result
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/kb/upload-pdf", response_model=OperationResponse)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    collection: CollectionEnum = Form(..., description="Target collection"),
    chunk_size: Optional[int] = Form(1000, description="Characters per chunk"),
    controller: KnowledgeBaseController = Depends(get_knowledgebase_controller)
):
    """
    Upload a PDF file and add its content to the knowledge base
    
    The PDF will be:
    1. Extracted page by page
    2. Split into chunks (default 1000 chars)
    3. Added to the specified collection with metadata
    
    Parameters:
    - **file**: PDF file (multipart/form-data)
    - **collection**: Target collection (chandas_patterns, example_shlokas, etc.)
    - **chunk_size**: Maximum characters per chunk (default: 1000)
    
    Returns:
    - Success status with number of chunks added
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        logger.info(f"📤 Uploading PDF: {file.filename} to {collection}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Load and process PDF
            pdf_loader = get_pdf_loader()
            chunks = await pdf_loader.load_and_chunk(
                tmp_file_path,
                chunk_size=chunk_size,
                overlap=100
            )
            
            # Add chunks to knowledge base
            added_count = 0
            for chunk in chunks:
                request = DocumentAddRequest(
                    collection=collection,
                    content=chunk["text"],
                    metadata={
                        **chunk["metadata"],
                        "source_file": file.filename,
                        "chunk_id": chunk["chunk_id"]
                    }
                )
                await controller.add_document(request)
                added_count += 1
            
            logger.info(f"✅ Added {added_count} chunks from {file.filename}")
            
            return OperationResponse(
                success=True,
                message=f"Successfully processed PDF: {added_count} chunks added to {collection}",
                data={
                    "filename": file.filename,
                    "chunks_added": added_count,
                    "collection": collection
                }
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )
