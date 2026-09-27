from __future__ import annotations

import hashlib
from pathlib import Path

from devpilot_core.application.pre_code_adr_bundle_service import ArchitectureAdrBundleService
from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _architecture() -> str:
    return '''---
doc_id: "ARCH-TEST"
title: "Architecture test"
status: "draft"
version: "1.0.0"
owner: "local-owner"
updated: "2026-09-27"
approval: "runtime"
---
# Architecture

## ADRs

### ADR-001 — Estilo arquitectónico local-first modular

- **Contexto:** contexto uno.
- **Decisión:** decisión uno.
- **Alternativas:** alternativa uno.
- **Consecuencias:** consecuencia uno.

### ADR-002 — Persistencia local gobernada por port/adaptor

- **Contexto:** contexto dos.
- **Decisión:** decisión dos.
- **Alternativas:** alternativa dos.
- **Consecuencias:** consecuencia dos.

### ADR-003 — Perfil tecnológico

- **Perfil propuesto para decisión Owner:** `react-ts-fastapi-sqlite`.
- Frontend: `react-ts`.
- Backend: `fastapi`.
- Database: `sqlite`.
- **Alternativas consideradas:**
- `react-ts-fastapi-sqlite`: frontend `react-ts`, backend `fastapi`, database `sqlite`.
- **Consecuencias:** el perfil queda aprobado solo cuando el Owner aprueba este DRAFT.

### ADR-004 — Consistencia de operaciones mutables

- **Contexto:** contexto cuatro.
- **Decisión:** decisión cuatro.
- **Alternativas:** alternativa cuatro.
- **Consecuencias:** consecuencia cuatro.

## Riesgos

- Ninguno para el fixture.
'''


def _state(architecture_sha: str) -> dict:
    return {
        "workspace_id": "inventory-sales-local-greenfield",
        "stages": {
            "architecture": {
                "stage_id": "architecture",
                "status": "FROZEN",
                "mode": "DEVPL_MOCK",
                "derivation": {"schema_id": "devpilot.gsdlc13c02.technical_design_derivation.v1"},
                "approved_sha256": architecture_sha,
                "approval_id": "APPROVAL-ARCH-TEST",
            }
        },
    }



def _approval_record(*, approval_id: str, plan: dict, workspace_id: str) -> CommandResult:
    return CommandResult(
        "approval show",
        True,
        ExitCode.PASS,
        "ok",
        data={
            "approval": {
                "approval_id": approval_id,
                "subject": plan["plan_id"],
                "tool_id": "workspace.edit.apply",
                "action": "filesystem.pre_code_architecture_adr_bundle_apply",
                "status": "approved",
                "scope": {
                    "subject_hash": plan["plan_hash"],
                    "workspace_id": workspace_id,
                    "exact_path_allowlist": list(plan["exact_path_allowlist"]),
                },
                "metadata": {"plan_hash": plan["plan_hash"]},
            }
        },
        findings=[],
    )

def test_adr_bundle_prepare_is_no_write_and_projects_four_exact_paths(tmp_path: Path) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    (platform / "outputs").mkdir(parents=True)
    adr_root = workspace / "docs/02_architecture/adrs"
    adr_root.mkdir(parents=True)
    arch = workspace / "docs/02_architecture/architecture_document.md"
    arch.write_text(_architecture(), encoding="utf-8", newline="\n")
    state = _state(_sha(arch.read_bytes()))
    service = ArchitectureAdrBundleService(platform)

    before = list(adr_root.iterdir())
    result = service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner")
    after = list(adr_root.iterdir())

    assert result.ok is True
    assert before == after == []
    runtime = state["architecture_adr_bundle"]
    assert runtime["status"] == "PLANNED"
    assert len(runtime["plan"]["changes"]) == 4
    assert runtime["plan"]["exact_path_allowlist"] == [
        "docs/02_architecture/adrs/ADR-001-estilo-arquitectonico-local-first-modular.md",
        "docs/02_architecture/adrs/ADR-002-persistencia-local-gobernada-por-port-adaptor.md",
        "docs/02_architecture/adrs/ADR-003-perfil-tecnologico.md",
        "docs/02_architecture/adrs/ADR-004-consistencia-de-operaciones-mutables.md",
    ]


