from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.approval import ApprovalRequest
from devpilot_core.approval.service import ApprovalService
from devpilot_core.cli_models import ExitCode
from devpilot_core.identity import IdentityRegistry, RbacCheckInput
from devpilot_core.policy import PolicyEngine, PolicyRequest
from devpilot_core.schemas import SchemaValidator
from devpilot_core.store import LocalStore
from devpilot_core.evals import EvalRunner

ROOT = Path(__file__).resolve().parents[1]


def test_identity_current_roles_and_schema_validate() -> None:
    schema = SchemaValidator(ROOT).validate(schema="docs/schemas/identity_registry.schema.json", instance=".devpilot/identity/identity_registry.json")
    assert schema.ok is True

    current = IdentityRegistry(ROOT).current()
    roles = IdentityRegistry(ROOT).roles()

    assert current.ok is True
    assert current.data["summary"]["current_actor_id"] == "local-owner"
    assert "owner" in current.data["summary"]["current_roles"]
    assert roles.ok is True
    assert roles.data["summary"]["required_roles_present"] is True
    assert {role["role_id"] for role in roles.data["roles"]} >= {"owner", "architect", "developer", "reviewer", "operator", "agent-supervisor"}


def test_identity_cli_current_roles_and_check_json(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["identity", "current", "--json"])
    current = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert current["command"] == "identity current"
    assert current["data"]["summary"]["remote_auth_used"] is False if "remote_auth_used" in current["data"]["summary"] else True
    assert current["data"]["summary"]["auth_remote_enabled"] is False

    exit_code = cli.main(["identity", "roles", "--json"])
    roles = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert roles["data"]["summary"]["roles_total"] >= 6

    exit_code = cli.main(["identity", "check", "--actor", "local-owner", "--action", "execute", "--tool", "tests.run", "--subject", "pytest", "--json"])
    check = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert check["ok"] is True
    assert check["data"]["summary"]["permission"] == "tool.execute.approve"


def test_rbac_blocks_unknown_actor_for_sensitive_action() -> None:
    result = IdentityRegistry(ROOT).check(RbacCheckInput(actor_id="unknown", action="execute", tool_id="tests.run", subject="pytest", require_sensitive=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RBAC_ACTOR_UNKNOWN" for finding in result.findings)


def test_policy_engine_includes_rbac_for_sensitive_approved_request() -> None:
    result = PolicyEngine(ROOT).evaluate(
        PolicyRequest(action="execute", path=".", tool_id="tests.run", subject="pytest", actor="local-owner")
    )

    assert result.ok is False
    decision_ids = {decision["rule_id"] for decision in result.data["decisions"]}
    assert "RBAC_PERMISSION_ALLOWED" in decision_ids
    assert "APPROVAL_REQUIRED_MISSING" in decision_ids


def test_approval_decision_requires_rbac_actor(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    registry_dir = tmp_path / ".devpilot" / "identity"
    registry_dir.mkdir(parents=True)
    source_registry = json.loads((ROOT / ".devpilot/identity/identity_registry.json").read_text(encoding="utf-8"))
    source_registry["actors"] = [
        {"actor_id": "developer-only", "display_name": "Developer Only", "roles": ["developer"], "status": "active", "workspace_scope": ["devpilot-local"], "credentials_stored": False, "remote_auth_enabled": False, "metadata": {}}
    ]
    source_registry["active_actor_id"] = "developer-only"
    (registry_dir / "identity_registry.json").write_text(json.dumps(source_registry, indent=2), encoding="utf-8")
    schema_dir = tmp_path / "docs" / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "identity_registry.schema.json").write_text((ROOT / "docs/schemas/identity_registry.schema.json").read_text(encoding="utf-8"), encoding="utf-8")

    record = ApprovalRequest(
        approval_id="APPROVAL-RBAC-BLOCK",
        subject="pytest",
        tool_id="tests.run",
        action="execute",
        actor="developer-only",
        reason="Request tests.",
        scope={"tool_id": "tests.run", "action": "execute", "subject": "pytest"},
        expires_at="2999-01-01T00:00:00Z",
    ).to_record(approval_id="APPROVAL-RBAC-BLOCK")
    LocalStore(tmp_path).create_approval(record.to_dict())

    decision = ApprovalService(tmp_path).approve("APPROVAL-RBAC-BLOCK", actor="developer-only", reason="No supervisor")

    assert decision.ok is False
    assert decision.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RBAC_PERMISSION_DENIED" for finding in decision.findings)
    assert IdentityRegistry(tmp_path).check(RbacCheckInput(actor_id="developer-only", action="approval.approve", permission="approval.decide.critical", require_sensitive=True)).ok is False


def test_identity_rbac_eval_suite_passes() -> None:
    result = EvalRunner(ROOT).run(suite="identity-rbac")

    assert result.ok is True
    assert result.data["summary"]["suite_id"] == "identity-rbac"
    assert result.data["summary"]["safety_score"] >= 90.0
    assert result.data["summary"]["false_negatives"] == 0
