"""Command line for phoenix-site."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .build import BuildRefused, build
from .check import check_site
from .contentio import load_content
from .deploy import DeployError, deploy
from .dnscheck import dns_check
from .images import ImageCommandError, add_image, approve_image
from .optimize import OptimizeError, optimize_tree
from .paths import CONTENT_PATH, find_repo_root
from .preview import serve
from .uptime import uptime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="phoenix-site",
        description="Build and check the Phoenix Restoration LLC website.",
    )
    parser.add_argument("--version", action="version", version=f"phoenix-site {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("build", help="Render the site into dist/")

    preview = sub.add_parser("preview", help="Build, then serve dist/ on 127.0.0.1")
    preview.add_argument("--port", type=int, default=8080)

    check = sub.add_parser("check", help="Check links, alt text, image size, and basic SEO")
    check.add_argument("check_command", nargs="?", choices=("optimize",))
    check.add_argument("--dist", type=Path_type, default=None)

    sub.add_parser("optimize", help="Write resized WebP and JPEG copies of images over 500 KB")

    images = sub.add_parser("images", help="Add or approve gallery photos")
    image_sub = images.add_subparsers(dest="images_command", required=True)
    add = image_sub.add_parser("add", help="Copy a photo into the gallery as not reviewed")
    add.add_argument("file")
    approve = image_sub.add_parser("approve", help="Mark a gallery photo reviewed so it can publish")
    approve.add_argument("name")

    ship = sub.add_parser("deploy", help="Show the upload plan. --commit actually uploads.")
    ship.add_argument(
        "--commit",
        action="store_true",
        help="Build, check, and upload dist/ with wrangler. Off by default.",
    )

    sub.add_parser("dns-check", help="Read DNS for the domain. Never changes records.")
    sub.add_parser("uptime", help="Fetch the live URLs and report status, time, and TLS expiry.")

    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except (BuildRefused, ImageCommandError, OptimizeError, DeployError) as exc:
        print(exc, file=sys.stderr)
        return 1


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "build":
        output = build()
        print(f"Built {output}")
        return 0
    if args.command == "preview":
        serve(port=args.port)
        return 0
    if args.command == "check" and args.check_command == "optimize":
        return _optimize()
    if args.command == "check":
        report = check_site(dist=args.dist)
        print(report.format())
        return 0 if report.ok else 1
    if args.command == "optimize":
        return _optimize()
    if args.command == "images" and args.images_command == "add":
        entry = add_image(Path_type(args.file))
        print(
            f"Added {entry['name']} to the gallery as reviewed: false.\n"
            "It will not be published until you set alt text and run "
            f"phoenix-site images approve {entry['name']}"
        )
        return 0
    if args.command == "images" and args.images_command == "approve":
        entry = approve_image(args.name)
        print(f"Approved {entry['name']}. The next build may publish {entry['src']}.")
        return 0
    if args.command == "deploy":
        print(deploy(commit=args.commit))
        return 0
    if args.command == "dns-check":
        content = load_content(CONTENT_PATH)
        text, code = dns_check(content)
        print(text)
        return code
    if args.command == "uptime":
        content = load_content(CONTENT_PATH)
        text, code = uptime(content)
        print(text)
        return code
    return 2


def _optimize() -> int:
    root = find_repo_root()
    written = optimize_tree(root)
    if not written:
        print("No images over 500 KB. Nothing to do.")
        return 0
    for item in written:
        print(
            f"{item['source']} -> {item['jpeg']} ({item['jpeg_bytes']} bytes), "
            f"{item['webp']} ({item['webp_bytes']} bytes)"
        )
    print(f"Optimized {len(written)} image(s). Originals were kept.")
    return 0


def Path_type(value: str):
    from pathlib import Path

    return Path(value)
