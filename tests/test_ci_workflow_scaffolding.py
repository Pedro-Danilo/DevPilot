from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "devpilot-ci.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_github_actions_workflow_is_safe_scaffolding() -> None:
    assert WORKFLOW.exists()
    content = _read(WORKFLOW)
    lowered = content.lower()

    assert "permissions:" in content
    assert "contents: read" in content
    assert "actions/checkout@v4" in content
    assert "actions/setup-python@v5" in content
    assert "python -m pytest -q" in content
    assert "quality-gate run --profile ci" in content
    assert "npm --prefix ui/web test" in content

    forbidden_markers = [
        "secrets.",
        "twine upload",
        "npm publish",
        "git push",
        "docker/login-action",
        "pypa/gh-action-pypi-publish",
        "release-action",
        "create-release",
        "upload-release",
    ]
    for marker in forbidden_markers:
        assert marker not in lowered

    assert "DEVPILOT_EXTERNAL_APIS_ENABLED: \"0\"" in content
    assert "DEVPILOT_PROVIDER_MODE: \"mock\"" in content


def test_quality_gate_ci_profile_static_workflow_validation_passes() -> None:
    from devpilot_core.quality import QualityGate, QualityGateOptions

    result = QualityGate(ROOT, options=QualityGateOptions(profile="ci")).run()

    assert result.ok is True
    subgates = {item["id"]: item for item in result.data["subgates"]}
    assert subgates["ci-workflow-static"]["ok"] is True
    assert subgates["ci-workflow-static"]["summary"]["uses_secrets"] is False
    assert subgates["ci-workflow-static"]["summary"]["deploy_or_publish_detected"] is False
    assert subgates["ci-workflow-static"]["summary"]["quality_gate_ci_profile_referenced"] is True
    assert "pytest" not in subgates


def test_quality_gate_ci_cli_is_available_without_running_pytest_in_this_test() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "quality-gate", "run", "--profile", "fast", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert "ci" in payload["data"]["summary"].get("supported_profiles", ["fast", "full", "ci"]) or payload["data"]["summary"]["profile"] == "fast"
