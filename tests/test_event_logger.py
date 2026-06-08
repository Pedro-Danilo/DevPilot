from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.observability import EventLogger, EventRecord, REDACTED, redact_sensitive_data, redact_sensitive_string
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_event_logger_writes_jsonl_and_redacts_synthetic_secrets(tmp_path: Path) -> None:
    logger = EventLogger(tmp_path)
    logger.emit(
        EventRecord(
            event_type="command.started",
            command="validate-frontmatter",
            message="api_key=sk-1234567890abcdef and token=ghp_1234567890abcdef",
            metadata={"api_key": "sk-1234567890abcdef", "nested": {"password": "super-secret"}},
        )
    )

    events_path = tmp_path / "outputs" / "traces" / "events.jsonl"
    events = read_jsonl(events_path)

    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "command.started"
    assert event["metadata"]["api_key"] == REDACTED
    assert event["metadata"]["nested"]["password"] == REDACTED
    assert "sk-1234567890abcdef" not in json.dumps(event)
    assert "ghp_1234567890abcdef" not in json.dumps(event)


def test_event_logger_rejects_paths_outside_project_root(tmp_path: Path) -> None:
    outside_path = tmp_path.parent / "outside" / "events.jsonl"

    with pytest.raises(ValueError, match="project root"):
        EventLogger(tmp_path, events_path=outside_path)


def test_event_from_command_result_generates_gate_event(tmp_path: Path) -> None:
    result = CommandResult(
        command="sample-gate",
        ok=False,
        exit_code=ExitCode.FAIL,
        message="Synthetic validation failed.",
        data={"summary": {"checked": 2}},
        findings=[Finding(id="SYNTHETIC_FAIL", message="A failure occurred.", severity=Severity.FAIL)],
    )

    EventLogger(tmp_path).emit_result(result, subject="docs/example.md")
    events = read_jsonl(tmp_path / "outputs" / "traces" / "events.jsonl")

    assert events[0]["event_type"] == "gate.evaluated"
    assert events[0]["status"] == "FAIL"
    assert events[0]["summary"] == {"checked": 2}
    assert events[0]["findings"][0]["id"] == "SYNTHETIC_FAIL"
    assert events[0]["subject"] == "docs/example.md"


def test_cli_version_emits_started_and_completed_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["--version"])
    capsys.readouterr()

    assert exit_code == 0
    events = read_jsonl(tmp_path / "outputs" / "traces" / "events.jsonl")
    assert [event["event_type"] for event in events] == ["command.started", "command.completed"]
    assert events[0]["command"] == "version"
    assert events[1]["ok"] is True


def test_cli_validate_frontmatter_emits_gate_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    document = docs_dir / "valid.md"
    document.write_text(
        "---\n"
        "title: Valid Document\n"
        "doc_id: DEVPL-TEST-001\n"
        "status: approved\n"
        "version: 1.0.0\n"
        "owner: Ordóñez\n"
        "updated: 2026-06-07\n"
        "approval: approved_by_owner_direction\n"
        "---\n"
        "# Valid Document\n",
        encoding="utf-8",
    )

    exit_code = cli.main(["validate-frontmatter", "docs/valid.md", "--strict", "--json"])
    capsys.readouterr()

    assert exit_code == 0
    events = read_jsonl(tmp_path / "outputs" / "traces" / "events.jsonl")
    assert [event["event_type"] for event in events] == [
        "command.started",
        "gate.evaluated",
        "command.completed",
    ]
    assert events[1]["command"] == "validate-frontmatter"
    assert events[1]["summary"]["path"] == "docs/valid.md"
    assert events[1]["status"] == "PASS"


def test_redaction_helpers_cover_strings_and_nested_values() -> None:
    text = "Authorization: Bearer abc token=hf_1234567890abcdef"
    redacted_text = redact_sensitive_string(text)
    nested = redact_sensitive_data({"access_token": "ghp_1234567890abcdef", "safe": ["plain"]})

    assert "hf_1234567890abcdef" not in redacted_text
    assert nested["access_token"] == REDACTED
    assert nested["safe"] == ["plain"]


def test_frontmatter_result_path_uses_posix_separator_for_windows_style_input() -> None:
    document = parse_frontmatter_text(
        "---\n"
        "title: Valid Document\n"
        "doc_id: DEVPL-TEST-001\n"
        "status: approved\n"
        "version: 1.0.0\n"
        "owner: Ordóñez\n"
        "updated: 2026-06-07\n"
        "approval: approved_by_owner_direction\n"
        "---\n"
        "# Valid Document\n",
        path=Path("docs\\valid.md"),
    )

    result = validate_frontmatter_document(document, strict=True)

    assert result.ok is True
    assert result.data["path"] == "docs/valid.md"
