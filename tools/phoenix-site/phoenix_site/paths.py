"""Locate the site repo, the content file, and build output."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = PACKAGE_ROOT / "content" / "site.json"
TEMPLATE_DIR = PACKAGE_ROOT / "templates"

IMAGE_BUDGET_BYTES = 500 * 1024


def find_repo_root(start: Path | None = None) -> Path:
    """Find the website repo (the directory that contains wrangler.toml)."""
    seeds = []
    if start is not None:
        seeds.append(Path(start).resolve())
    seeds.append(Path.cwd().resolve())
    seeds.append(PACKAGE_ROOT)
    seen = set()
    for seed in seeds:
        for candidate in [seed, *seed.parents]:
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / "wrangler.toml").is_file() and (candidate / "assets").is_dir():
                return candidate
    raise SystemExit(
        "Can't find the Phoenix Restoration site repo (wrangler.toml next to assets/). "
        "Run phoenix-site from that repository."
    )


def dist_dir(root: Path) -> Path:
    return root / "dist"
