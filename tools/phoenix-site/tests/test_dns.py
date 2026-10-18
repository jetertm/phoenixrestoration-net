from phoenix_site.dnscheck import dns_check, parse_dig, plan_breaks_mx


def _resolver(records):
    def lookup(name, rtype):
        return list(records.get((name, rtype), []))

    return lookup


GOOGLE_MX = [
    {"type": "MX", "priority": "1", "value": "aspmx.l.google.com"},
    {"type": "MX", "priority": "5", "value": "alt1.aspmx.l.google.com"},
]


def _content(plan):
    return {"dns_plan": plan}


def test_parse_dig_splits_a_and_cname_and_mx():
    output = "\n".join(
        [
            "www.phoenixrestoration.net. 300 IN CNAME phoenixrestoration-net.pages.dev.",
            "phoenixrestoration-net.pages.dev. 300 IN A 172.66.46.250",
        ]
    )
    assert parse_dig(output, "CNAME") == [
        {"type": "CNAME", "value": "phoenixrestoration-net.pages.dev"}
    ]
    assert parse_dig(output, "A") == [{"type": "A", "value": "172.66.46.250"}]
    mx = parse_dig("phoenixrestoration.net. 3600 IN MX 1 aspmx.l.google.com.", "MX")
    assert mx == [{"type": "MX", "priority": "1", "value": "aspmx.l.google.com"}]


def test_safe_plan_warns_about_google_workspace_and_does_not_fail():
    plan = {
        "domain": "phoenixrestoration.net",
        "preserve_mx": True,
        "changes": [
            {"host": "@", "type": "A_or_CNAME", "value": "Cloudflare Pages"},
            {"host": "www", "type": "CNAME", "value": "phoenixrestoration-net.pages.dev"},
        ],
    }
    records = {
        ("phoenixrestoration.net", "A"): [{"type": "A", "value": "15.197.225.128"}],
        ("phoenixrestoration.net", "CNAME"): [],
        ("www.phoenixrestoration.net", "A"): [{"type": "A", "value": "172.66.46.250"}],
        ("www.phoenixrestoration.net", "CNAME"): [
            {"type": "CNAME", "value": "phoenixrestoration-net.pages.dev"}
        ],
        ("phoenixrestoration.net", "MX"): GOOGLE_MX,
    }
    text, code = dns_check(_content(plan), resolver=_resolver(records))
    assert code == 0
    assert "WARNING" in text
    assert "Google Workspace" in text
    assert "aspmx.l.google.com" in text
    assert "never" in text.lower() or "must be left" in text
    assert plan_breaks_mx(plan) is False


def test_plan_that_changes_mx_fails_loudly():
    plan = {
        "domain": "phoenixrestoration.net",
        "preserve_mx": True,
        "changes": [{"host": "@", "type": "MX", "value": "mail.example.com"}],
    }
    records = {("phoenixrestoration.net", "MX"): GOOGLE_MX}
    text, code = dns_check(_content(plan), resolver=_resolver(records))
    assert code == 2
    assert "WOULD BREAK MAIL" in text
    assert "Google Workspace" in text
    assert "never modifies DNS" in text


def test_dns_module_has_no_write_api():
    from pathlib import Path

    source = Path(__file__).resolve().parents[1].joinpath("phoenix_site", "dnscheck.py").read_text(encoding="utf-8")
    lowered = source.lower()
    for banned in ("api.godaddy", "nsupdate", "cloudflare.request", "requests.patch", "requests.delete"):
        assert banned not in lowered
