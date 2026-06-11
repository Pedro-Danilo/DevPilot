from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.policy import REDACTED, PolicyEffect, SecretGuard


def test_secret_guard_detects_common_synthetic_token_shapes() -> None:
    guard = SecretGuard()
    payload = {
        "safe": "plain",
        "aws": "AKIA1234567890ABCDEF",
        "google": "AIza1234567890abcdefghijklmnop",
        "db": "postgres://demo:supersecret@localhost:5432/app",
        "nested": ["OPENAI_API_KEY=sk-proj-abcdefghijklmnop123456"],
    }

    result = guard.redact(payload)
    decision = guard.scan_text("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo-token")

    assert result.changed is True
    assert result.redactions >= 4
    assert result.value["aws"] == REDACTED
    assert result.value["google"] == REDACTED
    assert "supersecret" not in result.value["db"]
    assert REDACTED in result.value["nested"][0]
    assert decision.effect == PolicyEffect.BLOCK
    assert decision.rule_id == "SECRETGUARD_SECRET_DETECTED"


def test_policy_cli_writes_redacted_report_for_hardened_secret_patterns(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    raw_secret = "DATABASE_URL=postgres://demo:supersecret@localhost:5432/app"

    exit_code = main([
        "policy",
        "check",
        "suggest",
        "--text",
        raw_secret,
        "--json",
        "--write-report",
    ])
    payload = json.loads(capsys.readouterr().out)
    report_text = (tmp_path / payload["data"]["reports"]["json"]).read_text(encoding="utf-8")

    assert exit_code == int(ExitCode.BLOCK)
    assert payload["ok"] is False
    assert "SECRETGUARD_SECRET_DETECTED" in {finding["id"] for finding in payload["findings"]}
    assert "supersecret" not in json.dumps(payload, ensure_ascii=False)
    assert "supersecret" not in report_text
    assert REDACTED in report_text
