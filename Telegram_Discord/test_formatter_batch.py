#!/usr/bin/env python3
"""
Test the new picks formatter on a batch of images
"""
import os
import sys
import glob
from pathlib import Path

# Add src to path so we can import the formatter
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.picks_formatter import format_clean_picks
    from utils.ocr import extract_text_from_image
except ImportError as e:
    print(f"Error importing: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_image(image_path):
    """Test formatter on a single image"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    try:
        # Extract OCR text
        ocr_text = extract_text_from_image(image_path)
        
        if not ocr_text:
            print("ERROR: No OCR text extracted")
            return
            
        print(f"OCR Text:\n{ocr_text}\n")
        print("-" * 40)
        
        # Format with the new formatter
        formatted = format_clean_picks("Test", "", ocr_text)
        
        print(f"Formatted Output:\n{formatted}")
        
    except Exception as e:
        print(f"ERROR processing {image_path}: {e}")

def main():
    test_dir = "test_formatter/20250918"
    
    if not os.path.exists(test_dir):
        print(f"ERROR: Test directory not found: {test_dir}")
        return
    
    # Get all JPG files
    image_files = glob.glob(os.path.join(test_dir, "*.jpg"))
    
    if not image_files:
        print(f"ERROR: No JPG files found in {test_dir}")
        return
    
    print(f"Found {len(image_files)} images to test")
    
    # Test first 5 images to avoid overwhelming output
    for i, image_path in enumerate(sorted(image_files)[:5]):
        test_image(image_path)
        
        if i < 4:  # Don't pause after the last one
            input("\nPress Enter for next image...")
    
    print(f"\nSUCCESS: Tested {min(5, len(image_files))} images")
    if len(image_files) > 5:
        print(f"NOTE: {len(image_files) - 5} more images available for testing")

if __name__ == "__main__":
    main()