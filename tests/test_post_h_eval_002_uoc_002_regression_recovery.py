from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

def data(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_current_baseline_and_candidate_are_not_conflated() -> None:
    state = data(".devpilot/project_state.json")
    criteria = data(".devpilot/release/local_release_candidate_criteria.json")
    assert state["uoc_002_candidate_repo"] == "repo_DevPilot_Local_330_CANDIDATE_POST_H_EVAL_002_UOC_002.zip"
    if state["uoc_002_closed"]:
        assert state["uoc_002_authoritative_baseline"] == "repo_DevPilot_Local_330_POST_H_EVAL_002_UOC_002.zip"
        lifecycle = [
            ("uoc_005_closed", "repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip"),
            ("uoc_004_closed", "repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip"),
            ("uoc_003_closed", "repo_DevPilot_Local_331_POST_H_EVAL_002_UOC_003.zip"),
        ]
        expected_current = next((repo for flag, repo in lifecycle if state.get(flag)), "repo_DevPilot_Local_330_POST_H_EVAL_002_UOC_002.zip")
        assert state["current_repo"] == expected_current
    else:
        assert state["current_repo"] == "repo_DevPilot_Local_329_POST_H_EVAL_002_UOC_001.zip"
    assert criteria["expected_current_repo"] == state["current_repo"]
    item = next(x for x in criteria["evidence"] if x["evidence_id"] == "project-state-current-repo")
    assert item["expected_fields"]["current_repo"] == state["current_repo"]

def test_uoc_registry_lifecycle_schemas_accept_read_only_evolution() -> None:
    pairs = [
        ("docs/schemas/ui_capability_registry.schema.json", ".devpilot/interfaces/ui_capability_registry.json"),
        ("docs/schemas/ui_operational_console_flags.schema.json", ".devpilot/interfaces/ui_operational_console_flags.json"),
    ]
    for schema_path, instance_path in pairs:
        schema, instance = data(schema_path), data(instance_path)
        Draft202012Validator.check_schema(schema)
        assert list(Draft202012Validator(schema).iter_errors(instance)) == []

def test_route_registry_totals_match_live_contracts() -> None:
    api = data(".devpilot/interfaces/api_route_contract_registry.json")
    ui = data(".devpilot/interfaces/ui_route_contract_registry.json")
    capabilities = data(".devpilot/interfaces/ui_capability_registry.json")
    assert api["summary"]["routes_total"] == len(api["routes"])
    assert len(api["routes"]) >= 46
    assert ui["summary"]["routes_total"] == len(ui["routes"]) == 6
    assert capabilities["summary"]["api_routes_total"] == len(api["routes"])
    assert capabilities["summary"]["ui_routes_total"] == len(ui["routes"])

def test_visual_product_lineage_and_runtime_artifact_policy() -> None:
    package = data("ui/web/package.json")
    assert "-post-h-" in package["version"]
    assert package["devpilot"]["sprint"] == "FUNC-SPRINT-73"
    assert package["devpilot"]["postHEvolution"] is True
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in gitignore or "ui/web/node_modules/" in gitignore
    assert "dist/" in gitignore or "ui/web/dist/" in gitignore

def test_regression_recovery_manifest_is_non_mutating() -> None:
    manifest = data("docs/post_h_eval_002_uoc_002_regression_recovery_manifest.json")
    assert manifest["observed_regression"] == {"passed": 1987, "failed": 58, "errors": 0, "skipped": 0}
    assert manifest["full_regression_evidence_reused"] is True
    if manifest["status"] == "closed/PASS":
        assert manifest["selective_verification_required"] is False
        assert manifest["selective_verification_passed"] is True
    else:
        assert manifest["selective_verification_required"] is True
    assert manifest["safety"]["source_write_capability_enabled"] is False


def test_rag_cli_contract_isolated_from_repository_runtime_index() -> None:
    source = (ROOT / "tests/test_rag_local.py").read_text(encoding="utf-8")
    function = source.split("def test_rag_cli_index_and_query_json", 1)[1].split("def test_rag_runtime_index_is_excluded", 1)[0]
    assert "tmp_path: Path" in function
    assert "Path.cwd()" not in function
    assert 'root = tmp_path / "rag-cli-workspace"' in function
    assert 'env = os.environ.copy()' in function
    assert 'env["PYTHONPATH"] = str(ROOT / "src")' in function


def test_recovery_manifest_declares_runtime_index_reconciliation() -> None:
    manifest = data("docs/post_h_eval_002_uoc_002_regression_recovery_manifest.json")
    assert manifest["version"] == "1.0.5"
    mutation = manifest["known_runtime_mutation"]
    assert mutation["path"] == ".devpilot/rag/docs_index.json"
    assert mutation["producer_test"] == "tests/test_rag_local.py::test_rag_cli_index_and_query_json"
    assert mutation["reconciliation"] == "classify-HEAD-equivalent-or-canonical-regeneration-then-git-native-restore-and-verify-clean"
    assert mutation["carry_into_commit"] is False


def test_recovery_manifest_declares_portable_eol_preflight() -> None:
    manifest = data("docs/post_h_eval_002_uoc_002_regression_recovery_manifest.json")
    assert manifest["version"] == "1.0.5"
    assert manifest["preflight_eol_policy"] == "UTF8-LF-CRLF-only"
    assert manifest["source_preimages_bundled"] == 42

def test_documentation_registry_uses_lifecycle_aware_stable_identity() -> None:
    registry = data(".devpilot/docs_governance/source_registry.json")
    manifest = data("docs/post_h_eval_002_uoc_002_regression_recovery_manifest.json")
    state = data(".devpilot/project_state.json")
    assert manifest["documentation_registry_identity"] == "UOC-002-REGRESSION-RECOVERY"
    lifecycle = [
        (state.get("uoc_005_status"), {"UOC-005", "UOC-005-CLOSURE"}),
        (state.get("uoc_004_status"), {"UOC-004", "UOC-004-CLOSURE"}),
        (state.get("uoc_003_status"), {"UOC-003", "UOC-003-CLOSURE"}),
    ]
    expected = next((allowed for marker, allowed in lifecycle if marker), None)
    if expected is not None:
        assert registry["last_registered_sprint"] in expected
    elif state["uoc_002_closed"]:
        assert registry["last_registered_sprint"] == "UOC-002-CLOSURE"
    else:
        assert registry["last_registered_sprint"] == manifest["documentation_registry_identity"]
    assert manifest["selective_runner_contract"] == "partial-report-on-block-resume-from-first-failed-case-and-rag-git-clean-check-per-case"
    assert manifest["rag_git_clean_contract"] == "required-before-resume-and-after-every-case"
    assert manifest["operator_transaction_contract"] == "backup-all-destinations-and-rollback-on-write-failure"

