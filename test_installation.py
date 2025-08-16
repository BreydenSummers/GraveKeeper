#!/usr/bin/env python3
"""
Test script to verify GraveKeeper installation
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import pandas
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import requests
        print("✓ requests imported successfully")
    except ImportError as e:
        print(f"✗ requests import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✓ pytesseract imported successfully")
    except ImportError as e:
        print(f"✗ pytesseract import failed: {e}")
        return False
    
    try:
        import PIL
        print("✓ PIL imported successfully")
    except ImportError as e:
        print(f"✗ PIL import failed: {e}")
        return False
    
    try:
        import click
        print("✓ click imported successfully")
    except ImportError as e:
        print(f"✗ click import failed: {e}")
        return False
    
    return True

def test_project_structure():
    """Test that project structure is correct"""
    print("\nTesting project structure...")
    
    required_files = [
        "src/main.py",
        "src/config/settings.py",
        "src/input/csv_processor.py",
        "src/download/downloader.py",
        "src/ocr/text_extractor.py",
        "src/processing/text_chunker.py",
        "src/ai/sensitive_data_detector.py",
        "src/utils/logger.py",
        "src/utils/file_utils.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_gravekeeper_imports():
    """Test that GraveKeeper modules can be imported"""
    print("\nTesting GraveKeeper imports...")
    
    try:
        from src.config.settings import settings
        print("✓ settings imported successfully")
    except ImportError as e:
        print(f"✗ settings import failed: {e}")
        return False
    
    try:
        from src.utils.logger import logger
        print("✓ logger imported successfully")
    except ImportError as e:
        print(f"✗ logger import failed: {e}")
        return False
    
    try:
        from src.input.csv_processor import CSVProcessor
        print("✓ CSVProcessor imported successfully")
    except ImportError as e:
        print(f"✗ CSVProcessor import failed: {e}")
        return False
    
    try:
        from src.download.downloader import FileDownloader
        print("✓ FileDownloader imported successfully")
    except ImportError as e:
        print(f"✗ FileDownloader import failed: {e}")
        return False
    
    try:
        from src.ocr.text_extractor import TextExtractor
        print("✓ TextExtractor imported successfully")
    except ImportError as e:
        print(f"✗ TextExtractor import failed: {e}")
        return False
    
    return True

def test_tesseract():
    """Test Tesseract OCR installation"""
    print("\nTesting Tesseract OCR...")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"✗ Tesseract not found or not working: {e}")
        print("  Please install Tesseract OCR:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def main():
    """Run all tests"""
    print("GraveKeeper Installation Test")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_imports),
        ("Project Structure", test_project_structure),
        ("GraveKeeper Modules", test_gravekeeper_imports),
        ("Tesseract OCR", test_tesseract)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("Test Results:")
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! GraveKeeper is ready to use.")
        print("\nTo get started:")
        print("1. Create a CSV file with your links")
        print("2. Run: python src/main.py -c your_links.csv")
        print("3. Check the README.md for more options")
    else:
        print("❌ Some tests failed. Please fix the issues above before using GraveKeeper.")
        sys.exit(1)

if __name__ == "__main__":
    main() 