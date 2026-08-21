from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from devpl_gsdlc_04_b_fixture_state import inspect_fixture

SCRIPT_ID = "DEVPL-GSDLC-04-B-RUNTIME-CONSOLE"
VERSION = "1.0.9"
DEFAULT_BROWSER_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def verdict(status: str, message: str) -> None:
    _enable_windows_ansi()
    color = "\x1b[92m" if status == "PASS" else "\x1b[91m"
    print(f"{color}{status} — {message}\x1b[0m", flush=True)


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def url_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.5) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def stop_child(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        time.sleep(1)
        if proc.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()


def _validate_browser_fixture(raw: str) -> Path:
    fixture = Path(raw).resolve()
    expected = Path(DEFAULT_BROWSER_FIXTURE).resolve()
    if fixture != expected:
        raise RuntimeError(f"Fixture no autorizado para 04-B: {fixture}. Debe ser exactamente {expected}.")
    if not fixture.is_dir():
        raise RuntimeError(f"Fixture browser no existe: {fixture}. Ejecute prepare-browser desde Consola 1.")
    required = [fixture / "docs" / "manual_authoring.md", fixture / "docs" / "manual_authoring.json"]
    missing = [str(item) for item in required if not item.is_file()]
    if missing:
        raise RuntimeError(f"Fixture browser incompleto; faltan archivos controlados: {missing}")
    if "inventory-sales-local" in str(fixture).lower() or "devpilot_workspaces" in str(fixture).lower():
        raise RuntimeError("El runtime 04-B no puede vincularse al workspace piloto real.")
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dedicated GSDLC-04-B API/UI runtime console. Keep this console open while the role is running."
    )
    parser.add_argument("--role", choices=["api", "ui"], required=True)
    parser.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    parser.add_argument("--evidence-dir", default=r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B")
    parser.add_argument("--browser-fixture-root", default=DEFAULT_BROWSER_FIXTURE)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    runtime = evidence / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    role = args.role
    port = 8787 if role == "api" else 5173
    ready_url = "http://127.0.0.1:8787/api/v1/health" if role == "api" else "http://127.0.0.1:5173/"
    log_path = runtime / f"{role}_console.log"
    state_path = runtime / f"{role}_console_state.json"
    proc: subprocess.Popen[Any] | None = None
    log_handle = None

    try:
        if not repo.is_dir():
            raise RuntimeError(f"Repo no encontrado: {repo}")
        if port_open(port):
            raise RuntimeError(
                f"Puerto {port} ya está ocupado. Ejecute runtime-recover/runtime-stop desde Consola 1; no mate procesos por nombre."
            )

        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        workspace_binding: dict[str, Any] | None = None

        if role == "api":
            py = repo / ".venv" / "Scripts" / "python.exe"
            if not py.is_file():
                raise RuntimeError("Falta .venv\\Scripts\\python.exe; provisioning no está completo.")
            fixture = _validate_browser_fixture(args.browser_fixture_root)
            fixture_state = inspect_fixture(fixture, phase_policy="either")
            if not fixture_state["git_clean"]:
                raise RuntimeError(
                    f"Fixture Git dirty antes de iniciar API: {fixture_state['git_status_entries']}. "
                    "Ejecute el checkpoint de recovery/resume vigente desde Consola 1; no use git clean/reset."
                )

            # Narrow the API process to the disposable 04-B fixture only.
            # Replace inherited external roots instead of broadening them.
            env["DEVPILOT_ALLOWED_WORKSPACE_ROOTS"] = str(fixture)
            env["DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT"] = str(fixture)
            env.pop("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", None)

            # Server startup requires an explicit token. Generate it only in memory;
            # do not print or persist the secret. Human-session login remains the
            # browser authority for GSDLC-04-B protected draft routes.
            env["DEVPILOT_API_TOKEN"] = secrets.token_urlsafe(32)
            workspace_binding = {
                "allowed_workspace_root": str(fixture),
                "active_workspace_root": str(fixture),
                "registry_env_cleared": True,
                "scope": "gsdlc-04-b-browser-fixture-only",
                "fixture_phase": fixture_state["fixture_phase"],
                "post_open_metadata_present": fixture_state["post_open_metadata_present"],
            }
            argv = [
                str(py),
                "-m",
                "devpilot_core",
                "api",
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                "8787",
                "--execute",
            ]
        else:
            npm = shutil.which("npm.cmd") or shutil.which("npm")
            if not npm:
                raise RuntimeError("npm.cmd/npm no está disponible en PATH.")
            argv = [npm, "--prefix", "ui/web", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"]

        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if os.name != "nt":
            creationflags = 0
        log_handle = log_path.open("a", encoding="utf-8")
        popen_kwargs: dict[str, Any] = {
            "cwd": str(repo),
            "stdout": log_handle,
            "stderr": subprocess.STDOUT,
            "env": env,
            "shell": False,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = creationflags
        else:
            popen_kwargs["start_new_session"] = True
        proc = subprocess.Popen(argv, **popen_kwargs)

        state: dict[str, Any] = {
            "status": "STARTING",
            "role": role,
            "version": VERSION,
            "started_at": now(),
            "launcher_pid": os.getpid(),
            "child_pid": proc.pid,
            "port": port,
            "ready_url": ready_url,
            "log": str(log_path),
            "token_persisted": False,
            "token_printed": False,
            "three_console_runtime_required": True,
        }
        if workspace_binding is not None:
            state["workspace_binding"] = workspace_binding
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        deadline = time.time() + 60
        ready = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if url_ready(ready_url):
                ready = True
                break
            time.sleep(1)
        if not ready:
            stop_child(proc)
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-3000:] if log_path.is_file() else ""
            raise RuntimeError(f"{role.upper()} no alcanzó readiness. Revise {log_path}. Tail seguro:\n{tail}")

        state["status"] = "PASS"
        state["ready_at"] = now()
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(state, ensure_ascii=False, indent=2))
        if role == "api":
            print(f"INFO — Las peticiones HTTP se registran en {log_path}; esta consola queda silenciosa por diseño para evitar interbloqueos de stdout/stderr.", flush=True)
        verdict("PASS", f"{role.upper()} lista en {ready_url}; mantenga ESTA consola abierta")

        # Keep this dedicated console quiet and alive. Server logs go to evidence.
        while proc.poll() is None:
            time.sleep(1)
        verdict("PASS", f"{role.upper()} finalizada; puede cerrar esta consola")
        return 0
    except KeyboardInterrupt:
        if proc is not None:
            stop_child(proc)
        verdict("PASS", f"{role.upper()} detenida por operador")
        return 0
    except Exception as exc:
        if proc is not None:
            stop_child(proc)
        payload = {
            "status": "BLOCK",
            "script_id": SCRIPT_ID,
            "version": VERSION,
            "role": role,
            "timestamp": now(),
            "message": str(exc),
        }
        try:
            (runtime / f"{role}_console_BLOCK_{int(time.time())}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception:
            pass
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        verdict("BLOCK", f"{role.upper()}: {str(exc).splitlines()[0]}")
        return 20
    finally:
        if log_handle is not None:
            try:
                log_handle.flush()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
