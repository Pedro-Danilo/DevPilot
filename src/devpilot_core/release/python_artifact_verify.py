from __future__ import annotations

import json
import os
import shutil
import site
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_PYTHON_ARTIFACT_INSTALL_REPORT_JSON = Path("outputs/release/python_artifact_install_verification.json")
DEFAULT_PYTHON_ARTIFACT_INSTALL_REPORT_MARKDOWN = Path("outputs/release/python_artifact_install_verification.md")
_SUPPORTED_SUFFIXES = (".whl", ".tar.gz")
_POST_INSTALL_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("-m", "devpilot_core", "--version"),
    ("-m", "devpilot_core", "schema", "list", "--json"),
    ("-m", "devpilot_core", "project-state", "validate", "--json"),
    ("-m", "devpilot_core", "docs-governance", "validate", "--json"),
)


@dataclass(frozen=True)
class PythonArtifactInstallVerificationOptions:
    """Options for POST-H-027-B Python artifact install verification.

    The verifier creates a temporary local venv under a runtime directory,
    installs one local wheel/sdist artifact with pip in local-first mode and
    executes a minimal post-install CLI smoke. It never publishes, deploys,
    opens sockets or calls external APIs. It uses ``--no-index`` by default to
    avoid mandatory internet access; dependencies already present in the
    operator environment can be bridged through PYTHONPATH without adding the
    DevPilot source tree to sys.path.
    """

    artifact: str
    output_json: str = str(DEFAULT_PYTHON_ARTIFACT_INSTALL_REPORT_JSON)
    output_markdown: str = str(DEFAULT_PYTHON_ARTIFACT_INSTALL_REPORT_MARKDOWN)
    timeout_seconds: int = 60
    keep_temp: bool = False
    write_report: bool = False
    use_local_dependency_bridge: bool = True


