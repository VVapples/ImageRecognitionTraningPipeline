"""Orchestrate parallel Blender rendering for YOLO dataset generation.

This script manages multiple Blender processes in parallel to generate
synthetic training images with YOLO annotations.

Usage:
  python arranger.py --blend-file ./Untitled.blend --output-dir ./output \\
                     --image-count 100 --workers 4

Example (Windows):
  python arranger.py --blend-file "E:\\Workspace\\active\\NAFT\\MarsCamera\\MAIN\\test space\\Untitled.blend" --output-dir "./output" --image-count 50 --workers 2
"""

from __future__ import annotations

import argparse
from datetime import datetime
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


def find_blender_executable() -> str | None:
    """Try to find Blender executable in common locations."""
    common_paths = [
        "blender",  # In PATH
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        r"D:\SteamLibrary\steamapps\common\Blender\blender.exe",
        r"/usr/bin/blender",
        r"/usr/local/bin/blender",
        r"/Applications/Blender.app/Contents/MacOS/Blender",
    ]
    
    for path in common_paths:
        if shutil.which(path) or os.path.isfile(path):
            return path
    
    return None


def render_single_image(
    blender_exe: str,
    blend_file: str,
    render_script: str,
    output_dir: str,
    image_index: int,
    stagger_ms: int,
    workers: int,
) -> tuple[int, bool, str]:
    """Render a single image using Blender subprocess.
    
    Returns:
        (image_index, success, error_message)
    """
    try:
        if stagger_ms > 0 and workers > 0:
            worker_slot = image_index % workers
            offset_ms = int((stagger_ms * worker_slot) / max(workers, 1))
            time.sleep(offset_ms / 1000.0)

        cmd = [
            blender_exe,
            "--background",
            blend_file,
            "--python", render_script,
            "--",
            "--output-dir", output_dir,
            "--image-index", str(image_index),
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per image
        )
        
        if result.returncode == 0:
            return (image_index, True, "")
        else:
            error = result.stderr[-500:] if result.stderr else "Unknown error"
            return (image_index, False, error)
    
    except subprocess.TimeoutExpired:
        return (image_index, False, "Timeout after 5 minutes")
    except Exception as e:
        return (image_index, False, str(e))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate YOLO training images using Blender"
    )
    parser.add_argument(
        "--blend-file",
        required=True,
        help="Path to input .blend file"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory for images and labels (default: ./output)"
    )
    parser.add_argument(
        "--image-count",
        type=int,
        default=100,
        help="Number of images to generate (default: 100)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel Blender processes (default: 4)"
    )
    parser.add_argument(
        "--blender-exe",
        help="Path to Blender executable (auto-detected if not specified)"
    )
    parser.add_argument(
        "--stagger-ms",
        type=int,
        default=1000,
        help="Random stagger in ms before each render (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Validate blend file
    if not os.path.isfile(args.blend_file):
        print(f"Error: Blend file not found: {args.blend_file}", file=sys.stderr)
        return 1
    
    # Find render script
    script_dir = Path(__file__).parent
    render_script = script_dir / "render_and_label.py"
    if not render_script.is_file():
        print(f"Error: Render script not found: {render_script}", file=sys.stderr)
        return 1
    
    # Find Blender executable
    blender_exe = args.blender_exe or find_blender_executable()
    if not blender_exe:
        print("Error: Could not find Blender executable. Please specify --blender-exe", file=sys.stderr)
        return 1
    
    print(f"Blender executable: {blender_exe}")
    print(f"Blend file: {args.blend_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Image count: {args.image_count}")
    print(f"Parallel workers: {args.workers}")
    print(f"Stagger (ms): {args.stagger_ms}")
    print()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Track progress
    completed = 0
    failed = 0
    
    # Execute renders in parallel
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                render_single_image,
                blender_exe,
                args.blend_file,
                str(render_script),
                args.output_dir,
                i,
                    args.stagger_ms,
                    args.workers,
            ): i
            for i in range(args.image_count)
        }
        
        for future in as_completed(futures):
            image_index, success, error = future.result()
            timestamp = datetime.now().strftime("%H:%M")
            
            if success:
                completed += 1
                print(f"[{timestamp}] [{completed + failed}/{args.image_count}] ✓ Image {image_index:06d} completed")
            else:
                failed += 1
                print(f"[{timestamp}] [{completed + failed}/{args.image_count}] ✗ Image {image_index:06d} FAILED: {error}")
    
    print()
    print(f"=== Summary ===")
    print(f"Total: {args.image_count}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Output: {args.output_dir}")
    
    # Check for classes.txt
    classes_file = os.path.join(args.output_dir, "classes.txt")
    if os.path.isfile(classes_file):
        with open(classes_file, "r") as f:
            class_names = [line.strip() for line in f if line.strip()]
        print(f"Classes ({len(class_names)}): {', '.join(class_names)}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
