import json
import re

from pathlib import Path

from phoenix_site.build import BuildRefused, build, render_pages
from phoenix_site.contentio import PAYMENT_LINE, load_content
from phoenix_site.paths import CONTENT_PATH

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_build_writes_pages_and_keeps_existing_phone(tmp_path):
    output = build(REPO_ROOT, dist=tmp_path / "dist")
    pages = ["index.html", "services.html", "about.html", "team.html", "area.html", "contact.html"]
    for name in pages:
        html = (output / name).read_text(encoding="utf-8")
        assert PAYMENT_LINE in html
        assert "cash or check only" not in html.lower()
        assert "we do not take cards" not in html.lower()
        assert 'name="viewport" content="width=device-width, initial-scale=1"' in html
        assert "LocalBusiness" in html
        assert "Elmore" in html and "Chilton" in html
        tels = set(re.findall(r"tel:\+[0-9]+", html))
        assert tels == {"tel:+13343277450"}
    index = (output / "index.html").read_text(encoding="utf-8")
    assert "info@phoenixrestoration.net" in index
    assert "https://www.facebook.com/people/Phoenix-Restoration/61559147480515/" in index
    assert "Full bathroom remodels" in index
    assert "Montgomery County" in index
    assert (output / "styles.css").is_file()
    assert (output / "functions" / "api" / "quote.js").is_file()
    assert (output / "lib" / "quote.mjs").is_file()
    deck = output / "assets" / "from-drive" / "chuck-deck-01.jpg"
    assert deck.is_file()
    assert deck.stat().st_size <= 500 * 1024
    assert not (output / "assets" / "phoenix-restoration-logo.png").exists()


def test_build_refuses_unreviewed_gallery_image(tmp_path):
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    content["gallery"][0]["reviewed"] = False
    try:
        build(REPO_ROOT, content=content, dist=tmp_path / "dist")
    except BuildRefused as exc:
        assert content["gallery"][0]["name"] in str(exc)
    else:
        raise AssertionError("build published an unreviewed image")
    assert not (tmp_path / "dist").exists()


def test_render_omits_unreviewed_image():
    content = load_content(CONTENT_PATH)
    content["gallery"].append(
        {
            "name": "not-yet",
            "src": "assets/gallery/not-yet.jpg",
            "width": 10,
            "height": 10,
            "alt": "A porch",
            "caption": "Porch",
            "reviewed": False,
        }
    )
    pages = render_pages(content)
    assert "not-yet" not in pages["index.html"]
    assert "assets/gallery/not-yet.jpg" not in pages["index.html"]
