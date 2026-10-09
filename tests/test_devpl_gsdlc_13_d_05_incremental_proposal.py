from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.story_activation_service import StoryActivationApplicationService
from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
from devpilot_core.application.ui_workspace_context import UiWorkspaceContext
from devpilot_core.code_workbench.change_service import SourceChangeApplicationService
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService

ROOT = Path(__file__).resolve().parents[1]


class StaticResolver:
    def __init__(self, context: UiWorkspaceContext) -> None:
        self.context = context

    def resolve(self) -> UiWorkspaceContext:
        return self.context


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path):
    workspace = tmp_path / "inventory-sales-local-greenfield"
    workspace.mkdir(parents=True)
    workspace_id = "inventory-sales-local-greenfield"
    _write(workspace / ".devpilot/project.yaml", 'schema_version: "1.0"\nproject:\n  id: "inventory-sales-local-greenfield"\n  name: "Inventory Sales"\n  type: "application"\n  owner: "owner"\n')
    _write(
        workspace / "docs/01_requirements/requirements_specification.md",
        "# Requirements\n\n### RF-001\n- Statement: El sistema debe permitir al actor autorizado crear productos disponibles.\n\n### RF-002\n- Statement: El sistema debe permitir al actor autorizado consultar productos disponibles.\n",
    )
    _write(workspace / "docs/02_architecture/adrs/ADR-001.md", "# ADR-001\n\nLocal-first modular architecture.\n")
    _write(workspace / "docs/03_security/security_threat_model.md", "# Threats\n\n### SEC-001\nReject unauthorized access.\n")
    _write(workspace / "docs/04_quality/test_strategy.md", "# Tests\n\n### TEST-002\nAuthorized consultation + availability filter.\n")
    _write(
        workspace / "docs/02_architecture/architecture_document.md",
        '''---
status: "frozen"
---
# Architecture

## Tecnología
- **Perfil propuesto para decisión Owner:** `react-ts-fastapi-sqlite`.
- Frontend: `react-typescript`.
- Backend: `fastapi-python`.
- Database: `sqlite`.

## Componentes
- **ARC-C01 — Presentation / Interaction Adapter.** Interaction only.
- **ARC-C02 — Application Services.** Use-case orchestration.
- **ARC-C03 — Domain Core.** Domain behavior.
- **ARC-C04 — Persistence Port + Local Adapter.** Local persistence.
''',
    )
    namespace = "inventory_sales_local_greenfield"
    _write(
        workspace / f"src/{namespace}/domain/product.py",
        StoryImplementationCandidateApplicationService._domain_module(
            "story-rf-001", "Crear productos disponibles", {}, {}
        ),
    )
    _write(
        workspace / f"src/{namespace}/application/create_product.py",
        StoryImplementationCandidateApplicationService._application_module(
            "story-rf-001", "Crear productos disponibles", namespace, {}, {}
        ),
    )
    _write(
        workspace / f"src/{namespace}/infrastructure/sqlite_product_repository.py",
        StoryImplementationCandidateApplicationService._repository_module("story-rf-001", namespace),
    )
    _write(
        workspace / "tests/test_create_product.py",
        StoryImplementationCandidateApplicationService._test_module("story-rf-001", namespace, {}),
    )
    story = {
        "id": "story-rf-002",
        "version": "1.0.0",
        "title": "El sistema debe permitir al actor autorizado consultar productos disponibles",
        "acceptance_criteria": ["Un actor autorizado consulta productos disponibles sin incluir productos no disponibles."],
        "trace_links": [
            {"kind": "requirement", "target_id": "RF-002"},
            {"kind": "adr", "target_id": "ADR-001"},
            {"kind": "risk", "target_id": "SEC-001"},
            {"kind": "test-intent", "target_id": "TEST-002"},
        ],
    }
    sprint = {
        "schema_id": "DEVPL-GSDLC-08-D-SPRINT-PLANNER-V1",
        "lifecycle": "FROZEN",
        "backlog": {"stories": [story]},
        "sprint_plan": {
            "sprint_plan_id": "sprint-plan-pilot-a",
            "selected_stories": [{"story_id": story["id"], "readiness": "READY", "blocking_reasons": [], "estimate": 1}],
            "definition_of_ready": ["Requirement, ADR, risk and test intent are bound."],
            "definition_of_done": ["Targeted tests and governed Git evidence pass."],
            "test_intent_ids": ["TEST-002"],
            "risk_focus_ids": ["SEC-001"],
            "completed_story_ids": ["story-rf-001"],
        },
    }
    _write(workspace / "outputs/planning/gsdlc_08_d" / workspace_id / "sprint_planner.json", json.dumps(sprint, indent=2))
    context = UiWorkspaceContext(
        platform_root=ROOT,
        mode="active-root",
        configured=True,
        valid=True,
        active_workspace_id=workspace_id,
        active_workspace_root=workspace,
        reports_root=workspace / "outputs/reports",
        traces_root=workspace / "outputs/traces",
        project_file=workspace / ".devpilot/project.yaml",
    )
    resolver = StaticResolver(context)
    activation = StoryActivationApplicationService(ROOT, context_resolver=resolver)
    prepared = activation.prepare(story_id=story["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-09T14:00:00Z").to_dict()["data"]
    started = activation.start(expected_state_sha256=prepared["story_execution_state"]["state_sha256"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-09T14:01:00Z").to_dict()
    assert started["ok"] is True
    return workspace, resolver


def test_d05_rf002_existing_source_gets_incremental_deterministic_proposal(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)

    assert code.list_sources().to_dict()["data"]["summary"]["sources_total"] == 4
    result = service.propose(actor="owner-1", actor_role="owner").to_dict()

    assert result["ok"] is True
    proposal = result["data"]["proposal"]
    assert proposal["story_id"] == "story-rf-002"
    assert proposal["provider"]["model_id"] == "deterministic-story-incremental-template-v1"
    assert proposal["provider"]["proposal_mode"] == "incremental-existing-source"
    assert proposal["quality"]["ready_for_draft_materialization"] is True
    assert [x["operation"] for x in proposal["files"]].count("EDIT") == 2
    assert [x["operation"] for x in proposal["files"]].count("CREATE") == 2
    assert all(x.get("source_id") and x.get("source_preimage_sha256") for x in proposal["files"] if x["operation"] == "EDIT")
    assert not (workspace / "src/inventory_sales_local_greenfield/application/list_available_products.py").exists()
    assert not (workspace / "tests/test_list_available_products.py").exists()


def test_d05_rf002_accept_materializes_mixed_edit_create_drafts_without_source_write(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]

    before = {
        "domain": (workspace / "src/inventory_sales_local_greenfield/domain/product.py").read_text(encoding="utf-8"),
        "repo": (workspace / "src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py").read_text(encoding="utf-8"),
    }
    decided = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()

    assert decided["ok"] is True
    drafts = decided["data"]["drafts"]
    assert len(drafts) == 4
    assert {x["operation"] for x in drafts} == {"EDIT", "CREATE"}
    for draft in drafts:
        rechecked = code.recheck_draft(draft["draft_id"]).to_dict()
        assert rechecked["ok"] is True
        assert rechecked["data"]["draft"]["preimage_check"]["status"] == "PASS"
    assert (workspace / "src/inventory_sales_local_greenfield/domain/product.py").read_text(encoding="utf-8") == before["domain"]
    assert (workspace / "src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py").read_text(encoding="utf-8") == before["repo"]
    assert not (workspace / "src/inventory_sales_local_greenfield/application/list_available_products.py").exists()
    assert decided["data"]["source_mutations_performed"] is False

    changes = SourceChangeApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    plan_result = changes.create_plan(draft_ids=[x["draft_id"] for x in drafts], actor="owner-1", actor_role="owner").to_dict()
    assert plan_result["ok"] is True
    assert set(plan_result["data"]["plan"]["exact_path_allowlist"]) == {x["target_path"] for x in drafts}
    assert plan_result["data"]["source_mutations_performed"] is False


def test_d05_existing_source_ui_keeps_deterministic_proposal_action_available() -> None:
    view = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    assert "sourceRowsTotal!==0" not in view
    assert "provider incremental bounded" in view
    assert "Evalúa un provider incremental source-aware" in view
    assert "INCREMENTAL_GENERATOR_ID" in (ROOT / "src/devpilot_core/application/story_implementation_candidate_service.py").read_text(encoding="utf-8")



def test_d05_rf002_incremental_provider_is_eol_agnostic_and_preserves_crlf(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    namespace = "inventory_sales_local_greenfield"
    targets = [
        workspace / f"src/{namespace}/domain/product.py",
        workspace / f"src/{namespace}/infrastructure/sqlite_product_repository.py",
    ]
    for path in targets:
        raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        path.write_bytes(raw.replace(b"\n", b"\r\n"))

    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    result = service.propose(actor="owner-1", actor_role="owner").to_dict()

    assert result["ok"] is True
    proposal = result["data"]["proposal"]
    edited = [row for row in proposal["files"] if row["operation"] == "EDIT"]
    assert len(edited) == 2
    for row in edited:
        content = row["content"]
        assert "\r\n" in content
        assert "\n" not in content.replace("\r\n", "")
        assert "def list_available(self) -> list[Product]:" in content

    decided = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()
    assert decided["ok"] is True
    drafts = decided["data"]["drafts"]
    assert len(drafts) == 4
    assert all(code.recheck_draft(row["draft_id"]).to_dict()["ok"] for row in drafts)
    changes = SourceChangeApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    plan = changes.create_plan(draft_ids=[row["draft_id"] for row in drafts], actor="owner-1", actor_role="owner").to_dict()
    assert plan["ok"] is True
    assert plan["data"]["source_mutations_performed"] is False


def test_d05_incremental_provider_fails_closed_for_unsupported_existing_source_story(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    # Rebind the current runtime state/context to a later Story while preserving the same non-empty source baseline.
    state_path = workspace / "outputs/story_execution/gsdlc_09_a/inventory-sales-local-greenfield/current_state.json"
    context_path = workspace / "outputs/story_execution/gsdlc_09_a/inventory-sales-local-greenfield/story_context_pack.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    context = json.loads(context_path.read_text(encoding="utf-8"))
    state["story_id"] = "story-rf-003"
    state["story_version"] = "1.0.0"
    # StoryExecutionState verifies state_sha256. Keep this test at service level by rewriting through model helpers.
    from devpilot_core.story_execution.models import StoryExecutionState
    rebuilt = StoryExecutionState.from_dict({k: v for k, v in state.items() if k != "state_sha256"})
    state_path.write_text(json.dumps(rebuilt.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    context["story"] = {"id": "story-rf-003", "version": "1.0.0", "title": "Registrar una venta"}
    # Recompute context hash using the same stable JSON contract used by the store fixture is outside this bounded assertion;
    # the provider reads context after StoryExecution validation. Instead assert the provider's helper boundary directly.
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    rows = code.list_sources().to_dict()["data"]["sources"]
    blocked = service._incremental_rf002_files(
        story_id="story-rf-003",
        title="Registrar una venta",
        namespace="inventory_sales_local_greenfield",
        acceptance={},
        source_rows=rows,
    )
    assert hasattr(blocked, "ok") and blocked.ok is False
    assert blocked.findings[0].id == "GSDLC13D05_INCREMENTAL_PROVIDER_UNSUPPORTED_BLOCK"


def test_d05_incremental_accept_blocks_when_bound_source_preimage_drifts(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]

    domain = workspace / "src/inventory_sales_local_greenfield/domain/product.py"
    domain.write_text(domain.read_text(encoding="utf-8") + "\n# unexpected drift\n", encoding="utf-8")
    decided = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()

    assert decided["ok"] is False
    assert any(row["id"] == "GSDLC13D05_INCREMENTAL_SOURCE_DRIFT_BLOCK" for row in decided["findings"])
    assert code.list_drafts().to_dict()["data"]["drafts"] == []
