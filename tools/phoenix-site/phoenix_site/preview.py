"""Serve dist/ on 127.0.0.1 only."""

from __future__ import annotations

import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .build import build
from .paths import find_repo_root

HOST = "127.0.0.1"


def start_server(port: int = 8080, root: Path | None = None, build_first: bool = True):
    repo = Path(root) if root is not None else find_repo_root()
    output = build(repo) if build_first else repo / "dist"
    if not output.is_dir():
        raise SystemExit(f"Nothing to serve at {output}. Run phoenix-site build first.")
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(output))
    server = ThreadingHTTPServer((HOST, port), handler)
    return server


def serve(port: int = 8080, root: Path | None = None) -> None:
    server = start_server(port=port, root=root, build_first=True)
    host, bound = server.server_address[:2]
    print(f"Serving on http://{host}:{bound}/  (this machine only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def serve_in_thread(port: int = 0, root: Path | None = None, build_first: bool = True):
    server = start_server(port=port, root=root, build_first=build_first)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
