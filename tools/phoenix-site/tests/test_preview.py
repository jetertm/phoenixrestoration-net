import urllib.request

from pathlib import Path

from phoenix_site.preview import HOST, serve_in_thread

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_preview_serves_only_on_loopback():
    server, _thread = serve_in_thread(port=0, root=REPO_ROOT, build_first=True)
    try:
        host, port = server.server_address[:2]
        assert host == HOST == "127.0.0.1"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
            body = response.read(200).decode("utf-8", errors="replace")
            assert response.status == 200
        assert "Phoenix Restoration" in body or "<!DOCTYPE html>" in body
    finally:
        server.shutdown()
        server.server_close()
