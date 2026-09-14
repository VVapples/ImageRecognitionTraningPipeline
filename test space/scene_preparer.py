"""Randomize object locations and rotations for a provided .blend file.

Usage (from a terminal):
	blender --background /path/to/file.blend --python scene_preparer.py

Example usage (Windows):
	blender --background "E:\\Workspace\\active\\NAFT\\MarsCamera\\MAIN\\test space\\Untitled.blend" --python "E:\\Workspace\\active\\NAFT\\MarsCamera\\MAIN\\test space\\scene_preparer.py" -- --save

Optional save (overwrite the input file):
	blender --background /path/to/file.blend --python scene_preparer.py -- --save
"""

from __future__ import annotations

import os
import random
import sys


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


def _parse_blend_path(argv: list[str]) -> str | None:
	"""Return a .blend path passed after '--', if present."""
	if "--" not in argv:
		return None
	idx = argv.index("--") + 1
	if idx >= len(argv):
		return None
	for token in argv[idx:]:
		if token.startswith("-"):
			continue
		return token
	return None


def _has_flag(argv: list[str], flag: str) -> bool:
	return flag in argv


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
	# Random rotation in radians for each axis.
	return (
		random.uniform(0.0, 6.283185307179586),
		random.uniform(0.0, 6.283185307179586),
		random.uniform(0.0, 6.283185307179586),
	)


def _random_rotate_axis() -> tuple[float, float, float]:
	# Random unit-ish axis (non-zero vector). Blender normalizes internally.
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
			name
			for name in os.listdir(hdr_dir)
			if name.lower().endswith(".hdr")
		]
	except FileNotFoundError:
		return None
	if not entries:
		return None
	return os.path.join(hdr_dir, random.choice(entries))


def _update_world_nodes(blend_path: str | None) -> None:
	import bpy

	world = bpy.data.worlds.get("World")
	if not world or not world.use_nodes:
		return

	shader_nodes = world.node_tree.nodes
	vector_rotate = shader_nodes.get("Vector Rotate")
	if vector_rotate and hasattr(vector_rotate, "axis"):
		vector_rotate.axis = _random_rotate_axis()
	if vector_rotate and hasattr(vector_rotate, "angle"):
		vector_rotate.angle = _random_rotate_angle()

	environment_texture = shader_nodes.get("Environment Texture")
	if not environment_texture:
		return

	blend_dir = os.path.dirname(blend_path) if blend_path else os.path.dirname(bpy.data.filepath)
	hdr_dir = os.path.join(blend_dir, "hdrs")
	new_hdr = _pick_random_hdr(hdr_dir)
	if new_hdr and hasattr(environment_texture, "image"):
		environment_texture.image = bpy.data.images.load(new_hdr, check_existing=True)


def main() -> None:
	try:
		import bpy
	except Exception as exc:  # pragma: no cover - Blender-only environment
		raise SystemExit("This script must be run inside Blender.") from exc

	blend_path = _parse_blend_path(sys.argv)
	if blend_path:
		bpy.ops.wm.open_mainfile(filepath=blend_path)

	for obj in bpy.data.objects:
			if obj.type != "EMPTY" and obj.name != "orange_hammer":
				continue
			if obj.name == "orange_hammer":
				obj.location = _random_location_main()
			else:
				obj.location = _random_location_other()
			obj.rotation_mode = "XYZ"
			obj.rotation_euler = _random_rotation_euler()

	_update_world_nodes(blend_path)


	if _has_flag(sys.argv, "--save"):
		bpy.ops.wm.save_mainfile()


if __name__ == "__main__":
	main()
