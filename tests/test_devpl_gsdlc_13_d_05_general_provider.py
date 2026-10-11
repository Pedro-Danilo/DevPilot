from __future__ import annotations
import json
from pathlib import Path
import pytest
from devpilot_core.application.story_activation_service import StoryActivationApplicationService
from devpilot_core.application.story_implementation_candidate_service import StoryImplementationCandidateApplicationService
from devpilot_core.application.ui_workspace_context import UiWorkspaceContext
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
from devpilot_core.code_workbench.change_service import SourceChangeApplicationService
from test_devpl_gsdlc_13_d_05_incremental_proposal import ROOT, StaticResolver, _write

def _rf003_fixture(tmp_path: Path, story_id: str = "story-rf-003"):
    workspace = tmp_path / "inventory-sales-local-greenfield"
    workspace.mkdir(parents=True)
    workspace_id = "inventory-sales-local-greenfield"
    _write(workspace / ".devpilot/project.yaml", 'schema_version: "1.0"\nproject:\n  id: "inventory-sales-local-greenfield"\n  name: "Inventory Sales"\n  type: "application"\n  owner: "owner"\n')
    _write(
        workspace / "docs/01_requirements/requirements_specification.md",
        "# Requirements\n\n### RF-001\n- Statement: El sistema debe permitir al actor autorizado crear productos disponibles.\n\n### RF-003\n- Statement: El sistema debe permitir al actor autorizado modificar productos disponibles.\n",
    )
    _write(workspace / "docs/02_architecture/adrs/ADR-001.md", "# ADR-001\n\nLocal-first modular architecture.\n")
    _write(workspace / "docs/03_security/security_threat_model.md", "# Threats\n\n### SEC-001\nReject unauthorized access.\n")
    _write(workspace / "docs/04_quality/test_strategy.md", "# Tests\n\n### TEST-003\nAuthorized modification + durable update.\n")
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
    domain_path = workspace / f"src/{namespace}/domain/product.py"
    repo_path = workspace / f"src/{namespace}/infrastructure/sqlite_product_repository.py"
    _write(domain_path, StoryImplementationCandidateApplicationService._rf002_domain_content(domain_path.read_text(encoding="utf-8")))
    _write(repo_path, StoryImplementationCandidateApplicationService._rf002_repository_content(repo_path.read_text(encoding="utf-8")))
    _write(workspace / f"src/{namespace}/application/list_available_products.py",
        StoryImplementationCandidateApplicationService._rf002_application_module(
            "story-rf-002", "El sistema debe permitir al actor autorizado consultar productos disponibles", namespace, {}))
    _write(workspace / "tests/test_list_available_products.py",
        StoryImplementationCandidateApplicationService._rf002_test_module("story-rf-002", namespace, {}))
    story = {
        "id": story_id,
        "version": "1.0.0",
        "title": "El sistema debe permitir al actor autorizado modificar productos disponibles",
        "acceptance_criteria": ["Un actor autorizado modifica los atributos de un producto disponible y verifica el estado actualizado."],
        "trace_links": [
            {"kind": "requirement", "target_id": "RF-003"},
            {"kind": "adr", "target_id": "ADR-001"},
            {"kind": "risk", "target_id": "SEC-001"},
            {"kind": "test-intent", "target_id": "TEST-003"},
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
            "test_intent_ids": ["TEST-003"],
            "risk_focus_ids": ["SEC-001"],
            "completed_story_ids": ["story-rf-001", "story-rf-002"],
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
    prepared_result = activation.prepare(story_id=story["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-09T14:00:00Z").to_dict(); assert prepared_result["ok"], prepared_result; prepared = prepared_result["data"]
    assert prepared is not None, activation.prepare(story_id=story["id"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-09T14:00:00Z").to_dict()
    started = activation.start(expected_state_sha256=prepared["story_execution_state"]["state_sha256"], actor_id="owner-1", actor_role="owner", observed_at_utc="2026-10-09T14:01:00Z").to_dict()
    assert started["ok"] is True
    return workspace, resolver


def test_rf003_successor_generates_four_governed_files_and_drafts(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    sources_before = {p: (workspace / p).read_bytes() for p in (
        "src/inventory_sales_local_greenfield/domain/product.py",
        "src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py")}
    result = service.propose(actor="owner-1", actor_role="owner").to_dict()
    assert result["ok"] is True, result
    proposal = result["data"]["proposal"]
    assert proposal["provider"]["model_id"] == service.GENERAL_GENERATOR_ID
    assert proposal["provider"]["network_used"] is False
    assert proposal["safety"]["source_mutations_performed"] is False
    assert proposal["quality"]["ready_for_draft_materialization"] is True
    assert sorted(x["operation"] for x in proposal["files"]) == ["CREATE", "CREATE", "EDIT", "EDIT"]
    assert all(x["source_id"] and x["source_preimage_sha256"] for x in proposal["files"] if x["operation"] == "EDIT")
    assert all(not (workspace / x["target_path"]).exists() for x in proposal["files"] if x["operation"] == "CREATE")
    decided = service.decide(proposal_id=proposal["proposal_id"], proposal_sha256=proposal["proposal_sha256"],
                             decision="ACCEPT", actor="owner-1", actor_role="owner").to_dict()
    assert decided["ok"] is True, decided
    drafts = decided["data"]["drafts"]
    assert len(drafts) == 4
    assert all(code.recheck_draft(x["draft_id"]).to_dict()["ok"] for x in drafts)
    assert all((workspace / p).read_bytes() == before for p, before in sources_before.items())
    assert all(not (workspace / x["target_path"]).exists() for x in proposal["files"] if x["operation"] == "CREATE")
    change = SourceChangeApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    planned = change.create_plan(draft_ids=[x["draft_id"] for x in drafts], actor="owner-1", actor_role="owner").to_dict()
    assert planned["ok"] is True, planned
    assert set(planned["data"]["plan"]["exact_path_allowlist"]) == {x["target_path"] for x in proposal["files"]}


def test_rf003_generated_application_acceptance_against_rf002_baseline(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    for row in proposal["files"]:
        _write(workspace / row["target_path"], row["content"])
    import subprocess, sys, os
    env = dict(os.environ)
    env["PYTHONPATH"] = str(workspace)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_create_product.py",
                             "tests/test_list_available_products.py", "tests/test_modify_product.py"],
                            cwd=workspace, capture_output=True, text=True, env=env, timeout=45)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "passed" in result.stdout


def test_rf003_rejects_preimage_drift_and_missing_baseline(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    domain = workspace / "src/inventory_sales_local_greenfield/domain/product.py"
    domain.write_text(domain.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    result = service.decide(proposal_id=proposal["proposal_id"], proposal_sha256=proposal["proposal_sha256"],
                            decision="ACCEPT", actor="owner-1", actor_role="owner").to_dict()
    assert result["ok"] is False
    assert any(f["id"] == "GSDLC13D05_INCREMENTAL_SOURCE_DRIFT_BLOCK" for f in result["findings"])
    assert code.list_drafts().to_dict()["data"]["drafts"] == []
    domain.write_text(domain.read_text(encoding="utf-8").removesuffix("\n# drift\n"), encoding="utf-8")
    (workspace / "tests/test_list_available_products.py").unlink()
    blocked = service.propose(actor="owner-1", actor_role="owner").to_dict()
    assert blocked["ok"] is False
    assert any(f["id"] == "GSDLC13D05_RF003_BASELINE_BLOCK" for f in blocked["findings"])


def test_rf003_eol_preserved_without_changing_source_preimages(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path)
    domain_path = workspace / "src/inventory_sales_local_greenfield/domain/product.py"
    repo_path = workspace / "src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py"
    for path in (domain_path, repo_path):
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    proposal = service.propose(actor="owner-1", actor_role="owner").to_dict()["data"]["proposal"]
    for row in proposal["files"]:
        if row["operation"] == "EDIT":
            assert "\r\n" in row["content"]
            assert "\n" not in row["content"].replace("\r\n", "")
    assert service.decide(proposal_id=proposal["proposal_id"], proposal_sha256=proposal["proposal_sha256"],
                          decision="ACCEPT", actor="owner-1", actor_role="owner").to_dict()["ok"] is True


def test_rf002_helper_cannot_be_selected_for_other_story_by_title(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path)
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    blocked = service._incremental_rf002_files(
        story_id="story-rf-004", title="Consultar productos disponibles", namespace="inventory_sales_local_greenfield",
        acceptance={}, source_rows=code.list_sources().to_dict()["data"]["sources"],
    )
    assert blocked.ok is False
    assert blocked.findings[0].id == "GSDLC13D05_CAPABILITY_ALREADY_IMPLEMENTED_BLOCK"


def test_selected_story_id_is_not_a_provider_switch(tmp_path: Path) -> None:
    workspace, resolver = _rf003_fixture(tmp_path, story_id="story-audit-91")
    code = CodeWorkbenchApplicationService(ROOT, context_resolver=resolver)
    service = StoryImplementationCandidateApplicationService(ROOT, context_resolver=resolver, code_workbench=code)
    result = service.propose(actor="owner-1", actor_role="owner").to_dict()
    assert result["ok"] is True, result
    assert result["data"]["proposal"]["story_id"] == "story-audit-91"
    assert result["data"]["proposal"]["provider"]["capability_id"] == "product.update"
    assert all(x["operation"] in ("CREATE", "EDIT") for x in result["data"]["proposal"]["files"])
