from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.observability import ObservabilityCleanupPlanner, ObservabilityCleanupPlanOptions
from devpilot_core.schemas import SchemaRegistry, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_observability_cleanup_plan_schema_is_registered() -> None:
    catalog = read_json("docs/schemas/schema_catalog.json")
    entries = {item["schema_id"]: item for item in catalog["schemas"]}

    assert "SCHEMA-DEVPL-OBSERVABILITY-CLEANUP-PLAN-V1" in entries
    entry = entries["SCHEMA-DEVPL-OBSERVABILITY-CLEANUP-PLAN-V1"]
    assert entry["path"] == "docs/schemas/observability_cleanup_plan.schema.json"
    assert entry["contract"] == "ObservabilityCleanupPlan"
    assert entry["sprint"] == "POST-H-010-C"
    assert entry["dry_run_default"] is True
    assert (ROOT / entry["path"]).exists()

    registry_result = SchemaRegistry(ROOT).list()
    assert registry_result.ok, registry_result.to_dict()
    assert "SCHEMA-DEVPL-OBSERVABILITY-CLEANUP-PLAN-V1" in {item["schema_id"] for item in registry_result.data["schemas"]}


def test_observability_cleanup_plan_is_dry_run_and_policy_aware() -> None:
    result = ObservabilityCleanupPlanner(ROOT).run()
    summary = result.data["summary"]
    plan = result.data["cleanup_plan"]

    assert result.ok, result.to_dict()
    assert result.command == "observability cleanup-plan"
    assert summary["created_by"] == "POST-H-010-C"
    assert summary["dry_run"] is True
    assert summary["execute_requested"] is False
    assert summary["execute_allowed"] is False
    assert summary["mutations_performed"] is False
    assert summary["destructive_cleanup_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["raw_payloads_read"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["actions_by_kind"] == {
        "rotate": summary["would_rotate"],
        "delete": summary["would_delete"],
        "archive": summary["would_archive"],
        "redact": summary["would_redact"],
        "export": summary["would_export"],
    }
    assert plan["execution_mode"] == "dry-run"
    assert plan["safety"]["policy_engine_required_for_mutations"] is True
    assert plan["safety"]["cleanup_execution_enabled"] is False
    assert ".git/" in plan["safety"]["forbidden_source_prefixes"]
    assert "src/" in plan["safety"]["forbidden_source_prefixes"]

    destructive_actions = [item for item in plan["actions"] if item["action_kind"] in {"rotate", "delete", "archive"}]
    for action in destructive_actions:
        assert action["requires_execute"] is True
        assert action["requires_policy_engine"] is True
        assert action["requires_approval"] is True
        assert action["required_approval_id"]
        assert action["mutations_performed"] is False
        assert action["policy_evaluation"] is not None


def test_observability_cleanup_plan_write_report_validates_against_schema() -> None:
    result = ObservabilityCleanupPlanner(ROOT, ObservabilityCleanupPlanOptions(write_report=True)).run()
    reports = result.data["reports"]

    assert result.ok, result.to_dict()
    assert reports["json"] == "outputs/reports/observability_cleanup_plan.json"
    assert reports["markdown"] == "outputs/reports/observability_cleanup_plan.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    validation = SchemaValidator(ROOT).validate(
        schema="ObservabilityCleanupPlan",
        instance=reports["json"],
    )
    assert validation.ok, validation.to_dict()


def test_observability_cleanup_plan_cli_json_and_write_report(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["observability", "cleanup-plan", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "observability cleanup-plan"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["created_by"] == "POST-H-010-C"
    assert payload["data"]["summary"]["dry_run"] is True
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/observability_cleanup_plan.json"


def test_observability_cleanup_plan_blocks_execute_probe(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["observability", "cleanup-plan", "--json", "--execute"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["data"]["summary"]["execute_requested"] is True
    assert payload["data"]["summary"]["execute_allowed"] is False
    assert payload["data"]["summary"]["mutations_performed"] is False
    assert any(item["id"] == "OBSERVABILITY_CLEANUP_PLAN_EXECUTE_NOT_SUPPORTED" for item in payload["findings"])


def test_observability_cleanup_plan_blocks_path_escape(tmp_path: Path) -> None:
    policy = read_json(".devpilot/observability/retention_policy.json")
    policy["targets"][0]["path"] = "../outside/events.jsonl"
    policy["targets"][0]["required"] = True
    policy_root = tmp_path / "workspace"
    policy_path = policy_root / ".devpilot" / "observability" / "retention_policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    result = ObservabilityCleanupPlanner(policy_root).run()

    assert not result.ok
    assert result.exit_code == 2
    assert any(finding.id == "OBSERVABILITY_CLEANUP_PATH_ESCAPE" for finding in result.findings)
