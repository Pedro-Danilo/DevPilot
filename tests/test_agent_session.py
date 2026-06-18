from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from devpilot_core.agents.session import AgentSessionStore, inspect_agent_session
from devpilot_core.agents.runtime import AgentRuntime
from devpilot_core.cli_models import ExitCode

SESSION_RE = re.compile(r"^agsess_[a-f0-9]{32}$")


def test_agent_runtime_creates_inspectable_session(tmp_path: Path) -> None:
    root = Path.cwd()
    result = AgentRuntime(root).run("release-assistant", dry_run=True)
    assert result.ok is True
    session = result.data["metadata"]["agent_session"]
    assert SESSION_RE.match(session["session_id"])
    assert session["semantic_memory_enabled"] is False
    assert session["rag_enabled"] is False

    inspected = inspect_agent_session(root, session_id=session["session_id"])
    assert inspected.ok is True
    assert inspected.data["summary"]["session_found"] is True
    assert inspected.data["summary"]["raw_prompts_stored"] is False
    assert inspected.data["summary"]["raw_outputs_stored"] is False
    assert inspected.data["summary"]["semantic_memory_enabled"] is False
    assert inspected.data["summary"]["rag_enabled"] is False
    assert inspected.data["summary"]["localstore_projection_used"] is True
    assert len(inspected.data["events"]) >= 2


def test_agent_runtime_can_reuse_existing_session() -> None:
    root = Path.cwd()
    first = AgentRuntime(root).run("release-assistant", dry_run=True)
    session_id = first.data["summary"]["agent_session_id"]
    second = AgentRuntime(root).run("release-assistant", dry_run=True, session_id=session_id)
    assert second.ok is True
    assert second.data["summary"]["agent_session_id"] == session_id

    inspected = inspect_agent_session(root, session_id=session_id, limit=10)
    assert inspected.ok is True
    assert inspected.data["summary"]["events_total"] >= 4
    assert inspected.data["summary"]["agents_total"] >= 1


def test_agent_session_rejects_invalid_or_missing_session_id() -> None:
    root = Path.cwd()
    invalid = inspect_agent_session(root, session_id="../../evil")
    assert invalid.ok is False
    assert invalid.exit_code == ExitCode.BLOCK
    assert invalid.findings[0].id == "AGENT_SESSION_INVALID_ID"

    missing = inspect_agent_session(root, session_id="agsess_" + "0" * 32)
    assert missing.ok is False
    assert missing.exit_code == ExitCode.BLOCK
    assert missing.findings[0].id == "AGENT_SESSION_NOT_FOUND"


def test_agent_session_redacts_sensitive_operational_memory() -> None:
    root = Path.cwd()
    store = AgentSessionStore(root)
    session = store.start_session(
        agent_id="precode.audit",
        requested_agent="precode-audit",
        target="docs",
        dry_run=True,
        metadata={"api_key": "sk-test-secret-value", "safe": "visible"},
    )
    inspected = store.inspect(type("Options", (), {"session_id": session.session_id, "include_events": True, "limit": 20})())
    payload = json.dumps(inspected.to_dict(), ensure_ascii=False)
    assert "sk-test-secret-value" not in payload
    assert "[REDACTED]" in payload
    assert inspected.data["summary"]["rag_enabled"] is False


def test_agent_session_cli_json_and_write_report() -> None:
    root = Path.cwd()
    run = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "run", "release-assistant", "--dry-run", "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert run.returncode == 0, run.stderr or run.stdout
    payload = json.loads(run.stdout)
    session_id = payload["data"]["summary"]["agent_session_id"]

    inspect = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "session", "inspect", "--session-id", session_id, "--json", "--write-report"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert inspect.returncode == 0, inspect.stderr or inspect.stdout
    inspected = json.loads(inspect.stdout)
    assert inspected["ok"] is True
    assert inspected["data"]["summary"]["session_found"] is True
    assert inspected["data"]["reports"]["json"].endswith(".json")


def test_agent_session_is_excluded_from_release_package() -> None:
    from devpilot_core.release.package_builder import _is_excluded
    from devpilot_core.release.verification import _contains_forbidden_marker

    assert _is_excluded(".devpilot/agent_sessions/agsess_123.json") is True
    assert _contains_forbidden_marker("devpilot/.devpilot/agent_sessions/agsess_123.json") is True
