from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import jsonschema

from devpilot_core.guided_sdlc.executable_standard_registry import (
    ExecutableStandardRegistryService,
    ExecutableStandardRegistryValidator,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".devpilot/gsdlc/executable_standard_registry.json"
SCHEMA = ROOT / "docs/schemas/executable_standard_registry.schema.json"


def payload() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def make_root(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    for rel in [".devpilot/gsdlc", ".devpilot/readiness", "docs/standards", "docs/schemas"]:
        shutil.copytree(ROOT / rel, target / rel)
    return target


def test_05_a_schema_and_positive_registry_validation_pass():
    data = payload()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert report.ok, report.to_dict()
    assert report.metrics["mandatory_pre_code_mapping_percent"] == 100.0
    assert report.metrics["mandatory_pre_code_total"] == 26
    assert report.metrics["orphan_critical_steps"] == 0
    assert report.metrics["transition_cycle_nodes_total"] == 0
    assert report.metrics["source_drift_total"] == 0
    assert report.metrics["registry_authoritative"] is True


def test_05_a_mapping_is_derived_from_live_critical_readiness_requirements():
    data = payload()
    readiness = json.loads((ROOT / ".devpilot/readiness/readiness_requirements.json").read_text(encoding="utf-8"))
    expected = {"artifact:" + row["artifact"] for row in readiness["requirements"] if row["critical"]}
    actual = {row["artifact_id"] for row in data["requirements"] if row["mandatory"] and row["enabled"]}
    assert actual == expected
    coverage = ExecutableStandardRegistryService(ROOT).source_mapping_coverage()
    assert coverage["status"] == "PASS"
    assert coverage["mandatory_pre_code_mapping_percent"] == 100.0
    assert coverage["new_rule_without_source_total"] == 0


def test_05_a_every_source_link_path_heading_and_hash_is_verified():
    report = ExecutableStandardRegistryService(ROOT).source_drift_report()
    assert report["status"] == "PASS", report
    assert report["source_drift_total"] == 0
    assert report["sources_checked_total"] >= 15
    assert all(row["status"] == "PASS" for row in report["sources"])


def test_05_a_duplicate_id_blocks():
    data = payload()
    data["steps"].append(copy.deepcopy(data["steps"][0]))
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert not report.ok
    assert "STEP_ID_DUPLICATE" in {f.finding_id for f in report.findings}


def test_05_a_orphan_mandatory_step_blocks():
    data = payload()
    step_id = data["steps"][0]["step_id"]
    for phase in data["phases"]:
        phase["step_ids"] = [x for x in phase["step_ids"] if x != step_id]
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert not report.ok
    assert "ORPHAN_OR_MULTIPARENT_STEP" in {f.finding_id for f in report.findings}


def test_05_a_transition_cycle_blocks_but_reference_edges_are_non_transitional():
    data = payload()
    first, last = data["steps"][0], data["steps"][-1]
    first["prerequisites"] = [{"edge_kind": "transition", "step_id": last["step_id"]}]
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert not report.ok
    assert "TRANSITION_CYCLE" in {f.finding_id for f in report.findings}

    data = payload()
    data["steps"][0]["prerequisites"] = [{"edge_kind": "reference", "step_id": data["steps"][-1]["step_id"]}]
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert report.ok, report.to_dict()


def test_05_a_source_hash_drift_blocks(tmp_path: Path):
    root = make_root(tmp_path)
    source = root / "docs/standards/mipsoftware/03_producto_negocio_stakeholders.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nexternal source drift\n", encoding="utf-8")
    report = ExecutableStandardRegistryValidator(root).validate()
    assert not report.ok
    assert "SOURCE_HASH_DRIFT" in {f.finding_id for f in report.findings}


def test_05_a_critical_control_cannot_be_disabled_without_governed_decision():
    data = payload()
    data["requirements"][0]["enabled"] = False
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert not report.ok
    assert "CRITICAL_CONTROL_DISABLED_WITHOUT_DECISION" in {f.finding_id for f in report.findings}


def test_05_a_migration_semantics_and_owner_authority_are_fail_closed():
    data = payload()
    assert data["migration"]["strategy"] == "semantic-versioning"
    assert data["migration"]["unknown_version_effect"] == "BLOCK"
    assert data["migration"]["breaking_change_requires_owner_approval"] is True
    assert data["migration"]["source_hash_change_requires_revalidation"] is True
    snapshot = json.loads((ROOT / ".devpilot/gsdlc/executable_standard_registry_gsdlc05a_at_windows_close.json").read_text(encoding="utf-8"))
    assert snapshot["status"] == "draft/pending-owner-approval"
    assert snapshot["registry_authoritative"] is False
    assert snapshot["owner_approval_required_for_promotion"] is True

    # Current-active successor is promoted only by the final owner adjudication.
    assert data["status"] == "approved"
    assert data["registry_authoritative"] is True
    assert data["owner_approval_required_for_promotion"] is True

    invalid = copy.deepcopy(snapshot)
    invalid["registry_authoritative"] = True
    report = ExecutableStandardRegistryValidator(ROOT).validate(invalid)
    assert not report.ok
    assert "REGISTRY_AUTHORITY_PREMATURE" in {f.finding_id for f in report.findings}


def test_05_a_generic_workflow_catalog_coexists_and_remains_unchanged():
    data = payload()
    ref = data["integration_refs"][0]
    workflow = ROOT / ref["path"]
    current = json.loads(workflow.read_text(encoding="utf-8"))
    assert "artifact-specific executable workflow is deferred to DEVPL-GSDLC-05" in current["scope"]
    report = ExecutableStandardRegistryValidator(ROOT).validate(data)
    assert report.ok, report.to_dict()


def test_05_a_activation_rebind_is_materialized_without_consuming_full():
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert state["gsdlc_04_status"] == "closed/PASS"
    assert state["gsdlc_04_e_status"] == "closed/PASS"
    assert state["gsdlc_04_e_owner_adjudication_pending"] is False
    assert state["gsdlc_04_e_full_regression_runs"] == 1
    assert state["gsdlc_04_e_full_regression_rerun_performed"] is False
    # Current-active successor state after owner adjudication must preserve 05-A closure facts.
    assert state["gsdlc_05_status"] == "active/05-b"
    assert state["gsdlc_current_micro_sprint"] == "DEVPL-GSDLC-05-B"
    assert state["gsdlc_05_a_status"] == "closed/PASS"
    assert state["gsdlc_05_a_owner_adjudication_pending"] is False
    assert state["gsdlc_05_a_successor_repo_at_close"].startswith("repo_DevPilot_Local_370_")
    assert state["gsdlc_05_a_full_regression_runs"] == 0
    for name in [
        "DEVPL_GSDLC_04_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md",
        "DEVPL_GSDLC_04_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md",
        "DEVPL_GSDLC_04_FINAL_OWNER_CLOSURE_CURRENT.json",
        "DEVPL-GSDLC-05_executable_mipsoftware_miasi_and_step_action_advisor_v1_2_0_APPROVED_REBOUND.md",
        "01_PROMPT_DEVPL_GSDLC_05_A_v1_0_0.md",
    ]:
        assert (ROOT / name).is_file(), name
