from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.changes import ChangeSet, ChangeSetFile, RollbackPlanPreview
from devpilot_core.sandbox import PatchSandboxManager

ROOT = Path(__file__).resolve().parents[1]


def test_patch_sandbox_applies_patch_only_in_sandbox() -> None:
    target = ROOT / "src/devpilot_core/reports/models.py"
    before = target.read_text(encoding="utf-8")

    result = PatchSandboxManager(ROOT).apply(patch_file="safe.patch")

    after = target.read_text(encoding="utf-8")
    assert result.ok is True
    assert result.data["summary"]["patch_applied_in_sandbox"] is True
    assert result.data["summary"]["productive_workspace_unchanged"] is True
    assert result.data["summary"]["changeset_files"] == 1
    assert result.data["summary"]["effective_changes"] == 1
    changeset_file = result.data["changeset"]["files"][0]
    assert changeset_file["path"] == "src/devpilot_core/reports/models.py"
    assert changeset_file["action"] == "modify"
    assert changeset_file["before_sha256"] != changeset_file["after_sha256"]
    assert changeset_file["before_size_bytes"] != changeset_file["after_size_bytes"]
    assert before == after
    sandbox_workspace = ROOT / result.data["summary"]["sandbox_workspace"]
    assert sandbox_workspace.exists()
    sandbox_target = sandbox_workspace / "src/devpilot_core/reports/models.py"
    assert sandbox_target.read_text(encoding="utf-8") != before


def test_patch_sandbox_cleanup_removes_runtime_directory() -> None:
    result = PatchSandboxManager(ROOT).apply(patch_file="safe.patch", cleanup=True)

    assert result.ok is True
    assert result.data["summary"]["cleanup_requested"] is True
    assert result.data["summary"]["cleanup_removed"] is True
    assert not (ROOT / "outputs/sandbox" / result.data["summary"]["sandbox_id"]).exists()


def test_changeset_model_is_serializable_without_raw_content() -> None:
    changeset = ChangeSet(
        changeset_id="changeset-test",
        source_patch="safe.patch",
        sandbox_id="sandbox-test",
        sandbox_workspace="outputs/sandbox/sandbox-test/workspace",
        files=(
            ChangeSetFile(
                path="src/example.py",
                action="modify",
                before_sha256="a" * 64,
                after_sha256="b" * 64,
                before_size_bytes=10,
                after_size_bytes=12,
            ),
        ),
        rollback_plan=RollbackPlanPreview(available=False, strategy="future-rollback-manager", notes=("metadata only",)),
    )

    payload = changeset.to_dict()
    encoded = json.dumps(payload)
    assert payload["files_total"] == 1
    assert payload["files"][0]["before_sha256"] == "a" * 64
    assert "raw_patch" not in encoded
    assert "content" not in encoded.lower()



def test_patch_sandbox_falls_back_when_git_apply_reports_success_without_changes(monkeypatch) -> None:
    def fake_run(self, args, *, cwd=".", timeout_seconds=None):  # noqa: ANN001
        return CommandResult(
            command="execution safe-subprocess",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Simulated SafeSubprocessRunner success without filesystem mutation.",
            data={
                "summary": {
                    "executed": True,
                    "blocked": False,
                    "command_allowed": True,
                    "returncode": 0,
                    "timed_out": False,
                    "redactions": 0,
                    "duration_ms": 1,
                    "runner": "SafeSubprocessRunner",
                    "preliminary": True,
                }
            },
            findings=[Finding("SAFE_SUBPROCESS_PASS", "Simulated pass.", Severity.INFO)],
        )

    monkeypatch.setattr("devpilot_core.sandbox.patch_sandbox.SafeSubprocessRunner.run", fake_run)

    result = PatchSandboxManager(ROOT).apply(patch_file="safe.patch")

    assert result.ok is True
    assert result.data["summary"]["effective_changes"] == 1
    assert result.data["python_fallback"]["ok"] is True
    assert any(finding.id == "PATCH_SANDBOX_PYTHON_FALLBACK_APPLIED" for finding in result.findings)


def test_patch_sandbox_run_tests_requires_approval() -> None:
    result = PatchSandboxManager(ROOT).apply(patch_file="safe.patch", run_tests=True)

    assert result.ok is False
    assert result.exit_code == 2
    assert result.data["summary"]["run_tests_requested"] is True
    assert result.data["summary"]["tests_executed"] is False
    assert any(finding.id == "APPROVAL_REQUIRED_MISSING" for finding in result.findings)


def test_patch_sandbox_cli_json_and_write_report() -> None:
    exit_code = cli.main(["patch", "sandbox", "--patch-file", "safe.patch", "--json", "--write-report", "--cleanup"])

    assert exit_code == 0
    assert (ROOT / "outputs/reports/patch_sandbox.json").exists()
    payload = json.loads((ROOT / "outputs/reports/patch_sandbox.json").read_text(encoding="utf-8"))
    assert payload["command"] == "patch sandbox"
    assert payload["ok"] is True
    assert payload["summary"]["patch_applied_in_sandbox"] is True
