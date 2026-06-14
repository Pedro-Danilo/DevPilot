from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.observability import AgentOpsGateOptions, AgentOpsQualityGate, EventRecord, MetricsCollector, TraceContext, TraceStore

ROOT = Path(__file__).resolve().parents[1]


def _copy_agentops_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    (target / "README.md").write_text((ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def _seed_complete_agentops_signals(root: Path) -> None:
    context = TraceContext.start(command="agentops gate test", trace_id="trace_agentops_gate_test")
    store = TraceStore(root)
    metrics = MetricsCollector(root)
    records = [
        ("agent.run", "agent:demo", "agent", "run_total"),
        ("tool.call", "tool:artifact.read", "tool", "call_total"),
        ("policy.check", "policy:read", "policy", "check_total"),
        ("model.call", "model:mock:generate", "model", "calls_total"),
    ]
    metrics.record_count(
        category="command",
        operation="completed_total",
        status="PASS",
        ok=True,
        command="agentops gate test",
        trace_context=context,
        metadata={"payload_redacted": True},
    )
    for span_type, name, category, operation in records:
        span = context.child_span(name=name, span_type=span_type, subject=name).finish()
        span_id = store.record_span(span)
        store.record_event(
            EventRecord(
                event_type=f"{span_type}.completed",
                command="agentops gate test",
                status="PASS",
                ok=True,
                exit_code=0,
                subject=name,
                summary={"span_type": span_type},
                metadata={"payload_redacted": True},
            ),
            trace_context=context,
            span=span,
        )
        metrics.record_count(
            category=category,
            operation=operation,
            status="PASS",
            ok=True,
            command="agentops gate test",
            trace_context=context,
            span_id=span_id,
            metadata={"payload_redacted": True},
        )


def _payload(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)


def test_agentops_quality_gate_passes_with_required_controls_and_signals(tmp_path: Path) -> None:
    _copy_agentops_workspace(tmp_path)
    _seed_complete_agentops_signals(tmp_path)

    result = AgentOpsQualityGate(tmp_path).status(AgentOpsGateOptions(strict_runtime_signals=True))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["operational_status"] == "PASS"
    assert summary["phase_e_closure_ready"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["ui_required"] is False
    assert result.data["control_plane"]["miasi_tools"]["agentops.status"] is True
    assert result.data["control_plane"]["miasi_policy_rules"]["AGENTOPS_STATUS_ALLOW"] is True


def test_agentops_status_cli_writes_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_agentops_workspace(tmp_path)
    _seed_complete_agentops_signals(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["agentops", "status", "--strict-runtime-signals", "--json", "--write-report"])
    payload = _payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "agentops status"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["phase_e_closure_ready"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/agentops_status.json"
    assert (tmp_path / "outputs" / "reports" / "agentops_status.md").is_file()


def test_agentops_quality_gate_blocks_missing_phase_e_closure_report(tmp_path: Path) -> None:
    _copy_agentops_workspace(tmp_path)
    _seed_complete_agentops_signals(tmp_path)
    (tmp_path / "docs" / "audits" / "phase_e_agentops_closure_report.md").unlink()

    result = AgentOpsQualityGate(tmp_path).status(AgentOpsGateOptions(strict_runtime_signals=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "AGENTOPS_REQUIRED_DOCUMENT_MISSING" for finding in result.findings)


def test_agentops_quality_gate_warns_in_empty_runtime_without_false_block(tmp_path: Path) -> None:
    _copy_agentops_workspace(tmp_path)

    result = AgentOpsQualityGate(tmp_path).status()

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["operational_status"] == "WARN"
    assert any(finding.id == "AGENTOPS_SPANS_EMPTY" for finding in result.findings)
    assert any(finding.id == "AGENTOPS_METRICS_EMPTY" for finding in result.findings)
