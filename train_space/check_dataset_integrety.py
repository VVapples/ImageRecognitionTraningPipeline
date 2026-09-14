"""
=============================================================================
YOLO Dataset Integrity Checker
=============================================================================

DESCRIPTION:
This script scans a YOLO-formatted dataset to ensure it is perfectly structured 
for training. It prevents training crashes by identifying missing files, broken 
images, and incorrectly formatted bounding box coordinates.

WHAT IT CHECKS:
1. Missing Labels: Images that have no matching .txt file.
2. Missing Images: .txt files that have no matching image.
3. Corrupt Images: Image files that are broken or cannot be opened by the system.
4. Format Errors: Bounding box values that aren't numeric or fall outside the 
   required 0.0 to 1.0 range.
5. Backgrounds: Correctly identifies empty .txt files as valid background images
   (images with no objects).

REQUIREMENTS:
- Python 3.x
- Pillow library (Install via: pip install pillow)

HOW TO USE:
1. Scroll to the very bottom of this script to the 'EXECUTION' block.
2. Change the `BASE_DIR` variable to point to the root of the dataset you 
   want to check (the folder containing the 'images' and 'labels' folders).
   Example: BASE_DIR = "datasets/phase1_sim"
3. Run the script in your terminal:
   python check_dataset_integrety.py

OUTPUT:
The script will print a clean report to your terminal detailing the total number 
of images, backgrounds, and objects, followed by a specific list of any broken 
or missing files it found.
=============================================================================
"""

import os
from pathlib import Path
from PIL import Image

def check_yolo_split(images_dir, labels_dir, split_name):
    print(f"\n" + "="*50)
    print(f"🔍 SCANNING SPLIT: {split_name.upper()}")
    print(f"Images: {images_dir}")
    print(f"Labels: {labels_dir}")
    print("="*50)

    if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
        print("⚠️ ERROR: Directory not found. Skipping split.")
        return

    # 1. Gather files
    valid_exts = {'.jpg', '.jpeg', '.png'}
    image_files = [f for f in os.listdir(images_dir) if Path(f).suffix.lower() in valid_exts]
    label_files = [f for f in os.listdir(labels_dir) if f.endswith('.txt')]

    img_stems = set(Path(f).stem for f in image_files)
    lbl_stems = set(Path(f).stem for f in label_files)

    # 2. Check for missing pairs
    missing_labels = img_stems - lbl_stems
    missing_images = lbl_stems - img_stems

    # 3. Check for corruption and label formatting
    corrupt_images = []
    format_errors = []
    background_count = 0
    total_objects = 0

    print("Checking image integrity and label formats...")
    
    # Check images
    for img in image_files:
        img_path = os.path.join(images_dir, img)
        try:
            with Image.open(img_path) as im:
                im.verify() # Checks if it's a valid, uncorrupted image file
        except Exception:
            corrupt_images.append(img)

    # Check labels
    for lbl in label_files:
        lbl_path = os.path.join(labels_dir, lbl)
        with open(lbl_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            background_count += 1 # Empty file = Background image
            continue

        for line_idx, line in enumerate(lines):
            parts = line.strip().split()
            if not parts:
                continue # Skip empty blank lines
            
            total_objects += 1
            
            if len(parts) != 5:
                format_errors.append(f"{lbl} (Line {line_idx+1}): Expected 5 values, found {len(parts)}.")
                continue
            
            try:
                class_id = int(parts[0])
                x, y, w, h = map(float, parts[1:])
                
                if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                    format_errors.append(f"{lbl} (Line {line_idx+1}): Coordinates out of bounds (must be 0.0 - 1.0).")
            except ValueError:
                format_errors.append(f"{lbl} (Line {line_idx+1}): Contains non-numeric characters.")

    # 4. Print Report
    print(f"\n📊 REPORT FOR {split_name.upper()}")
    print(f"Total Images Found:     {len(image_files)}")
    print(f"Total Backgrounds:      {background_count} (Empty .txt files)")
    print(f"Total Objects Labeled:  {total_objects}")
    
    print("\n🚨 ISSUES FOUND:")
    if not missing_labels and not missing_images and not corrupt_images and not format_errors:
        print("✅ No issues found! Dataset is perfectly formatted.")
    else:
        if missing_labels:
            print(f"❌ Missing Labels ({len(missing_labels)}):")
            for m in list(missing_labels)[:5]: print(f"   - {m}.jpg (or png)")
            if len(missing_labels) > 5: print("   - ...and more")
            
        if missing_images:
            print(f"❌ Missing Images ({len(missing_images)}):")
            for m in list(missing_images)[:5]: print(f"   - {m}.txt")
            if len(missing_images) > 5: print("   - ...and more")
            
        if corrupt_images:
            print(f"❌ Corrupt Images ({len(corrupt_images)}):")
            for c in corrupt_images[:5]: print(f"   - {c}")
            
        if format_errors:
            print(f"❌ Format Errors ({len(format_errors)}):")
            for e in format_errors[:10]: print(f"   - {e}")
            if len(format_errors) > 10: print("   - ...and more")

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    # Change this to point to the root of your dataset 
    # (the folder containing the 'images' and 'labels' folders)
    BASE_DIR = "imageset\step2"
    
    train_images = os.path.join(BASE_DIR, "images", "train")
    train_labels = os.path.join(BASE_DIR, "labels", "train")
    
    val_images = os.path.join(BASE_DIR, "images", "val")
    val_labels = os.path.join(BASE_DIR, "labels", "val")
    
    # Check Train Split
    check_yolo_split(train_images, train_labels, "Train")
    
    # Check Val Split
    check_yolo_split(val_images, val_labels, "Validation")