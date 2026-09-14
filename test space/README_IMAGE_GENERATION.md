# YOLO Training Image Generation System

This system generates synthetic training images for YOLO object detection using Blender's rendering engine.

## Overview

The system consists of two main components:

1. **`arranger.py`** - Orchestrator that manages parallel Blender rendering processes
2. **`render_and_label.py`** - Blender script that randomizes scenes, renders images, and generates YOLO labels

## Requirements

- Blender 3.0+ (tested with Blender 5.0.1)
- Python 3.7+ (for arranger.py)
- A `.blend` file with:
  - Two collections: "Main" (objects to label) and "Other" (filler objects)
  - Active camera configured in the scene
  - Optional: World shader with "Vector Rotate" and "Environment Texture" nodes
- A `background_images/` folder next to the .blend file with background images (.png, .jpg, .jpeg, etc.)
- Optional: An `hdrs/` folder next to the .blend file with HDR environment maps

## Quick Start

### Basic Usage

Generate 100 training images with 4 parallel workers:

```bash
python arranger.py --blend-file ./Untitled.blend --output-dir ./output --image-count 100 --workers 4
```

### Windows Example

```powershell
python arranger.py --blend-file "E:\Workspace\active\NAFT\MarsCamera\MAIN\test space\Untitled.blend" --output-dir ".\output" --image-count 100 --workers 4
```

### Test Run (Small Batch)

```bash
python arranger.py --blend-file ./Untitled.blend --output-dir ./output --image-count 5 --workers 2
```

## Command Line Options

### arranger.py

```
--blend-file PATH      Path to input .blend file (required)
--output-dir PATH      Output directory for images and labels (default: ./output)
--image-count N        Number of images to generate (default: 100)
--workers N            Number of parallel Blender processes (default: 4)
--blender-exe PATH     Path to Blender executable (auto-detected if not specified)
```

## Output Structure

The system generates:

```
output/
├── classes.txt            # List of object class names (one per line)
├── image_000000.png       # Rendered image
├── image_000000.txt       # YOLO label file
├── image_000001.png
├── image_000001.txt
└── ...
```

### YOLO Label Format

Each `.txt` file contains one line per object:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates are normalized (0-1 range).

Example:
```
0 0.857542 0.160086 0.110008 0.232296
```

### classes.txt Format

One class name per line:

```
MAIN_OBJ
orange
apple
```

Class IDs in label files correspond to line numbers (0-indexed) in `classes.txt`.

## Scene Randomization

For each render, the system randomizes:

### Background Image
- **Random background**: Selects a random image from `./background_images/` folder
- Background is composited behind the transparent render using Blender's compositor
- Supports: .png, .jpg, .jpeg, .bmp, .tga, .tiff formats
- Background is automatically scaled to match render resolution

### Objects
- **All objects in "Main" collection**: Random position within MAIN bounds and rotation
- **All objects in "Other" collection**: Random position within OTHER bounds and rotation
- Position ranges are configurable in `render_and_label.py`:
  ```python
  LOCATION_RANGES_MAIN = {"x": (-10, 10), "y": (-13, 0), "z": (-6, 6)}
  LOCATION_RANGES_OTHER = {"x": (-12, 12), "y": (-15, 0), "z": (-8.0, 8.0)}
  ```

### World Shader (if available)
- **Vector Rotate node**: Random axis and angle
- **Environment Texture node**: Random HDR from `./hdrs/` folder

## Blend File Requirements

### Collections

1. **"Main" collection**: Contains objects to be labeled for YOLO training
   - Object names become class names (e.g., object named "orange" → class "orange")
   - Typically contains EMPTY objects as parents to actual geometry
   - Objects should be visible to camera

2. **"Other" collection**: Contains filler/background objects
   - Not labeled in YOLO output
   - Used for scene variety
   - Also randomized but ignored during labeling

### Camera

- Must have an active camera in the scene
- Camera position/angle determines the rendered view
- Bounding boxes are calculated relative to camera view

### World Shader (Optional)

For environment randomization, set up:
- **Vector Rotate** node (controls HDR rotation)
- **Environment Texture** node (loads HDR files)

Place HDR files in `./hdrs/` folder next to the .blend file.

### Background Images

For background compositing:
- Create a `./background_images/` folder next to the .blend file
- Add background images (supported formats: .png, .jpg, .jpeg, .bmp, .tga, .tiff)
- The system will randomly select one background per render
- Backgrounds are automatically scaled to match render resolution
- The render is composited over the background with transparency support

**Note**: The .blend file should be set to render with transparent film (`Film > Transparent` in render properties) for best results with background compositing.

## Advanced Usage

### Direct Blender Rendering

You can run the render script directly without the arranger:

```bash
blender --background ./Untitled.blend --python render_and_label.py -- --output-dir ./output --image-index 0
```

### Customizing Randomization

Edit `render_and_label.py` to customize:
- Position ranges: `LOCATION_RANGES_MAIN` and `LOCATION_RANGES_OTHER`
- Rotation ranges (currently full 360° on all axes)
- Object filtering criteria
- Label generation logic

### Performance Tuning

- **Workers**: Set to number of CPU cores for maximum speed
- **Timeout**: Modify in `arranger.py` (default: 300 seconds per image)
- **Resolution**: Configure in .blend file render settings

## Troubleshooting

### "Could not find Blender executable"

Specify the Blender path manually:

```bash
python arranger.py --blender-exe "C:\Program Files\Blender Foundation\Blender\blender.exe" ...
```

### "No objects found in Main collection"

- Verify the .blend file has a collection named "Main"
- Check that the collection contains renderable objects (MESH, CURVE, etc.)

### Images render but no labels generated

- Ensure objects are visible to the camera
- Check that objects aren't behind the camera
- Verify bounding boxes overlap the camera view

### Timeout errors

Increase timeout in `arranger.py`:

```python
timeout=600,  # 10 minutes
```

Or reduce render quality/resolution in the .blend file.

## Example Workflow

1. **Prepare .blend file**:
   - Create "Main" and "Other" collections
   - Place target objects in "Main"
   - Set up camera and lighting
   - Configure render settings
   - Enable transparent film (Film > Transparent in render properties)

2. **Collect background images**:
   - Create `./background_images/` folder next to .blend file
   - Add diverse background images for variety
   - Recommended: 50+ different backgrounds for good variety

3. **Collect HDR files** (optional):
   - Download HDR environment maps
   - Place in `./hdrs/` folder next to .blend file

3. **Test with small batch**:
   ```bash
   python arranger.py --blend-file ./scene.blend --output-dir ./test --image-count 5 --workers 1
   ```

4. **Verify output**:
   - Check images render correctly
   - Verify labels are accurate
   - Examine `classes.txt` for correct class names

5. **Generate full dataset**:
   ```bash
   python arranger.py --blend-file ./scene.blend --output-dir ./dataset --image-count 10000 --workers 8
   ```

6. **Train YOLO model** with generated dataset

## Files

- **`arranger.py`**: Main orchestrator script
- **`render_and_label.py`**: Blender rendering and labeling script
- **`scene_preparer.py`**: Legacy scene randomization (reference only)
- **`README_IMAGE_GENERATION.md`**: This file

## Notes

- The system preserves render settings from the .blend file
- Each image uses a fresh randomization seed
- Labels only include objects visible in the camera view
- Bounding boxes are clipped to image boundaries (0-1 range)
- Very small bounding boxes (< 0.1% area) are filtered out