class PythonArtifactInstallVerifier:
    """Verify local wheel/sdist installation from generated artifacts.

    POST-H-027-B intentionally performs a real temporary installation, but it
    remains local-first: pip is invoked with ``--no-index`` and ``--no-deps``.
    For sdist, ``--no-build-isolation`` is used so local build tooling already
    present in the operator environment can be used without downloading build
    dependencies. The source tree is not placed on PYTHONPATH; a dedicated
    import check verifies that ``devpilot_core`` is loaded from the venv site
    packages, not from ``src/devpilot_core``.
    """

    def __init__(self, root: Path, options: PythonArtifactInstallVerificationOptions) -> None:
        self.root = Path(root).resolve()
        self.options = options

    def run(self) -> CommandResult:
        started = perf_counter()
        findings: list[Finding] = []
        checks: list[dict[str, Any]] = []
        commands: list[dict[str, Any]] = []
        artifact_path, artifact_error = self._resolve_artifact(self.options.artifact)
        artifact_kind = self._artifact_kind(artifact_path) if artifact_path else "unknown"
        temp_dir: Path | None = None
        venv_python: Path | None = None
        temp_cleaned = False

        if artifact_error:
            findings.append(artifact_error)
            self._record(checks, "artifact-local-supported", False, artifact_error.message, category="artifact", metadata={"artifact": self.options.artifact})
            return self._result(started, artifact_path, artifact_kind, checks, commands, findings, temp_dir, venv_python, temp_cleaned)

        assert artifact_path is not None
        self._record(checks, "artifact-local-supported", True, "Artifact exists inside workspace and has a supported Python package suffix.", category="artifact", metadata={"artifact": self._rel(artifact_path), "artifact_kind": artifact_kind})

        outputs_tmp = self.root / "outputs" / "tmp" / "python-artifact-install"
        outputs_tmp.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=f"post-h-027-b-{artifact_kind}-", dir=outputs_tmp)).resolve()
        venv_dir = temp_dir / "venv"
        env = self._subprocess_env()

        try:
            venv_cmd = [sys.executable, "-m", "venv", str(venv_dir)]
            venv_result = self._run_command(venv_cmd, cwd=self.root, env=env, timeout=self.options.timeout_seconds)
            commands.append(self._command_record("create-venv", venv_cmd, venv_result))
            self._record(checks, "temporary-venv-created", venv_result["exit_code"] == 0, "Temporary venv was created under outputs/tmp.", category="runtime", metadata={"temp_dir": self._display_path(temp_dir)})
            if venv_result["exit_code"] != 0:
                findings.append(Finding("PYTHON_ARTIFACT_VENV_CREATE_BLOCK", "Temporary venv creation failed.", Severity.BLOCK, metadata={"stderr": venv_result["stderr_tail"]}))
                return self._result(started, artifact_path, artifact_kind, checks, commands, findings, temp_dir, venv_python, temp_cleaned)

            venv_python = self._venv_python(venv_dir)
            dependency_bridge = self._write_dependency_bridge(venv_python)
            command_env = self._env_with_dependency_bridge(env, dependency_bridge)
            pip_cmd = self._pip_install_command(venv_python, artifact_path, artifact_kind)
            pip_result = self._run_command(pip_cmd, cwd=self.root, env=command_env, timeout=max(self.options.timeout_seconds, 120))
            commands.append(self._command_record("pip-install-artifact", pip_cmd, pip_result))
            pip_ok = pip_result["exit_code"] == 0
            self._record(checks, "pip-install-local-artifact", pip_ok, "pip installed the local artifact with --no-index and without publishing/downloading by design.", category="install", metadata={"artifact_kind": artifact_kind, "no_index": True, "no_deps": True, "no_build_isolation": artifact_kind == "sdist", "dependency_bridge": dependency_bridge})
            if not pip_ok:
                findings.append(Finding("PYTHON_ARTIFACT_PIP_INSTALL_BLOCK", "pip could not install the local Python artifact in the temporary venv.", Severity.BLOCK, metadata={"artifact_kind": artifact_kind, "stderr": pip_result["stderr_tail"], "hint": self._pip_failure_hint(artifact_kind, pip_result)}))
                return self._result(started, artifact_path, artifact_kind, checks, commands, findings, temp_dir, venv_python, temp_cleaned)

            import_cmd = [str(venv_python), "-c", self._import_check_code()]
            import_result = self._run_command(import_cmd, cwd=self.root, env=command_env, timeout=self.options.timeout_seconds)
            commands.append(self._command_record("import-installed-package", import_cmd, import_result, redact_code=True))
            import_payload = self._json_from_stdout(import_result.get("stdout_full") or import_result["stdout_tail"])
            import_from_installed = bool(import_payload.get("import_from_installed_site_packages"))
            source_dependency_detected = bool(import_payload.get("source_path_dependency_detected")) if import_payload else True
            import_ok = import_result["exit_code"] == 0 and import_from_installed and not source_dependency_detected
            self._record(checks, "import-from-installed-site-packages", import_ok, "devpilot_core imports from the temporary venv installation rather than the source tree.", category="install", metadata=import_payload or {"stdout": import_result["stdout_tail"], "stderr": import_result["stderr_tail"]})
            if not import_ok:
                findings.append(Finding("PYTHON_ARTIFACT_SOURCE_PATH_DEPENDENCY_BLOCK", "Installed package import check detected source-tree dependency or failed import.", Severity.BLOCK, metadata={"stdout": import_result["stdout_tail"], "stderr": import_result["stderr_tail"]}))

            post_install_passed = True
            for index, command_args in enumerate(_POST_INSTALL_COMMANDS, start=1):
                cmd = [str(venv_python), *command_args]
                cmd_result = self._run_command(cmd, cwd=self.root, env=command_env, timeout=max(self.options.timeout_seconds, 120))
                command_id = f"post-install-{index}-{'-'.join(command_args).replace('--', '').replace(' ', '-')[:48]}"
                commands.append(self._command_record(command_id, cmd, cmd_result))
                ok = cmd_result["exit_code"] == 0
                if command_args[-1] == "--json":
                    payload = self._json_from_stdout(cmd_result.get("stdout_full") or cmd_result["stdout_tail"])
                    ok = ok and isinstance(payload, dict) and bool(payload.get("ok"))
                post_install_passed = post_install_passed and ok
                self._record(checks, command_id, ok, f"Post-install command {' '.join(command_args)} executed successfully.", category="post-install", metadata={"exit_code": cmd_result["exit_code"]})
                if not ok:
                    findings.append(Finding("PYTHON_ARTIFACT_POST_INSTALL_COMMAND_BLOCK", "A post-install smoke command failed in the temporary venv.", Severity.BLOCK, metadata={"command": " ".join(command_args), "stdout": cmd_result["stdout_tail"], "stderr": cmd_result["stderr_tail"]}))

            if post_install_passed and import_ok:
                findings.append(Finding("PYTHON_ARTIFACT_INSTALL_VERIFICATION_PASS", "Python artifact install verification passed without network, external APIs, publication or source mutations.", Severity.INFO, metadata={"artifact_kind": artifact_kind}))
        finally:
            if temp_dir and temp_dir.exists() and not self.options.keep_temp:
                shutil.rmtree(temp_dir, ignore_errors=True)
                temp_cleaned = not temp_dir.exists()

        return self._result(started, artifact_path, artifact_kind, checks, commands, findings, temp_dir, venv_python, temp_cleaned)

    def _result(
        self,
        started: float,
        artifact_path: Path | None,
        artifact_kind: str,
        checks: list[dict[str, Any]],
        commands: list[dict[str, Any]],
        findings: list[Finding],
        temp_dir: Path | None,
        venv_python: Path | None,
        temp_cleaned: bool,
    ) -> CommandResult:
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        checks_passed = sum(1 for check in checks if check.get("status") == "pass")
        decision = "PASS" if not blocking and checks and checks_passed == len(checks) else "BLOCK"
        command_map = {item["command_id"]: item for item in commands}
        import_record = command_map.get("import-installed-package", {})
        import_payload = self._json_from_stdout(import_record.get("stdout_tail") or "")
        report = {
            "schema_version": "1.0",
            "schema_id": "SCHEMA-DEVPL-PYTHON-ARTIFACT-INSTALL-VERIFICATION-V1",
            "report_id": f"python-artifact-install-verification-post_h_027_b-{artifact_kind}",
            "created_by": "POST-H-027-B",
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "scope": "local-python-artifact-install",
            "decision": decision,
            "implemented_status": "implemented-initial",
            "execution_mode": "temporary-venv-local-pip-install-smoke",
            "artifact": self._rel(artifact_path) if artifact_path else self.options.artifact,
            "artifact_kind": artifact_kind,
            "artifact_exists": bool(artifact_path and artifact_path.exists()),
            "temp_dir": self._display_path(temp_dir) if temp_dir else None,
            "temp_cleaned": temp_cleaned,
            "venv_python": self._display_path(venv_python) if venv_python else None,
            "checks_total": len(checks),
            "checks_passed_total": checks_passed,
            "checks_failed_total": len(checks) - checks_passed,
            "critical_checks_total": sum(1 for check in checks if check.get("critical") is True),
            "critical_checks_failed_total": sum(1 for check in checks if check.get("critical") is True and check.get("status") != "pass"),
            "commands_executed_total": len(commands),
            "commands_executed": commands,
            "checks": checks,
            "duration_ms": round((perf_counter() - started) * 1000, 3),
            "summary": {
                "decision": decision,
                "created_by": "POST-H-027-B",
                "preliminary": True,
                "artifact_kind": artifact_kind,
                "artifact_installed": any(item["command_id"] == "pip-install-artifact" and item["exit_code"] == 0 for item in commands),
                "cli_version_passed": any(item["command_id"].startswith("post-install-1") and item["exit_code"] == 0 for item in commands),
                "schema_list_passed": any("schema-list" in item["command_id"] and item["exit_code"] == 0 for item in commands),
                "project_state_validate_passed": any("project-state" in item["command_id"] and item["exit_code"] == 0 for item in commands),
                "docs_governance_validate_passed": any("docs-governance" in item["command_id"] and item["exit_code"] == 0 for item in commands),
                "import_from_installed_site_packages": bool(import_payload.get("import_from_installed_site_packages")),
                "source_path_dependency_detected": bool(import_payload.get("source_path_dependency_detected")) if import_payload else False,
                "post_install_commands_passed": decision == "PASS",
                "venv_created": any(item["command_id"] == "create-venv" and item["exit_code"] == 0 for item in commands),
                "temp_cleaned": temp_cleaned,
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "mutations_performed": bool(commands),
                "source_mutations": False,
                "reports_written": self.options.write_report,
            },
            "safety": {
                "local_first": True,
                "read_only": False,
                "dry_run": False,
                "temporary_venv_created": any(item["command_id"] == "create-venv" and item["exit_code"] == 0 for item in commands),
                "subprocess_executed": bool(commands),
                "pip_executed": any(item["command_id"] == "pip-install-artifact" for item in commands),
                "pip_no_index": True,
                "pip_no_deps": True,
                "socket_opened": False,
                "network_used": False,
                "external_api_used": False,
                "publish_performed": False,
                "deploy_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "mutations_performed": bool(commands),
                "source_mutations": False,
                "reports_written": self.options.write_report,
            },
            "limitations": [
                "POST-H-027-B verifies local Python wheel/sdist install smoke only; it does not publish packages, sign artifacts or validate a multi-OS matrix.",
                "The verifier uses pip --no-index by default. Runtime dependencies must already be available in the operator environment and are bridged into the temporary venv with a generated .pth file; no mandatory internet access is introduced.",
                "Windows operator copy-paste guide, unified artifact manifest/checksums and upgrade/rollback dry-run remain later POST-H-027 micro-sprints.",
            ],
        }
        if self.options.write_report:
            self._write_reports(report)
        return CommandResult(
            command="release python-artifact-verify",
            ok=decision == "PASS",
            exit_code=ExitCode.PASS if decision == "PASS" else ExitCode.BLOCK,
            message="Python artifact install verification passed." if decision == "PASS" else "Python artifact install verification blocked.",
            data={"summary": report["summary"], "report": report, "reports": self._report_paths() if self.options.write_report else {}},
            findings=findings,
        )

    def _resolve_artifact(self, artifact: str) -> tuple[Path | None, Finding | None]:
        raw = Path(artifact)
        resolved = raw if raw.is_absolute() else self.root / raw
        resolved = resolved.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            return None, Finding("PYTHON_ARTIFACT_OUTSIDE_WORKSPACE_BLOCK", "Python artifact path must stay inside the DevPilot workspace.", Severity.BLOCK, metadata={"artifact": artifact})
        if not resolved.exists() or not resolved.is_file():
            return None, Finding("PYTHON_ARTIFACT_MISSING_BLOCK", "Python artifact does not exist.", Severity.BLOCK, metadata={"artifact": artifact})
        if not (resolved.name.endswith(".whl") or resolved.name.endswith(".tar.gz")):
            return None, Finding("PYTHON_ARTIFACT_UNSUPPORTED_KIND_BLOCK", "Python artifact must be a .whl or .tar.gz sdist.", Severity.BLOCK, metadata={"artifact": self._rel(resolved)})
        return resolved, None

    @staticmethod
    def _artifact_kind(path: Path | None) -> str:
        if path is None:
            return "unknown"
        if path.name.endswith(".whl"):
            return "wheel"
        if path.name.endswith(".tar.gz"):
            return "sdist"
        return "unknown"

    def _pip_install_command(self, venv_python: Path, artifact: Path, artifact_kind: str) -> list[str]:
        cmd = [str(venv_python), "-m", "pip", "install", "--no-index", "--no-deps"]
        if artifact_kind == "sdist":
            cmd.append("--no-build-isolation")
        cmd.append(str(artifact))
        return cmd

    def _write_dependency_bridge(self, venv_python: Path) -> dict[str, Any]:
        """Expose already-installed operator dependencies to the temp venv.

        The verifier intentionally uses ``pip --no-index --no-deps`` so it does
        not download dependencies.  On Windows the operator usually runs tests
        from ``<repo>/.venv``; the previous bridge implementation rejected every
        path under the workspace and therefore hid ``jsonschema`` from the
        temporary install venv.  Writing a ``.pth`` file into the temp venv keeps
        the artifact's own ``site-packages`` first on ``sys.path`` while making
        dependency-only host site-packages available afterwards.
        """

        if not self.options.use_local_dependency_bridge:
            return {"enabled": False, "paths_total": 0, "paths": [], "pth_path": None}

        bridge_paths = self._dependency_bridge_paths()
        if not bridge_paths:
            return {"enabled": True, "paths_total": 0, "paths": [], "pth_path": None}

        site_packages = self._venv_site_packages(venv_python)
        site_packages.mkdir(parents=True, exist_ok=True)
        pth_path = site_packages / "devpilot_post_h_027_b_dependency_bridge.pth"
        pth_path.write_text("\n".join(bridge_paths) + "\n", encoding="utf-8")
        return {
            "enabled": True,
            "paths_total": len(bridge_paths),
            "paths": [self._display_path(Path(item)) for item in bridge_paths],
            "pth_path": self._display_path(pth_path),
        }


    def _env_with_dependency_bridge(self, env: dict[str, str], dependency_bridge: dict[str, Any]) -> dict[str, str]:
        """Add dependency-only host paths to PYTHONPATH for pip build hooks and CLI smoke.

        The generated .pth file is enough for normal interpreter startup in the
        temporary venv, but pip PEP 517 build hook subprocesses can fail before
        that path is effective for build-backend imports on Python 3.12+ where
        fresh venvs do not bundle setuptools.  This environment bridge keeps the
        DevPilot source tree excluded while allowing local build/runtime
        dependencies already installed in the operator environment.
        """

        paths = [str((self.root / item).resolve()) if not Path(str(item)).is_absolute() else str(Path(str(item)).resolve()) for item in dependency_bridge.get("paths", [])]
        safe_paths: list[str] = []
        workspace_src = (self.root / "src").resolve()
        source_root = (self.root / "src" / "devpilot_core").resolve()
        for item in paths:
            path = Path(item).resolve()
            if not path.exists() or not path.is_dir():
                continue
            if path == workspace_src:
                continue
            try:
                source_root.relative_to(path)
                continue
            except ValueError:
                pass
            if (path / "devpilot_core" / "__init__.py").exists():
                continue
            rendered = str(path)
            if rendered not in safe_paths:
                safe_paths.append(rendered)
        if not safe_paths:
            return env
        bridged = dict(env)
        existing = bridged.get("PYTHONPATH")
        bridged["PYTHONPATH"] = os.pathsep.join(safe_paths + ([existing] if existing else []))
        return bridged

    def _venv_site_packages(self, venv_python: Path) -> Path:
        venv_dir = venv_python.parent.parent if venv_python.parent.name in {"Scripts", "bin"} else venv_python.parent
        windows_site = venv_dir / "Lib" / "site-packages"
        if windows_site.exists() or venv_python.name.lower() == "python.exe":
            return windows_site
        return venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

    def _subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        env["PIP_NO_INPUT"] = "1"
        env["DEVPILOT_POST_H_027_B_SOURCE_ROOT"] = str((self.root / "src" / "devpilot_core").resolve())
        env["DEVPILOT_POST_H_027_B_WORKSPACE_ROOT"] = str(self.root)
        return env

    def _dependency_bridge_paths(self) -> list[str]:
        candidates: list[str] = []
        for getter in (site.getsitepackages,):
            try:
                candidates.extend(getter())
            except Exception:
                pass
        try:
            candidates.append(site.getusersitepackages())
        except Exception:
            pass

        source_root = (self.root / "src" / "devpilot_core").resolve()
        workspace_src = (self.root / "src").resolve()
        result: list[str] = []
        for item in candidates:
            path = Path(item).resolve()
            if not path.exists() or not path.is_dir():
                continue
            normalized = str(path).replace("\\", "/")
            if path == workspace_src or normalized.endswith("/src"):
                continue
            try:
                source_root.relative_to(path)
                continue
            except ValueError:
                pass
            # A bridge may legitimately point to the operator's .venv under the
            # workspace.  It must not point at a site-packages that contains an
            # actual devpilot_core package, because that would invalidate the
            # artifact-origin check.  Editable-install .pth files are not
            # executed when referenced through this generated .pth bridge.
            if (path / "devpilot_core" / "__init__.py").exists():
                continue
            if str(path) not in result:
                result.append(str(path))
        return result

    @staticmethod
    def _venv_python(venv_dir: Path) -> Path:
        windows = venv_dir / "Scripts" / "python.exe"
        if windows.exists():
            return windows
        return venv_dir / "bin" / "python"

    def _run_command(self, cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
        started = perf_counter()
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            return {
                "exit_code": int(completed.returncode),
                "stdout_full": completed.stdout,
                "stderr_full": completed.stderr,
                "stdout_tail": _tail(completed.stdout),
                "stderr_tail": _tail(completed.stderr),
                "duration_ms": round((perf_counter() - started) * 1000, 3),
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "exit_code": 124,
                "stdout_full": exc.stdout or "",
                "stderr_full": exc.stderr or "timeout",
                "stdout_tail": _tail(exc.stdout or ""),
                "stderr_tail": _tail(exc.stderr or "timeout"),
                "duration_ms": round((perf_counter() - started) * 1000, 3),
                "timed_out": True,
            }

    def _command_record(self, command_id: str, cmd: list[str], result: dict[str, Any], *, redact_code: bool = False) -> dict[str, Any]:
        rendered = [self._display_command_part(part) for part in cmd]
        if redact_code:
            rendered = rendered[:2] + ["<import-check-code-redacted>"]
        return {
            "command_id": command_id,
            "command": rendered,
            "exit_code": result["exit_code"],
            "duration_ms": result["duration_ms"],
            "timed_out": result["timed_out"],
            "stdout_tail": result["stdout_tail"],
            "stderr_tail": result["stderr_tail"],
        }

    def _display_command_part(self, part: str) -> str:
        text = str(part)
        try:
            path = Path(text).resolve()
            if path.exists():
                return self._display_path(path)
        except Exception:
            pass
        return text

    def _display_path(self, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def _rel(self, path: Path | None) -> str | None:
        return self._display_path(path)

    @staticmethod
    def _json_from_stdout(stdout: str) -> Any:
        text = (stdout or "").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            lines = [line for line in text.splitlines() if line.strip()]
            for line in reversed(lines):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return {}

    @staticmethod
    def _import_check_code() -> str:
        return """
import json
import os
import pathlib
import sys
import devpilot_core
source_root = pathlib.Path(os.environ.get('DEVPILOT_POST_H_027_B_SOURCE_ROOT', '')).resolve()
module_path = pathlib.Path(devpilot_core.__file__).resolve()
workspace_root = pathlib.Path(os.environ.get('DEVPILOT_POST_H_027_B_WORKSPACE_ROOT', '')).resolve()
source_path_dependency_detected = False
try:
    module_path.relative_to(source_root)
    source_path_dependency_detected = True
except ValueError:
    pass
src_path = str(workspace_root / 'src')
if any(str(pathlib.Path(item).resolve()) == src_path for item in sys.path if item):
    source_path_dependency_detected = True
payload = {
    'module_path': str(module_path),
    'source_root': str(source_root),
    'workspace_src_on_syspath': any(str(pathlib.Path(item).resolve()) == src_path for item in sys.path if item),
    'source_path_dependency_detected': source_path_dependency_detected,
    'import_from_installed_site_packages': 'site-packages' in str(module_path) or 'dist-packages' in str(module_path),
    'version': getattr(devpilot_core, '__version__', None),
}
print(json.dumps(payload, sort_keys=True))
raise SystemExit(0 if payload['import_from_installed_site_packages'] and not source_path_dependency_detected else 3)
""".strip()

    def _pip_failure_hint(self, artifact_kind: str, result: dict[str, Any]) -> str:
        stderr = (result.get("stderr_tail") or "").lower()
        if artifact_kind == "sdist" and ("setuptools" in stderr or "build dependencies" in stderr or "build backend" in stderr):
            return "sdist requires local build tooling. Re-run in an environment with local setuptools/build backend available; the verifier will not download build dependencies."
        if "no matching distribution" in stderr or "could not find" in stderr:
            return "Local dependency wheelhouse is missing required dependencies; the verifier intentionally uses --no-index."
        return "Inspect stderr_tail for the local pip failure; no remote index was used."

    def _record(self, checks: list[dict[str, Any]], check_id: str, passed: bool, reason: str, *, category: str = "install", critical: bool = True, metadata: dict[str, Any] | None = None) -> None:
        checks.append({
            "check_id": check_id,
            "category": category,
            "status": "pass" if passed else "block",
            "critical": critical,
            "reason": reason,
            "metadata": metadata or {},
        })

    def _write_reports(self, report: dict[str, Any]) -> None:
        output_json = self.root / self.options.output_json
        output_markdown = self.root / self.options.output_markdown
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        output_markdown.write_text(self._markdown(report), encoding="utf-8")

    def _report_paths(self) -> dict[str, str]:
        return {"json": self.options.output_json, "markdown": self.options.output_markdown}

    @staticmethod
    def _markdown(report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# POST-H-027-B — Python artifact install verification",
            "",
            f"Decision: **{report.get('decision')}**",
            f"Artifact: `{report.get('artifact')}`",
            f"Artifact kind: `{report.get('artifact_kind')}`",
            f"Commands executed: `{report.get('commands_executed_total')}`",
            "",
            "## Safety",
            "",
            f"- Network used: `{summary.get('network_used')}`",
            f"- External API used: `{summary.get('external_api_used')}`",
            f"- Source mutations: `{summary.get('source_mutations')}`",
            f"- Temporary cleaned: `{summary.get('temp_cleaned')}`",
            "",
            "## Checks",
            "",
        ]
        for check in report.get("checks", []):
            lines.append(f"- `{check.get('status')}` — `{check.get('check_id')}`: {check.get('reason')}")
        lines.append("")
        lines.append("## Limitations")
        lines.append("")
        for item in report.get("limitations", []):
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"


def _tail(text: str, limit: int = 2400) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[-limit:]
