"""Render scene with randomization and generate YOLO labels.

This script runs inside Blender to:
1. Randomize object positions/rotations (EMPTY objects in Main/Other collections)
2. Randomize world shader (HDR environment + vector rotate)
3. Render the scene to an image
4. Generate YOLO bounding box labels for objects in "Main" collection

Usage:
  blender --background file.blend --python render_and_label.py -- --output-dir ./output --image-index 0
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
from pathlib import Path


LOCATION_RANGES_OTHER = {
    "x": (-12, 12),
    "y": (-15, 30),
    "z": (-8.0, 8.0),
}

LOCATION_RANGES_MAIN = {
    "x": (-11, 11),
    "y": (-13, 20),
    "z": (-7.0, 7.0),
}


def _parse_args(argv: list[str]) -> dict:
    """Parse arguments after '--'."""
    args = {"output_dir": "./output", "image_index": 0}
    if "--" not in argv:
        return args
    
    idx = argv.index("--") + 1
    tokens = argv[idx:]
    
    i = 0
    while i < len(tokens):
        if tokens[i] == "--output-dir" and i + 1 < len(tokens):
            args["output_dir"] = tokens[i + 1]
            i += 2
        elif tokens[i] == "--image-index" and i + 1 < len(tokens):
            args["image_index"] = int(tokens[i + 1])
            i += 2
        else:
            i += 1
    
    return args


def _random_location_other() -> tuple[float, float, float]:
    return (
        random.uniform(*LOCATION_RANGES_OTHER["x"]),
        random.uniform(*LOCATION_RANGES_OTHER["y"]),
        random.uniform(*LOCATION_RANGES_OTHER["z"]),
    )


def _random_location_main() -> tuple[float, float, float]:
    return (
        random.uniform(*LOCATION_RANGES_MAIN["x"]),
        random.uniform(*LOCATION_RANGES_MAIN["y"]),
        random.uniform(*LOCATION_RANGES_MAIN["z"]),
    )


def _random_rotation_euler() -> tuple[float, float, float]:
    return (
        random.uniform(0.0, 6.283185307179586),
        random.uniform(0.0, 6.283185307179586),
        random.uniform(0.0, 6.283185307179586),
    )


def _random_rotate_axis() -> tuple[float, float, float]:
    return (
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0),
        random.uniform(-1.0, 1.0),
    )


def _random_rotate_angle() -> float:
    return random.uniform(0.0, 6.283185307179586)


def _pick_random_hdr(hdr_dir: str) -> str | None:
    try:
        entries = [
            name for name in os.listdir(hdr_dir)
            if name.lower().endswith(".hdr")
        ]
    except FileNotFoundError:
        return None
    if not entries:
        return None
    return os.path.join(hdr_dir, random.choice(entries))


def _pick_random_background(bg_dir: str) -> str | None:
    """Pick a random background image from the background_images directory."""
    try:
        entries = [
            name for name in os.listdir(bg_dir)
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tga", ".tiff"))
        ]
    except FileNotFoundError:
        return None
    if not entries:
        return None
    return os.path.join(bg_dir, random.choice(entries))


def _compose_with_background(
    bg_image_path: str,
    fg_image_path: str,
    output_path: str,
    width: int,
    height: int,
) -> bool:
    """Composite foreground render over background using ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("Warning: ffmpeg not found, skipping background compositing")
        return False

    filter_graph = (
        f"[0:v]scale={width}:{height}[bg];"
        "[bg][1:v]overlay=0:0:format=auto"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        bg_image_path,
        "-i",
        fg_image_path,
        "-filter_complex",
        filter_graph,
        "-frames:v",
        "1",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr_tail = (result.stderr or "").strip()[-500:]
        print(f"Warning: ffmpeg failed to composite background: {stderr_tail}")
        return False
    return True


def _randomize_world_shader() -> None:
    """Randomize world shader nodes (Vector Rotate + Environment Texture)."""
    import bpy
    
    world = bpy.data.worlds.get("World")
    if not world or not world.use_nodes:
        return
    
    shader_nodes = world.node_tree.nodes
    vector_rotate = shader_nodes.get("Vector Rotate")
    if vector_rotate:
        if hasattr(vector_rotate, "rotation"):
            vector_rotate.rotation = _random_rotate_axis()
        if hasattr(vector_rotate, "angle"):
            vector_rotate.angle = _random_rotate_angle()
    
    environment_texture = shader_nodes.get("Environment Texture")
    if not environment_texture:
        return
    
    blend_dir = os.path.dirname(bpy.data.filepath)
    hdr_dir = os.path.join(blend_dir, "hdrs")
    new_hdr = _pick_random_hdr(hdr_dir)
    if new_hdr:
        environment_texture.image = bpy.data.images.load(new_hdr, check_existing=True)


def _randomize_objects() -> None:
    """Randomize positions/rotations of EMPTY objects in Main/Other collections."""
    import bpy
    
    main_collection = bpy.data.collections.get("Main")
    other_collection = bpy.data.collections.get("Other")
    
    main_objects = set(main_collection.all_objects) if main_collection else set()
    other_objects = set(other_collection.all_objects) if other_collection else set()
    
    for obj in bpy.data.objects:
        if obj in main_objects:
            obj.location = _random_location_main()
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = _random_rotation_euler()
        elif obj in other_objects:
            obj.location = _random_location_other()
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = _random_rotation_euler()


def _get_bounding_box_2d(obj) -> tuple[float, float, float, float] | None:
    """Get normalized YOLO bounding box (x_center, y_center, width, height) for object."""
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    
    scene = bpy.context.scene
    camera = scene.camera
    
    if not camera:
        return None
    
    # Collect all vertices/points to project
    vertices = []
    
    # For mesh objects, use actual vertices for tighter bounding box
    if obj.type == 'MESH' and obj.data.vertices:
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
    # For other object types or objects with children, use bounding box corners
    else:
        vertices = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        # Also include children's vertices if this is a parent (like EMPTY)
        for child in obj.children:
            if child.type == 'MESH' and child.data.vertices:
                vertices.extend([child.matrix_world @ v.co for v in child.data.vertices])
            else:
                vertices.extend([child.matrix_world @ Vector(corner) for corner in child.bound_box])
    
    # Project to camera view (normalized 0-1 coordinates)
    coords_2d = []
    for vertex in vertices:
        # Project world coordinate to camera view
        co_2d = world_to_camera_view(scene, camera, vertex)
        
        # Skip if behind camera (z < 0 in camera space)
        if co_2d.z < 0:
            continue
        
        # co_2d.x and co_2d.y are already normalized (0-1)
        # Flip Y for YOLO format (0 at top, 1 at bottom)
        coords_2d.append((co_2d.x, 1.0 - co_2d.y))
    
    if not coords_2d:
        return None
    
    # Get bounding rectangle
    x_coords = [c[0] for c in coords_2d]
    y_coords = [c[1] for c in coords_2d]
    
    x_min = max(0.0, min(x_coords))
    x_max = min(1.0, max(x_coords))
    y_min = max(0.0, min(y_coords))
    y_max = min(1.0, max(y_coords))
    
    width = x_max - x_min
    height = y_max - y_min
    
    # Skip if too small or out of frame
    if width <= 0.001 or height <= 0.001:
        return None
    
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    
    return (x_center, y_center, width, height)


def _collect_main_objects() -> list[tuple[str, any]]:
    """Return list of (object_name, object) from Main collection."""
    import bpy
    
    main_collection = bpy.data.collections.get("Main")
    if not main_collection:
        return []
    
    # Get all mesh/renderable objects (not EMPTYs)
    objects = []
    for obj in main_collection.all_objects:
        if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            objects.append((obj.name, obj))
    
    return objects


def _generate_yolo_labels(output_dir: str, image_index: int) -> None:
    """Generate YOLO label file for current scene."""
    import bpy
    
    main_objects = _collect_main_objects()
    if not main_objects:
        print("Warning: No objects found in Main collection")
        return
    
    # Build class mapping
    class_names = sorted(set(name for name, _ in main_objects))
    class_to_id = {name: idx for idx, name in enumerate(class_names)}
    
    # Save classes.txt
    classes_path = os.path.join(output_dir, "classes.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(classes_path, "w") as f:
        for name in class_names:
            f.write(f"{name}\n")
    
    # Generate labels
    labels = []
    for obj_name, obj in main_objects:
        bbox = _get_bounding_box_2d(obj)
        if bbox is None:
            continue
        
        class_id = class_to_id[obj_name]
        x_center, y_center, width, height = bbox
        labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    # Save label file
    label_path = os.path.join(output_dir, f"image_{image_index:06d}.txt")
    with open(label_path, "w") as f:
        f.write("\n".join(labels))
    
    print(f"Generated {len(labels)} labels for image_{image_index:06d}")


def _render_scene(output_dir: str, image_index: int, bg_image: str | None) -> None:
    """Render the current scene to an image file."""
    import bpy
    
    scene = bpy.context.scene
	
    # Track final output path (respects render settings)
    scene.render.use_file_extension = True
    final_ext = scene.render.file_extension
    final_output = os.path.join(output_dir, f"image_{image_index:06d}{final_ext}")
    
    # Set output path
    os.makedirs(output_dir, exist_ok=True)

    if bg_image:
        # Render with alpha to a temp PNG, then composite with ffmpeg
        prev_format = scene.render.image_settings.file_format
        prev_color_mode = scene.render.image_settings.color_mode
        prev_transparent = scene.render.film_transparent
		
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.film_transparent = True
		
        temp_output = os.path.join(output_dir, f"image_{image_index:06d}_alpha.png")
        scene.render.filepath = temp_output
        bpy.ops.render.render(write_still=True)
		
        scene.render.image_settings.file_format = prev_format
        scene.render.image_settings.color_mode = prev_color_mode
        scene.render.film_transparent = prev_transparent
		
        width = scene.render.resolution_x
        height = scene.render.resolution_y
        composited = _compose_with_background(bg_image, temp_output, final_output, width, height)
        if composited and os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                pass
        elif not os.path.exists(final_output) and os.path.exists(temp_output):
            os.replace(temp_output, final_output)
    else:
        scene.render.filepath = final_output
    
    # Render
    if not bg_image:
        bpy.ops.render.render(write_still=True)
	
    if not os.path.exists(final_output):
        render_result = bpy.data.images.get("Render Result")
        if render_result:
            render_result.save_render(filepath=final_output)
    print(f"Rendered: {final_output}")


def main() -> None:
    try:
        import bpy
    except ImportError as exc:
        raise SystemExit("This script must be run inside Blender.") from exc
    
    args = _parse_args(sys.argv)
    output_dir = os.path.abspath(args["output_dir"])
    image_index = args["image_index"]
    
    print(f"Starting render {image_index} -> {output_dir}")
    
    # Pick a background image for external compositing
    import bpy
    blend_dir = os.path.dirname(bpy.data.filepath)
    bg_dir = os.path.join(blend_dir, "background_images")
    bg_image = _pick_random_background(bg_dir)
    if not bg_image:
        print("Warning: No background images found, rendering without background compositing")
    
    # Randomize scene
    _randomize_objects()
    _randomize_world_shader()
    
    # Update scene
    bpy.context.view_layer.update()
    
    # Render image
    _render_scene(output_dir, image_index, bg_image)
    
    # Generate YOLO labels
    _generate_yolo_labels(output_dir, image_index)
    
    print(f"Completed image {image_index}")


if __name__ == "__main__":
    main()
