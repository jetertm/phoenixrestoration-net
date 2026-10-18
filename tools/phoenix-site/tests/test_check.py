from phoenix_site.check import check_site
from phoenix_site.paths import IMAGE_BUDGET_BYTES


GOOD_LD = """
{"@context":"https://schema.org","@type":["LocalBusiness","HomeAndConstructionBusiness"],
 "name":"Phoenix Restoration LLC","address":{"@type":"PostalAddress","addressRegion":"AL"},
 "areaServed":[{"@type":"AdministrativeArea","name":"Elmore County, Alabama"},
               {"@type":"AdministrativeArea","name":"Chilton County, Alabama"}]}
"""


def _page(body, head_extra=""):
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phoenix Restoration LLC</title>
<meta name="description" content="Residential renovation in Elmore and Chilton County, Alabama.">
<meta property="og:title" content="Phoenix Restoration LLC">
<meta property="og:description" content="Residential renovation in Elmore and Chilton County, Alabama.">
<meta property="og:image" content="https://phoenixrestoration.net/assets/logo-512.jpg">
<meta property="og:url" content="https://phoenixrestoration.net/">
{head_extra}
</head><body>
{body}
<script type="application/ld+json">{GOOD_LD}</script>
</body></html>
"""


def test_check_flags_links_alt_size_and_seo(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "styles.css").write_text("body{}", encoding="utf-8")
    (dist / "site.js").write_text("/* ok */", encoding="utf-8")
    (dist / "photo.jpg").write_bytes(b"\xff" * (IMAGE_BUDGET_BYTES + 10))
    (dist / "ok.jpg").write_bytes(b"\xff\xd8\xff")
    (dist / "index.html").write_text(
        _page(
            '<img src="photo.jpg" alt="Deck boards">'
            '<img src="ok.jpg">'
            '<a href="missing.html">Gone</a>'
            '<a href="https://example.com/keep">Outside</a>'
        ),
        encoding="utf-8",
    )
    (dist / "about.html").write_text(
        "<!DOCTYPE html><html><head><title>About</title></head><body></body></html>",
        encoding="utf-8",
    )
    report = check_site(dist, root=tmp_path)
    text = "\n".join(report.errors)
    assert not report.ok
    assert "photo.jpg" in text and "500 KB" in text
    assert "empty alt" in text or "no alt" in text
    assert "missing.html" in text
    assert "example.com" not in text
    assert "about.html" in text and "viewport" in text
    assert "LocalBusiness" in text


def test_check_passes_a_small_valid_page(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "styles.css").write_text("body{}", encoding="utf-8")
    (dist / "site.js").write_text("", encoding="utf-8")
    (dist / "ok.jpg").write_bytes(b"tiny")
    (dist / "index.html").write_text(
        _page('<img class="logo-img" src="ok.jpg" alt=""><img src="ok.jpg" alt="Finished deck">'),
        encoding="utf-8",
    )
    report = check_site(dist, root=tmp_path)
    assert report.ok, report.format()
