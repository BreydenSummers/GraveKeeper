"""
CSV input processor for GraveKeeper
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import re

from src.utils.logger import logger
from src.utils.file_utils import is_supported_file_type

class CSVProcessor:
    """Process CSV files containing links to documents"""
    
    def __init__(self, csv_path: Path):
        """
        Initialize CSV processor
        
        Args:
            csv_path: Path to CSV file
        """
        self.csv_path = csv_path
        self.data = None
        self.valid_links = []
        self.invalid_links = []
        
    def load_csv(self) -> bool:
        """
        Load and validate CSV file
        
        Returns:
            True if CSV loaded successfully
        """
        try:
            self.data = pd.read_csv(self.csv_path)
            logger.info(f"Loaded CSV file: {self.csv_path}")
            logger.info(f"Found {len(self.data)} rows")
            return True
        except Exception as e:
            logger.error(f"Error loading CSV file {self.csv_path}: {e}")
            return False
    
    def validate_links(self, link_column: str = "link") -> Tuple[List[Dict], List[Dict]]:
        """
        Validate links in CSV file
        
        Args:
            link_column: Name of column containing links
            
        Returns:
            Tuple of (valid_links, invalid_links)
        """
        if self.data is None:
            logger.error("No CSV data loaded")
            return [], []
        
        if link_column not in self.data.columns:
            logger.error(f"Link column '{link_column}' not found in CSV")
            return [], []
        
        valid_links = []
        invalid_links = []
        
        for index, row in self.data.iterrows():
            link = str(row[link_column]).strip()
            
            if self._is_valid_link(link):
                link_info = {
                    'index': index,
                    'link': link,
                    'filename': self._extract_filename(link),
                    'file_type': self._get_file_type(link),
                    'source': self._get_source_type(link),
                    'row_data': row.to_dict()
                }
                
                if is_supported_file_type(link):
                    valid_links.append(link_info)
                else:
                    link_info['reason'] = 'Unsupported file type'
                    invalid_links.append(link_info)
            else:
                invalid_links.append({
                    'index': index,
                    'link': link,
                    'reason': 'Invalid URL format',
                    'row_data': row.to_dict()
                })
        
        self.valid_links = valid_links
        self.invalid_links = invalid_links
        
        logger.info(f"Validated {len(valid_links)} valid links and {len(invalid_links)} invalid links")
        return valid_links, invalid_links
    
    def _is_valid_link(self, link: str) -> bool:
        """
        Check if link is a valid URL
        
        Args:
            link: URL to validate
            
        Returns:
            True if valid URL
        """
        if not link or link.lower() in ['nan', 'none', '']:
            return False
        
        try:
            result = urlparse(link)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _extract_filename(self, link: str) -> str:
        """
        Extract filename from URL
        
        Args:
            link: URL to extract filename from
            
        Returns:
            Extracted filename
        """
        try:
            parsed = urlparse(link)
            filename = Path(parsed.path).name
            
            if not filename or '.' not in filename:
                # Generate filename from URL
                filename = f"file_{hash(link) % 10000}"
            
            return filename
        except Exception:
            return f"file_{hash(link) % 10000}"
    
    def _get_file_type(self, link: str) -> str:
        """
        Get file type from URL
        
        Args:
            link: URL to analyze
            
        Returns:
            File extension
        """
        return Path(link).suffix.lower()
    
    def _get_source_type(self, link: str) -> str:
        """
        Determine source type from URL
        
        Args:
            link: URL to analyze
            
        Returns:
            Source type (e.g., 'box', 'sharepoint', 'onedrive', etc.)
        """
        link_lower = link.lower()
        
        if 'box.com' in link_lower or 'box.com' in link_lower:
            return 'box'
        elif 'sharepoint.com' in link_lower or 'sharepoint' in link_lower:
            return 'sharepoint'
        elif 'onedrive.live.com' in link_lower or '1drv.ms' in link_lower:
            return 'onedrive'
        elif 'drive.google.com' in link_lower:
            return 'google_drive'
        elif 'dropbox.com' in link_lower:
            return 'dropbox'
        else:
            return 'unknown'
    
    def get_summary(self) -> Dict:
        """
        Get summary of CSV processing results
        
        Returns:
            Summary dictionary
        """
        return {
            'total_rows': len(self.data) if self.data is not None else 0,
            'valid_links': len(self.valid_links),
            'invalid_links': len(self.invalid_links),
            'file_types': self._get_file_type_distribution(),
            'sources': self._get_source_distribution()
        }
    
    def _get_file_type_distribution(self) -> Dict[str, int]:
        """Get distribution of file types"""
        distribution = {}
        for link_info in self.valid_links:
            file_type = link_info['file_type']
            distribution[file_type] = distribution.get(file_type, 0) + 1
        return distribution
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of source types"""
        distribution = {}
        for link_info in self.valid_links:
            source = link_info['source']
            distribution[source] = distribution.get(source, 0) + 1
        return distribution
    
    def export_results(self, output_path: Path) -> bool:
        """
        Export processing results to CSV
        
        Args:
            output_path: Path to save results
            
        Returns:
            True if export successful
        """
        try:
            results_data = []
            
            for link_info in self.valid_links:
                row = link_info['row_data'].copy()
                row.update({
                    'status': 'valid',
                    'extracted_filename': link_info['filename'],
                    'file_type': link_info['file_type'],
                    'source': link_info['source']
                })
                results_data.append(row)
            
            for link_info in self.invalid_links:
                row = link_info['row_data'].copy()
                row.update({
                    'status': 'invalid',
                    'reason': link_info.get('reason', 'Unknown error')
                })
                results_data.append(row)
            
            results_df = pd.DataFrame(results_data)
            results_df.to_csv(output_path, index=False)
            logger.info(f"Exported results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return False 