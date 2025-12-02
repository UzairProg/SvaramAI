"""
PDF Loader - Extract and process PDF documents for knowledge base
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFLoader:
    """Load and process PDF documents"""
    
    def __init__(self):
        """Initialize PDF loader"""
        logger.info("✅ PDF Loader initialized")
    
    async def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load and extract text from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of page dictionaries with text and metadata
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            if not path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {file_path}")
            
            logger.info(f"📄 Loading PDF: {file_path}")
            
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            logger.info(f"📊 PDF has {total_pages} pages")
            
            pages = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text()
                    logger.debug(f"Page {page_num} extracted {len(text)} characters")
                    
                    if text and text.strip():
                        pages.append({
                            "page_number": page_num,
                            "text": text.strip(),
                            "metadata": {
                                "source": file_path,
                                "total_pages": total_pages,
                                "page": page_num
                            }
                        })
                    else:
                        logger.warning(f"⚠️ Page {page_num} has no extractable text (might be image-based)")
                except Exception as page_error:
                    logger.error(f"❌ Failed to extract page {page_num}: {str(page_error)}")
            
            if not pages:
                raise ValueError(
                    f"No text could be extracted from PDF. "
                    f"This might be a scanned/image-based PDF. "
                    f"Total pages: {total_pages}"
                )
            
            logger.info(f"✅ Extracted {len(pages)} pages with text from {total_pages} total pages")
            return pages
            
        except Exception as e:
            logger.error(f"Failed to load PDF: {str(e)}")
            raise
    
    async def load_and_chunk(
        self,
        file_path: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Load PDF and split into chunks
        
        Args:
            file_path: Path to PDF file
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks with metadata
        """
        try:
            pages = await self.load_pdf(file_path)
            
            if not pages:
                logger.warning("No pages extracted from PDF")
                return []
            
            chunks = []
            chunk_id = 0
            
            for page in pages:
                text = page["text"]
                page_num = page["page_number"]
                
                # Skip empty pages
                if not text or len(text.strip()) < 10:
                    logger.debug(f"Skipping page {page_num} - too short")
                    continue
                
                # Simple chunking by character count
                for i in range(0, len(text), chunk_size - overlap):
                    chunk_text = text[i:i + chunk_size]
                    
                    if chunk_text.strip() and len(chunk_text.strip()) > 20:
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": chunk_text.strip(),
                            "metadata": {
                                "source": file_path,
                                "page_number": page_num,
                                "chunk_index": chunk_id
                            }
                        })
                        chunk_id += 1
            
            if not chunks:
                raise ValueError("No valid text chunks could be created from PDF")
            
            logger.info(f"✅ Created {len(chunks)} chunks from {len(pages)} pages")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk PDF: {str(e)}")
            raise
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary of metadata
        """
        try:
            reader = PdfReader(file_path)
            metadata = reader.metadata
            
            info = {
                "title": metadata.get("/Title", "Unknown"),
                "author": metadata.get("/Author", "Unknown"),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
                "creation_date": str(metadata.get("/CreationDate", "")),
                "total_pages": len(reader.pages)
            }
            
            logger.info(f"📋 Extracted metadata from {file_path}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}")
            raise


# Singleton instance
_pdf_loader: PDFLoader = None


def get_pdf_loader() -> PDFLoader:
    """Get or create PDF loader singleton"""
    global _pdf_loader
    
    if _pdf_loader is None:
        _pdf_loader = PDFLoader()
    
    return _pdf_loader
