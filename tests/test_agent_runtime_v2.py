from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import ExitCode

ROOT = Path(__file__).resolve().parents[1]


def _copy_agent_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "evals", target / "evals", dirs_exist_ok=True)
    (target / ".devpilot" / "providers.yaml.example").write_text((ROOT / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8"), encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot'\n", encoding="utf-8")


def _enable_lmstudio_on_unused_localhost_port(root: Path) -> None:
    example = (root / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8")
    local = example.replace(
        '  - id: "lmstudio"\n    kind: "local"\n    enabled: false\n    default_model: "local-model"\n    endpoint: "http://localhost:1234"',
        '  - id: "lmstudio"\n    kind: "local"\n    enabled: true\n    default_model: "local-model"\n    endpoint: "http://localhost:65530"',
    )
    (root / ".devpilot" / "providers.yaml").write_text(local, encoding="utf-8")


def test_agent_runtime_v2_preserves_existing_agents_without_model(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("documentation-audit", target="docs/01_requirements", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "precode.audit"
    assert result.data["summary"]["model_calls_total"] == 0
    assert result.data["metadata"]["model_runtime_enabled"] is False
    assert result.data["metadata"]["handoffs_enabled"] is False


def test_agent_runtime_v2_uses_mock_via_router_and_records_redacted_model_call(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run("documentation-audit", target="docs/01_requirements", provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["model_calls_total"] == 1
    call = result.data["model_calls"][0]
    assert call["provider"] == "mock"
    assert call["prompt_id"] == "model.generate.default"
    assert call["prompt_payload_redacted"] is True
    assert call["raw_prompt_stored"] is False
    assert call["raw_output_stored"] is False
    assert call["external_api_used"] is False
    assert "result_digest" in call
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_agent_runtime_v2_blocks_secret_prompt_input_before_provider_payload_leaks(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)

    result = AgentRuntime(tmp_path).run(
        "documentation-audit",
        target="docs/01_requirements",
        provider="mock",
        prompt_inputs={"user_request": "usar api_key=sk-1234567890abcdef"},
        dry_run=True,
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["model_calls_total"] == 1
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    assert "sk-1234567890abcdef" not in serialized
    assert "api_key=sk-" not in serialized
    assert "SECRETGUARD_SECRET_DETECTED" in {finding.id for finding in result.findings}


def test_agent_runtime_v2_fallback_to_mock_for_enabled_unavailable_local_provider(tmp_path: Path) -> None:
    _copy_agent_workspace(tmp_path)
    _enable_lmstudio_on_unused_localhost_port(tmp_path)

    result = AgentRuntime(tmp_path).run(
        "precode-documentation",
        idea="Agregar trazabilidad model-aware para agentes monoagente",
        provider="lmstudio",
        fallback_to_mock=True,
        timeout_seconds=0.05,
        dry_run=True,
    )

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    call = result.data["model_calls"][0]
    assert call["provider"] == "mock"
    assert call["fallback_applied"] is True
    assert call["fallback_from_provider"] == "lmstudio"
    assert call["fallback_to_provider"] == "mock"
    assert any(finding.id == "MODEL_FALLBACK_TO_MOCK_APPLIED" for finding in result.findings)


def test_agent_runtime_v2_cli_json_and_eval_suite_are_parseable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "run", "documentation-audit", "--target", "docs/01_requirements", "--provider", "mock", "--json"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["data"]["summary"]["model_calls_total"] == 1
    assert payload["data"]["metadata"]["runtime_version"] == "v2-model-aware"

    eval_completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "eval", "run", "--json"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert eval_completed.returncode == 0, eval_completed.stderr + eval_completed.stdout
    eval_payload = json.loads(eval_completed.stdout)
    assert eval_payload["ok"] is True
    assert eval_payload["data"]["summary"]["cases_total"] >= 9
