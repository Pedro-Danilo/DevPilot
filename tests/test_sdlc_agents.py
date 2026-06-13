from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.agents import AgentRuntime


def test_requirements_agent_detects_requirement_without_criterion_fixture(tmp_path: Path) -> None:
    root = tmp_path
    (root / ".devpilot" / "miasi").mkdir(parents=True)
    # Use the real project registries and prompt contracts through current repo root.
    # This test focuses on the shipped fixture path via AgentRuntime in the project.
    project_root = Path(__file__).resolve().parents[1]
    case_dir = project_root / "outputs" / "tests" / "sdlc_requirements_fixture"
    if case_dir.exists():
        import shutil
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    (case_dir / "requirements.md").write_text("# Requirements\n\nFR-SDLC-001 must exist without explicit criterion.\n", encoding="utf-8")

    result = AgentRuntime(project_root).run("requirements", target=str(case_dir.relative_to(project_root)), provider="mock")

    assert result.ok is True
    assert result.data["agent"]["agent_id"] == "requirements.agent"
    assert result.data["summary"]["model_calls_total"] == 1
    assert any(finding.id == "REQUIREMENTS_AGENT_REQUIREMENTS_WITHOUT_ACCEPTANCE_CRITERIA" for finding in result.findings)
    assert result.data["artifacts"]["mutations_performed"] is False


def test_architecture_agent_detects_unbacked_component_fixture(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    case_dir = project_root / "outputs" / "tests" / "sdlc_architecture_fixture"
    if case_dir.exists():
        import shutil
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    (case_dir / "architecture.md").write_text("# Architecture\n\nComponent: Synthetic Gateway implemented.\n", encoding="utf-8")

    result = AgentRuntime(project_root).run("architecture", target=str(case_dir.relative_to(project_root)), provider="mock")

    assert result.ok is True
    assert result.data["agent"]["agent_id"] == "architecture.agent"
    assert result.data["summary"]["model_calls_total"] == 1
    assert any(finding.id == "ARCHITECTURE_AGENT_UNBACKED_COMPONENT" for finding in result.findings)
    assert result.data["artifacts"]["mutations_performed"] is False


def test_security_agent_detects_secret_fixture_without_exposing_raw_secret(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    case_dir = project_root / "outputs" / "tests" / "sdlc_security_fixture"
    if case_dir.exists():
        import shutil
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    (case_dir / "security.md").write_text("# Security\n\nOPENAI_API_KEY=sk-1234567890abcdef\n", encoding="utf-8")

    result = AgentRuntime(project_root).run("security", target=str(case_dir.relative_to(project_root)))
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert result.data["agent"]["agent_id"] == "security.agent"
    assert any(finding.id == "SECURITY_AGENT_SECRET_DETECTED" for finding in result.findings)
    assert "sk-1234567890abcdef" not in payload
    assert result.data["artifacts"]["mutations_performed"] is False


def test_sdlc_agent_aliases_remain_monoagent_and_local_on_small_fixtures() -> None:
    project_root = Path(__file__).resolve().parents[1]
    case_dir = project_root / "outputs" / "tests" / "sdlc_alias_fixture"
    if case_dir.exists():
        import shutil
        shutil.rmtree(case_dir)
    (case_dir / "requirements").mkdir(parents=True)
    (case_dir / "architecture").mkdir(parents=True)
    (case_dir / "security").mkdir(parents=True)
    (case_dir / "requirements" / "requirements.md").write_text("# Requirements\n\nFR-SDLC-002 has AC-SDLC-002 and TEST-SDLC-002.\n", encoding="utf-8")
    (case_dir / "architecture" / "architecture.md").write_text("# Architecture\n\nComponent: Fixture Gateway implemented.\n", encoding="utf-8")
    (case_dir / "security" / "security.md").write_text("# Security\n\n## Propósito\n\nNo raw secrets.\n", encoding="utf-8")

    requirements = AgentRuntime(project_root).run("requirements", target=str((case_dir / "requirements").relative_to(project_root)), provider="mock")
    architecture = AgentRuntime(project_root).run("architecture", target=str((case_dir / "architecture").relative_to(project_root)), provider="mock")
    security = AgentRuntime(project_root).run("security", target=str((case_dir / "security").relative_to(project_root)), provider="mock")

    assert requirements.ok is True
    assert architecture.ok is True
    assert security.ok is True
    assert requirements.data["metadata"]["handoffs_enabled"] is False
    assert architecture.data["metadata"]["external_api_used"] is False
    assert security.data["metadata"]["external_api_used"] is False
