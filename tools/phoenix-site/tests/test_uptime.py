from datetime import datetime, timedelta, timezone

from phoenix_site.uptime import uptime


def _content():
    return {
        "live_urls": [
            "https://phoenixrestoration-net.pages.dev",
            "https://phoenixrestoration.net",
        ]
    }


def test_uptime_reports_status_time_and_tls():
    expiry = datetime.now(timezone.utc) + timedelta(days=40)

    def fetch(url):
        if "pages.dev" in url:
            return 200, None
        return None, "name not resolved"

    def tls(host):
        return expiry

    text, code = uptime(_content(), fetch=fetch, tls=tls)
    assert code == 0
    assert "up  https://phoenixrestoration-net.pages.dev" in text
    assert "HTTP 200" in text
    assert "ms" in text
    assert "TLS until" in text
    assert "DOWN  https://phoenixrestoration.net" in text
    assert "pointed yet" in text


def test_uptime_fails_when_pages_is_down():
    def fetch(url):
        return None, "connection refused"

    def tls(host):
        return None

    text, code = uptime(_content(), fetch=fetch, tls=tls)
    assert code == 1
    assert "DOWN" in text
    assert "did not respond" in text


def test_uptime_fails_when_certificate_is_expired():
    def fetch(url):
        return 200, None

    def tls(host):
        return datetime.now(timezone.utc) - timedelta(days=1)

    _text, code = uptime(
        {"live_urls": ["https://phoenixrestoration-net.pages.dev"]},
        fetch=fetch,
        tls=tls,
    )
    assert code == 1