def test_adr_bundle_approved_apply_materializes_exact_projection_atomically(tmp_path: Path, monkeypatch) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    (platform / "outputs").mkdir(parents=True)
    adr_root = workspace / "docs/02_architecture/adrs"
    adr_root.mkdir(parents=True)
    arch = workspace / "docs/02_architecture/architecture_document.md"
    arch.write_text(_architecture(), encoding="utf-8", newline="\n")
    state = _state(_sha(arch.read_bytes()))
    service = ArchitectureAdrBundleService(platform)
    assert service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner").ok

    monkeypatch.setattr(service.approvals, "request", lambda *_args, **_kwargs: CommandResult(
        "approval request", True, ExitCode.PASS, "ok", data={"approval": {"approval_id": "APPROVAL-ADR-TEST"}}, findings=[]
    ))
    approval = service.request_approval(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner", reason="Approve exact ADR plan")
    assert approval.ok is True
    assert state["architecture_adr_bundle"]["approval_id"] == "APPROVAL-ADR-TEST"

    monkeypatch.setattr("devpilot_core.application.pre_code_adr_bundle_service.PolicyEngine.evaluate", lambda *_args, **_kwargs: CommandResult(
        "policy", True, ExitCode.PASS, "ok", data={}, findings=[Finding("POLICY_PASS", "ok", Severity.INFO)]
    ))
    monkeypatch.setattr(service.approvals, "show", lambda approval_id: _approval_record(
        approval_id=approval_id, plan=state["architecture_adr_bundle"]["plan"], workspace_id=state["workspace_id"]
    ))
    applied = service.apply(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner")
    assert applied.ok is True
    files = sorted(adr_root.glob("ADR-*.md"))
    assert len(files) == 4
    assert service.projection(workspace_root=workspace, workspace_id=state["workspace_id"], state=state)["ready"] is True
    for item in state["architecture_adr_bundle"]["plan"]["changes"]:
        target = workspace / item["relative_path"]
        assert _sha(target.read_bytes()) == item["postimage_sha256"]
        text = target.read_text(encoding="utf-8")
        assert "source_architecture_sha256" in text
        assert "## Criterios PASS/BLOCK" in text


def test_downstream_stage_is_blocked_until_adr_companion_ready(tmp_path: Path) -> None:
    class Gate:
        def __init__(self, ready: bool) -> None:
            self.ready = ready
        def projection(self, **_kwargs):
            return {"required": True, "ready": self.ready, "status": "APPLIED" if self.ready else "REQUIRED"}

    wizard = object.__new__(PreCodeWizardApplicationService)
    wizard._stage_by_id = {"security": {"order": 5}, "architecture": {"order": 4}}
    wizard.adr_bundle = Gate(False)
    state = {"workspace_id": "ws"}
    blocked = wizard._adr_companion_gate(state=state, workspace_root=tmp_path, requested_stage_id="security")
    assert blocked is not None and blocked.ok is False
    assert blocked.findings[0].id == "GSDLC13C02_ADR_COMPANION_REQUIRED_BLOCK"
    assert wizard._adr_companion_gate(state=state, workspace_root=tmp_path, requested_stage_id="architecture") is None
    wizard.adr_bundle = Gate(True)
    assert wizard._adr_companion_gate(state=state, workspace_root=tmp_path, requested_stage_id="security") is None


def test_exact_files_without_approval_bound_receipt_do_not_bypass_gate(tmp_path: Path) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    (platform / "outputs").mkdir(parents=True)
    adr_root = workspace / "docs/02_architecture/adrs"
    adr_root.mkdir(parents=True)
    arch = workspace / "docs/02_architecture/architecture_document.md"
    arch.write_text(_architecture(), encoding="utf-8", newline="\n")
    state = _state(_sha(arch.read_bytes()))
    service = ArchitectureAdrBundleService(platform)
    prepared = service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner")
    assert prepared.ok
    for change in state["architecture_adr_bundle"]["plan"]["changes"]:
        target = workspace / change["relative_path"]
        target.write_text(change["content"], encoding="utf-8", newline="\n")
    state.pop("architecture_adr_bundle", None)
    projection = service.projection(workspace_root=workspace, workspace_id=state["workspace_id"], state=state)
    assert projection["status"] == "BLOCK"
    assert projection["ready"] is False
    recovery = service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner")
    assert recovery.ok is False
    assert recovery.findings[0].id == "GSDLC13C02_ADR_UNTRUSTED_EXISTING_SOURCE_BLOCK"



def test_forged_receipt_without_persisted_approved_record_does_not_unlock_recovery(tmp_path: Path, monkeypatch) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    (platform / "outputs").mkdir(parents=True)
    adr_root = workspace / "docs/02_architecture/adrs"
    adr_root.mkdir(parents=True)
    arch = workspace / "docs/02_architecture/architecture_document.md"
    arch.write_text(_architecture(), encoding="utf-8", newline="\n")
    state = _state(_sha(arch.read_bytes()))
    service = ArchitectureAdrBundleService(platform)
    assert service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner").ok
    plan = state["architecture_adr_bundle"]["plan"]
    for change in plan["changes"]:
        target = workspace / change["relative_path"]
        target.write_text(change["content"], encoding="utf-8", newline="\n")
    receipt = {
        "schema_id": "devpilot.gsdlc13c02.architecture_adr_bundle_execution.v1",
        "execution_id": "adr-exec-forged",
        "workspace_id": state["workspace_id"],
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "approval_id": "APPROVAL-FORGED",
        "architecture_sha256": plan["architecture_sha256"],
        "paths": [{"relative_path": c["relative_path"], "sha256": c["postimage_sha256"]} for c in plan["changes"]],
        "atomic_all_or_nothing": True,
    }
    service._atomic_json(service._receipt_path(state["workspace_id"]), receipt)
    monkeypatch.setattr(service.approvals, "show", lambda _approval_id: CommandResult(
        "approval show", False, ExitCode.FAIL, "not found", data={}, findings=[]
    ))
    state.pop("architecture_adr_bundle", None)
    projection = service.projection(workspace_root=workspace, workspace_id=state["workspace_id"], state=state)
    assert projection["status"] == "BLOCK"
    assert projection["ready"] is False


def test_receipt_write_failure_rolls_back_all_adr_source(tmp_path: Path, monkeypatch) -> None:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    (platform / "outputs").mkdir(parents=True)
    adr_root = workspace / "docs/02_architecture/adrs"
    adr_root.mkdir(parents=True)
    arch = workspace / "docs/02_architecture/architecture_document.md"
    arch.write_text(_architecture(), encoding="utf-8", newline="\n")
    state = _state(_sha(arch.read_bytes()))
    service = ArchitectureAdrBundleService(platform)
    assert service.prepare(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner").ok
    monkeypatch.setattr(service.approvals, "request", lambda *_args, **_kwargs: CommandResult(
        "approval request", True, ExitCode.PASS, "ok", data={"approval": {"approval_id": "APPROVAL-ADR-ROLLBACK"}}, findings=[]
    ))
    assert service.request_approval(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner", reason="Approve exact ADR plan").ok
    monkeypatch.setattr("devpilot_core.application.pre_code_adr_bundle_service.PolicyEngine.evaluate", lambda *_args, **_kwargs: CommandResult(
        "policy", True, ExitCode.PASS, "ok", data={}, findings=[Finding("POLICY_PASS", "ok", Severity.INFO)]
    ))
    def fail_receipt(_path, _value):
        raise OSError("simulated receipt persistence failure")
    monkeypatch.setattr(service, "_atomic_json", fail_receipt)
    applied = service.apply(workspace_root=workspace, workspace_id=state["workspace_id"], state=state, actor="local-owner", actor_role="owner")
    assert applied.ok is False
    assert applied.findings[0].id == "GSDLC13C02_ADR_ATOMIC_APPLY_BLOCK"
    assert sorted(adr_root.glob("ADR-*.md")) == []
    assert state["architecture_adr_bundle"]["status"] == "APPROVAL_PENDING"

def test_adr_companion_api_policy_catalog_and_ui_contract_are_explicit() -> None:
    import json
    root = Path(__file__).resolve().parents[1]
    router = (root / "src/devpilot_core/interfaces/api/routers/guided_sdlc.py").read_text(encoding="utf-8")
    security = (root / "src/devpilot_core/interfaces/api/security.py").read_text(encoding="utf-8")
    view = (root / "ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    client = (root / "ui/web/src/api/client.ts").read_text(encoding="utf-8")
    for suffix in ("prepare", "approval-request", "apply"):
        route = f"/api/v1/guided-sdlc/pre-code/architecture-adrs/{suffix}"
        assert route in router
        assert route in security
        assert route.removeprefix("/api/v1") in client
    assert "architectureAdrGate" in view
    assert "Decisiones incluidas en Architecture" in view
    assert "DevPilot local · grounding ContextPack" in view
    catalog = json.loads((root / ".devpilot/approval/sensitive_action_catalog.json").read_text(encoding="utf-8"))
    action = next(x for x in catalog["actions"] if x["action_id"] == "filesystem.pre_code_architecture_adr_bundle_apply")
    assert action["requires_approval"] is True
    assert action["requires_rbac_role"] == "owner"
    assert action["source_mutation_allowed"] is True
    assert action["tool_ids"] == ["workspace.edit.apply"]
