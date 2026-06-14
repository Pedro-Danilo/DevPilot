from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.agents import AgentRuntime
from devpilot_core.approval.service import ApprovalCliInput, ApprovalService
from devpilot_core.cli_models import ExitCode
from devpilot_core.modeling import ModelAdapterRouter
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.store import LocalStore

ROOT = Path(__file__).resolve().parents[1]


def _copy_agent_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "evals", target / "evals", dirs_exist_ok=True)
    (target / ".devpilot" / "providers.yaml.example").write_text(
        (ROOT / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def test_agent_runtime_persists_correlated_agentops_spans_and_metrics(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("documentation-audit", target="docs/01_requirements", provider="mock", dry_run=True)

    assert result.ok is True
    agentops = result.data["metadata"]["agentops"]
    assert agentops["enabled"] is True
    assert agentops["payload_redacted"] is True
    trace_id = agentops["trace_id"]
    spans = LocalStore(tmp_path).list_spans(trace_id=trace_id, limit=100)
    span_types = {span["span_type"] for span in spans}
    assert {"agent.run", "tool.call", "policy.check", "model.call"}.issubset(span_types)
    metrics = LocalStore(tmp_path).list_metrics(limit=200)
    categories = {metric["category"] for metric in metrics}
    assert {"agent", "tool", "policy", "model"}.issubset(categories)
    serialized = json.dumps({"spans": spans, "metrics": metrics}, ensure_ascii=False).lower()
    assert "sk-" not in serialized
    assert "api_key=" not in serialized


def test_policy_engine_records_policy_span_metric_without_leaking_text(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "file.md").write_text("# File\n", encoding="utf-8")

    result = PolicyEngine(tmp_path).evaluate(
        PolicyRequest(action="read", path="docs/file.md", text="api_key=sk-1234567890abcdef", dry_run=True)
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    spans = LocalStore(tmp_path).list_spans(limit=20)
    assert any(span["span_type"] == "policy.check" for span in spans)
    metrics = LocalStore(tmp_path).list_metrics(category="policy", limit=20)
    assert metrics
    serialized = json.dumps({"spans": spans, "metrics": metrics}, ensure_ascii=False)
    assert "sk-1234567890abcdef" not in serialized


def test_approval_service_records_approval_workflow_spans_and_metrics(tmp_path: Path) -> None:
    service = ApprovalService(tmp_path)

    request = service.request(
        ApprovalCliInput(
            tool_id="tests.run",
            action="execute",
            subject="pytest",
            actor="owner",
            reason="Validar cambios locales",
            scope='{"profile":"unit"}',
        )
    )
    approval_id = request.data["approval"]["approval_id"]
    approve = service.approve(approval_id, actor="owner", reason="Revisión OK")

    assert request.ok is True
    assert approve.ok is True
    spans = LocalStore(tmp_path).list_spans(limit=20)
    assert sum(1 for span in spans if span["span_type"] == "approval.workflow") >= 2
    metrics = LocalStore(tmp_path).list_metrics(category="approval", limit=20)
    assert {metric["operation"] for metric in metrics} >= {"request_total", "approved_total"}


def test_model_router_records_model_call_span_and_model_metrics(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = ModelAdapterRouter(tmp_path).generate(prompt="hello", provider="mock")

    assert result.ok is True
    spans = LocalStore(tmp_path).list_spans(limit=20)
    assert any(span["span_type"] == "model.call" for span in spans)
    metrics = LocalStore(tmp_path).list_metrics(category="model", limit=20)
    assert {metric["operation"] for metric in metrics} >= {"calls_total", "tokens_estimated", "cost_estimate_usd"}
