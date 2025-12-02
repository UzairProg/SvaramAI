"""Utils package initialization"""

from .text_cleaner import (
    remove_diacritics,
    clean_devanagari,
    normalize_whitespace,
    extract_devanagari,
    split_verses,
    is_devanagari,
    count_syllables_approximate,
    romanize_basic
)

from .splitter import SanskritSplitter, get_splitter

from .helpers import (
    format_timestamp,
    truncate_text,
    extract_json_from_text,
    sanitize_filename,
    validate_sanskrit_text,
    chunk_text,
    merge_dicts,
    calculate_confidence,
    safe_divide,
    count_words,
    get_file_extension,
    ProgressTracker
)

__all__ = [
    # text_cleaner
    'remove_diacritics',
    'clean_devanagari',
    'normalize_whitespace',
    'extract_devanagari',
    'split_verses',
    'is_devanagari',
    'count_syllables_approximate',
    'romanize_basic',
    # splitter
    'SanskritSplitter',
    'get_splitter',
    # helpers
    'format_timestamp',
    'truncate_text',
    'extract_json_from_text',
    'sanitize_filename',
    'validate_sanskrit_text',
    'chunk_text',
    'merge_dicts',
    'calculate_confidence',
    'safe_divide',
    'count_words',
    'get_file_extension',
    'ProgressTracker'
]
