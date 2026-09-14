"""List workspace contents of a provided .blend file.

Usage (from a terminal):
  blender --background /path/to/file.blend --python blenderedit.py

Optional (pass a different file):
  blender --background --python blenderedit.py -- /path/to/file.blend
"""

from __future__ import annotations

import sys


def _parse_blend_path(argv: list[str]) -> str | None:
	"""Return a .blend path passed after '--', if present."""
	if "--" not in argv:
		return None
	idx = argv.index("--") + 1
	if idx >= len(argv):
		return None
	return argv[idx]


def _print_header(title: str) -> None:
	print("\n" + title)
	print("-" * len(title))


def _list_scene(scene) -> None:
	_print_header(f"Scene: {scene.name}")

	if scene.collection is not None:
		print(f"Root Collection: {scene.collection.name}")

	_print_header("Collections")
	if scene.collection.children:
		for coll in scene.collection.children:
			print(f"- {coll.name}")
	else:
		print("(none)")

	_print_header("Objects")
	if scene.objects:
		for obj in scene.objects:
			obj_type = getattr(obj, "type", "UNKNOWN")
			print(f"- {obj.name} ({obj_type})")
	else:
		print("(none)")


def _list_data_blocks(bpy) -> None:
	_print_header("Materials")
	if bpy.data.materials:
		for mat in bpy.data.materials:
			print(f"- {mat.name}")
	else:
		print("(none)")

	_print_header("Meshes")
	if bpy.data.meshes:
		for mesh in bpy.data.meshes:
			print(f"- {mesh.name}")
	else:
		print("(none)")

	_print_header("Cameras")
	if bpy.data.cameras:
		for cam in bpy.data.cameras:
			print(f"- {cam.name}")
	else:
		print("(none)")

	_print_header("Lights")
	if bpy.data.lights:
		for light in bpy.data.lights:
			print(f"- {light.name}")
	else:
		print("(none)")


def main() -> None:
	try:
		import bpy
	except Exception as exc:  # pragma: no cover - Blender-only environment
		raise SystemExit("This script must be run inside Blender.") from exc

	blend_path = _parse_blend_path(sys.argv)
	if blend_path:
		bpy.ops.wm.open_mainfile(filepath=blend_path)

	_print_header("Workspace Overview")
	for scene in bpy.data.scenes:
		_list_scene(scene)

	_list_data_blocks(bpy)


if __name__ == "__main__":
	main()
