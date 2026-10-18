"""Add a photo to the gallery, and approve it after Eve has looked at it."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .contentio import image_name, load_content, save_content
from .optimize import OptimizeError, optimize_file
from .paths import CONTENT_PATH, find_repo_root


class ImageCommandError(Exception):
    pass


def add_image(source: Path, root: Path | None = None, content_path: Path | None = None) -> dict:
    repo = Path(root) if root is not None else find_repo_root()
    content_file = Path(content_path) if content_path is not None else CONTENT_PATH
    src = Path(source)
    if not src.is_file():
        raise ImageCommandError(f"File not found: {src}")
    suffix = src.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise ImageCommandError("Use a JPEG, PNG, WebP, or GIF photo.")
    name = _slug(src.stem)
    if not name:
        raise ImageCommandError("That file name has no usable letters or numbers.")
    content = load_content(content_file)
    if any(image_name(item).lower() == name.lower() for item in content["gallery"]):
        raise ImageCommandError(f"A gallery image named {name} is already in the content file.")
    gallery_dir = repo / "assets" / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    stored = gallery_dir / f"{name}{suffix}"
    shutil.copy2(src, stored)
    try:
        optimized = optimize_file(stored, gallery_dir / name)
    except OptimizeError:
        stored.unlink(missing_ok=True)
        raise
    width, height = _dimensions(Path(optimized["jpeg"]))
    entry = {
        "name": name,
        "src": f"assets/gallery/{name}.jpg",
        "webp": f"assets/gallery/{name}.webp",
        "width": width,
        "height": height,
        "alt": "",
        "caption": "",
        "reviewed": False,
    }
    # The optimized JPEG is what the page will use. Drop the untouched original
    # when it is a different file, so a huge upload is not what gets published.
    if stored.resolve() != Path(optimized["jpeg"]).resolve() and stored.exists():
        stored.unlink()
    content["gallery"].append(entry)
    save_content(content, content_file)
    return entry


def approve_image(name: str, content_path: Path | None = None) -> dict:
    content_file = Path(content_path) if content_path is not None else CONTENT_PATH
    content = load_content(content_file)
    needle = name.strip().lower()
    match = None
    for item in content["gallery"]:
        item_name = image_name(item).lower()
        stem = Path(str(item.get("src") or "")).stem.lower()
        if needle in {item_name, stem}:
            match = item
            break
    if match is None:
        known = ", ".join(image_name(item) for item in content["gallery"]) or "(none)"
        raise ImageCommandError(f"No gallery image named {name}. Known names: {known}")
    match["reviewed"] = True
    save_content(content, content_file)
    return match


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _dimensions(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        return (0, 0)
    with Image.open(path) as image:
        return image.size
