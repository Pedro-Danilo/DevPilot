from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.application.story_activation_service import StoryActivationApplicationService
from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
from devpilot_core.application.ui_workspace_context import UiWorkspaceContext
from devpilot_core.code_workbench.change_service import SourceChangeApplicationService
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
from devpilot_core.interfaces.api.security import resolve_route_policy

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
    _write(workspace / "docs/01_requirements/requirements_specification.md", "# Requirements\n\n### RF-001\n- Statement: El sistema debe permitir al actor autorizado crear productos disponibles.\n")
    _write(workspace / "docs/02_architecture/adrs/ADR-001.md", "# ADR-001\n\nLocal-first modular architecture.\n")
    _write(workspace / "docs/03_security/security_threat_model.md", "# Threats\n\n### SEC-001\nReject unauthorized mutation.\n")
    _write(workspace / "docs/04_quality/test_strategy.md", "# Tests\n\n### TEST-001\nIntegration + unit for RF-001.\n")
    _write(
        workspace / "docs/02_architecture/architecture_document.md",
        '''---\nstatus: "frozen"\n---\n# Architecture\n\n## Tecnología\n- **Perfil propuesto para decisión Owner:** `react-ts-fastapi-sqlite`.\n- Frontend: `react-typescript`.\n- Backend: `fastapi-python`.\n- Database: `sqlite`.\n\n## Componentes\n- **ARC-C01 — Presentation / Interaction Adapter.** Interaction only.\n- **ARC-C02 — Application Services.** Use-case orchestration.\n- **ARC-C03 — Domain Core.** Domain behavior.\n- **ARC-C04 — Persistence Port + Local Adapter.** Local persistence.\n''',
    )
    story = {
        "id": "story-rf-001",
        "version": "1.0.0",
        "title": "El sistema debe permitir al actor autorizado crear productos disponibles",
        "acceptance_criteria": ["Dados datos válidos, el resultado queda registrado y puede verificarse posteriormente."],
        "trace_links": [
            {"kind": "requirement", "target_id": "RF-001"},
            {"kind": "adr", "target_id": "ADR-001"},
            {"kind": "risk", "target_id": "SEC-001"},
            {"kind": "test-intent", "target_id": "TEST-001"},
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
            "test_intent_ids": ["TEST-001"],
            "risk_focus_ids": ["SEC-001"],
            "completed_story_ids": [],
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
    prepared = activation.prepare(story_id=story["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-01T20:00:00Z").to_dict()["data"]
    started = activation.start(expected_state_sha256=prepared["story_execution_state"]["state_sha256"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-01T20:01:00Z").to_dict()
    assert started["ok"] is True
    return workspace, resolver


def test_d02_source_empty_greenfield_gets_reviewable_deterministic_proposal_without_source_write(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)

    assert code.list_sources().to_dict()["data"]["summary"]["sources_total"] == 0
    result = service.propose(actor="owner-1", actor_role="owner").to_dict()
    assert result["ok"] is True
    proposal = result["data"]["proposal"]
    assert proposal["status"] == "PROPOSED"
    assert proposal["provider"]["provider_id"] == "devpilot-local"
    assert proposal["provider"]["model_id"] == "deterministic-story-implementation-template-v2.1"
    assert proposal["provider"]["network_used"] is False
    assert proposal["provider"]["external_api_used"] is False
    assert proposal["safety"]["proposal_only"] is True
    assert proposal["safety"]["source_mutations_performed"] is False
    assert len(proposal["files"]) == 4
    assert {row["operation"] for row in proposal["files"]} == {"CREATE"}
    assert all(row["target_path"].endswith(".py") for row in proposal["files"])
    assert not (workspace / "src").exists()
    assert not (workspace / "tests").exists()


def test_d02_v2_proposal_is_domain_reusable_docstring_reviewable_and_blocks_business_field_invention(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]

    paths = {row["target_path"] for row in proposal["files"]}
    assert paths == {
        "src/inventory_sales_local_greenfield/domain/product.py",
        "src/inventory_sales_local_greenfield/application/create_product.py",
        "src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py",
        "tests/test_create_product.py",
    }
    assert proposal["quality"]["ready_for_draft_materialization"] is True
    assert proposal["quality"]["docstring_contract_pass"] is True
    assert proposal["quality"]["architecture_coverage"] == {"ARC-C02": True, "ARC-C03": True, "ARC-C04": True}
    assert proposal["quality"]["story_specific_storage"] is False
    assert proposal["quality"]["reusable_product_storage"] is True
    assert proposal["quality"]["business_field_invention"] is False
    assert proposal["quality"]["product_data_contract_posture"].startswith("json-compatible-opaque-attributes")
    assert proposal["quality"]["json_serializable_type_contract"] is True

    combined = "\n".join(row["content"] for row in proposal["files"])
    assert "story_rf_001_records" not in combined
    assert "CREATE TABLE IF NOT EXISTS products" in combined
    assert "class Product:" in combined
    assert "class ProductRepository(Protocol):" in combined
    assert "class CreateProductService:" in combined
    for row in proposal["files"]:
        assert row["docstring_summary"]
        content = row["content"]
        for section in ("Purpose:", "Responsibilities:", "Boundaries:", "Traceability:"):
            assert section in content
        compile(content, row["target_path"], "exec")

    assert not (workspace / "src").exists()
    assert not (workspace / "tests").exists()


def test_d02_accept_materializes_multi_file_runtime_draft_set_and_existing_change_plan_consumes_it(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]

    decided = service.decide(proposal_id=proposal["proposal_id"], proposal_sha256=proposal["proposal_sha256"], decision="ACCEPT", actor="owner-1", actor_role="owner").to_dict()
    assert decided["ok"] is True
    drafts = decided["data"]["drafts"]
    assert len(drafts) == 4
    assert all(row["operation"] == "CREATE" and row["status"] == "DRAFT" for row in drafts)
    assert decided["data"]["source_mutations_performed"] is False
    assert code.list_sources().to_dict()["data"]["summary"]["sources_total"] == 0
    listed = code.list_drafts().to_dict()["data"]["drafts"]
    assert {x["draft_id"] for x in listed} == {x["draft_id"] for x in drafts}

    changes = SourceChangeApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    plan_result = changes.create_plan(draft_ids=[x["draft_id"] for x in drafts], actor="owner-1", actor_role="owner").to_dict()
    assert plan_result["ok"] is True
    plan = plan_result["data"]["plan"]
    assert len(plan["changes"]) == 4
    assert set(plan["exact_path_allowlist"]) == {x["target_path"] for x in drafts}
    assert plan_result["data"]["source_mutations_performed"] is False
    assert not (workspace / "src").exists()
    assert not (workspace / "tests").exists()


def test_d02_v1_proposal_cannot_be_accepted_after_quality_corrective(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    store = service._store_path(workspace, "inventory-sales-local-greenfield")
    payload = json.loads(store.read_text(encoding="utf-8"))
    row = payload["proposals"][proposal["proposal_id"]]
    row["provider"]["model_id"] = "deterministic-story-implementation-template-v1"
    row.pop("quality", None)
    store.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()
    assert result["ok"] is False
    assert result["exit_code"] == 2
    assert "OBSOLETE_PROPOSAL" in json.dumps(result["findings"])
    assert code.list_drafts().to_dict()["data"]["summary"]["drafts_total"] == 0


def test_d02_reject_is_terminal_without_draft_or_source_mutation(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    rejected = service.decide(proposal_id=proposal["proposal_id"], proposal_sha256=proposal["proposal_sha256"], decision="REJECT", actor="owner-1", actor_role="owner").to_dict()
    assert rejected["ok"] is True
    assert rejected["data"]["proposal"]["status"] == "REJECTED"
    assert rejected["data"]["drafts"] == []
    assert code.list_drafts().to_dict()["data"]["summary"]["drafts_total"] == 0
    assert not (workspace / "src").exists()


def test_d02_transport_rbac_ui_and_multifile_bridge_are_registered() -> None:
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    rbac = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    expected = {"api.story-code.drafts.list", "api.story-implementation.proposal.create", "api.story-implementation.proposal.decision"}
    assert expected <= {x["route_id"] for x in api["routes"]}
    assert expected <= {x["route_id"] for x in rbac["route_policies"]}
    assert len(api["routes"]) == len(rbac["route_policies"]) == 246
    story_ui = next(x for x in ui["routes"] if x["route_id"] == "ui.story-code-workbench")
    assert expected <= set(story_ui["allowed_api_routes"])
    assert story_ui["state_contract"]["implementation_proposal_accepted_to_draft_set"] is True
    assert resolve_route_policy("GET", "/api/v1/story/code/drafts") is not None
    assert resolve_route_policy("POST", "/api/v1/story/code/implementation-proposals") is not None
    assert resolve_route_policy("POST", "/api/v1/story/code/implementation-proposals/example/decision") is not None

    view = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    for marker in (
        "integrated-source-tree",
        "Árbol unificado para source real, propuesta DevPilot y Draft Set runtime-only",
        "Proponer implementación desde contexto",
        "Aceptar propuesta → Draft Set",
        "PROPOSAL",
        "read-only hasta ACCEPT",
        "renderUnifiedSourceTree",
        "quality=",
    ):
        assert marker in view
    assert "Implementación propuesta por DevPilot" not in view
    assert "storySourceChangePlanCreate(usable.map((x)=>x.draft_id))" in view


def test_d02_corrective_documents_define_proposal_draftset_and_preserve_first_attempt() -> None:
    contract = (ROOT / "docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_4.md").read_text(encoding="utf-8")
    for marker in (
        "Proposal review model",
        "SourceDraftBuffer Set",
        "multi-file SourceChangePlan",
        "deterministic-story-implementation-template-v2.1",
        "Manual CREATE/EDIT/RENAME",
        "Human-session boundary",
        "Action-feedback locality",
        "filename",
    ):
        assert marker in contract
    adr = (ROOT / "docs/02_architecture/adrs/ADR-DEVPL-GSDLC-13-D-02-deterministic-implementation-proposal-before-source-plan.md").read_text(encoding="utf-8")
    assert "FUNC-13D02-IMPLEMENTATION-BRIDGE-001" in adr
    assert "SourceDraftBuffer Set" in adr
    adjudication = (ROOT / "docs/audits/DEVPL_GSDLC_13_D_02_FIRST_ATTEMPT_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    assert "RUN_01 = BLOCK" in adjudication
    assert "99_block_state.png" in adjudication
    run_card = (ROOT / "docs/validation/RUN_CARD_13_D_02_v1_0_3_APPROVED.md").read_text(encoding="utf-8")
    for marker in (
        'version: "1.0.3"',
        'continuation_run: "RUN_02"',
        "Proponer implementación desde contexto",
        "Información y provenance",
        "99_block_state_v2.png",
        "SourceChangePlan",
        "CHANGES_READY",
        "screenshots 01..06",
        "Full Regression=0",
    ):
        assert marker in run_card
    payload = run_card.encode("utf-8")
    assert sorted({x for x in payload if x < 32 and x not in {9, 10, 13}}) == []


def test_d02_repeated_propose_recovers_same_terminal_proposal_without_reopening(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    decided = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()
    assert decided["ok"] is True
    recovered = service.propose(actor="owner-1", actor_role="owner").to_dict()
    assert recovered["ok"] is True
    assert recovered["data"]["recovered"] is True
    assert recovered["data"]["proposal"]["proposal_id"] == proposal["proposal_id"]
    assert recovered["data"]["proposal"]["status"] == "ACCEPTED"
    assert len(recovered["data"]["proposal"]["draft_ids"]) == 4
    assert code.list_drafts().to_dict()["data"]["summary"]["drafts_total"] == 4
    assert not (workspace / "src").exists()


def test_d02_accept_reconciles_exact_partial_draft_set_after_interruption(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    first = proposal["files"][0]
    seeded = code.save_draft(
        operation="CREATE",
        content=first["content"],
        target_path=first["target_path"],
        source_id=None,
        expected_source_sha256=None,
        expected_revision_sha256=None,
        actor="owner-1",
        actor_role="owner",
    ).to_dict()
    assert seeded["ok"] is True
    decided = service.decide(
        proposal_id=proposal["proposal_id"],
        proposal_sha256=proposal["proposal_sha256"],
        decision="ACCEPT",
        actor="owner-1",
        actor_role="owner",
    ).to_dict()
    assert decided["ok"] is True
    assert len(decided["data"]["drafts"]) == 4
    assert code.list_drafts().to_dict()["data"]["summary"]["drafts_total"] == 4
    assert not (workspace / "src").exists()


def test_d02_session_expiry_feedback_and_compact_tree_contract() -> None:
    view = (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    styles = (ROOT / "ui/web/src/styles.css").read_text(encoding="utf-8")
    for marker in (
        "Información y provenance",
        "storyImplementationFeedback",
        "storySourceChangeFeedback",
        "ensureLiveHumanSession",
        "client().authSession()",
        "Reautenticar y volver a Story Code",
        "proposalReviewFile",
        "actions.hidden=true",
        "actions.hidden=false",
        "b=button(name)",
        "aria-label',`${entry.state} · ${entry.path}`",
    ):
        assert marker in view
    assert "button(`${entry.state} · ${name}`)" not in view
    for marker in (".code-source-tree-info", ".code-source-item{appearance:none", ".code-action-feedback"):
        assert marker in styles


def test_d02_story_code_session_policy_remains_fail_closed() -> None:
    # Corrective improves browser preflight/feedback; it must not relax server-side human-session policy.
    security = (ROOT / "src/devpilot_core/interfaces/api/security.py").read_text(encoding="utf-8")
    app = (ROOT / "src/devpilot_core/interfaces/api/app.py").read_text(encoding="utf-8")
    assert '("POST", "/api/v1/story/code/implementation-proposals/{proposal_id}/decision")' in security
    assert "Authenticated human session is required for this local API endpoint." in app
    assert "session_required and human_session is None" in app


def test_d02_session_feedback_corrective_documents_are_governed() -> None:
    audit = (ROOT / "docs/audits/DEVPL_GSDLC_13_D_02_SESSION_FEEDBACK_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    assert "FUNC-UX-13D02-SESSION-012" in audit
    assert "1800-second idle timeout" in audit
    assert "Do not weaken this security boundary" in audit
    run_card = (ROOT / "docs/validation/RUN_CARD_13_D_02_v1_0_3_APPROVED.md").read_text(encoding="utf-8")
    for marker in ("Información y provenance", "Reauthentication", "four exact Drafts", "Full Regression=0"):
        assert marker.lower() in run_card.lower()


def test_d02_v21_product_attribute_contract_is_json_compatible_without_business_schema(tmp_path: Path) -> None:
    workspace, resolver = _fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    assert proposal["provider"]["model_id"] == "deterministic-story-implementation-template-v2.1"
    assert proposal["quality"]["json_serializable_type_contract"] is True
    domain = next(row for row in proposal["files"] if row.get("artifact_role") == "domain")["content"]
    assert 'JsonValue: TypeAlias' in domain
    assert 'ProductAttributes: TypeAlias = Mapping[str, JsonValue]' in domain
    assert 'name:' not in domain and 'sku:' not in domain and 'price:' not in domain and 'stock:' not in domain


def test_d02_draft_plan_governance_ui_and_docs_contract() -> None:
    view=(ROOT/"ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    styles=(ROOT/"ui/web/src/styles.css").read_text(encoding="utf-8")
    for marker in (
        "Guardar cambios en draft",
        "preimage_check",
        "Owner review · qué debes decidir antes de approval",
        "sourceChangeOwnerReviewed",
        "Test Impact preview · no equivale a cobertura de tests",
        "dryRunPassed",
        "finalRecheckPassed",
        "approval requiere Dry-run PASS persistido",
    ):
        assert marker in view
    assert ".code-workbench-actions[hidden]{display:none!important}" in styles
    contract=(ROOT/"docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_5.md").read_text(encoding="utf-8")
    run_card=(ROOT/"docs/validation/RUN_CARD_13_D_02_v1_0_4_APPROVED.md").read_text(encoding="utf-8")
    audit=(ROOT/"docs/audits/DEVPL_GSDLC_13_D_02_DRAFT_PLAN_GOVERNANCE_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    for marker in ("dry-run PASS receipt","per-Draft","unmatched_paths_total"):
        assert marker.lower() in contract.lower()
    assert 'version: "1.0.4"' in run_card and "FUNC-GOV-13D02-DRYRUN-014" in audit


def test_d02_source_change_resumability_owner_gate_and_collapsible_story_sections_contract() -> None:
    view=(ROOT/"ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")
    styles=(ROOT/"ui/web/src/styles.css").read_text(encoding="utf-8")
    services=(ROOT/"src/devpilot_core/application/services.py").read_text(encoding="utf-8")
    change_service=(ROOT/"src/devpilot_core/code_workbench/change_service.py").read_text(encoding="utf-8")
    for marker in (
        "source_change_recovery",
        "active_plan",
        "dry_run_receipt_valid",
    ):
        assert marker in services or marker in change_service
    for marker in (
        "SourceChangeRecovery",
        "restoreApplyContext(story,recovery)",
        "Colapsar inactivas",
        "Expandir todas",
        "story-code-section",
        "Falta confirmar la revisión Owner para habilitar Dry-run",
        "source-change-owner-review-gate",
        "activeSectionId",
    ):
        assert marker in view
    assert "for(const row of candidates)" not in view
    assert ".story-code-section" in styles
    assert ".source-change-owner-review-confirmation" in styles

    contract=(ROOT/"docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_6.md").read_text(encoding="utf-8")
    run_card=(ROOT/"docs/validation/RUN_CARD_13_D_02_v1_0_5_APPROVED.md").read_text(encoding="utf-8")
    audit=(ROOT/"docs/audits/DEVPL_GSDLC_13_D_02_SOURCE_CHANGE_PLAN_RESUMABILITY_ADJUDICATION_v1_0_0.md").read_text(encoding="utf-8")
    for marker in (
        "server-authoritative",
        "current StoryExecution",
        "Draft revisions",
        "Progressive disclosure",
    ):
        assert marker.lower() in contract.lower()
    assert 'version: "1.0.5"' in run_card
    assert "source-plan-e4c37acd9038329150734b4c" in run_card
    assert "FUNC-RESUME-13D02-SOURCE-PLAN-019" in audit
