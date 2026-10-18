"""Read-only DNS check for phoenixrestoration.net.

This module only looks up records. It has no path that creates, updates,
or deletes DNS. The planned website change is apex/www only. MX is never
part of that plan.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Callable

GOOGLE_MX_MARKERS = (
    "aspmx.l.google.com",
    "googlemail.com",
    "smtp.google.com",
)

Resolver = Callable[[str, str], list[dict[str, str]]]


def dns_check(content: dict[str, Any], resolver: Resolver | None = None) -> tuple[str, int]:
    plan = content.get("dns_plan") or {}
    domain = str(plan.get("domain") or "phoenixrestoration.net")
    lookup = resolver or dig_lookup
    apex_a = lookup(domain, "A")
    apex_cname = lookup(domain, "CNAME")
    www_a = lookup("www." + domain, "A")
    www_cname = lookup("www." + domain, "CNAME")
    mx = lookup(domain, "MX")
    google = [record for record in mx if _is_google_mx(record.get("value", ""))]
    breaks = plan_breaks_mx(plan)
    lines = [
        f"DNS for {domain} (read-only; nothing was changed)",
        "Apex A: " + (_format(apex_a) or "(none)"),
        "Apex CNAME: " + (_format(apex_cname) or "(none)"),
        "www A: " + (_format(www_a) or "(none)"),
        "www CNAME: " + (_format(www_cname) or "(none)"),
        "MX: " + (_format(mx) or "(none)"),
        "",
        "Planned website change (not applied):",
    ]
    for change in plan.get("changes") or []:
        lines.append(
            f"  {change.get('host')} {change.get('type')} {change.get('value')}"
        )
    lines.append("MX is not part of the planned change and must be left exactly as it is.")
    code = 0
    if google:
        lines.append("")
        lines.append("*** WARNING: Google Workspace mail is on this domain. ***")
        lines.append("These MX records are Google Workspace:")
        for record in google:
            lines.append(f"    {record.get('priority', '')} {record.get('value')}")
        lines.append(
            "Do not add, edit, or remove MX, and do not replace the GoDaddy zone, "
            "when pointing the website at Cloudflare Pages. Doing so would break Google Workspace email."
        )
    if breaks:
        lines.append("")
        lines.append("*** WARNING: THE SAVED PLAN WOULD BREAK MAIL. ***")
        lines.append(
            "The plan changes MX or nameservers, or it does not say preserve_mx. "
            "phoenix-site will not apply it. This command never modifies DNS."
        )
        if google:
            lines.append("That change would break Google Workspace MX. Stop.")
        code = 2
    elif google:
        lines.append("The saved plan does not touch MX. Mail records stay on Google Workspace.")
    return "\n".join(lines), code


def plan_breaks_mx(plan: dict[str, Any]) -> bool:
    if plan.get("preserve_mx") is not True:
        return True
    for change in plan.get("changes") or []:
        kind = str(change.get("type") or "").upper()
        host = str(change.get("host") or "").upper()
        if kind in {"MX", "NS"} or host == "MX":
            return True
    return False


def _is_google_mx(host: str) -> bool:
    value = host.lower().rstrip(".")
    for marker in GOOGLE_MX_MARKERS:
        if value == marker or value.endswith("." + marker):
            return True
    return False


def _format(records: list[dict[str, str]]) -> str:
    parts = []
    for record in records:
        if record.get("type") == "MX":
            parts.append(f"{record.get('priority', '')} {record.get('value')}".strip())
        else:
            parts.append(f"{record.get('type')} {record.get('value')}".strip())
    return "; ".join(parts)


def dig_lookup(name: str, rtype: str) -> list[dict[str, str]]:
    dig = shutil.which("dig")
    if not dig:
        raise SystemExit("dig is not installed, so DNS could not be read. No records were changed.")
    completed = subprocess.run(
        [dig, "+time=3", "+tries=1", "+noall", "+answer", rtype, name],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 and not completed.stdout.strip():
        raise SystemExit(f"DNS lookup failed for {rtype} {name}. No records were changed.")
    return parse_dig(completed.stdout, rtype)


def parse_dig(output: str, expected: str) -> list[dict[str, str]]:
    records = []
    for line in output.splitlines():
        if not line or line.startswith(";"):
            continue
        parts = line.split()
        if len(parts) < 5 or parts[2] != "IN":
            continue
        rtype = parts[3]
        if expected != "A" and rtype != expected:
            # A lookups may also show the CNAME they followed. Keep both when asked for A.
            if not (expected == "CNAME" and rtype == "CNAME"):
                if rtype != expected:
                    continue
        if rtype == "MX" and len(parts) >= 6:
            records.append({"type": "MX", "priority": parts[4], "value": parts[5].rstrip(".").lower()})
        elif rtype in {"A", "AAAA", "CNAME", "NS"}:
            records.append({"type": rtype, "value": parts[4].rstrip(".").lower()})
    if expected == "CNAME":
        return [record for record in records if record["type"] == "CNAME"]
    if expected == "A":
        return [record for record in records if record["type"] == "A"]
    return [record for record in records if record["type"] == expected]
