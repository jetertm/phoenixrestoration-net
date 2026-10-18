from phoenix_site.deploy import GIT_INTEGRATION, deploy


class _Result:
    def __init__(self, code, stdout="", stderr=""):
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def test_deploy_dry_run_does_not_upload_or_print_secrets():
    calls = []

    def runner(*args, **kwargs):
        calls.append(kwargs)
        raise AssertionError("dry run must not run a command")

    env = {
        "CLOUDFLARE_API_TOKEN": "super-secret-token",
        "CLOUDFLARE_ACCOUNT_ID": "account-secret",
    }
    text = deploy(commit=False, env=env, runner=runner)
    assert calls == []
    assert "Dry run" in text
    assert "super-secret-token" not in text
    assert "account-secret" not in text
    assert "CLOUDFLARE_API_TOKEN: set" in text
    assert "CLOUDFLARE_ACCOUNT_ID: set" in text
    assert "does not push" in text
    assert GIT_INTEGRATION is False


def test_deploy_commit_runs_wrangler_and_redacts_output():
    seen = {}

    def runner(command, cwd, env, check, capture_output, text):
        seen["command"] = command
        seen["cwd"] = cwd
        return _Result(0, stdout="uploaded with " + env["CLOUDFLARE_API_TOKEN"])

    env = {
        "CLOUDFLARE_API_TOKEN": "super-secret-token",
        "CLOUDFLARE_ACCOUNT_ID": "account-secret",
        "PATH": "/usr/bin",
    }
    text = deploy(commit=True, env=env, runner=runner)
    assert seen["command"] == [
        "wrangler",
        "pages",
        "deploy",
        "dist",
        "--project-name",
        "phoenixrestoration-net",
    ]
    assert "super-secret-token" not in text
    assert "account-secret" not in text
    assert "[CLOUDFLARE_API_TOKEN]" in text
    assert "Upload finished." in text


def test_deploy_commit_stops_when_credentials_are_missing():
    def runner(*args, **kwargs):
        raise AssertionError("wrangler must not run without credentials")

    try:
        deploy(commit=True, env={"PATH": "/usr/bin"}, runner=runner)
    except Exception as exc:
        message = str(exc)
    else:
        raise AssertionError("missing credentials were ignored")
    assert "CLOUDFLARE_API_TOKEN" in message
    assert "Missing" in message
