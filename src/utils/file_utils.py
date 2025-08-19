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
    # Check if it's a URL (starts with http/https)
    if file_path.startswith(('http://', 'https://')):
        # Use urlparse to safely extract extension from URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(file_path)
            path = parsed.path
            
            # Find the last dot in the path
            last_dot = path.rfind('.')
            if last_dot != -1:
                return path[last_dot:].lower()
            else:
                return ''
        except Exception:
            return ''
    
    # For local file paths, use Path
    try:
        extension = Path(file_path).suffix.lower()
        
        # If no extension, try to detect from file content
        if not extension and Path(file_path).exists():
            extension = _detect_file_extension_from_content(Path(file_path))
        
        return extension
    except Exception:
        return ''

def _detect_file_extension_from_content(file_path: Path) -> str:
    """
    Detect file extension by examining file content
    
    Args:
        file_path: Path to file
        
    Returns:
        Detected file extension with dot (e.g., '.pdf')
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first few bytes to detect file type
            header = f.read(8)
            
            # PDF files start with %PDF
            if header.startswith(b'%PDF'):
                return '.pdf'
            
            # ZIP files (including .docx, .pptx, .xlsx) start with PK
            if header.startswith(b'PK'):
                # Check if it's a PowerPoint file by looking for slide files
                try:
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as zip_file:
                        slide_files = [f for f in zip_file.namelist() if f.startswith('ppt/slides/')]
                        if slide_files:
                            return '.pptx'
                        
                        # Check for Word document
                        word_files = [f for f in zip_file.namelist() if f.startswith('word/')]
                        if word_files:
                            return '.docx'
                        
                        # Check for Excel document
                        excel_files = [f for f in zip_file.namelist() if f.startswith('xl/')]
                        if excel_files:
                            return '.xlsx'
                        
                        # Generic ZIP
                        return '.zip'
                except Exception:
                    return '.zip'
            
            # Check for other file types
            if header.startswith(b'\xff\xd8\xff'):  # JPEG
                return '.jpg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                return '.png'
            elif header.startswith(b'GIF8'):  # GIF
                return '.gif'
            elif header.startswith(b'BM'):  # BMP
                return '.bmp'
            elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):  # TIFF
                return '.tiff'
            
    except Exception as e:
        logger.warning(f"Error detecting file extension for {file_path}: {e}")
    
    return ''

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
    
    # Handle very long URLs by using a hash-based filename
    if len(url) > 200:  # If URL is very long, use hash-based filename
        # Try to extract meaningful info from URL
        if 'box.com' in url.lower() or 'public.boxcloud.com' in url.lower():
            filename = f"box_file_{hash(url) % 100000}"
        elif 'sharepoint.com' in url.lower():
            filename = f"sharepoint_file_{hash(url) % 100000}"
        elif 'drive.google.com' in url.lower():
            filename = f"gdrive_file_{hash(url) % 100000}"
        else:
            filename = f"downloaded_file_{hash(url) % 100000}"
    elif not filename or '.' not in filename:
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