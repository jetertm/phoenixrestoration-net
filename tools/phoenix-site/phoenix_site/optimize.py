"""Resize oversized photos to WebP and JPEG copies under the 500 KB budget."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from .paths import IMAGE_BUDGET_BYTES, find_repo_root

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class OptimizeError(Exception):
    pass


def optimize_tree(root: Path | None = None, max_bytes: int = IMAGE_BUDGET_BYTES) -> list[dict[str, str]]:
    """Write resized JPEG and WebP copies for every image over max_bytes.

    Originals are left in place. Copies land in assets/optimized/<same path>.
    """
    repo = Path(root) if root is not None else find_repo_root()
    assets = repo / "assets"
    written = []
    if not assets.is_dir():
        return written
    for source in sorted(assets.rglob("*")):
        if not source.is_file():
            continue
        if "optimized" in source.relative_to(assets).parts:
            continue
        if source.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if source.stat().st_size <= max_bytes:
            continue
        rel = source.relative_to(assets)
        dest_stem = assets / "optimized" / rel
        result = optimize_file(source, dest_stem, max_bytes=max_bytes)
        written.append(result)
    return written


def optimize_file(source: Path, dest_stem: Path, max_bytes: int = IMAGE_BUDGET_BYTES) -> dict[str, str]:
    """Create dest_stem.jpg and dest_stem.webp. dest_stem may include a suffix; it is stripped."""
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise OptimizeError(
            "Image optimization needs Pillow. Install it with: pip install pillow"
        ) from exc
    dest_stem = Path(dest_stem).with_suffix("")
    dest_stem.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image.load()
        if max(image.size) > 1600:
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        jpeg_path = dest_stem.with_suffix(".jpg")
        webp_path = dest_stem.with_suffix(".webp")
        _save_under(image, jpeg_path, "JPEG", max_bytes)
        _save_under(image, webp_path, "WEBP", max_bytes)
    return {
        "source": str(source),
        "jpeg": str(jpeg_path),
        "webp": str(webp_path),
        "jpeg_bytes": str(jpeg_path.stat().st_size),
        "webp_bytes": str(webp_path.stat().st_size),
    }


def _save_under(image, dest: Path, fmt: str, max_bytes: int) -> None:
    from PIL import Image

    working = image.copy()
    quality = 85
    while True:
        buffer = BytesIO()
        if fmt == "JPEG":
            frame = working.convert("RGB")
            frame.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
        else:
            frame = working
            if frame.mode not in {"RGB", "RGBA"}:
                frame = frame.convert("RGB")
            frame.save(buffer, "WEBP", quality=quality, method=6)
        if buffer.tell() <= max_bytes or (quality <= 40 and max(working.size) <= 640):
            dest.write_bytes(buffer.getvalue())
            return
        if quality > 50:
            quality -= 10
            continue
        width = max(1, int(working.size[0] * 0.75))
        height = max(1, int(working.size[1] * 0.75))
        working = working.resize((width, height), Image.Resampling.LANCZOS)
        quality = 75
