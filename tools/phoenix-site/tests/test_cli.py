import pytest

from phoenix_site.cli import main
from phoenix_site.deploy import deploy


def test_each_command_is_wired():
    for command in ("build", "check", "optimize", "deploy", "images", "dns-check", "uptime", "preview"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        main(["images", "add", "--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        main(["images", "approve", "--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        main(["check", "optimize", "--help"])
    assert exc.value.code == 0


def test_cli_deploy_dry_run(capsys):
    assert main(["deploy"]) == 0
    output = capsys.readouterr().out
    assert "Dry run" in output
    # The real process environment may contain credentials. They must not be printed.
    text = deploy(commit=False, env={"CLOUDFLARE_API_TOKEN": "should-not-leak", "CLOUDFLARE_ACCOUNT_ID": "also-hidden"})
    assert "should-not-leak" not in text
    assert "also-hidden" not in text
