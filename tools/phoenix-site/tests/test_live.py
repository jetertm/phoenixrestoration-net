import pytest

from phoenix_site.contentio import load_content
from phoenix_site.dnscheck import dns_check
from phoenix_site.paths import CONTENT_PATH
from phoenix_site.uptime import uptime


@pytest.mark.live
def test_dns_check_live_is_read_only():
    text, code = dns_check(load_content(CONTENT_PATH))
    assert "phoenixrestoration.net" in text
    assert "MX" in text
    assert code in (0, 1, 2)


@pytest.mark.live
def test_uptime_live_reports_pages_dev():
    text, code = uptime(load_content(CONTENT_PATH), timeout=20)
    assert "phoenixrestoration-net.pages.dev" in text
    assert code in (0, 1)
