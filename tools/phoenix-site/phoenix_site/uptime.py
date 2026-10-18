"""Fetch the live site and report status, response time, and TLS expiry."""

from __future__ import annotations

import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlparse

Fetch = Callable[[str], tuple[int | None, str | None]]
Tls = Callable[[str], datetime | None]


def uptime(
    content: dict[str, Any],
    fetch: Fetch | None = None,
    tls: Tls | None = None,
    timeout: float = 15.0,
) -> tuple[str, int]:
    urls = list(content.get("live_urls") or [])
    if not urls:
        return "No live URLs are listed in the content file.", 1
    do_fetch = fetch or (lambda url: _fetch(url, timeout))
    do_tls = tls or (lambda host: _tls_expiry(host, timeout))
    results = []
    lines = ["Uptime"]
    for url in urls:
        result = _one(url, do_fetch, do_tls)
        results.append(result)
        lines.append(_format_result(result))
    code = 0 if _pages_ok(results) else 1
    if code == 0:
        lines.append("Pages production URL responded.")
    else:
        lines.append("Pages production URL did not respond successfully.")
    return "\n".join(lines), code


def _one(url: str, fetch: Fetch, tls: Tls) -> dict[str, Any]:
    started = time.perf_counter()
    status, error = fetch(url)
    elapsed_ms = (time.perf_counter() - started) * 1000
    host = urlparse(url).hostname or ""
    expiry = None
    tls_error = None
    if host and urlparse(url).scheme == "https" and error is None:
        try:
            expiry = tls(host)
        except Exception as exc:  # noqa: BLE001 - report whatever the socket raised
            tls_error = str(exc)
    ok = error is None and status is not None and 200 <= status < 400
    if expiry is not None and expiry < datetime.now(timezone.utc):
        ok = False
        tls_error = "certificate is already expired"
    return {
        "url": url,
        "ok": ok,
        "status": status,
        "response_ms": round(elapsed_ms, 1),
        "tls_not_after": expiry.isoformat() if expiry else None,
        "error": error or tls_error,
    }


def _pages_ok(results: list[dict[str, Any]]) -> bool:
    pages = [item for item in results if "pages.dev" in item["url"]]
    if not pages:
        return all(item["ok"] for item in results)
    return all(item["ok"] for item in pages)


def _format_result(result: dict[str, Any]) -> str:
    status = result["status"] if result["status"] is not None else "n/a"
    state = "up" if result["ok"] else "DOWN"
    extra = ""
    if result.get("tls_not_after"):
        extra = f", TLS until {result['tls_not_after']}"
    if result.get("error") and "pages.dev" not in result["url"] and not result["ok"]:
        extra += f" — {result['error']} (custom domain may not be pointed yet)"
    elif result.get("error"):
        extra += f" — {result['error']}"
    return f"{state}  {result['url']}  HTTP {status}  {result['response_ms']} ms{extra}"


def _fetch(url: str, timeout: float) -> tuple[int | None, str | None]:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "phoenix-site-uptime"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)
            return response.status, None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:  # noqa: BLE001 - network failures are the report
        return None, str(exc)


def _tls_expiry(host: str, timeout: float) -> datetime | None:
    context = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as secure:
            cert = secure.getpeercert()
    if not cert or "notAfter" not in cert:
        return None
    text = str(cert["notAfter"]).replace(" GMT", "")
    parsed = datetime.strptime(text, "%b %d %H:%M:%S %Y")
    return parsed.replace(tzinfo=timezone.utc)
