from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core import cli
from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import ExitCode
from devpilot_core.evals import EvalRunner

ROOT = Path(__file__).resolve().parents[1]


def _copy_review_workspace(target: Path) -> None:
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / ".devpilot" / "miasi", target / ".devpilot" / "miasi")
    shutil.copytree(ROOT / "docs", target / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "evals", target / "evals", dirs_exist_ok=True)
    (target / ".devpilot" / "providers.yaml.example").write_text((ROOT / ".devpilot" / "providers.yaml.example").read_text(encoding="utf-8"), encoding="utf-8")
    (target / "pyproject.toml").write_text("[project]\nname='tmp-devpilot-review-agents'\n", encoding="utf-8")


def _write_safe_patch(root: Path) -> Path:
    target = root / "patch_targets" / "safe.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def value():\n    return 'old'\n", encoding="utf-8")
    patch = root / "safe.patch"
    patch.write_text(
        "diff --git a/patch_targets/safe.py b/patch_targets/safe.py\n"
        "--- a/patch_targets/safe.py\n"
        "+++ b/patch_targets/safe.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def value():\n"
        "-    return 'old'\n"
        "+    return 'new'\n",
        encoding="utf-8",
    )
    return patch


def test_code_review_agent_clean_code_uses_mock_model(tmp_path: Path) -> None:
    _copy_review_workspace(tmp_path)
    source = tmp_path / "src" / "clean.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("def greet(name: str) -> str:\n    return f'hello {name}'\n", encoding="utf-8")

    result = AgentRuntime(tmp_path).run("code-review", target="src", provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "code.review"
    assert result.data["metadata"]["monoagent"] is True
    assert result.data["metadata"]["handoffs_enabled"] is False
    assert result.data["summary"]["model_calls_total"] == 1
    assert result.data["artifacts"]["mutations_performed"] is False
    call = result.data["model_calls"][0]
    assert call["provider"] == "mock"
    assert call["prompt_id"] == "code.review.agent"
    assert call["raw_prompt_stored"] is False
    assert call["raw_output_stored"] is False
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_code_review_agent_detects_eval_and_os_system(tmp_path: Path) -> None:
    _copy_review_workspace(tmp_path)
    source = tmp_path / "src" / "risky.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("import os\n\ndef run(value: str):\n    os.system(value)\n    return eval(value)\n", encoding="utf-8")

    result = AgentRuntime(tmp_path).run("code-review", target="src", dry_run=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    ids = {finding.id for finding in result.findings}
    assert "CODE_REVIEW_OS_SYSTEM" in ids
    assert "CODE_REVIEW_EVAL" in ids
    assert result.data["artifacts"]["mutations_performed"] is False
    assert result.data["summary"]["model_calls_total"] == 0


def test_patch_review_agent_safe_patch_uses_preflight_and_mock(tmp_path: Path) -> None:
    _copy_review_workspace(tmp_path)
    patch = _write_safe_patch(tmp_path)

    result = AgentRuntime(tmp_path).run("patch-review", patch_file=patch.name, provider="mock", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["agent"]["agent_id"] == "patch.review"
    assert result.data["artifacts"]["patch_applied"] is False
    assert result.data["artifacts"]["mutations_performed"] is False
    assert result.data["artifacts"]["summary"]["apply_check_executed"] is True
    assert result.data["artifacts"]["summary"]["applies"] is True
    assert result.data["summary"]["model_calls_total"] == 1
    assert result.data["model_calls"][0]["prompt_id"] == "patch.review.agent"
    assert any(finding.id == "MODEL_ADAPTER_PASS" for finding in result.findings)


def test_patch_review_agent_blocks_secret_like_patch(tmp_path: Path) -> None:
    _copy_review_workspace(tmp_path)
    patch = tmp_path / "secret.patch"
    patch.write_text(
        "diff --git a/secret.txt b/secret.txt\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/secret.txt\n"
        "@@ -0,0 +1 @@\n"
        "+api_key=sk-1234567890abcdef\n",
        encoding="utf-8",
    )

    result = AgentRuntime(tmp_path).run("patch-review", patch_file="secret.patch", dry_run=True)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    ids = {finding.id for finding in result.findings}
    assert "PATCH_SECRET_LIKE_CONTENT" in ids
    assert result.data["artifacts"]["patch_applied"] is False
    assert result.data["artifacts"]["mutations_performed"] is False


def test_review_agents_cli_and_eval_cases_are_parseable(tmp_path: Path, monkeypatch, capsys) -> None:
    _copy_review_workspace(tmp_path)
    source = tmp_path / "src" / "clean.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("def ok() -> str:\n    return 'ok'\n", encoding="utf-8")
    patch = _write_safe_patch(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["agent", "run", "code-review", "--target", "src", "--provider", "mock", "--json"])
    code_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert code_payload["data"]["agent"]["agent_id"] == "code.review"
    assert code_payload["data"]["summary"]["model_calls_total"] == 1

    exit_code = cli.main(["agent", "run", "patch-review", "--patch-file", patch.name, "--provider", "mock", "--json"])
    patch_payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert patch_payload["data"]["agent"]["agent_id"] == "patch.review"
    assert patch_payload["data"]["artifacts"]["patch_applied"] is False

    eval_code = EvalRunner(tmp_path).run(case_id="agent-code-review-clean-model-aware-mock")
    eval_patch = EvalRunner(tmp_path).run(case_id="agent-patch-review-safe-model-aware-mock")

    assert eval_code.ok is True
    assert eval_patch.ok is True
