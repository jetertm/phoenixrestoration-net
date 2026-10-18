import os
from pathlib import Path

from PIL import Image

from phoenix_site.optimize import optimize_file, optimize_tree


def test_optimize_file_writes_jpeg_and_webp_under_budget(tmp_path):
    source = tmp_path / "noise.png"
    raw = os.urandom(180 * 180 * 3)
    Image.frombytes("RGB", (180, 180), raw).save(source, "PNG")
    original = source.stat().st_size
    result = optimize_file(source, tmp_path / "out" / "noise.png", max_bytes=12_000)
    jpeg = Path(result["jpeg"])
    webp = Path(result["webp"])
    assert jpeg.is_file() and webp.is_file()
    assert jpeg.stat().st_size < original
    assert webp.stat().st_size < original
    assert jpeg.stat().st_size <= 12_000
    assert source.stat().st_size == original


def test_optimize_tree_skips_small_files_and_the_optimized_folder(tmp_path):
    assets = tmp_path / "assets" / "jobs"
    assets.mkdir(parents=True)
    Image.new("RGB", (20, 20), "white").save(assets / "small.jpg", "JPEG")
    big = assets / "big.jpg"
    Image.frombytes("RGB", (120, 120), os.urandom(120 * 120 * 3)).save(big, "PNG")
    small_size = (assets / "small.jpg").stat().st_size
    assert big.stat().st_size > small_size
    written = optimize_tree(tmp_path, max_bytes=small_size)
    names = [Path(item["source"]).name for item in written]
    assert names == ["big.jpg"]
    assert "small.jpg" not in names
    assert not list((tmp_path / "assets" / "optimized").rglob("small.*"))
