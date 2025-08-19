"""
Text chunking for AI processing
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
import json

from src.utils.logger import logger

class TextChunker:
    """Chunk text content for AI processing"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize text chunker
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, file_path: str = "") -> List[Dict]:
        """
        Split text into chunks for AI processing
        
        Args:
            text: Text content to chunk
            file_path: Original file path for reference
            
        Returns:
            List of text chunks with metadata
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        text = text.strip()
        
        # Split by paragraphs first
        paragraphs = self._split_by_paragraphs(text)
        
        current_chunk = ""
        chunk_start = 0
        
        for i, paragraph in enumerate(paragraphs):
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = {
                    'chunk_id': len(chunks),
                    'content': current_chunk.strip(),
                    'start_char': chunk_start,
                    'end_char': chunk_start + len(current_chunk),
                    'file_path': file_path,
                    'metadata': {
                        'paragraph_count': current_chunk.count('\n\n') + 1,
                        'word_count': len(current_chunk.split()),
                        'char_count': len(current_chunk)
                    }
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(paragraph)
            else:
                current_chunk += paragraph
        
        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_data = {
                'chunk_id': len(chunks),
                'content': current_chunk.strip(),
                'start_char': chunk_start,
                'end_char': chunk_start + len(current_chunk),
                'file_path': file_path,
                'metadata': {
                    'paragraph_count': current_chunk.count('\n\n') + 1,
                    'word_count': len(current_chunk.split()),
                    'char_count': len(current_chunk)
                }
            }
            chunks.append(chunk_data)
        
        logger.info(f"Created {len(chunks)} chunks from text (file: {file_path})")
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean up paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                cleaned_paragraphs.append(paragraph + '\n\n')
        
        return cleaned_paragraphs
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk
        
        Args:
            text: Text to get overlap from
            
        Returns:
            Overlap text
        """
        if len(text) <= self.overlap:
            return text
        
        # Try to break at word boundary
        overlap_text = text[-self.overlap:]
        last_space = overlap_text.rfind(' ')
        
        if last_space > 0:
            return overlap_text[last_space + 1:]
        
        return overlap_text
    
    def chunk_extraction_results(self, extraction_results: List[Dict]) -> List[Dict]:
        """
        Chunk text from extraction results
        
        Args:
            extraction_results: List of text extraction results
            
        Returns:
            List of chunked text data
        """
        all_chunks = []
        
        for result in extraction_results:
            if result.get('text_content') and not result.get('error'):
                file_path = result.get('file_path', '')
                text_content = result.get('text_content', '')
                
                # Try to get original link from metadata or reconstruct from filename
                original_link = result.get('original_link', 'Unknown')
                if original_link == 'Unknown':
                    # Try to reconstruct from filename patterns
                    filename = Path(file_path).name
                    if filename.startswith('box_file_'):
                        original_link = f"Box file: {filename}"
                    elif filename.startswith('file_'):
                        original_link = f"Downloaded file: {filename}"
                    else:
                        original_link = f"File: {filename}"
                
                chunks = self.chunk_text(text_content, file_path)
                
                # Add extraction metadata and original link to each chunk
                for chunk in chunks:
                    chunk['extraction_metadata'] = {
                        'extraction_method': result.get('extraction_method'),
                        'confidence': result.get('confidence', 0.0),
                        'file_extension': result.get('file_extension'),
                        'file_category': result.get('file_category')
                    }
                    chunk['original_link'] = original_link
                
                all_chunks.extend(chunks)
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks
    
    def save_chunks(self, chunks: List[Dict], output_path: Path) -> bool:
        """
        Save chunks to JSON file
        
        Args:
            chunks: List of chunk data
            output_path: Path to save chunks
            
        Returns:
            True if saved successfully
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(chunks)} chunks to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chunks to {output_path}: {e}")
            return False
    
    def load_chunks(self, input_path: Path) -> List[Dict]:
        """
        Load chunks from JSON file
        
        Args:
            input_path: Path to load chunks from
            
        Returns:
            List of chunk data
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            logger.info(f"Loaded {len(chunks)} chunks from {input_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading chunks from {input_path}: {e}")
            return []
    
    def get_chunking_summary(self, chunks: List[Dict]) -> Dict:
        """
        Get summary of chunking results
        
        Args:
            chunks: List of chunk data
            
        Returns:
            Summary dictionary
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_words': 0,
                'total_characters': 0,
                'avg_chunk_size': 0,
                'files_processed': 0
            }
        
        total_words = sum(chunk['metadata']['word_count'] for chunk in chunks)
        total_chars = sum(chunk['metadata']['char_count'] for chunk in chunks)
        avg_chunk_size = total_chars / len(chunks)
        
        # Count unique files
        unique_files = set(chunk['file_path'] for chunk in chunks if chunk['file_path'])
        
        return {
            'total_chunks': len(chunks),
            'total_words': total_words,
            'total_characters': total_chars,
            'avg_chunk_size': avg_chunk_size,
            'files_processed': len(unique_files)
        } 