"""
Main application entry point for GraveKeeper
"""
import click
from pathlib import Path
from typing import Optional
import sys

from src.config.settings import settings
from src.utils.logger import logger
from src.input.csv_processor import CSVProcessor
from src.download.downloader import FileDownloader
from src.ocr.text_extractor import TextExtractor
from src.processing.text_chunker import TextChunker
from src.ai.sensitive_data_detector import SensitiveDataDetector

@click.command()
@click.option('--csv-file', '-c', required=True, help='Path to CSV file containing links')
@click.option('--link-column', '-l', default='link', help='Name of column containing links')
@click.option('--output-dir', '-o', help='Output directory for results')
@click.option('--chunk-size', default=1000, help='Text chunk size for AI processing')
@click.option('--skip-download', is_flag=True, help='Skip download step (use existing files)')
@click.option('--skip-ocr', is_flag=True, help='Skip OCR/text extraction step')
@click.option('--skip-ai', is_flag=True, help='Skip AI processing step')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(
    csv_file: str,
    link_column: str,
    output_dir: Optional[str],
    chunk_size: int,
    skip_download: bool,
    skip_ocr: bool,
    skip_ai: bool,
    verbose: bool
):
    """
    GraveKeeper - Document Processing and Sensitive Data Detection
    
    Process links from CSV file, download files, extract text, and detect sensitive data.
    """
    try:
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = settings.DATA_DIR / "results"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Set log level
        if verbose:
            logger.setLevel('DEBUG')
        
        logger.info("Starting GraveKeeper document processing")
        logger.info(f"CSV file: {csv_file}")
        logger.info(f"Output directory: {output_path}")
        
        # Step 1: Process CSV file
        logger.info("Step 1: Processing CSV file")
        csv_processor = CSVProcessor(Path(csv_file))
        
        if not csv_processor.load_csv():
            logger.error("Failed to load CSV file")
            sys.exit(1)
        
        valid_links, invalid_links = csv_processor.validate_links(link_column)
        
        if not valid_links:
            logger.error("No valid links found in CSV file")
            sys.exit(1)
        
        # Export CSV processing results
        csv_results_path = output_path / "csv_processing_results.csv"
        csv_processor.export_results(csv_results_path)
        
        logger.info(f"CSV processing complete: {len(valid_links)} valid links, {len(invalid_links)} invalid links")
        
        # Step 2: Download files
        downloaded_files = []
        if not skip_download:
            logger.info("Step 2: Downloading files")
            downloader = FileDownloader()
            
            download_results = downloader.download_files_batch(valid_links)
            
            # Filter successful downloads
            for result in download_results:
                if result['status'] == 'success':
                    downloaded_files.append(Path(result['file_path']))
            
            # Export download results
            download_summary = downloader.get_download_summary(download_results)
            logger.info(f"Download complete: {download_summary}")
            
            # Save download results
            import json
            with open(output_path / "download_results.json", 'w') as f:
                json.dump(download_results, f, indent=2)
        else:
            logger.info("Skipping download step")
            # Use existing files in download directory
            downloaded_files = list(settings.DOWNLOADS_DIR.glob("*"))
        
        if not downloaded_files:
            logger.error("No files available for processing")
            sys.exit(1)
        
        # Step 3: Extract text
        extracted_texts = []
        if not skip_ocr:
            logger.info("Step 3: Extracting text from files")
            text_extractor = TextExtractor()
            
            extracted_texts = text_extractor.extract_batch(downloaded_files)
            
            # Filter successful extractions
            successful_extractions = [r for r in extracted_texts if r.get('text_content', '').strip()]
            
            # Export extraction results
            extraction_summary = text_extractor.get_extraction_summary(extracted_texts)
            logger.info(f"Text extraction complete: {extraction_summary}")
            
            # Save extraction results
            import json
            with open(output_path / "extraction_results.json", 'w') as f:
                json.dump(extracted_texts, f, indent=2)
        else:
            logger.info("Skipping OCR/text extraction step")
        
        # Step 4: Chunk text for AI processing
        if extracted_texts and not skip_ai:
            logger.info("Step 4: Chunking text for AI processing")
            text_chunker = TextChunker(chunk_size=chunk_size)
            
            chunks = text_chunker.chunk_extraction_results(extracted_texts)
            
            if chunks:
                # Save chunks
                chunks_path = output_path / "text_chunks.json"
                text_chunker.save_chunks(chunks, chunks_path)
                
                chunking_summary = text_chunker.get_chunking_summary(chunks)
                logger.info(f"Text chunking complete: {chunking_summary}")
                
                # Step 5: AI processing for sensitive data detection
                logger.info("Step 5: Processing chunks for sensitive data detection")
                sensitive_data_detector = SensitiveDataDetector()
                
                processed_chunks = sensitive_data_detector.process_chunks(chunks)
                
                # Save AI processing results
                ai_results_path = output_path / "ai_detection_results.json"
                sensitive_data_detector.save_results(processed_chunks, ai_results_path)
                
                # Get detection summary
                detection_summary = sensitive_data_detector.get_detection_summary(processed_chunks)
                logger.info(f"AI processing complete: {detection_summary}")
                
                # Generate final report
                generate_final_report(
                    output_path,
                    csv_processor.get_summary(),
                    download_summary if not skip_download else None,
                    extraction_summary if not skip_ocr else None,
                    chunking_summary if not skip_ai else None,
                    detection_summary if not skip_ai else None
                )
            else:
                logger.warning("No text chunks created for AI processing")
        else:
            logger.info("Skipping AI processing step")
        
        logger.info("GraveKeeper processing complete!")
        logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def generate_final_report(
    output_path: Path,
    csv_summary: dict,
    download_summary: Optional[dict],
    extraction_summary: Optional[dict],
    chunking_summary: Optional[dict],
    detection_summary: Optional[dict]
):
    """Generate a final summary report"""
    report = {
        "timestamp": str(Path().cwd()),
        "summary": {
            "csv_processing": csv_summary,
            "download": download_summary,
            "text_extraction": extraction_summary,
            "text_chunking": chunking_summary,
            "ai_detection": detection_summary
        }
    }
    
    import json
    with open(output_path / "final_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also create a human-readable summary
    with open(output_path / "summary.txt", 'w') as f:
        f.write("GraveKeeper Processing Summary\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"CSV Processing:\n")
        f.write(f"  Total rows: {csv_summary['total_rows']}\n")
        f.write(f"  Valid links: {csv_summary['valid_links']}\n")
        f.write(f"  Invalid links: {csv_summary['invalid_links']}\n\n")
        
        if download_summary:
            f.write(f"Download:\n")
            f.write(f"  Total files: {download_summary['total_files']}\n")
            f.write(f"  Successful: {download_summary['successful_downloads']}\n")
            f.write(f"  Failed: {download_summary['failed_downloads']}\n")
            f.write(f"  Success rate: {download_summary['success_rate']:.2%}\n\n")
        
        if extraction_summary:
            f.write(f"Text Extraction:\n")
            f.write(f"  Total files: {extraction_summary['total_files']}\n")
            f.write(f"  Successful: {extraction_summary['successful_extractions']}\n")
            f.write(f"  Failed: {extraction_summary['failed_extractions']}\n")
            f.write(f"  Success rate: {extraction_summary['success_rate']:.2%}\n\n")
        
        if chunking_summary:
            f.write(f"Text Chunking:\n")
            f.write(f"  Total chunks: {chunking_summary['total_chunks']}\n")
            f.write(f"  Total words: {chunking_summary['total_words']}\n")
            f.write(f"  Files processed: {chunking_summary['files_processed']}\n\n")
        
        if detection_summary:
            f.write(f"AI Detection:\n")
            f.write(f"  Total chunks: {detection_summary['total_chunks']}\n")
            f.write(f"  Sensitive chunks: {detection_summary['sensitive_chunks']}\n")
            f.write(f"  Sensitivity rate: {detection_summary['sensitivity_rate']:.2%}\n")
            f.write(f"  Categories: {detection_summary['sensitive_categories']}\n")

if __name__ == "__main__":
    main() 