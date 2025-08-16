"""
Configuration settings for GraveKeeper
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    DOWNLOADS_DIR = DATA_DIR / "downloads"
    PROCESSED_DIR = DATA_DIR / "processed"
    TEMP_DIR = DATA_DIR / "temp"
    
    # Create directories if they don't exist
    for dir_path in [DATA_DIR, DOWNLOADS_DIR, PROCESSED_DIR, TEMP_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # File processing settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    SUPPORTED_EXTENSIONS = {
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
        'images': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
        'spreadsheets': ['.xls', '.xlsx', '.csv'],
        'presentations': ['.ppt', '.pptx']
    }
    
    # OCR settings
    OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")
    OCR_TIMEOUT = int(os.getenv("OCR_TIMEOUT", "30"))
    
    # Download settings
    DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "8192"))
    
    # AI/ML settings (for future implementation)
    AI_MODEL_PATH = os.getenv("AI_MODEL_PATH", "")
    AI_BATCH_SIZE = int(os.getenv("AI_BATCH_SIZE", "10"))
    AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.8"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = DATA_DIR / "logs" / "gravekeeper.log"
    
    # Create logs directory
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings() 