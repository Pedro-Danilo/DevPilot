from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.store import LocalStore, SCHEMA_VERSION
from devpilot_core.validators.artifact import validate_artifact_file


def test_local_store_initializes_schema_idempotently(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)

    first = store.initialize()
    second = store.initialize()
    status = store.status()

    assert first.ok is True
    assert second.ok is True
    assert (tmp_path / ".devpilot" / "devpilot.db").is_file()
    assert status.data["summary"]["initialized"] is True
    assert status.data["summary"]["schema_version"] == SCHEMA_VERSION
    assert set(["runs", "findings", "gates", "events", "approvals", "cost_events"]).issubset(status.data["tables"])


def test_local_store_records_command_result_and_findings(tmp_path: Path) -> None:
    store = LocalStore(tmp_path)
    result = CommandResult(
        command="synthetic gate",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message="Synthetic gate blocked.",
        data={"summary": {"checked": 1}},
        findings=[Finding(id="SYNTHETIC_BLOCK", message="Blocked.", severity=Severity.BLOCK, path="docs/file.md")],
    )

    run_id = store.record_command_result(result, subject="docs/file.md")
    history = store.list_runs(limit=5)
    status = store.status()

    assert run_id
    assert history.ok is True
    assert history.data["summary"]["runs_returned"] == 1
    assert history.data["runs"][0]["command"] == "synthetic gate"
    assert history.data["runs"][0]["ok"] is False
    assert status.data["counts"]["runs"] == 1
    assert status.data["counts"]["findings"] == 1
    assert status.data["counts"]["gates"] == 1


def test_local_store_rejects_database_outside_project_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.db"

    with pytest.raises(ValueError, match="inside the DevPilot project root"):
        LocalStore(tmp_path, db_path=outside)


def test_history_list_without_database_is_empty_and_parseable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["history", "list", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "history list"
    assert payload["data"]["runs"] == []
    assert payload["data"]["summary"]["runs_returned"] == 0


def test_cli_state_init_status_and_history_are_parseable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    init_exit = cli.main(["state", "init", "--json"])
    init_payload = json.loads(capsys.readouterr().out)
    status_exit = cli.main(["state", "status", "--json"])
    status_payload = json.loads(capsys.readouterr().out)
    history_exit = cli.main(["history", "list", "--json", "--limit", "3"])
    history_payload = json.loads(capsys.readouterr().out)

    assert init_exit == 0
    assert init_payload["command"] == "state init"
    assert status_exit == 0
    assert status_payload["data"]["summary"]["initialized"] is True
    assert history_exit == 0
    assert history_payload["command"] == "history list"
    assert history_payload["data"]["summary"]["limit"] == 3


def test_cli_readiness_persists_run_in_local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()

    exit_code = cli.main(["readiness-check", "--json"])
    json.loads(capsys.readouterr().out)
    history_exit = cli.main(["history", "list", "--json", "--limit", "5"])
    history_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert history_exit == 0
    commands = [run["command"] for run in history_payload["data"]["runs"]]
    assert "readiness-check" in commands


def test_validate_artifact_result_path_uses_posix_separator_for_windows_style_input(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "01_requirements"
    docs_dir.mkdir(parents=True)
    target = docs_dir / "requirements_specification.md"
    target.write_text(
        "---\n"
        "title: Requirements\n"
        "doc_id: DEVPL-REQ-TEST\n"
        "status: approved\n"
        "version: 1.0.0\n"
        "owner: Ordóñez\n"
        "updated: 2026-06-08\n"
        "approval: approved_by_owner_direction\n"
        "---\n"
        "# Requirements\n\n"
        "## Propósito\n\nTexto suficientemente largo para validar el artefacto.\n\n"
        "## Alcance\n\nTexto.\n\n"
        "## Requerimientos funcionales del MVP\n\nTexto.\n\n"
        "## Requerimientos no funcionales\n\nTexto.\n\n"
        "## Criterios de bloqueo\n\nTexto.\n",
        encoding="utf-8",
    )

    windows_style = Path("docs\\01_requirements\\requirements_specification.md")
    result = validate_artifact_file(tmp_path / windows_style, root=tmp_path)

    assert result.data["path"] == "docs/01_requirements/requirements_specification.md"


def test_local_store_closes_connections_for_windows_temp_cleanup(tmp_path: Path) -> None:
    """Regression: SQLite file handles must not remain open after operations.

    The security readiness matrix creates temporary workspaces and deletes them
    at the end. On Windows, sqlite3.Connection used as a context manager does
    not close the underlying file handle, which can leave `.devpilot/devpilot.db`
    locked and make TemporaryDirectory cleanup fail with WinError 32.
    """

    store = LocalStore(tmp_path)
    store.initialize()
    store.record_event(event_type="test.event", command="test", ok=True, exit_code=0)
    store.status()

    db_path = tmp_path / ".devpilot" / "devpilot.db"
    assert db_path.is_file()
    db_path.unlink()
    assert not db_path.exists()
