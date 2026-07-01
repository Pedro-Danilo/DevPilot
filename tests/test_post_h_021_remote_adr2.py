from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = ROOT / "docs/adr/ADR-POSTH-004-remote-runner-adr2.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_remote_runner_adr2_exists_approved_and_design_only() -> None:
    text = ADR_PATH.read_text(encoding="utf-8")

    assert 'doc_id: "ADR-POSTH-004"' in text
    assert 'status: "approved"' in text
    assert 'decision_status: "design-only"' in text
    assert 'micro_sprint: "POST-H-021-B"' in text
    assert "remote_execution_allowed: false" in text
    assert "remote_runner_enabled: false" in text
    assert "requires_future_adr: true" in text


def test_remote_runner_adr2_rejects_unsafe_alternatives() -> None:
    text = ADR_PATH.read_text(encoding="utf-8").lower()

    for required in [
        "enable-now",
        "ssh ad hoc",
        "connector-as-runner",
        "plugin-as-runner",
    ]:
        assert required in text
    assert text.count("rechazada") >= 4


def test_remote_runner_adr2_lists_future_prerequisites_and_controls() -> None:
    text = ADR_PATH.read_text(encoding="utf-8").lower()

    for required in [
        "post-h-022",
        "post-h-023",
        "rbac",
        "approval",
        "sandbox",
        "observabilidad",
        "secretos",
        "kill-switch",
        "quality gate",
        "dry-run",
    ]:
        assert required in text


def test_remote_runner_adr2_does_not_authorize_immediate_execution() -> None:
    text = ADR_PATH.read_text(encoding="utf-8").lower()

    assert "no habilita ejecución remota" in text
    assert "block" in text
    assert "execution_allowed=false" in text
    assert "remote_execution_used=false" in text

    forbidden_phrases = [
        "remote execution habilitada",
        "remote runner habilitado",
        "execution_allowed=true",
        "remote_runner_enabled=true",
        "remote_execution_allowed=true",
        "credentials_required=true",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_post_h_021_backlog_tracks_adr2_micro_sprint_state() -> None:
    backlog = read("docs/backlogs/POST-H-021_remote_runner_adr2.md")
    implementation = read("docs/POST-H-021_remote_runner_adr2.md")
    state = json.loads(read(".devpilot/project_state.json"))

    for text in (backlog, implementation):
        assert 'current_micro_sprint: "POST-H-021-C"' in text
        assert 'next_micro_sprint: "POST-H-021-D"' in text
        assert "POST-H-021-B — ADR-2 de Remote Runner" in text
        assert "POST-H-021-C — Remote readiness report read-only" in text
        assert "ADR-POSTH-004-remote-runner-adr2.md" in text

    assert state["current_micro_sprint"] == "POST-H-021-C"
    assert state["next_micro_sprint"] == "POST-H-021-D"
    assert any("POST-H-021-B adds ADR-POSTH-004" in note for note in state["notes"])
    assert any("POST-H-021-C adds RemoteReadinessChecker" in note for note in state["notes"])


def test_remote_runner_adr2_manifest_and_report_are_synchronized() -> None:
    manifest = json.loads(read("docs/post_h_021_b_manifest.json"))
    report = read("docs/audits/post_h_021_b_remote_adr2_report.md")

    assert manifest["micro_sprint"] == "POST-H-021-B"
    assert manifest["status"] == "implemented-initial"
    assert manifest["remote_execution_enabled"] is False
    assert manifest["network_used"] is False
    assert manifest["external_api_used"] is False
    assert "docs/adr/ADR-POSTH-004-remote-runner-adr2.md" in manifest["created_files"]
    assert "tests/test_post_h_021_remote_adr2.py" in manifest["created_files"]
    assert "remote_execution_allowed=false" in report
    assert "POST-H-022" in report
    assert "POST-H-023" in report
