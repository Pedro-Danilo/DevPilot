from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.agents import INSUFFICIENT_EVIDENCE, RagAgentContextOptions, RagAwareAgentContextBuilder
from devpilot_core.application.services import ApplicationService
from devpilot_core.schemas.validator import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_post_h_032_d_context_pack_passes_with_citations_for_selected_agents() -> None:
    result = RagAwareAgentContextBuilder(ROOT).build()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-032-D"
    assert summary["decision"] == "PASS"
    assert summary["agents_total"] == 5
    assert summary["target_agents_total"] == 5
    assert summary["grounded_agents_total"] >= 5
    assert summary["sources_total"] >= 5
    assert summary["citations_total"] >= 5
    assert summary["all_grounded_suggestions_have_sources"] is True
    assert summary["negative_cases_passed"] is True
    assert summary["prohibited_claims_justified_total"] == 0
    assert summary["rag_reads_allowlisted_sources_only"] is True
    assert summary["schema_valid"] is True
    assert summary["llm_used"] is False
    assert summary["external_api_used"] is False
    assert summary["memory_used"] is False
    assert summary["tools_executed"] is False
    assert summary["source_mutations_performed"] is False

    pack = result.data["context_pack"]
    expected_agents = {"requirements.agent", "architecture.agent", "security.agent", "testplanner.agent", "release.assistant"}
    assert {agent["agent_id"] for agent in pack["agents"]} == expected_agents
    for agent in pack["agents"]:
        assert agent["mode"] == "rag-aware"
        assert agent["grounded"] is True
        assert agent["source_ids"]
        assert agent["citations"]
        suggestion = agent["suggestions"][0]
        assert suggestion["insufficient_evidence"] is False
        assert suggestion["source_ids"] == agent["source_ids"]
        assert suggestion["citations"] == agent["citations"]
        assert "#L" in suggestion["citations"][0]


def test_post_h_032_d_prohibited_or_unsupported_claim_returns_insufficient_evidence() -> None:
    result = RagAwareAgentContextBuilder(
        ROOT,
        RagAgentContextOptions(
            agent_id="security.agent",
            query="DevPilot is enterprise-ready SaaS-ready without evidence",
        ),
    ).build()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["agents_total"] == 1
    assert summary["grounded_agents_total"] == 0
    assert summary["insufficient_evidence_agents_total"] == 1
    assert summary["sources_total"] == 0
    assert summary["citations_total"] == 0
    agent = result.data["context_pack"]["agents"][0]
    assert agent["status"] == "insufficient-evidence"
    assert agent["grounded"] is False
    assert agent["insufficient_evidence"] is True
    assert agent["source_ids"] == []
    assert agent["citations"] == []
    assert agent["suggestions"][0]["body"] == INSUFFICIENT_EVIDENCE
    assert agent["suggestions"][0]["prohibited_claim_blocked"] is True


def test_post_h_032_d_schema_catalog_policy_and_bindings_are_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    schemas = {item["schema_id"]: item for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-RAG-AGENT-CONTEXT-PACK-V1" in schemas
    assert schemas["SCHEMA-DEVPL-RAG-AGENT-CONTEXT-PACK-V1"]["contract"] == "RagAgentContextPack"

    bindings = read_json(".devpilot/agents/rag_agent_bindings.json")
    assert bindings["created_by"] == "POST-H-032-D"
    assert bindings["defaults"]["require_citations"] is True
    assert bindings["defaults"]["insufficient_evidence_response"] == INSUFFICIENT_EVIDENCE
    assert len(bindings["negative_cases"]) >= 3
    assert {agent["agent_id"] for agent in bindings["agents"]} >= {
        "requirements.agent",
        "architecture.agent",
        "security.agent",
        "testplanner.agent",
        "release.assistant",
    }

    registry = read_json(".devpilot/docs_governance/source_registry.json")
    registered = {item["path"] for item in registry["documents"]}
    for expected in [
        ".devpilot/agents/rag_agent_bindings.json",
        "docs/schemas/rag_agent_context_pack.schema.json",
        "src/devpilot_core/agents/rag_context.py",
        "tests/test_post_h_032_rag_aware_agents.py",
        "docs/audits/post_h_032_d_rag_aware_agents_report.md",
        "docs/post_h_032_d_manifest.json",
    ]:
        assert expected in registered


def test_post_h_032_d_cli_application_service_and_schema_validation() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "rag-context", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "agent rag-context"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["decision"] == "PASS"
    reports = payload["data"]["reports"]
    assert reports["json"] == "outputs/reports/rag_agent_context_pack.json"
    assert reports["markdown"] == "outputs/reports/rag_agent_context_pack.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="RagAgentContextPack",
        instance=reports["json"],
    )
    assert schema_result.ok is True, schema_result.to_dict()

    service_result = ApplicationService(ROOT).rag_agent_context(agent_id="requirements.agent")
    assert service_result.ok is True
    assert service_result.data["summary"]["agents_total"] == 1
    assert service_result.data["context_pack"]["agents"][0]["source_ids"]


def test_post_h_032_d_tcr_v1_v2_and_project_state_are_synchronized() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    assert any(contract["contract_id"] == "post-h-032-rag-aware-agents" for contract in tcr["contracts"])
    contract_v2 = next(contract for contract in tcr_v2["contracts"] if contract["contract_id"] == "post-h-032-rag-aware-agents")
    assert contract_v2["domain"] == "knowledge.rag"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False
    assert "SCHEMA-DEVPL-RAG-AGENT-CONTEXT-PACK-V1" in contract_v2["schema_ids"]

    state = read_json(".devpilot/project_state.json")
    assert state["current_micro_sprint"] in {"POST-H-032-D", "POST-H-032-E"}
    assert state["next_micro_sprint"] in {"POST-H-032-E", "POST-H-032-F"}
    assert state["current_repo"] in {"repo_DevPilot_Local_297_POST_H_032_D.zip", "repo_DevPilot_Local_298_POST_H_032_E.zip"}
    assert state["post_h_032_status"] in {"active/rag-aware-agents-implemented-initial", "active/agent-memory-model-implemented-initial"}
    assert state["post_h_032_current_micro_sprint"] in {"POST-H-032-D", "POST-H-032-E"}
    assert state["post_h_032_next_micro_sprint"] in {"POST-H-032-E", "POST-H-032-F"}
    assert state["post_h_032_d_rag_agent_context_schema_registered"] is True
    assert state["post_h_032_d_rag_agent_bindings_path"] == ".devpilot/agents/rag_agent_bindings.json"
    assert state["post_h_032_d_rag_agent_context_cli_command"] == "python -m devpilot_core agent rag-context --json"
    assert state["post_h_032_d_target_agents_total"] == 5
    assert state["post_h_032_d_all_grounded_suggestions_have_sources"] is True
    assert state["post_h_032_d_insufficient_evidence_behavior_enabled"] is True
    assert state["post_h_032_d_prohibited_claims_justified_total"] == 0
    assert state["post_h_032_d_llm_used"] is False
    assert state["post_h_032_d_external_api_used"] is False
    assert state["post_h_032_d_memory_used"] is False
    assert state["post_h_032_d_tools_executed"] is False
