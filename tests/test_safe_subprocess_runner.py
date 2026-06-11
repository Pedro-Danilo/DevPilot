from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.execution import CommandAllowlist, SafeSubprocessRunner


def _project(root: Path) -> None:
    (root / "docs").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")


def test_safe_subprocess_runner_executes_allowlisted_pytest_without_shell(tmp_path: Path) -> None:
    _project(tmp_path)
    result = SafeSubprocessRunner(tmp_path).run([sys.executable, "-m", "pytest", "--version"], cwd=".", timeout_seconds=30)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["executed"] is True
    assert result.data["summary"]["command_allowed"] is True
    assert result.data["execution"]["command_id"] == "python.pytest"
    assert result.data["execution"]["returncode"] == 0
    assert result.data["environment_controls"]["pytest_plugin_autoload_disabled"] is True
    assert result.data["summary"]["environment_controls"]["python_user_site_disabled"] is True


def test_safe_subprocess_runner_blocks_shell_strings_and_unallowlisted_commands(tmp_path: Path) -> None:
    _project(tmp_path)
    runner = SafeSubprocessRunner(tmp_path)

    shell_result = runner.run("python -m pytest", cwd=".")  # type: ignore[arg-type]
    blocked = runner.run([sys.executable, "-c", "print('unsafe')"], cwd=".")

    assert shell_result.ok is False
    assert shell_result.exit_code == ExitCode.BLOCK
    assert shell_result.findings[0].id == "SAFE_SUBPROCESS_ARGS_NOT_LIST"
    assert blocked.ok is False
    assert blocked.exit_code == ExitCode.BLOCK
    assert blocked.findings[0].id == "SAFE_SUBPROCESS_COMMAND_NOT_ALLOWLISTED"


def test_safe_subprocess_runner_blocks_cwd_outside_workspace(tmp_path: Path) -> None:
    _project(tmp_path)
    outside = tmp_path.parent

    result = SafeSubprocessRunner(tmp_path).run([sys.executable, "-m", "pytest", "--version"], cwd=outside)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "PATHGUARD_OUTSIDE_ROOT"
    assert result.data["summary"]["executed"] is False


def test_safe_subprocess_runner_applies_timeout(tmp_path: Path) -> None:
    _project(tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_slow.py").write_text(
        textwrap.dedent(
            """
            import time

            def test_slow():
                time.sleep(2)
            """
        ),
        encoding="utf-8",
    )

    result = SafeSubprocessRunner(tmp_path).run([sys.executable, "-m", "pytest", "tests/test_slow.py", "-q"], cwd=".", timeout_seconds=1)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "SAFE_SUBPROCESS_TIMEOUT"
    assert result.data["execution"]["timed_out"] is True


def test_safe_subprocess_runner_redacts_and_truncates_output(tmp_path: Path) -> None:
    _project(tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_output.py").write_text(
        textwrap.dedent(
            """
            def test_output():
                print('api_key=sk-1234567890abcdef')
                print('x' * 1000)
            """
        ),
        encoding="utf-8",
    )

    result = SafeSubprocessRunner(tmp_path, max_output_chars=120).run(
        [sys.executable, "-m", "pytest", "tests/test_output.py", "-q", "-s"], cwd=".", timeout_seconds=30
    )

    assert result.ok is True
    output = result.data["execution"]["stdout"]
    assert "sk-1234567890abcdef" not in output
    assert "[REDACTED]" in output
    assert result.data["execution"]["redactions"] >= 1
    assert result.data["execution"]["stdout_truncated"] is True


def test_command_allowlist_loads_local_config(tmp_path: Path) -> None:
    _project(tmp_path)
    allowlist_dir = tmp_path / ".devpilot" / "execution"
    allowlist_dir.mkdir(parents=True)
    (allowlist_dir / "command_allowlist.json").write_text(
        """
        {
          "schema_version": "1.0",
          "commands": [
            {
              "command_id": "python.pytest.custom",
              "executable": "python",
              "executable_aliases": ["python", "python.exe", "python3", "python3.exe"],
              "args_prefix": ["-m", "pytest"],
              "max_timeout_seconds": 30
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    allowlist = CommandAllowlist(tmp_path)
    match = allowlist.match([sys.executable, "-m", "pytest", "--version"])

    assert match.allowed is True
    assert match.entry is not None
    assert match.entry.command_id == "python.pytest.custom"
    assert allowlist.to_dict()["fallback_used"] is False
