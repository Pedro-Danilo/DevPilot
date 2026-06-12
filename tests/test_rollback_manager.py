from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.changes import RollbackManager


def _write_changeset(root: Path) -> Path:
    target = root / "src/example.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('before')\n", encoding="utf-8")
    before = __import__("hashlib").sha256(target.read_bytes()).hexdigest()
    after = __import__("hashlib").sha256(b"print('after')\n").hexdigest()
    payload = {
        "changeset_id": "changeset-test-001",
        "source_patch": "safe.patch",
        "sandbox_id": "sandbox-test",
        "sandbox_workspace": "outputs/sandbox/sandbox-test/workspace",
        "files_total": 1,
        "files": [
            {
                "path": "src/example.py",
                "action": "modify",
                "before_sha256": before,
                "after_sha256": after,
                "before_size_bytes": len(target.read_bytes()),
                "after_size_bytes": len(b"print('after')\n"),
            }
        ],
        "preliminary": True,
    }
    changeset_path = root / "changeset.json"
    changeset_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return changeset_path


def test_rollback_plan_from_changeset_creates_metadata_and_backup(tmp_path: Path) -> None:
    changeset_path = _write_changeset(tmp_path)

    result = RollbackManager(tmp_path).create_plan_from_file("changeset.json")

    assert result.ok is True
    summary = result.data["summary"]
    rollback_id = summary["rollback_id"]
    assert summary["backup_available"] is True
    assert summary["backed_up_files"] == 1
    assert summary["execute_supported"] is False
    assert result.data["plan"]["approval_required_for_execute"] is True
    assert result.data["plan"]["operations"][0]["action"] == "restore_modified_file_from_backup"
    assert result.data["plan"]["operations"][0]["backup_path"].startswith(".devpilot/rollback/backups/")
    assert (tmp_path / ".devpilot/rollback/points" / f"{rollback_id}.json").exists()
    assert (tmp_path / result.data["plan"]["operations"][0]["backup_path"]).exists()
    assert "print('before')" not in json.dumps(result.to_dict())
    assert changeset_path.exists()



def test_rollback_plan_accepts_patch_sandbox_evidence_report(tmp_path: Path) -> None:
    changeset_path = _write_changeset(tmp_path)
    raw_changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
    evidence = {"command": "patch sandbox", "ok": True, "data": {"changeset": raw_changeset}}
    evidence_path = tmp_path / "patch_sandbox_report.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    result = RollbackManager(tmp_path).create_plan_from_file("patch_sandbox_report.json")

    assert result.ok is True
    assert result.data["plan"]["changeset_id"] == "changeset-test-001"


def test_rollback_list_and_show_are_read_only_parseable(tmp_path: Path) -> None:
    _write_changeset(tmp_path)
    created = RollbackManager(tmp_path).create_plan_from_file("changeset.json")
    rollback_id = created.data["summary"]["rollback_id"]

    listed = RollbackManager(tmp_path).list()
    shown = RollbackManager(tmp_path).show(rollback_id)

    assert listed.ok is True
    assert listed.data["summary"]["points_total"] == 1
    assert listed.data["rollback_points"][0]["rollback_id"] == rollback_id
    assert shown.ok is True
    assert shown.data["plan"]["rollback_id"] == rollback_id
    assert shown.data["summary"]["read_only"] is True


def test_rollback_execute_without_approval_is_blocked(tmp_path: Path) -> None:
    _write_changeset(tmp_path)
    created = RollbackManager(tmp_path).create_plan_from_file("changeset.json")
    rollback_id = created.data["summary"]["rollback_id"]

    result = RollbackManager(tmp_path).execute(rollback_id)

    assert result.ok is False
    assert int(result.exit_code) == 2
    assert result.data["summary"]["mutations_performed"] is False
    assert any(finding.id == "APPROVAL_REQUIRED_MISSING" for finding in result.findings)


def test_rollback_cli_list_show_and_execute_block(monkeypatch, tmp_path: Path) -> None:
    _write_changeset(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert cli.main(["rollback", "plan", "--changeset-file", "changeset.json", "--json"]) == 0
    payload = json.loads((tmp_path / ".devpilot/rollback/points").glob("rollback-*.json").__next__().read_text(encoding="utf-8"))
    rollback_id = payload["point"]["rollback_id"]
    assert cli.main(["rollback", "list", "--json"]) == 0
    assert cli.main(["rollback", "show", rollback_id, "--json"]) == 0
    assert cli.main(["rollback", "execute", rollback_id, "--json"]) == 2


def test_rollback_runtime_paths_are_excluded_from_gitignore() -> None:
    gitignore = Path(__file__).resolve().parents[1].joinpath(".gitignore").read_text(encoding="utf-8")

    assert ".devpilot/rollback/" in gitignore
