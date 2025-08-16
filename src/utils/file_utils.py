"""
File utility functions for GraveKeeper
"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import mimetypes

from src.config.settings import settings
from src.utils.logger import logger

def get_file_extension(file_path: str) -> str:
    """
    Get file extension from file path or URL
    
    Args:
        file_path: Path or URL to file
        
    Returns:
        File extension with dot (e.g., '.pdf')
    """
    return Path(file_path).suffix.lower()

def is_supported_file_type(file_path: str) -> bool:
    """
    Check if file type is supported for processing
    
    Args:
        file_path: Path or URL to file
        
    Returns:
        True if file type is supported
    """
    extension = get_file_extension(file_path)
    all_supported = []
    for extensions in settings.SUPPORTED_EXTENSIONS.values():
        all_supported.extend(extensions)
    
    return extension in all_supported

def get_file_category(file_path: str) -> Optional[str]:
    """
    Get the category of a file based on its extension
    
    Args:
        file_path: Path or URL to file
        
    Returns:
        Category name or None if not supported
    """
    extension = get_file_extension(file_path)
    
    for category, extensions in settings.SUPPORTED_EXTENSIONS.items():
        if extension in extensions:
            return category
    
    return None

def generate_file_hash(file_path: Path) -> str:
    """
    Generate SHA-256 hash of a file
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA-256 hash string
    """
    hash_sha256 = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error generating hash for {file_path}: {e}")
        return ""

def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0.0

def is_file_too_large(file_path: Path) -> bool:
    """
    Check if file exceeds maximum allowed size
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is too large
    """
    size_mb = get_file_size_mb(file_path)
    return size_mb > settings.MAX_FILE_SIZE_MB

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def extract_filename_from_url(url: str) -> str:
    """
    Extract filename from URL
    
    Args:
        url: URL to extract filename from
        
    Returns:
        Extracted filename
    """
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    if not filename or '.' not in filename:
        # Try to get filename from content-disposition or generate one
        filename = f"downloaded_file_{hash(url) % 10000}"
    
    return sanitize_filename(filename)

def create_unique_filename(base_path: Path, filename: str) -> Path:
    """
    Create a unique filename to avoid conflicts
    
    Args:
        base_path: Base directory path
        filename: Original filename
        
    Returns:
        Unique file path
    """
    counter = 1
    name, ext = os.path.splitext(filename)
    unique_path = base_path / filename
    
    while unique_path.exists():
        unique_path = base_path / f"{name}_{counter}{ext}"
        counter += 1
    
    return unique_path

def get_mime_type(file_path: str) -> str:
    """
    Get MIME type of file
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream' 