from __future__ import annotations

from pathlib import Path

import pytest

from devpilot_core.application.workspace_validation_service import VALIDATION_SCOPES, WorkspaceValidationApplicationService

from uoc003_fixtures import create_uoc003_workspace, source_snapshot

ROOT = Path(__file__).resolve().parents[1]


def _service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[WorkspaceValidationApplicationService, Path]:
    workspace = create_uoc003_workspace(tmp_path / "inventory-sales-local")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    return WorkspaceValidationApplicationService(ROOT), workspace


def test_uoc003_plan_is_immutable_bounded_and_covers_eight_precode_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _ = _service(tmp_path, monkeypatch)
    result = service.plan(scopes=["frontmatter", "links", "traceability"], strict=True, timeout_seconds=999)
    assert result.ok, [item.to_dict() for item in result.findings]
    plan = result.data["plan"]
    assert len(plan["artifacts"]) == 8
    assert plan["scopes"] == ["frontmatter", "links", "traceability"]
    assert plan["budgets"]["timeout_seconds"] == 120
    assert plan["safety"]["read_only_source"] is True
    assert plan["safety"]["runtime_evidence_written"] is False
    assert plan["preliminary"] is True


def test_uoc003_execute_passes_selected_deterministic_scopes_and_only_writes_runtime_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, workspace = _service(tmp_path, monkeypatch)
    before = source_snapshot(workspace)
    planned = service.plan(scopes=["frontmatter", "links", "checklist_pre_code", "traceability"])
    plan = planned.data["plan"]
    result = service.execute(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], plan=plan)
    assert result.ok, [item.to_dict() for item in result.findings]
    assert [item["scope"] for item in result.data["steps"]] == ["frontmatter", "links", "checklist_pre_code", "traceability"]
    assert result.data["summary"]["read_only_source"] is True
    assert result.data["summary"]["runtime_evidence_written"] is True
    job = result.data["job"]
    assert (workspace / job["trace_path"]).is_file()
    assert (workspace / job["report_paths"]["json"]).is_file()
    assert source_snapshot(workspace) == before
    status = service.get_job(job_id=job["job_id"])
    assert status.ok


def test_uoc003_blocks_tampered_stale_and_unknown_plans(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, workspace = _service(tmp_path, monkeypatch)
    planned = service.plan(scopes=["frontmatter"])
    plan = dict(planned.data["plan"])
    tampered = {**plan, "strict": False}
    blocked = service.execute(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], plan=tampered)
    assert not blocked.ok
    assert any(item.id == "UOC003_VALIDATION_PLAN_TAMPER_BLOCK" for item in blocked.findings)

    planned = service.plan(scopes=["frontmatter"])
    plan = planned.data["plan"]
    product = workspace / "docs/00_product/product_vision.md"
    product.write_text(product.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    stale = service.execute(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], plan=plan)
    assert any(item.id == "UOC003_VALIDATION_PLAN_STALE_BLOCK" for item in stale.findings)
    missing = service.get_job(job_id="vjob_" + "0" * 32)
    assert not missing.ok
    assert not (workspace / "outputs/traces/uoc_003_validation_jobs").exists()


def test_uoc003_traceability_is_explicit_navigable_and_no_inference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _ = _service(tmp_path, monkeypatch)
    result = service.traceability()
    assert result.ok
    payload = result.data["traceability"]
    assert payload["summary"]["requirements_total"] == 1
    assert payload["summary"]["coverage_percent"] == 100.0
    assert payload["summary"]["semantic_inference_used"] is False
    row = payload["matrix"][0]
    assert row["requirement_id"] == "FR-001"
    assert row["coverage"]["complete"] is True
    assert row["navigation"]["document_id"].startswith("doc_")


def test_uoc003_default_scope_contract_is_complete() -> None:
    assert tuple(VALIDATION_SCOPES) == (
        "frontmatter", "artifact_profile", "links", "miasi", "readiness_strict", "checklist_pre_code", "traceability"
    )
