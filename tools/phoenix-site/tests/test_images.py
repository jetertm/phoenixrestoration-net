import json
from pathlib import Path

from PIL import Image

from phoenix_site.build import BuildRefused, build
from phoenix_site.contentio import load_content
from phoenix_site.images import add_image, approve_image
from phoenix_site.paths import CONTENT_PATH

REPO_ROOT = Path(__file__).resolve().parents[3]


def _photo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (40, 30), (180, 90, 40)).save(path, "PNG")


def test_add_then_approve_round_trip(tmp_path):
    content_path = tmp_path / "site.json"
    content_path.write_text(CONTENT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    source = tmp_path / "incoming" / "Porch Evening.PNG"
    _photo(source)
    entry = add_image(source, root=tmp_path, content_path=content_path)
    assert entry["reviewed"] is False
    assert entry["name"] == "porch-evening"
    saved = json.loads(content_path.read_text(encoding="utf-8"))
    assert saved["gallery"][-1]["reviewed"] is False
    assert (tmp_path / "assets" / "gallery" / "porch-evening.jpg").is_file()
    assert (tmp_path / "assets" / "gallery" / "porch-evening.webp").is_file()
    try:
        build(REPO_ROOT, content=load_content(content_path), dist=tmp_path / "blocked")
    except BuildRefused as exc:
        assert "porch-evening" in str(exc)
    else:
        raise AssertionError("unreviewed photo was published")
    approved = approve_image("porch-evening", content_path=content_path)
    assert approved["reviewed"] is True
    again = json.loads(content_path.read_text(encoding="utf-8"))
    assert again["gallery"][-1]["reviewed"] is True
    output = build(tmp_path, content=load_content(content_path), dist=tmp_path / "dist")
    html = (output / "index.html").read_text(encoding="utf-8")
    assert "assets/gallery/porch-evening.jpg" in html
    assert (output / "assets" / "gallery" / "porch-evening.jpg").is_file()
