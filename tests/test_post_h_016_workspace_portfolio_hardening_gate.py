from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.portfolio import WorkspacePortfolioHardeningGate, WorkspacePortfolioHardeningGateOptions
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_016_e_workspace_portfolio_hardening_gate_passes_and_writes_report() -> None:
    result = WorkspacePortfolioHardeningGate(ROOT, WorkspacePortfolioHardeningGateOptions(write_report=True)).run()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-016-E"
    assert summary["quality_gate_subgate"] == "workspace-portfolio-hardening"
    assert summary["workspace_portfolio_hardening_ready"] is True
    assert summary["registry_ok"] is True
    assert summary["isolation_ok"] is True
    assert summary["portfolio_status_ok"] is True
    assert summary["operation_catalog_ok"] is True
    assert summary["registered_workspaces_only"] is True
    assert summary["portfolio_status_read_only"] is True
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False
    assert result.data["reports"] == {
        "json": "outputs/reports/workspace_portfolio_hardening_report.json",
        "markdown": "outputs/reports/workspace_portfolio_hardening_report.md",
    }
    assert (ROOT / "outputs/reports/workspace_portfolio_hardening_report.md").exists()


def test_post_h_016_e_quality_gate_hardening_and_industrial_include_workspace_portfolio_hardening() -> None:
    hardening_gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))
    hardening_subgates = hardening_gate._subgates()
    hardening_ids = [subgate.id for subgate in hardening_subgates]
    assert "workspace-portfolio-hardening" in hardening_ids

    industrial_gate = QualityGate(ROOT, options=QualityGateOptions(profile="industrial"))
    industrial_ids = [subgate.id for subgate in industrial_gate._subgates()]
    assert "workspace-portfolio-hardening" in industrial_ids

    subgate = next(item for item in hardening_subgates if item.id == "workspace-portfolio-hardening")
    assert subgate.critical is True
    result = subgate.runner()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["quality_gate_subgate"] == "workspace-portfolio-hardening"


def test_post_h_016_e_portfolio_hardening_gate_cli_generates_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = main(["portfolio", "hardening-gate", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["command"] == "quality workspace-portfolio-hardening"
    assert payload["data"]["summary"]["reports_written"] is True
    assert payload["data"]["reports"]["json"] == "outputs/reports/workspace_portfolio_hardening_report.json"


def test_post_h_016_e_gate_blocks_invalid_registry_path() -> None:
    result = WorkspacePortfolioHardeningGate(
        ROOT,
        WorkspacePortfolioHardeningGateOptions(registry_path=".devpilot/workspaces/missing_registry.json"),
    ).run()

    assert result.ok is False
    assert result.exit_code in {ExitCode.BLOCK, ExitCode.ERROR}
    assert result.data["summary"]["workspace_portfolio_hardening_ready"] is False
    assert any("WORKSPACE_PORTFOLIO_REGISTRY" in finding.id for finding in result.findings)


def test_post_h_016_e_docs_manifests_and_contracts_are_synchronized() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/05_operations/runbook.md").read_text(encoding="utf-8")
    local_runbook = (ROOT / "docs/05_operations/workspace_portfolio_runbook.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs/05_operations/workspace_onboarding_checklist.md").read_text(encoding="utf-8")
    backlog = (ROOT / "docs/backlogs/POST-H-016_workspace_portfolio_hardening.md").read_text(encoding="utf-8")
    post_doc = (ROOT / "docs/POST-H-016_workspace_portfolio_hardening.md").read_text(encoding="utf-8")
    tcr_v1 = (ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8")
    tcr_v2 = (ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/post_h_016_e_manifest.json").read_text(encoding="utf-8"))

    assert "POST-H-016-E — Quality gate y runbook" in readme
    assert "POST-H-016-E — Quality gate y runbook" in runbook
    assert "workspace-portfolio-hardening" in local_runbook
    assert "Workspace onboarding checklist" in checklist
    assert 'current_micro_sprint: "POST-H-016-E"' in backlog
    assert 'implementation_status: "closed"' in backlog
    assert "POST-H-016-E — Quality gate y runbook" in post_doc
    assert "post-h-016-workspace-portfolio-hardening-gate" in tcr_v1
    assert "post-h-016-workspace-portfolio-hardening-gate" in tcr_v2
    assert manifest["post_h_id"] == "POST-H-016"
    assert manifest["phase"] == "POST-H-016-E"
