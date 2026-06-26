from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.observability import ObservabilityRetentionHygieneGate, ObservabilityRetentionHygieneOptions
from devpilot_core.quality import QualityGate, QualityGateOptions
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _make_clean_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".devpilot" / "observability").mkdir(parents=True)
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    shutil.copy(ROOT / ".devpilot" / "observability" / "retention_policy.json", root / ".devpilot" / "observability" / "retention_policy.json")
    (root / "README.md").write_text("# synthetic workspace\n", encoding="utf-8")
    (root / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "docs" / "note.md").write_text("# Note\n", encoding="utf-8")
    (root / "tests" / "test_note.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return root


def test_observability_retention_hygiene_schema_is_registered() -> None:
    result = SchemaRegistry(ROOT).list()
    ids = {item["schema_id"] for item in result.data["schemas"]}

    assert result.ok is True
    assert "SCHEMA-DEVPL-OBSERVABILITY-RETENTION-HYGIENE-V1" in ids


def test_observability_retention_hygiene_gate_passes_in_clean_workspace_without_runtime_outputs(tmp_path: Path) -> None:
    root = _make_clean_workspace(tmp_path)

    result = ObservabilityRetentionHygieneGate(root, ObservabilityRetentionHygieneOptions(include_git_archive_check=False)).run()

    assert result.ok is True, result.to_dict()
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-010-E"
    assert summary["quality_gate_ready"] is True
    assert summary["policy_validation_passed"] is True
    assert summary["inventory_validation_passed"] is True
    assert summary["clean_zip_hygiene_passed"] is True
    assert summary["inventory_missing_required_total"] >= 1
    assert summary["blocking_findings_total"] == 0
    assert summary["raw_payloads_read"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False


def test_observability_retention_hygiene_write_report_validates_against_schema(tmp_path: Path) -> None:
    root = _make_clean_workspace(tmp_path)

    result = ObservabilityRetentionHygieneGate(root, ObservabilityRetentionHygieneOptions(write_report=True, include_git_archive_check=False)).run()

    assert result.ok is True, result.to_dict()
    report_path = root / result.data["reports"]["json"]
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    validation = SchemaValidator(ROOT).validate_payload(
        schema="ObservabilityRetentionHygiene",
        payload=payload,
        instance_label="observability_retention_hygiene.synthetic.json",
    )
    assert validation.ok, validation.to_dict()


def test_observability_retention_hygiene_blocks_unsafe_policy_target(tmp_path: Path) -> None:
    root = _make_clean_workspace(tmp_path)
    policy_path = root / ".devpilot" / "observability" / "retention_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["targets"][0]["clean_zip_excluded"] = False
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    result = ObservabilityRetentionHygieneGate(root, ObservabilityRetentionHygieneOptions(include_git_archive_check=False)).run()

    assert result.ok is False
    assert result.exit_code == 2
    assert any(finding.id in {"TARGET_POLICY_SAFE_EVENTS_JSONL", "OBSERVABILITY_POLICY_CHECK"} for finding in result.findings)


def test_quality_gate_hardening_contains_observability_retention_subgate() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening", include_pytest=False)).run()
    subgates = {item["id"]: item for item in result.data["subgates"]}

    assert result.ok is True, result.to_dict()
    assert "observability-retention" in subgates
    assert subgates["observability-retention"]["ok"] is True
    assert subgates["observability-retention"]["summary"]["quality_gate_ready"] is True
    assert subgates["observability-retention"]["summary"]["network_used"] is False
    assert subgates["observability-retention"]["summary"]["external_api_used"] is False
