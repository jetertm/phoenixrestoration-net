from pathlib import Path

from phoenix_site.template_engine import render_string


def test_escapes_text():
    html = render_string("<p>{{ name }}</p>", {"name": "a < b & c"}, Path("."))
    assert html == "<p>a &lt; b &amp; c</p>"


def test_raw_is_not_escaped():
    html = render_string("{{{ html }}}", {"html": "<em>x</em>"}, Path("."))
    assert html == "<em>x</em>"


def test_list_section_and_empty_inverted():
    source = "{{#items}}[{{ value }}]{{/items}}{{^items}}none{{/items}}"
    assert render_string(source, {"items": ["a", "b"]}, Path(".")) == "[a][b]"
    assert render_string(source, {"items": []}, Path(".")) == "none"


def test_nested_sections():
    source = "{{#rows}}{{ name }}:{{#nums}}{{ value }}{{/nums}};{{/rows}}"
    html = render_string(source, {"rows": [{"name": "a", "nums": ["1", "2"]}]}, Path("."))
    assert html == "a:12;"
