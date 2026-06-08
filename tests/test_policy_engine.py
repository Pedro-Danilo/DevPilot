from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.policy import CostGuard, CostPolicy, PathGuard, PolicyEffect, PolicyEngine, PolicyRequest, REDACTED, SecretGuard, load_cost_policy


def test_path_guard_allows_safe_read_inside_workspace(tmp_path: Path) -> None:
    document = tmp_path / "docs" / "example.md"
    document.parent.mkdir()
    document.write_text("# Example\n", encoding="utf-8")

    decision = PathGuard(tmp_path).evaluate("docs/example.md", action="read")

    assert decision.effect == PolicyEffect.ALLOW
    assert decision.subject == "docs/example.md"


def test_path_guard_blocks_path_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"

    decision = PathGuard(tmp_path).evaluate(outside, action="read")

    assert decision.effect == PolicyEffect.BLOCK
    assert decision.rule_id == "PATHGUARD_OUTSIDE_ROOT"


def test_path_guard_blocks_destructive_actions(tmp_path: Path) -> None:
    decision = PathGuard(tmp_path).evaluate("docs/example.md", action="delete")

    assert decision.effect == PolicyEffect.BLOCK
    assert decision.rule_id == "PATHGUARD_DESTRUCTIVE_ACTION_BLOCKED"


def test_path_guard_denies_write_outside_allowed_prefixes(tmp_path: Path) -> None:
    decision = PathGuard(tmp_path).evaluate("README.md", action="write")

    assert decision.effect == PolicyEffect.DENY
    assert decision.rule_id == "PATHGUARD_WRITE_PREFIX_DENIED"


def test_secret_guard_redacts_nested_payloads_and_blocks_detected_secrets() -> None:
    guard = SecretGuard()

    redaction = guard.redact({"safe": "ok", "api_key": "sk-1234567890abcdef", "text": "token=ghp_1234567890abcdef"})
    decision = guard.scan_text("authorization=hf_1234567890abcdef")

    assert redaction.changed is True
    assert redaction.value["api_key"] == REDACTED
    assert REDACTED in redaction.value["text"]
    assert decision.effect == PolicyEffect.BLOCK
    assert decision.rule_id == "SECRETGUARD_SECRET_DETECTED"


def test_cost_guard_blocks_external_api_without_budget_policy() -> None:
    decision = CostGuard().evaluate(external_api=True, provider="openai", estimated_cost_usd=0.01)

    assert decision.effect == PolicyEffect.BLOCK
    assert decision.rule_id == "COSTGUARD_EXTERNAL_API_BLOCKED"


def test_cost_guard_warns_when_external_api_is_budgeted() -> None:
    guard = CostGuard(CostPolicy(external_api_allowed=True, budget_limit_usd=1.0, budget_used_usd=0.1))

    decision = guard.evaluate(external_api=True, provider="openai", estimated_cost_usd=0.25)

    assert decision.effect == PolicyEffect.WARN
    assert decision.rule_id == "COSTGUARD_BUDGETED_WARNING"


def test_load_cost_policy_from_local_policy_yaml(tmp_path: Path) -> None:
    policy_file = tmp_path / ".devpilot" / "policy.yaml"
    policy_file.parent.mkdir()
    policy_file.write_text(
        'schema_version: "1.0"\n'
        'cost:\n'
        '  external_api_allowed: true\n'
        '  budget_limit_usd: 2.5\n'
        '  budget_used_usd: 0.5\n'
        '  allowed_providers:\n'
        '    - "mock"\n'
        '    - "openai"\n',
        encoding="utf-8",
    )

    policy = load_cost_policy(tmp_path)

    assert policy.external_api_allowed is True
    assert policy.budget_limit_usd == 2.5
    assert policy.budget_used_usd == 0.5
    assert policy.allowed_providers == ("mock", "openai")


def test_policy_engine_blocks_delete_and_external_api(tmp_path: Path) -> None:
    engine = PolicyEngine(tmp_path)

    result = engine.evaluate(PolicyRequest(action="delete", path="docs/example.md", external_api=True, provider="openai"))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    finding_ids = {finding.id for finding in result.findings}
    assert "POLICY_DANGEROUS_ACTION_BLOCKED" in finding_ids
    assert "PATHGUARD_DESTRUCTIVE_ACTION_BLOCKED" in finding_ids
    assert "COSTGUARD_EXTERNAL_API_BLOCKED" in finding_ids


def test_policy_cli_check_json_passes_for_safe_local_read(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "docs" / "file.md").write_text("# File\n", encoding="utf-8")

    exit_code = main(["policy", "check", "read", "--path", "docs/file.md", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "policy check"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["allowed"] is True


def test_policy_cli_blocks_secret_and_writes_redacted_report(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    exit_code = main([
        "policy",
        "check",
        "read",
        "--path",
        "docs/file.md",
        "--text",
        "api_key=sk-1234567890abcdef",
        "--json",
        "--write-report",
    ])
    payload = json.loads(capsys.readouterr().out)
    report_path = tmp_path / payload["data"]["reports"]["json"]
    report_text = report_path.read_text(encoding="utf-8")

    assert exit_code == 2
    assert payload["ok"] is False
    assert any(finding["id"] == "SECRETGUARD_SECRET_DETECTED" for finding in payload["findings"])
    assert "sk-1234567890abcdef" not in report_text
    assert REDACTED in report_text


def test_policy_cli_blocks_external_api_without_budget(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    exit_code = main([
        "policy",
        "check",
        "external-api",
        "--external-api",
        "--provider",
        "openai",
        "--estimated-cost-usd",
        "0.01",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert any(finding["id"] == "POLICY_DANGEROUS_ACTION_BLOCKED" for finding in payload["findings"])
    assert any(finding["id"] == "COSTGUARD_EXTERNAL_API_BLOCKED" for finding in payload["findings"])
