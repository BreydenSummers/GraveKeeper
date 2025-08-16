"""
OCR and text extraction for GraveKeeper
"""
import pytesseract
from PIL import Image
import PyPDF2
import docx
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import io
import fitz  # PyMuPDF for better PDF handling
import openpyxl
from openpyxl import load_workbook

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.file_utils import get_file_extension, get_file_category

class TextExtractor:
    """Extract text from various file types using OCR and native extraction"""
    
    def __init__(self):
        """Initialize text extractor"""
        # Configure tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        
    def extract_text(self, file_path: Path) -> Dict:
        """
        Extract text from file based on its type
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            file_extension = get_file_extension(str(file_path))
            file_category = get_file_category(str(file_path))
            
            result = {
                'file_path': str(file_path),
                'file_extension': file_extension,
                'file_category': file_category,
                'text_content': '',
                'extraction_method': '',
                'confidence': 0.0,
                'error': None,
                'metadata': {}
            }
            
            if file_category == 'images':
                result.update(self._extract_from_image(file_path))
            elif file_category == 'documents':
                result.update(self._extract_from_document(file_path))
            elif file_category == 'spreadsheets':
                result.update(self._extract_from_spreadsheet(file_path))
            elif file_category == 'presentations':
                result.update(self._extract_from_presentation(file_path))
            else:
                result['error'] = f'Unsupported file type: {file_extension}'
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'error': str(e),
                'text_content': '',
                'extraction_method': 'failed'
            }
    
    def _extract_from_image(self, file_path: Path) -> Dict:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary with extracted text and OCR metadata
        """
        try:
            # Open image
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=settings.OCR_LANGUAGE,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Get confidence data
            data = pytesseract.image_to_data(
                image,
                lang=settings.OCR_LANGUAGE,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text_content': text.strip(),
                'extraction_method': 'ocr',
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode,
                    'ocr_language': settings.OCR_LANGUAGE
                }
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'ocr_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_document(self, file_path: Path) -> Dict:
        """
        Extract text from document files (PDF, DOC, DOCX, TXT)
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary with extracted text
        """
        file_extension = get_file_extension(str(file_path))
        
        if file_extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_extension in ['.doc', '.docx']:
            return self._extract_from_word(file_path)
        elif file_extension == '.txt':
            return self._extract_from_text(file_path)
        else:
            return {
                'text_content': '',
                'extraction_method': 'unsupported',
                'error': f'Unsupported document type: {file_extension}'
            }
    
    def _extract_from_pdf(self, file_path: Path) -> Dict:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text
        """
        try:
            text_content = ""
            
            # Try PyMuPDF first (better text extraction)
            try:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_content += page.get_text()
                doc.close()
                extraction_method = "pymupdf"
            except Exception as e:
                logger.warning(f"PyMuPDF failed for {file_path}, trying PyPDF2: {e}")
                
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() or ""
                extraction_method = "pypdf2"
            
            return {
                'text_content': text_content.strip(),
                'extraction_method': extraction_method,
                'confidence': 1.0,  # Native extraction is usually reliable
                'metadata': {
                    'pdf_pages': len(doc) if 'doc' in locals() else 'unknown'
                }
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'pdf_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_word(self, file_path: Path) -> Dict:
        """
        Extract text from Word documents
        
        Args:
            file_path: Path to Word file
            
        Returns:
            Dictionary with extracted text
        """
        try:
            doc = docx.Document(file_path)
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return {
                'text_content': text_content.strip(),
                'extraction_method': 'python-docx',
                'confidence': 1.0,
                'metadata': {
                    'paragraphs': len(doc.paragraphs)
                }
            }
            
        except Exception as e:
            logger.error(f"Word document extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'word_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_text(self, file_path: Path) -> Dict:
        """
        Extract text from plain text files
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with extracted text
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            return {
                'text_content': text_content.strip(),
                'extraction_method': 'native',
                'confidence': 1.0,
                'metadata': {
                    'encoding': 'utf-8'
                }
            }
            
        except Exception as e:
            logger.error(f"Text file extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'text_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_spreadsheet(self, file_path: Path) -> Dict:
        """
        Extract text from spreadsheet files
        
        Args:
            file_path: Path to spreadsheet file
            
        Returns:
            Dictionary with extracted text
        """
        file_extension = get_file_extension(str(file_path))
        
        if file_extension == '.csv':
            return self._extract_from_csv(file_path)
        elif file_extension in ['.xls', '.xlsx']:
            return self._extract_from_excel(file_path)
        else:
            return {
                'text_content': '',
                'extraction_method': 'unsupported',
                'error': f'Unsupported spreadsheet type: {file_extension}'
            }
    
    def _extract_from_csv(self, file_path: Path) -> Dict:
        """
        Extract text from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary with extracted text
        """
        try:
            df = pd.read_csv(file_path)
            text_content = df.to_string(index=False)
            
            return {
                'text_content': text_content,
                'extraction_method': 'pandas',
                'confidence': 1.0,
                'metadata': {
                    'rows': len(df),
                    'columns': len(df.columns)
                }
            }
            
        except Exception as e:
            logger.error(f"CSV extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'csv_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_excel(self, file_path: Path) -> Dict:
        """
        Extract text from Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary with extracted text
        """
        try:
            workbook = load_workbook(file_path, data_only=True)
            text_content = ""
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                text_content += f"\n--- Sheet: {sheet_name} ---\n"
                
                for row in sheet.iter_rows(values_only=True):
                    row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                    if row_text.strip():
                        text_content += row_text + "\n"
            
            return {
                'text_content': text_content.strip(),
                'extraction_method': 'openpyxl',
                'confidence': 1.0,
                'metadata': {
                    'sheets': len(workbook.sheetnames),
                    'sheet_names': workbook.sheetnames
                }
            }
            
        except Exception as e:
            logger.error(f"Excel extraction failed for {file_path}: {e}")
            return {
                'text_content': '',
                'extraction_method': 'excel_failed',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _extract_from_presentation(self, file_path: Path) -> Dict:
        """
        Extract text from presentation files (placeholder)
        
        Args:
            file_path: Path to presentation file
            
        Returns:
            Dictionary with extracted text
        """
        # TODO: Implement presentation text extraction
        return {
            'text_content': '',
            'extraction_method': 'not_implemented',
            'confidence': 0.0,
            'error': 'Presentation text extraction not yet implemented'
        }
    
    def extract_batch(self, file_paths: List[Path]) -> List[Dict]:
        """
        Extract text from multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of extraction results
        """
        results = []
        
        for file_path in file_paths:
            logger.info(f"Extracting text from {file_path}")
            result = self.extract_text(file_path)
            results.append(result)
        
        return results
    
    def get_extraction_summary(self, results: List[Dict]) -> Dict:
        """
        Get summary of text extraction results
        
        Args:
            results: List of extraction results
            
        Returns:
            Summary dictionary
        """
        total = len(results)
        successful = sum(1 for r in results if r.get('text_content', '').strip())
        failed = sum(1 for r in results if r.get('error'))
        
        methods = {}
        for result in results:
            method = result.get('extraction_method', 'unknown')
            methods[method] = methods.get(method, 0) + 1
        
        return {
            'total_files': total,
            'successful_extractions': successful,
            'failed_extractions': failed,
            'success_rate': successful / total if total > 0 else 0,
            'extraction_methods': methods
        } 