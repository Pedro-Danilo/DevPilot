from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from devpilot_core.agents import AgentMemoryModelManager, AgentMemoryModelOptions
from devpilot_core.application import ApplicationService
from devpilot_core.schemas.validator import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
TEST_MEMORY_DIR = Path("outputs/test_post_h_032_agent_memory_model/memory")
TEST_REPORT_JSON = Path("outputs/test_post_h_032_agent_memory_model/agent_memory_model_report.json")
TEST_REPORT_MD = Path("outputs/test_post_h_032_agent_memory_model/agent_memory_model_report.md")


def _clean() -> None:
    shutil.rmtree(ROOT / "outputs/test_post_h_032_agent_memory_model", ignore_errors=True)


def _manager(*, execute: bool = False, write_report: bool = False) -> AgentMemoryModelManager:
    return AgentMemoryModelManager(
        ROOT,
        AgentMemoryModelOptions(
            memory_dir=TEST_MEMORY_DIR,
            output_json=TEST_REPORT_JSON,
            output_markdown=TEST_REPORT_MD,
            execute=execute,
            dry_run=not execute,
            write_report=write_report,
        ),
    )


def _write_record(name: str, payload: dict) -> Path:
    path = ROOT / TEST_MEMORY_DIR / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _valid_record(**overrides: object) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "record_id": "mem-test-valid",
        "agent_id": "requirements.agent",
        "workspace_id": "local-workspace",
        "memory_type": "session_memory",
        "created_at_utc": now,
        "updated_at_utc": now,
        "content_redacted": {"summary": "Synthetic redacted memory fact.", "tags": ["synthetic", "redacted"]},
        "source_refs": ["docs/backlogs/POST-H-032_advanced_ai_agents_llm_rag_memory_tools.md#POST-H-032-E"],
        "retention": {"retention_days": 14},
    }
    payload.update(overrides)
    return payload


def test_post_h_032_e_default_memory_model_is_disabled_and_passes() -> None:
    _clean()
    result = _manager().inspect()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-032-E"
    assert summary["semantic_memory_enabled"] is False
    assert summary["memory_enabled_by_default"] is False
    assert summary["records_total"] == 0
    assert summary["inspect_available"] is True
    assert summary["cleanup_available"] is True
    assert summary["export_redacted"] is True
    assert summary["memory_counts_as_formal_evidence"] is False
    assert summary["session_memory_separated"] is True
    assert summary["project_memory_separated"] is True
    assert summary["report_evidence_separated"] is True
    assert summary["schema_valid"] is True


def test_post_h_032_e_schema_policy_and_adr_exist_and_validate() -> None:
    assert (ROOT / "docs/adr/ADR-POSTH-032-E-agent-memory-local-opt-in.md").exists()
    assert (ROOT / ".devpilot/agents/agent_memory_policy.json").exists()
    assert (ROOT / "docs/schemas/agent_memory_record.schema.json").exists()

    result = _manager(write_report=True).export()
    assert result.ok is True, result.to_dict()
    report_path = ROOT / result.data["reports"]["json"]
    schema = SchemaValidator(ROOT).validate(schema="AgentMemoryRecord", instance=report_path)
    assert schema.ok is True, schema.to_dict()


def test_post_h_032_e_negative_raw_prompt_and_secret_are_blocked() -> None:
    _clean()
    _write_record(
        "bad_memory",
        _valid_record(
            record_id="mem-test-bad",
            raw_prompt="Please remember this secret sk-test-secret-value-1234567890",
            content_redacted={"summary": "This should be redacted", "token": "sk-test-secret-value-1234567890"},
        ),
    )

    result = _manager().inspect()
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.ok is False
    assert any(finding.id == "AGENT_MEMORY_RAW_PROMPT_OR_OUTPUT_BLOCKED" for finding in result.findings)
    assert any(finding.id == "AGENT_MEMORY_SECRET_PERSISTENCE_BLOCKED" for finding in result.findings)
    assert "sk-test-secret-value-1234567890" not in payload
    assert "[REDACTED]" in payload


def test_post_h_032_e_cleanup_dry_run_and_execute_for_expired_records() -> None:
    _clean()
    old = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    path = _write_record(
        "expired_memory",
        _valid_record(record_id="mem-test-expired", created_at_utc=old, updated_at_utc=old, retention={"retention_days": 1}),
    )

    dry_run = _manager().cleanup()
    assert dry_run.ok is True, dry_run.to_dict()
    assert dry_run.data["summary"]["cleanup_plan_items_total"] == 1
    assert dry_run.data["summary"]["cleanup_deleted_total"] == 0
    assert path.exists()

    executed = _manager(execute=True).cleanup()
    assert executed.ok is True, executed.to_dict()
    assert executed.data["summary"]["cleanup_deleted_total"] == 1
    assert executed.data["report"]["safety"]["source_mutations_performed"] is False
    assert not path.exists()


def test_post_h_032_e_cli_and_application_service_are_synchronized() -> None:
    _clean()
    cli_result = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "memory", "inspect", "--json", "--memory-dir", str(TEST_MEMORY_DIR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={"PYTHONPATH": "src"},
    )
    assert cli_result.returncode == 0, cli_result.stderr or cli_result.stdout
    payload = json.loads(cli_result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["summary"]["semantic_memory_enabled"] is False

    app_result = ApplicationService(ROOT).agent_memory_model(action="inspect", memory_dir=str(TEST_MEMORY_DIR))
    assert app_result.ok is True
    assert app_result.data["summary"] == payload["data"]["summary"]


def test_post_h_032_e_governance_artifacts_registered() -> None:
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    source_registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    tcr_v1 = json.loads((ROOT / ".devpilot/testing/test_contract_registry.json").read_text(encoding="utf-8"))
    tcr_v2 = json.loads((ROOT / ".devpilot/testing/test_contract_registry_v2.json").read_text(encoding="utf-8"))

    assert state["post_h_032_current_micro_sprint"] == "POST-H-032-E"
    assert state["post_h_032_next_micro_sprint"] == "POST-H-032-F"
    assert state["post_h_032_e_agent_memory_schema_registered"] is True
    assert state["post_h_032_e_memory_enabled_by_default"] is False
    assert state["post_h_032_e_raw_prompts_stored"] is False
    assert state["post_h_032_e_raw_outputs_stored"] is False
    assert state["post_h_032_e_secrets_stored"] is False
    assert state["post_h_032_e_memory_counts_as_formal_evidence"] is False

    schema_ids = {item["schema_id"] for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-AGENT-MEMORY-RECORD-V1" in schema_ids
    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "ADR-POSTH-032-E" in doc_ids
    assert "POST-H-032-E-AGENT-MEMORY-POLICY" in doc_ids
    assert "POST-H-032-E-AGENT-MEMORY-MODULE" in doc_ids
    assert "POST-H-032-E-AGENT-MEMORY-REPORT" in doc_ids
    contract_ids = {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-032-agent-memory-model" in contract_ids
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-032-agent-memory-model" in contract_ids_v2
