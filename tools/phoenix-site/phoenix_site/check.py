"""Checks for the built site. Exits nonzero when something would be bad to publish."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .paths import IMAGE_BUDGET_BYTES, find_repo_root

# Lighthouse-style transfer budgets for a small brochure site with a photo gallery.
HTML_BUDGET = 100 * 1024
CSS_BUDGET = 80 * 1024
JS_BUDGET = 80 * 1024
PAGE_BUDGET = 6 * 1024 * 1024

DECORATIVE_CLASSES = {"logo-img", "footer-logo"}
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


@dataclass
class CheckReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def format(self) -> str:
        lines = []
        if self.ok:
            lines.append("Check passed.")
        else:
            lines.append(f"Check failed ({len(self.errors)} problem(s)).")
        for error in self.errors:
            lines.append(f"ERROR  {error}")
        for warning in self.warnings:
            lines.append(f"warn   {warning}")
        return "\n".join(lines)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: list[tuple[str, list[tuple[str, str | None]]]] = []
        self.title_parts: list[str] = []
        self._in_title = False
        self.jsonld: list[str] = []
        self._in_jsonld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.attrs.append((tag, attrs))
        if tag == "title":
            self._in_title = True
        if tag == "script" and _attr(attrs, "type") == "application/ld+json":
            self._in_jsonld = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script":
            self._in_jsonld = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_jsonld:
            self.jsonld.append(data)


def check_site(dist: Path | None = None, root: Path | None = None) -> CheckReport:
    repo = Path(root) if root is not None else find_repo_root()
    output = Path(dist) if dist is not None else repo / "dist"
    report = CheckReport()
    if not output.is_dir():
        report.errors.append(f"Build folder not found: {output}. Run phoenix-site build first.")
        return report
    pages = sorted(output.glob("*.html"))
    if not pages:
        report.errors.append("No HTML pages in the build folder.")
        return report
    css_bytes = _file_size(output / "styles.css")
    js_bytes = _file_size(output / "site.js")
    if css_bytes > CSS_BUDGET:
        report.errors.append(f"styles.css is {_kb(css_bytes)}, over the {_kb(CSS_BUDGET)} CSS budget.")
    if js_bytes > JS_BUDGET:
        report.errors.append(f"site.js is {_kb(js_bytes)}, over the {_kb(JS_BUDGET)} JavaScript budget.")
    seen_images: set[Path] = set()
    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        parser = _PageParser()
        parser.feed(html)
        _check_seo(page.name, html, parser, report)
        _check_links(output, page, parser, report)
        images = _page_images(output, page, parser, report, seen_images)
        page_total = page.stat().st_size + css_bytes + js_bytes + sum(path.stat().st_size for path in images)
        if page.stat().st_size > HTML_BUDGET:
            report.errors.append(f"{page.name} HTML is {_kb(page.stat().st_size)}, over the {_kb(HTML_BUDGET)} document budget.")
        if page_total > PAGE_BUDGET:
            report.errors.append(
                f"{page.name} page weight is {_kb(page_total)} (HTML+CSS+JS+images), over the {_kb(PAGE_BUDGET)} budget."
            )
    for path in sorted(seen_images):
        size = path.stat().st_size
        if size > IMAGE_BUDGET_BYTES:
            report.errors.append(
                f"{path.relative_to(output).as_posix()} is {_kb(size)}, over the 500 KB image budget. "
                "Run phoenix-site optimize."
            )
    return report


def _check_seo(name: str, html: str, parser: _PageParser, report: CheckReport) -> None:
    title = "".join(parser.title_parts).strip()
    if not title:
        report.errors.append(f"{name} is missing a <title>.")
    description = _meta(parser, "name", "description")
    if not description:
        report.errors.append(f"{name} is missing a meta description.")
    elif len(description) > 320:
        report.errors.append(f"{name} meta description is {len(description)} characters (limit 320).")
    for prop in ("og:title", "og:description", "og:image", "og:url"):
        if not _meta(parser, "property", prop):
            report.errors.append(f"{name} is missing Open Graph {prop}.")
    viewport = _meta(parser, "name", "viewport")
    if not viewport or "width=device-width" not in viewport.replace(" ", ""):
        report.errors.append(f"{name} is missing a mobile viewport (width=device-width).")
    blocks = []
    for raw in parser.jsonld:
        raw = raw.strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            report.errors.append(f"{name} has JSON-LD that does not parse: {exc}")
    local = _find_local_business(blocks)
    if local is None:
        report.errors.append(f"{name} is missing LocalBusiness JSON-LD.")
        return
    blob = json.dumps(local)
    if "Elmore" not in blob or "Chilton" not in blob:
        report.errors.append(f"{name} LocalBusiness schema does not list Elmore and Chilton County.")
    address = local.get("address") or {}
    if isinstance(address, dict) and address.get("addressRegion") != "AL":
        report.errors.append(f"{name} LocalBusiness schema is not marked as Alabama.")
    if not local.get("name"):
        report.errors.append(f"{name} LocalBusiness schema has no business name.")


def _find_local_business(blocks: list[Any]) -> dict[str, Any] | None:
    for block in blocks:
        if isinstance(block, list):
            found = _find_local_business(block)
            if found:
                return found
        if not isinstance(block, dict):
            continue
        types = block.get("@type")
        if isinstance(types, str):
            types = [types]
        if isinstance(types, list) and "LocalBusiness" in types:
            return block
        graph = block.get("@graph")
        if isinstance(graph, list):
            found = _find_local_business(graph)
            if found:
                return found
    return None


def _check_links(output: Path, page: Path, parser: _PageParser, report: CheckReport) -> None:
    for tag, attrs in parser.attrs:
        for key in ("href", "src", "data-jobs"):
            value = _attr(attrs, key)
            if not value:
                continue
            target = value.strip()
            if not target or target.startswith("#") or target.startswith(SKIP_SCHEMES):
                continue
            path = _local_target(output, page, target)
            if path is None:
                report.errors.append(f"{page.name} has an unreadable link: {target}")
                continue
            if not path.is_file():
                report.errors.append(f"{page.name} links to missing {target}")


def _page_images(
    output: Path,
    page: Path,
    parser: _PageParser,
    report: CheckReport,
    seen: set[Path],
) -> list[Path]:
    images = []
    for tag, attrs in parser.attrs:
        if tag != "img":
            continue
        alt = _attr(attrs, "alt")
        classes = set((_attr(attrs, "class") or "").split())
        if alt is None:
            report.errors.append(f"{page.name} has an image with no alt attribute ({_attr(attrs, 'src')}).")
        elif not alt.strip() and not (classes & DECORATIVE_CLASSES):
            report.errors.append(f"{page.name} has an image with empty alt text ({_attr(attrs, 'src')}).")
        src = _attr(attrs, "src")
        if not src or src.startswith(SKIP_SCHEMES):
            continue
        path = _local_target(output, page, src)
        if path is not None and path.is_file():
            seen.add(path)
            images.append(path)
    return images


def _local_target(output: Path, page: Path, target: str) -> Path | None:
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    raw = unquote(parsed.path)
    if not raw:
        return None
    if raw.startswith("/"):
        candidate = output / raw.lstrip("/")
    else:
        candidate = (page.parent / raw).resolve()
    try:
        candidate.relative_to(output.resolve())
    except ValueError:
        return None
    return candidate


def _meta(parser: _PageParser, attr: str, value: str) -> str:
    for tag, attrs in parser.attrs:
        if tag != "meta":
            continue
        if _attr(attrs, attr) == value:
            return _attr(attrs, "content") or ""
    return ""


def _attr(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    for key, value in attrs:
        if key == name:
            return value
    return None


def _file_size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def _kb(size: int) -> str:
    return f"{size / 1024:.1f} KB"
