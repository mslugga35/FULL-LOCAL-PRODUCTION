#!/usr/bin/env python3
"""
Test script to OCR images and run them through our picks formatter
"""

import os
import sys
import glob
from pathlib import Path

# Add src to path to import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from utils.ocr import extract_text_from_image
    from utils.picks_formatter import format_clean_picks
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)

def test_image(image_path):
    """Test a single image through OCR and formatter"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    try:
        # Extract text via OCR
        ocr_text = extract_text_from_image(image_path)
        
        print("RAW OCR OUTPUT:")
        print("-" * 30)
        print(repr(ocr_text))
        print("-" * 30)
        print(ocr_text)
        print()
        
        # Run through formatter
        formatted = format_clean_picks("test_image", "", ocr_text)
        
        print("FORMATTED OUTPUT:")
        print("-" * 30)
        print(formatted)
        print("-" * 30)
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def main():
    test_dir = Path("test_formatter/20250918")
    
    if not test_dir.exists():
        print(f"Test directory {test_dir} not found")
        return
    
    # Get a few sample images for testing
    image_files = list(test_dir.glob("*.jpg"))[:10]  # Test first 10 images
    
    if not image_files:
        print("No .jpg files found in test directory")
        return
    
    print(f"Found {len(image_files)} images to test")
    
    for img_path in image_files:
        test_image(str(img_path))
        
        # Wait for user input between images
        user_input = input("\nPress Enter for next image, 'q' to quit, 's' to skip ahead 5: ")
        if user_input.lower() == 'q':
            break
        elif user_input.lower() == 's':
            # Skip ahead 5 images
            current_idx = image_files.index(img_path)
            if current_idx + 5 < len(image_files):
                image_files = image_files[current_idx + 5:]
            else:
                break

if __name__ == "__main__":
    main()