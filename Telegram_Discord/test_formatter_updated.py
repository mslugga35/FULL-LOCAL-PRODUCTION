#!/usr/bin/env python3
"""
Test script for the updated picks formatter
"""
import os
import sys
from PIL import Image
import easyocr

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.picks_formatter import format_clean_picks

def test_single_image(image_path, reader):
    """Test a single image with OCR and formatting"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(image_path)}")
    print('='*60)
    
    try:
        # Run OCR
        result = reader.readtext(image_path)
        ocr_text = ' '.join([detection[1] for detection in result])
        
        print("RAW OCR TEXT:")
        print("-" * 40)
        print(ocr_text)
        print()
        
        # Apply our formatter
        formatted = format_clean_picks("test_channel", "", ocr_text)
        
        print("FORMATTED OUTPUT:")
        print("-" * 40)
        print(formatted)
        print()
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def main():
    """Test the formatter on sample images"""
    test_dir = "test_formatter/20250918"
    
    if not os.path.exists(test_dir):
        print(f"Test directory {test_dir} not found!")
        return
    
    # Initialize OCR reader
    print("Initializing OCR reader...")
    reader = easyocr.Reader(['en'])
    
    # Test specific interesting images
    test_images = [
        "photo_2025-09-18_19-37-33.jpg",  # @cappersfree with Dolphins pick
        "photo_2025-09-18_20-07-29.jpg",  # NFL Bills pick
        "-1002592669126_11637.jpg",       # Marlins ML with @cappersfree
        "photo_2025-09-18_20-08-37.jpg",  # Another sample
        "-1002592669126_11640.jpg",       # Another sample
    ]
    
    for img_name in test_images:
        img_path = os.path.join(test_dir, img_name)
        if os.path.exists(img_path):
            test_single_image(img_path, reader)
        else:
            print(f"Image {img_name} not found, skipping...")
    
    print(f"\n{'='*60}")
    print("Testing complete!")
    print('='*60)

if __name__ == "__main__":
    main()