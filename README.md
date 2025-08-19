# GraveKeeper

A comprehensive document processing and sensitive data detection tool that processes links from CSV files, downloads documents, extracts text using OCR, and analyzes content for sensitive information.

## Features

- **CSV Link Processing**: Read and validate links from CSV files
- **Multi-Source Downloads**: Download files from Box, SharePoint, OneDrive, Google Drive, and other cloud storage services
- **Text Extraction**: Extract text from various file formats using OCR and native extraction
- **Text Chunking**: Prepare extracted text for AI processing by breaking into manageable chunks
- **Sensitive Data Detection**: AI-powered detection of sensitive information (placeholder for future implementation)
- **Comprehensive Logging**: Detailed logging and progress tracking
- **Modular Architecture**: Well-organized code structure for easy expansion

## Supported File Types

### Documents
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Plain Text (.txt)
- Rich Text (.rtf)

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff)
- BMP (.bmp)

### Spreadsheets
- Excel (.xls, .xlsx)
- CSV (.csv)

### Presentations
- PowerPoint (.ppt, .pptx) - *Text extraction not yet implemented*

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd GraveKeeper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (required for image text extraction):

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### Basic Usage

Process a CSV file containing links:

```bash
python src/main.py -c links.csv
```

### Advanced Usage

```bash
python src/main.py \
  --csv-file links.csv \
  --link-column "url" \
  --output-dir ./results \
  --chunk-size 1500 \
  --verbose
```


### Command Line Options

- `-c, --csv-file`: Path to CSV file containing links
- `-l, --link-column`: Name of column containing links (default: "link")
- `-f, --local-files`: One or more local document files to process directly (bypasses CSV)
- `-o, --output-dir`: Output directory for results
- `--chunk-size`: Text chunk size for AI processing (default: 1000)
- `--skip-download`: Skip download step (use existing files)
- `--skip-ocr`: Skip OCR/text extraction step
- `--skip-ai`: Skip AI processing step
- `--disable-pdf-ocr`: Disable OCR on PDF images (by default, OCR is run on all PDF pages)
- `--ai-provider`: AI provider to use (default: ollama)
- `--ai-model`: AI model to use (provider-specific, e.g. llama3.1, qwen2.5vl)
- `--ai-host`: AI host/base URL (provider-specific)
- `-v, --verbose`: Enable verbose logging

#### Modes
- You must provide either `--csv-file` or `--local-files` (not both).
- In local file mode, you can process any supported document directly.

#### PDF OCR
- By default, OCR is run on every page of every PDF, even if text extraction succeeds. Use `--disable-pdf-ocr` to turn this off.

#### Multi-Model AI (Ollama + Qwen2.5VL)
- The pipeline supports running multiple models for sensitive data detection.
- For every image processed with OCR, the text is analyzed by both the main model (e.g. llama3.1) and Qwen2.5VL. Qwen2.5VL results are included in the extraction metadata.
- The file name is also included in the AI and heuristic analysis for better detection.

### CSV Format

Your CSV file should contain a column with links. Example:

```csv
link,description,source
https://box.com/s/abc123,Contract document,Box
https://sharepoint.com/sites/xyz/file.pdf,Report,SharePoint
https://drive.google.com/file/d/def456,Presentation,Google Drive
```

## Project Structure

```
GraveKeeper/
├── src/
│   ├── config/           # Configuration settings
│   ├── input/            # CSV processing
│   ├── download/         # File downloading
│   ├── ocr/              # Text extraction and OCR
│   ├── processing/       # Text chunking
│   ├── ai/               # AI processing (placeholder)
│   ├── utils/            # Utility functions
│   └── main.py           # Main application entry point
├── data/                 # Generated data directory
│   ├── downloads/        # Downloaded files
│   ├── processed/        # Processed files
│   ├── temp/             # Temporary files
│   └── logs/             # Log files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

Create a `.env` file in the project root to customize settings:

```env
# File processing
MAX_FILE_SIZE_MB=100

# OCR settings
OCR_LANGUAGE=eng
OCR_TIMEOUT=30

# Download settings
DOWNLOAD_TIMEOUT=30
MAX_RETRIES=3
CHUNK_SIZE=8192

# AI settings (for future implementation)
AI_MODEL_PATH=
AI_BATCH_SIZE=10
AI_CONFIDENCE_THRESHOLD=0.8

# Logging
LOG_LEVEL=INFO
```

## Output Files

The application generates several output files:

- `csv_processing_results.csv`: Results of CSV link validation
- `download_results.json`: Download status and metadata
- `extraction_results.json`: Text extraction results
- `text_chunks.json`: Chunked text for AI processing
- `ai_detection_results.json`: AI processing results
- `final_report.json`: Complete processing summary
- `summary.txt`: Human-readable summary

## Extending the Project

### Adding New File Types

1. Update `settings.py` to add new extensions to `SUPPORTED_EXTENSIONS`
2. Implement extraction logic in `TextExtractor` class
3. Add appropriate dependencies to `requirements.txt`

### Implementing AI Detection

1. Replace the placeholder implementation in `SensitiveDataDetector`
2. Add your AI model and inference logic
3. Update the detection methods to use your model

### Adding New Download Sources

1. Implement source-specific logic in the `FileDownloader` class
2. Add authentication handling if required
3. Update the source detection logic in `CSVProcessor`

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Install Tesseract OCR and ensure it's in your PATH
2. **Download failures**: Check network connectivity and file permissions
3. **Memory issues**: Reduce chunk size or process files in smaller batches
4. **File size limits**: Adjust `MAX_FILE_SIZE_MB` in settings

### Logs

Check the logs in `data/logs/gravekeeper.log` for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- [ ] Implement presentation text extraction
- [ ] Add support for more cloud storage providers
- [ ] Implement advanced AI models for sensitive data detection
- [ ] Add web interface for easier interaction
- [ ] Support for batch processing with resume capability
- [ ] Integration with external AI services
- [ ] Real-time processing dashboard


## AI Providers & Multi-Model Support


### Local (Ollama)

#### Install Ollama

**macOS:**
```bash
brew install ollama
```

**Ubuntu / Debian:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download the Windows installer from [Ollama's official website](https://ollama.com/download) and run it.

#### Start the Ollama Server
```bash
ollama serve
# (runs in the background on port 11434)
```

#### Pull Models
You must pull each model you want to use (e.g. llama3.1, qwen2.5vl):
```bash
ollama pull llama3.1
ollama pull qwen2.5vl
# List all available models:
ollama list
```

#### Run GraveKeeper with Ollama
```bash
python src/main.py -c links.csv --ai-provider ollama --ai-model llama3.1 --ai-host http://localhost:11434
```

- `--ai-provider`: currently `ollama`
- `--ai-model`: model name available in Ollama (`ollama list`), e.g. `llama3.1`, `qwen2.5vl`
- `--ai-host`: base URL (default `http://localhost:11434`)

#### Multi-Model OCR Analysis
- For every image processed with OCR, the text is analyzed by both the main model and Qwen2.5VL. Qwen2.5VL results are included in the extraction metadata for each image.
- The file name is always included in the AI and heuristic analysis for improved detection.

The detector merges provider results with simple pattern heuristics (emails, phones, SSNs, credit cards) for better recall.