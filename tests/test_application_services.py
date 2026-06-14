from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.application import ApplicationRequest, ApplicationResponse, ApplicationService
from devpilot_core.cli_models import ExitCode


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "docs"


def test_application_service_validates_frontmatter_without_cli() -> None:
    service = ApplicationService(ROOT)

    result = service.validate_frontmatter(FIXTURES / "valid_frontmatter.md")
    response = service.as_application_response(result, operation="validators.validate_frontmatter")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert response.operation == "validators.validate_frontmatter"
    assert response.to_dict()["contract"] == "DevPilotApplicationResponse"
    assert json.dumps(response.to_dict(), ensure_ascii=False)


def test_application_service_validates_artifact_without_cli() -> None:
    service = ApplicationService(ROOT)

    result = service.validate_artifact("docs/01_requirements/requirements_specification.md")

    assert result.ok is True
    assert result.data["profile"]["id"] == "requirements-specification"


def test_application_service_blocks_paths_outside_workspace(tmp_path: Path) -> None:
    service = ApplicationService(tmp_path, enforce_workspace_paths=True)
    outside = tmp_path.parent / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")

    try:
        service.validate_frontmatter(outside)
    except ValueError as exc:
        assert "inside the workspace" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected ApplicationService to reject outside path")


def test_application_contract_is_serializable_and_declares_no_ui() -> None:
    result = ApplicationService(ROOT).application_contract()
    payload = result.to_dict()

    assert result.ok is True
    assert payload["data"]["summary"]["ui_implemented"] is False
    assert payload["data"]["summary"]["visual_strategy"] == "web_ui_first"
    assert payload["data"]["summary"]["api_local_planned"] is True
    assert payload["data"]["summary"]["web_ui_local_planned"] is True
    assert payload["data"]["summary"]["desktop_deferred"] is True
    assert payload["data"]["summary"]["desktop_ready_for_shell"] is False
    assert payload["data"]["summary"]["web_ready_for_shell"] is True
    operations = {capability["operation"] for capability in payload["data"]["capabilities"]}
    assert "validators.validate_frontmatter" in operations
    assert "validators.validate_artifact" in operations
    assert json.dumps(payload, ensure_ascii=False)


def test_application_request_dto_is_serializable() -> None:
    request = ApplicationRequest(
        operation="validators.validate_frontmatter",
        payload={"path": "docs/00_product/product_vision.md", "strict": True},
        client="web-ui-local-future",
    )

    payload = request.to_dict()

    assert payload["dry_run"] is True
    assert payload["client"] == "web-ui-local-future"
    assert json.dumps(payload, ensure_ascii=False)


def test_app_contract_cli_json_and_report_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    # Use the real repo as the source contract but execute from ROOT because the
    # command relies on WorkspaceManager discovery and repo docs.
    monkeypatch.chdir(ROOT)

    exit_code = cli.main(["app", "contract", "--json", "--write-report"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["command"] == "app contract"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["ui_implemented"] is False
    assert payload["data"]["reports"]["json"] == "outputs/reports/app_contract.json"
    assert (ROOT / "outputs" / "reports" / "app_contract.json").is_file()
