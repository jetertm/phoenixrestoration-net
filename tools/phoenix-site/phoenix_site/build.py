"""Render the site into dist/."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .contentio import image_name, load_content, unreviewed_images
from .htmlparts import prepare_context, render_cta, render_footer, render_head, render_header, render_jsonld
from .paths import CONTENT_PATH, IMAGE_BUDGET_BYTES, TEMPLATE_DIR, find_repo_root
from .template_engine import render_string

STATIC_FILES = ("styles.css", "site.js", "robots.txt", "sitemap.xml", "favicon.svg")
PAGE_IDS = ("home", "services", "about", "team", "area", "contact")

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


class BuildRefused(Exception):
    """Jessy's rule: an unreviewed gallery image must not be published."""


def build(
    root: Path | None = None,
    content: dict[str, Any] | Path | None = None,
    dist: Path | None = None,
    template_dir: Path | None = None,
) -> Path:
    repo = Path(root) if root is not None else find_repo_root()
    templates = Path(template_dir) if template_dir is not None else TEMPLATE_DIR
    data = _load(content)
    pending = unreviewed_images(data)
    if pending:
        names = ", ".join(image_name(item) for item in pending)
        raise BuildRefused(
            "Refusing to build. These gallery images are not reviewed: "
            f"{names}. Eve has to look at each one, then run: "
            "phoenix-site images approve <name>"
        )
    output = Path(dist) if dist is not None else repo / "dist"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    pages = render_pages(data, templates)
    for filename, html in pages.items():
        (output / filename).write_text(html, encoding="utf-8")
    for name in STATIC_FILES:
        source = repo / name
        if source.is_file():
            shutil.copy2(source, output / name)
    for folder in ("functions", "lib"):
        source = repo / folder
        if source.is_dir():
            shutil.copytree(source, output / folder)
    _copy_assets(repo, output, pages)
    return output


def render_pages(content: dict[str, Any], template_dir: Path | None = None) -> dict[str, str]:
    templates = template_dir or TEMPLATE_DIR
    shell = (templates / "shell.html").read_text(encoding="utf-8")
    pages: dict[str, str] = {}
    for page_id in PAGE_IDS:
        ctx = prepare_context(content, page_id)
        ctx["head"] = render_head(ctx)
        ctx["jsonld"] = render_jsonld(ctx)
        ctx["header"] = render_header(ctx)
        ctx["cta_html"] = render_cta(ctx)
        ctx["footer"] = render_footer(ctx)
        body_path = templates / f"{page_id}.html"
        ctx["body"] = render_string(body_path.read_text(encoding="utf-8"), ctx, templates)
        pages[ctx["page"]["file"]] = render_string(shell, ctx, templates)
    return pages


def _load(content: dict[str, Any] | Path | None) -> dict[str, Any]:
    if content is None:
        return load_content(CONTENT_PATH)
    if isinstance(content, Path):
        return load_content(content)
    return content


def _copy_assets(repo: Path, output: Path, pages: dict[str, str]) -> None:
    assets = repo / "assets"
    if not assets.is_dir():
        return
    referenced = _referenced_asset_paths(repo, pages)
    for source in assets.rglob("*"):
        if not source.is_file():
            continue
        rel = source.relative_to(repo).as_posix()
        if rel.startswith("assets/optimized/"):
            continue
        dest = output / rel
        if source.suffix.lower() in IMAGE_SUFFIXES and source.stat().st_size > IMAGE_BUDGET_BYTES:
            if rel not in referenced:
                # Leave unused oversized originals out of the publish folder.
                continue
            optimized = _optimized_jpeg(repo, rel)
            if optimized is not None and optimized.stat().st_size <= IMAGE_BUDGET_BYTES:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(optimized, dest)
                continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def _optimized_jpeg(repo: Path, rel: str) -> Path | None:
    """assets/foo/bar.jpg -> assets/optimized/foo/bar.jpg"""
    path = Path(rel)
    if not path.parts or path.parts[0] != "assets":
        return None
    candidate = repo / "assets" / "optimized" / Path(*path.parts[1:])
    candidate = candidate.with_suffix(".jpg")
    if candidate.is_file():
        return candidate
    return None


def _referenced_asset_paths(repo: Path, pages: dict[str, str]) -> set[str]:
    import re

    found = set()
    pattern = re.compile(r"""(?:src|href)=["'](assets/[^"']+)["']""")
    for html in pages.values():
        found.update(pattern.findall(html))
    jobs = repo / "assets" / "recent-work" / "jobs.json"
    if jobs.is_file():
        try:
            data = json.loads(jobs.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for job in data.get("jobs", []):
            for key in ("before", "after"):
                value = str(job.get(key) or "")
                if value.startswith("assets/"):
                    found.add(value)
    return found
