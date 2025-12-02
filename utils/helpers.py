"""
Helper utilities for Sanskrit AI backend
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime to ISO string
    
    Args:
        dt: Datetime object (defaults to now)
        
    Returns:
        ISO formatted string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that may contain code blocks or other content
    
    Args:
        text: Text containing JSON
        
    Returns:
        Extracted JSON string or None
    """
    # Try to find JSON in code blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*?\})'
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename


def validate_sanskrit_text(text: str) -> bool:
    """
    Basic validation that text contains Sanskrit (Devanagari) characters
    
    Args:
        text: Text to validate
        
    Returns:
        True if contains Devanagari
    """
    devanagari_pattern = r'[\u0900-\u097F]'
    return bool(re.search(devanagari_pattern, text))


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    
    return chunks


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries
    
    Args:
        *dicts: Variable number of dictionaries
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def calculate_confidence(score: float, threshold: float = 0.8) -> str:
    """
    Convert numeric score to confidence level
    
    Args:
        score: Numeric score (0.0 to 1.0)
        threshold: Threshold for high confidence
        
    Returns:
        Confidence level string
    """
    if score >= threshold:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def count_words(text: str) -> int:
    """
    Count words in text
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    return len(text.split())


def get_file_extension(filename: str) -> str:
    """
    Get file extension
    
    Args:
        filename: Filename
        
    Returns:
        Extension (without dot)
    """
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[-1].lower()


class ProgressTracker:
    """Simple progress tracker for long-running operations"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def complete(self):
        """Mark as complete"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"{self.description} completed in {elapsed:.2f} seconds")
