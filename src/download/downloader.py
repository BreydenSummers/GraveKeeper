"""
File downloader for GraveKeeper
"""
import requests
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse
import os
from tqdm import tqdm

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.file_utils import (
    extract_filename_from_url,
    create_unique_filename,
    is_file_too_large,
    generate_file_hash
)

class FileDownloader:
    """Download files from various sources"""
    
    def __init__(self, download_dir: Path = None):
        """
        Initialize downloader
        
        Args:
            download_dir: Directory to save downloaded files
        """
        self.download_dir = download_dir or settings.DOWNLOADS_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GraveKeeper/1.0 (Document Processing Tool)'
        })
        
    def download_file(self, url: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        Download a single file
        
        Args:
            url: URL to download from
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Extract filename if not provided
            if not filename:
                filename = extract_filename_from_url(url)
            
            # Create unique filename
            file_path = create_unique_filename(self.download_dir, filename)
            
            logger.info(f"Downloading {url} to {file_path}")
            
            # Check if file already exists (avoid re-downloading)
            if file_path.exists():
                logger.info(f"File already exists: {file_path}")
                return file_path
            
            # Download with progress bar
            response = self.session.get(
                url,
                stream=True,
                timeout=settings.DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()
            
            # Get file size for progress bar
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=filename
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=settings.CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            # Verify file size
            if is_file_too_large(file_path):
                logger.warning(f"File too large: {file_path}")
                file_path.unlink()  # Delete the file
                return None
            
            logger.info(f"Successfully downloaded: {file_path}")
            return file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None
    
    def download_files_batch(self, links: List[Dict]) -> List[Dict]:
        """
        Download multiple files in batch
        
        Args:
            links: List of link dictionaries with 'link' and 'filename' keys
            
        Returns:
            List of download results
        """
        results = []
        
        for link_info in links:
            url = link_info['link']
            filename = link_info.get('filename')
            
            result = {
                'url': url,
                'original_filename': filename,
                'status': 'pending',
                'file_path': None,
                'error': None,
                'file_hash': None,
                'file_size_mb': 0.0
            }
            
            try:
                file_path = self.download_file(url, filename)
                
                if file_path:
                    result.update({
                        'status': 'success',
                        'file_path': str(file_path),
                        'file_hash': generate_file_hash(file_path),
                        'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                    })
                else:
                    result.update({
                        'status': 'failed',
                        'error': 'Download failed'
                    })
                    
            except Exception as e:
                result.update({
                    'status': 'failed',
                    'error': str(e)
                })
            
            results.append(result)
            
            # Add delay between downloads to be respectful
            time.sleep(1)
        
        return results
    
    def download_with_retry(self, url: str, max_retries: int = None) -> Optional[Path]:
        """
        Download file with retry logic
        
        Args:
            url: URL to download
            max_retries: Maximum number of retries
            
        Returns:
            Path to downloaded file or None if failed
        """
        max_retries = max_retries or settings.MAX_RETRIES
        
        for attempt in range(max_retries + 1):
            try:
                file_path = self.download_file(url)
                if file_path:
                    return file_path
                    
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        logger.error(f"All download attempts failed for {url}")
        return None
    
    def handle_sharepoint_link(self, url: str) -> Optional[str]:
        """
        Handle SharePoint links (convert to direct download if possible)
        
        Args:
            url: SharePoint URL
            
        Returns:
            Direct download URL or original URL
        """
        # This is a placeholder for SharePoint-specific logic
        # In a real implementation, you might need to:
        # 1. Authenticate with SharePoint
        # 2. Convert sharing links to direct download URLs
        # 3. Handle different SharePoint link formats
        
        if 'sharepoint.com' in url.lower():
            logger.info(f"Processing SharePoint link: {url}")
            # For now, return the original URL
            # TODO: Implement SharePoint-specific handling
            return url
        
        return url
    
    def handle_box_link(self, url: str) -> Optional[str]:
        """
        Handle Box links (convert to direct download if possible)
        
        Args:
            url: Box URL
            
        Returns:
            Direct download URL or original URL
        """
        # This is a placeholder for Box-specific logic
        # In a real implementation, you might need to:
        # 1. Authenticate with Box API
        # 2. Convert sharing links to direct download URLs
        # 3. Handle different Box link formats
        
        if 'box.com' in url.lower():
            logger.info(f"Processing Box link: {url}")
            # For now, return the original URL
            # TODO: Implement Box-specific handling
            return url
        
        return url
    
    def get_download_summary(self, results: List[Dict]) -> Dict:
        """
        Get summary of download results
        
        Args:
            results: List of download results
            
        Returns:
            Summary dictionary
        """
        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        total_size = sum(r.get('file_size_mb', 0) for r in results if r['status'] == 'success')
        
        return {
            'total_files': total,
            'successful_downloads': successful,
            'failed_downloads': failed,
            'success_rate': successful / total if total > 0 else 0,
            'total_size_mb': total_size
        } 