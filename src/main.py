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
@click.option('--csv-file', '-c', required=False, help='Path to CSV file containing links')
@click.option('--link-column', '-l', default='link', help='Name of column containing links (CSV mode)')
@click.option('--local-files', '-f', multiple=True, type=click.Path(exists=True, dir_okay=False), required=False, help='One or more local document files to process directly (bypasses CSV)')
@click.option('--output-dir', '-o', help='Output directory for results')
@click.option('--chunk-size', default=1000, help='Text chunk size for AI processing')
@click.option('--skip-download', is_flag=True, help='Skip download step (use existing files)')
@click.option('--skip-ocr', is_flag=True, help='Skip OCR/text extraction step')
@click.option('--skip-ai', is_flag=True, help='Skip AI processing step')
@click.option('--disable-pdf-ocr', is_flag=True, help='Disable OCR on PDF images (by default, OCR is run on all PDF pages)')
@click.option('--ai-provider', type=click.Choice(['ollama']), default='ollama', help='AI provider to use')
@click.option('--ai-model', default='llama3.1', help='AI model to use (provider-specific)')
@click.option('--ai-host', default='http://localhost:11434', help='AI host/base URL (provider-specific)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(
    csv_file: Optional[str],
    link_column: str,
    local_files: tuple,
    output_dir: Optional[str],
    chunk_size: int,
    skip_download: bool,
    skip_ocr: bool,
    skip_ai: bool,
    disable_pdf_ocr: bool,
    verbose: bool,
    ai_provider: str,
    ai_model: str,
    ai_host: str
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
        logger.info(f"Output directory: {output_path}")

        # Determine mode: CSV or local files
        if local_files and len(local_files) > 0:
            logger.info(f"Processing local files: {local_files}")
            file_to_link_mapping = {str(Path(f)): f"Local file: {Path(f).name}" for f in local_files}
            download_summary = None
            csv_processor = None
            extraction_summary = None
            chunking_summary = None
            detection_summary = None
        elif csv_file:
            logger.info(f"CSV file: {csv_file}")
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
            if not skip_download:
                logger.info("Step 2: Downloading files")
                downloader = FileDownloader()
                download_results = downloader.download_files_batch(valid_links)
                # Create mapping between downloaded files and original links
                file_to_link_mapping = {}
                for result in download_results:
                    if result['status'] == 'success':
                        file_path = result['file_path']
                        original_link = result.get('url', 'Unknown')
                        file_to_link_mapping[file_path] = original_link
                # Export download results
                download_summary = downloader.get_download_summary(download_results)
                logger.info(f"Download complete: {download_summary}")
                # Save download results
                import json
                with open(output_path / "download_results.json", 'w') as f:
                    json.dump(download_results, f, indent=2)
            else:
                logger.info("Skipping download step")
                download_summary = None
                # Use existing files in download directory
                file_to_link_mapping = {}
                for file_path in settings.DOWNLOADS_DIR.glob("*"):
                    if file_path.is_file():
                        # Try to reconstruct link from filename
                        filename = file_path.name
                        if filename.startswith('box_file_'):
                            file_to_link_mapping[str(file_path)] = f"Box file: {filename}"
                        elif filename.startswith('file_'):
                            file_to_link_mapping[str(file_path)] = f"Downloaded file: {filename}"
                        else:
                            file_to_link_mapping[str(file_path)] = f"File: {filename}"
        else:
            logger.error("You must provide either --csv-file or --local-files.")
            sys.exit(1)
        
        if not file_to_link_mapping:
            logger.error("No files available for processing")
            sys.exit(1)

        # Step 3: Extract text from files
        if not skip_ocr:
            logger.info("Step 3: Extracting text from files")
            text_extractor = TextExtractor(pdf_ocr=not disable_pdf_ocr)
            downloaded_files = [Path(file_path) for file_path in file_to_link_mapping.keys()]
            extracted_texts = text_extractor.extract_batch(downloaded_files)
            # Add original link information to extraction results
            for result in extracted_texts:
                file_path = result.get('file_path', '')
                if file_path in file_to_link_mapping:
                    result['original_link'] = file_to_link_mapping[file_path]
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
            extracted_texts = []

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
                sensitive_data_detector = SensitiveDataDetector(provider=ai_provider, model=ai_model, host=ai_host)
                # Process chunks by file (group results by file)
                file_results = sensitive_data_detector.process_chunks_by_file(chunks)
                # Save AI processing results
                ai_results_path = output_path / "ai_detection_results.json"
                with open(ai_results_path, 'w', encoding='utf-8') as f:
                    json.dump(file_results, f, indent=2, ensure_ascii=False)
                # Generate human-readable sensitivity report
                report_path = sensitive_data_detector.generate_file_report(file_results, output_path)
                logger.info(f"Saved detection results to {ai_results_path}")
                logger.info(f"Generated Excel sensitivity report: {report_path}")
                # Calculate detection summary
                total_files = len(file_results)
                high_sensitivity_files = sum(1 for r in file_results if r.get('sensitivity_score', 1) >= 7)
                avg_sensitivity = sum(r.get('sensitivity_score', 1) for r in file_results) / total_files if total_files > 0 else 0
                detection_summary = {
                    'total_files': total_files,
                    'high_sensitivity_files': high_sensitivity_files,
                    'avg_sensitivity_score': avg_sensitivity,
                    'sensitivity_rate': high_sensitivity_files / total_files if total_files > 0 else 0
                }
                logger.info(f"AI processing complete: {detection_summary}")
                # Generate final report
                if csv_processor:
                    csv_summary = csv_processor.get_summary()
                else:
                    csv_summary = {
                        'total_rows': len(file_to_link_mapping),
                        'valid_links': len(file_to_link_mapping),
                        'invalid_links': 0
                    }
                generate_final_report(
                    output_path,
                    csv_summary,
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
            f.write(f"  Total files: {detection_summary['total_files']}\n")
            f.write(f"  High sensitivity files: {detection_summary['high_sensitivity_files']}\n")
            f.write(f"  Average sensitivity score: {detection_summary['avg_sensitivity_score']:.1f}/10\n")
            f.write(f"  High sensitivity rate: {detection_summary['sensitivity_rate']:.2%}\n")

if __name__ == "__main__":
    main() 