"""Deploy the built site to Cloudflare Pages.

The Pages project phoenixrestoration-net is a direct upload. It is not
connected to Git (the project source is empty, and there is no build
command). deploy --commit therefore runs wrangler. It does not push, and
it does not change DNS.

Dry run is the default. Nothing is uploaded unless --commit is passed.
CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are read from the
environment and never printed.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable, Mapping

from .build import BuildRefused, build
from .check import check_site
from .paths import find_repo_root

PROJECT_NAME = "phoenixrestoration-net"
SECRET_ENV = ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")

# The live project has no Git source. If that ever changes, set this to
# True and deploy --commit will push the current branch instead of uploading.
GIT_INTEGRATION = False


class DeployError(Exception):
    pass


def deploy(
    commit: bool = False,
    root: Path | None = None,
    env: Mapping[str, str] | None = None,
    runner: Callable | None = None,
) -> str:
    repo = Path(root) if root is not None else find_repo_root()
    environment = dict(os.environ if env is None else env)
    lines = [
        "Phoenix Restoration deploy",
        f"Project: {PROJECT_NAME}",
        "Git integration: no. Cloudflare Pages is a direct upload, so this command "
        "does not push and does not change DNS.",
        f"CLOUDFLARE_API_TOKEN: {_presence(environment, 'CLOUDFLARE_API_TOKEN')}",
        f"CLOUDFLARE_ACCOUNT_ID: {_presence(environment, 'CLOUDFLARE_ACCOUNT_ID')}",
    ]
    if not commit:
        lines.append("Dry run. Nothing was built, checked, or uploaded.")
        lines.append("Re-run with --commit to build, check, and upload dist/.")
        if GIT_INTEGRATION:
            lines.append("A Git-connected project would push the current branch instead.")
        return "\n".join(lines)

    if GIT_INTEGRATION:
        lines.append("Pushing the current branch. Cloudflare builds from Git.")
        text = "\n".join(lines)
        _run(["git", "push"], repo, environment, runner, text)
        return text + "\nPushed."

    try:
        output = build(repo)
    except BuildRefused as exc:
        raise DeployError(str(exc)) from exc
    report = check_site(output, root=repo)
    lines.append(report.format())
    if not report.ok:
        raise DeployError("\n".join(lines))
    command = [
        "wrangler",
        "pages",
        "deploy",
        "dist",
        "--project-name",
        PROJECT_NAME,
    ]
    lines.append("Uploading with: wrangler pages deploy dist --project-name " + PROJECT_NAME)
    text = "\n".join(lines)
    output = _run(command, repo, environment, runner, text)
    return text + ("\n" + output if output else "") + "\nUpload finished."


def _presence(env: Mapping[str, str], key: str) -> str:
    return "set" if env.get(key) else "missing"


def _run(
    command: list[str],
    repo: Path,
    env: Mapping[str, str],
    runner: Callable | None,
    preface: str,
) -> str:
    missing = [key for key in SECRET_ENV if not env.get(key)]
    if command[0] == "wrangler" and missing:
        raise DeployError(
            preface
            + "\nMissing "
            + " and ".join(missing)
            + ". Set them in the environment. They were not printed."
        )
    run = runner or subprocess.run
    completed = run(
        command,
        cwd=str(repo),
        env=dict(env),
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = _redact(getattr(completed, "stdout", "") or "", env)
    stderr = _redact(getattr(completed, "stderr", "") or "", env)
    combined = "\n".join(part for part in (stdout.strip(), stderr.strip()) if part)
    if getattr(completed, "returncode", 1) != 0:
        raise DeployError(preface + "\n" + (combined or "The command failed."))
    return combined


def _redact(text: str, env: Mapping[str, str]) -> str:
    redacted = text
    for key in SECRET_ENV:
        value = env.get(key) or ""
        if value:
            redacted = redacted.replace(value, f"[{key}]")
    return redacted
