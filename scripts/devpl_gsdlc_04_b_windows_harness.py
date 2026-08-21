from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from devpl_gsdlc_04_b_fixture_state import EXPECTED_BLOB_SHA256, FixtureStateError, inspect_fixture, repair_legacy_marker

HARNESS_ID = "DEVPL-GSDLC-04-B-WINDOWS-HARNESS"
HARNESS_VERSION = "1.0.10"
DEFAULT_EVIDENCE = r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-B"
DEFAULT_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER"
DEFAULT_ARTIFACTS = r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002"
OBSERVATION_VERSION = "1.0.8"
OBSERVATION_FILENAME = "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_8.md"
OBSERVATION_POINTER_FILENAME = "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_CURRENT.json"
BROWSER_MATRIX_BEGIN = "<!-- BEGIN_BROWSER_MATRIX -->"
BROWSER_MATRIX_END = "<!-- END_BROWSER_MATRIX -->"
BROWSER_SUMMARY_BEGIN = "<!-- BEGIN_BROWSER_SUMMARY -->"
BROWSER_SUMMARY_END = "<!-- END_BROWSER_SUMMARY -->"
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "outputs", ".pytest_cache", "__pycache__"}


class HarnessBlock(RuntimeError):
    pass


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


def terminal_status(status: str, message: str) -> None:
    _enable_windows_ansi()
    ok = status.upper() == "PASS"
    color = "\x1b[92m" if ok else "\x1b[91m"
    print(f"{color}{status.upper()} — {message}\x1b[0m", flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], *, cwd: Path, timeout: int = 600, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, shell=False, env=env
    )
    if check and completed.returncode != 0:
        raise HarnessBlock(f"Command failed ({completed.returncode}): {' '.join(argv)}\n{completed.stdout[-8000:]}")
    return completed


def write_evidence(evidence: Path, name: str, payload: dict[str, Any]) -> Path:
    evidence.mkdir(parents=True, exist_ok=True)
    path = evidence / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def provision(repo: Path, evidence: Path) -> dict[str, Any]:
    venv_python = repo / ".venv" / "Scripts" / "python.exe"
    created = False
    if not venv_python.is_file():
        launcher = shutil.which("py")
        if launcher:
            run([launcher, "-3.12", "-m", "venv", str(repo / ".venv")], cwd=repo, timeout=300)
        else:
            run([sys.executable, "-m", "venv", str(repo / ".venv")], cwd=repo, timeout=300)
        created = True
    if not venv_python.is_file():
        raise HarnessBlock("Virtual environment creation did not produce .venv\\Scripts\\python.exe")
    pip = run([str(venv_python), "-m", "pip", "install", "-e", ".[dev]"], cwd=repo, timeout=1200, check=False)
    if pip.returncode != 0:
        raise HarnessBlock(f"Python provisioning BLOCK.\n{pip.stdout[-8000:]}")
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise HarnessBlock("npm is not available in PATH.")
    npm_ci = run([npm, "--prefix", "ui/web", "ci"], cwd=repo, timeout=1200, check=False)
    if npm_ci.returncode != 0:
        raise HarnessBlock(f"npm ci BLOCK.\n{npm_ci.stdout[-8000:]}")
    versions = {
        "python": run([str(venv_python), "--version"], cwd=repo).stdout.strip(),
        "node": run([shutil.which("node") or "node", "--version"], cwd=repo).stdout.strip(),
        "npm": run([npm, "--version"], cwd=repo).stdout.strip(),
        "git": run(["git", "--version"], cwd=repo).stdout.strip(),
    }
    payload = {
        "status": "PASS", "step": "provision", "timestamp": now(), "venv_created": created,
        "network_provisioning_may_have_been_used": True, "runtime_network_authorized": False,
        "versions": versions, "pip_tail": pip.stdout[-3000:], "npm_ci_tail": npm_ci.stdout[-3000:]
    }
    write_evidence(evidence, "08_provisioning_and_tool_versions.json", payload)
    return payload


def _url_ready(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _listener_pid_windows(port: int) -> int | None:
    if os.name != "nt":
        return None
    completed = subprocess.run(["netstat", "-ano", "-p", "tcp"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    if completed.returncode != 0:
        return None
    needle = f":{port}"
    for raw in completed.stdout.splitlines():
        line = raw.strip()
        if "LISTENING" not in line.upper() or needle not in line:
            continue
        parts = line.split()
        if len(parts) >= 5 and parts[-1].isdigit():
            return int(parts[-1])
    return None


def _task_image_windows(pid: int) -> str | None:
    if os.name != "nt":
        return None
    completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    if completed.returncode != 0:
        return None
    line = completed.stdout.strip().splitlines()
    if not line or line[0].startswith("INFO:"):
        return None
    try:
        import csv
        row = next(csv.reader([line[0]]))
        return row[0] if row else None
    except Exception:
        return None


def _runtime_state_files(evidence: Path) -> list[Path]:
    runtime = evidence / "runtime"
    return [runtime / "api_console_state.json", runtime / "ui_console_state.json"]


def _stop_pid(pid: int) -> dict[str, Any]:
    if os.name == "nt":
        first = subprocess.run(["taskkill", "/PID", str(pid), "/T"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        time.sleep(1)
        if first.returncode == 0:
            return {"pid": pid, "stopped": True, "forced": False, "output": first.stdout[-2000:]}
        forced = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        if forced.returncode in (0, 128):
            return {"pid": pid, "stopped": True, "forced": forced.returncode == 0, "output": forced.stdout[-2000:]}
        return {"pid": pid, "stopped": False, "forced": True, "output": forced.stdout[-2000:]}
    try:
        os.kill(pid, signal.SIGTERM)
        return {"pid": pid, "stopped": True, "forced": False}
    except ProcessLookupError:
        return {"pid": pid, "stopped": True, "forced": False, "already_stopped": True}


def _read_runtime_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HarnessBlock(f"Invalid runtime state JSON: {path}")


def runtime_status(evidence: Path, fixture: Path) -> dict[str, Any]:
    api_port = _port_open("127.0.0.1", 8787)
    ui_port = _port_open("127.0.0.1", 5173)
    api_ready = _url_ready("http://127.0.0.1:8787/api/v1/health") if api_port else False
    ui_ready = _url_ready("http://127.0.0.1:5173/") if ui_port else False
    api_state = _read_runtime_state(evidence / "runtime" / "api_console_state.json")
    ui_state = _read_runtime_state(evidence / "runtime" / "ui_console_state.json")
    binding = api_state.get("workspace_binding") if isinstance(api_state.get("workspace_binding"), dict) else {}
    expected = str(fixture.resolve())
    fixture_binding_ready = (
        api_state.get("status") == "PASS"
        and api_state.get("version") == HARNESS_VERSION
        and ui_state.get("status") == "PASS"
        and ui_state.get("version") == HARNESS_VERSION
        and binding.get("allowed_workspace_root") == expected
        and binding.get("active_workspace_root") == expected
        and binding.get("registry_env_cleared") is True
        and binding.get("scope") == "gsdlc-04-b-browser-fixture-only"
        and binding.get("fixture_phase") == "POST_OPEN_PASS"
        and binding.get("post_open_metadata_present") is True
    )
    payload = {
        "status": "PASS" if api_ready and ui_ready and fixture_binding_ready else "BLOCK",
        "step": "runtime-status",
        "timestamp": now(),
        "api_port_open": api_port,
        "ui_port_open": ui_port,
        "api_ready": api_ready,
        "ui_ready": ui_ready,
        "api_url": "http://127.0.0.1:8787/api/v1/health",
        "ui_url": "http://127.0.0.1:5173/",
        "three_console_runtime_required": True,
        "fixture_binding_ready": fixture_binding_ready,
        "fixture": expected,
        "api_runtime_version": api_state.get("version"),
        "ui_runtime_version": ui_state.get("version"),
        "workspace_binding": binding,
        "fixture_phase": binding.get("fixture_phase"),
        "post_open_metadata_present": binding.get("post_open_metadata_present"),
    }
    write_evidence(evidence, "runtime/runtime_status_latest.json", payload)
    if payload["status"] != "PASS":
        raise HarnessBlock(
            f"Runtime status BLOCK: api_ready={api_ready} ui_ready={ui_ready} fixture_binding_ready={fixture_binding_ready}. "
            "Start API with the v1.0.10 Console 2 command and UI with the v1.0.10 Console 3 command, then retry from Console 1."
        )
    return payload


def fixture_binding_precheck(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    if not fixture.is_dir():
        raise HarnessBlock(f"Browser fixture missing: {fixture}")
    if "inventory-sales-local" in str(fixture).lower() or "devpilot_workspaces" in str(fixture).lower():
        raise HarnessBlock("Refusing to probe the real pilot workspace.")
    venv_python = repo / ".venv" / "Scripts" / "python.exe"
    if not venv_python.is_file():
        raise HarnessBlock("Missing repo .venv Python; run provision first.")
    probe = repo / "scripts" / "devpl_gsdlc_04_b_fixture_binding_probe.py"
    if not probe.is_file():
        raise HarnessBlock(f"Fixture binding probe missing: {probe}")
    completed = run(
        [str(venv_python), str(probe), "--repo-root", str(repo), "--browser-fixture-root", str(fixture)],
        cwd=repo,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessBlock(f"Fixture binding precheck BLOCK.\n{completed.stdout[-8000:]}")
    payload = {
        "status": "PASS",
        "step": "fixture-binding-precheck",
        "timestamp": now(),
        "fixture": str(fixture),
        "probe_returncode": completed.returncode,
        "probe_output_tail": completed.stdout[-6000:],
        "pathguard_and_dry_run_prechecked": True,
        "ui_active_workspace_prechecked": True,
        "pilot_workspace_accessed": False,
    }
    write_evidence(evidence, "11b_fixture_binding_precheck.json", payload)
    return payload


def runtime_stop(evidence: Path) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for state_path in _runtime_state_files(evidence):
        if not state_path.is_file():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise HarnessBlock(f"Invalid runtime state file: {state_path}. Preserve it and review before continuing.")
        role = str(state.get("role") or "")
        expected_port = 8787 if role == "api" else 5173 if role == "ui" else 0
        child_pid = int(state.get("child_pid") or 0)
        launcher_pid = int(state.get("launcher_pid") or 0)
        port_open = bool(expected_port and _port_open("127.0.0.1", expected_port))
        launcher_image = (_task_image_windows(launcher_pid) or "").lower() if launcher_pid else ""
        launcher_alive = launcher_image in {"python.exe", "pythonw.exe", "py.exe", "python"}
        if not port_open:
            results.append({"state": str(state_path), "role": role, "child_pid": child_pid, "stopped": True, "already_stopped": True, "reason": "expected-port-already-free"})
            continue
        if not launcher_alive:
            raise HarnessBlock(
                f"Runtime stop refuses stale PID state for role={role}: expected port {expected_port} is open but launcher PID {launcher_pid} is not the dedicated Python launcher. "
                "Do not kill by process name; preserve evidence."
            )
        if child_pid <= 0:
            raise HarnessBlock(f"Runtime state for role={role} has no valid child_pid; refusing unsafe termination.")
        results.append({"state": str(state_path), "role": role, "launcher_pid": launcher_pid, "launcher_image": launcher_image, **_stop_pid(child_pid)})
    time.sleep(1)
    api_open = _port_open("127.0.0.1", 8787)
    ui_open = _port_open("127.0.0.1", 5173)
    if api_open or ui_open:
        raise HarnessBlock(f"Runtime stop BLOCK; target ports remain occupied. api_8787={api_open} ui_5173={ui_open}. Use runtime-recover only for the documented v1.0.3 orphan case; do not kill unknown processes.")
    payload = {"status": "PASS", "step": "runtime-stop", "timestamp": now(), "results": results, "ports_free": True, "stale_pid_kill_allowed": False}
    write_evidence(evidence, f"runtime/runtime_stop_{int(time.time())}.json", payload)
    return payload


def browser_recovery_008(fixture: Path, evidence: Path) -> dict[str, Any]:
    """Recover the exact v1.0.7 browser state without reset/rebase/clean.

    The current Windows run may still have API/UI alive and the disposable fixture
    may be dirty only because v1.0.7 wrote its operator-owned marker after the
    baseline commit. Stop only the dedicated runtime trees, then remove only that
    validated legacy marker. Any other dirty state remains fail-closed.
    """
    stop = runtime_stop(evidence)
    try:
        repaired = repair_legacy_marker(fixture, evidence_dir=evidence)
        state = inspect_fixture(fixture)
    except FixtureStateError as exc:
        raise HarnessBlock(str(exc)) from exc
    if not state.get("git_clean"):
        raise HarnessBlock(f"Fixture sigue dirty después de recovery-008: {state.get('git_status_entries')}")
    payload = {
        "status": "PASS",
        "step": "browser-recovery-008",
        "timestamp": now(),
        "runtime_stop": stop,
        "fixture_repair": repaired,
        "fixture_git_clean": True,
        "prior_approval_reusable": False,
        "restart_project_entry_from_new_dry_run_required": True,
        "manual_observations_preserved": True,
        "pilot_workspace_accessed": False,
        "rollback_required": False,
    }
    write_evidence(evidence, "10d_browser_recovery_008.json", payload)
    return payload


def _draft_restart_precheck(repo: Path, fixture: Path) -> dict[str, Any]:
    """Prove that B2 created an active runtime draft before B3 restart.

    The store is runtime state under the platform repo, not fixture source. Read
    only identity/shape metadata; do not copy draft content into evidence.
    """
    draft_root = repo / "outputs" / "drafts" / "gsdlc_04_b"
    if not draft_root.is_dir():
        raise HarnessBlock("B3 restart precheck: no existe outputs/drafts/gsdlc_04_b; el autosave B2 no dejó persistencia runtime verificable.")
    source_sha = sha256_file(fixture / "docs" / "manual_authoring.md")
    matches: list[dict[str, Any]] = []
    for path in sorted(draft_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("schema_id") != "devpilot.gsdlc04b.artifact_draft_store_record.v1":
            continue
        if payload.get("relative_path") != "docs/manual_authoring.md":
            continue
        if payload.get("workspace_id") != "DEVPL_GSDLC_04_B_BROWSER":
            continue
        revisions = payload.get("revisions")
        if not isinstance(revisions, list) or not revisions:
            raise HarnessBlock("B3 restart precheck: el draft store Markdown existe pero no contiene revisiones.")
        current = str(payload.get("current_revision_sha256") or "")
        if payload.get("active") is not True or not current:
            raise HarnessBlock("B3 restart precheck: el draft Markdown no está activo antes del restart.")
        if payload.get("source_preimage_sha256") != source_sha:
            raise HarnessBlock("B3 restart precheck: el draft store está ligado a un preimage source distinto al fixture actual.")
        if payload.get("source_mutations_performed") is not False:
            raise HarnessBlock("B3 restart precheck: el draft store no prueba source_mutations_performed=false.")
        if not any(isinstance(r, dict) and r.get("revision_sha256") == current for r in revisions):
            raise HarnessBlock("B3 restart precheck: current_revision_sha256 no referencia una revisión persistida.")
        matches.append({
            "store_path": str(path.relative_to(repo)).replace("\\", "/"),
            "workspace_id": payload.get("workspace_id"),
            "document_id": payload.get("document_id"),
            "relative_path": payload.get("relative_path"),
            "active": True,
            "revisions_total": len(revisions),
            "current_revision_sha256": current,
            "source_preimage_sha256": payload.get("source_preimage_sha256"),
            "source_mutations_performed": False,
        })
    if len(matches) != 1:
        raise HarnessBlock(f"B3 restart precheck: se esperaba exactamente un draft activo de manual_authoring.md para el fixture; encontrados={len(matches)}.")
    return matches[0]


def browser_resume_009(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    """Resume the already-started v1.0.8 browser run exactly at B3.

    This checkpoint is read-only. It distinguishes the valid POST_OPEN_PASS
    metadata created by a successful OPEN_EXISTING from invalid partial residue,
    preserves B0/B1/B2 evidence, and proves the runtime draft exists before the
    server restart is attempted.
    """
    if _port_open("127.0.0.1", 8787) or _port_open("127.0.0.1", 5173):
        raise HarnessBlock("browser-resume-009 exige 8787/5173 libres. El cierre B3 debe haberse completado antes de reanudar.")
    try:
        state = inspect_fixture(fixture, phase_policy="post-open-pass")
    except FixtureStateError as exc:
        raise HarnessBlock(str(exc)) from exc
    if not state.get("git_clean"):
        raise HarnessBlock(f"Fixture POST_OPEN_PASS está Git-dirty: {state.get('git_status_entries')}")

    browser = evidence / "browser"
    required = [
        "00_project_entry_fixture_open.png",
        "01_editor_markdown_loaded.png",
        "02_autosave_saved.png",
    ]
    missing = [name for name in required if not (browser / name).is_file() or (browser / name).stat().st_size < 1000]
    if missing:
        raise HarnessBlock(f"No se puede reanudar en B3; faltan capturas previas válidas: {missing}")

    during_path = evidence / "12_markdown_source_hash_during_draft.json"
    if not during_path.is_file():
        raise HarnessBlock("No se puede reanudar B3; falta 12_markdown_source_hash_during_draft.json.")
    try:
        during = json.loads(during_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HarnessBlock("12_markdown_source_hash_during_draft.json es inválido.") from exc
    if during.get("status") != "PASS" or during.get("markdown_source_unchanged") is not True:
        raise HarnessBlock("La evidencia B2 no demuestra que el source Markdown permaneció sin cambios.")

    observation = _current_observation_path(evidence)
    if not observation.is_file():
        raise HarnessBlock("Falta el archivo de observaciones del browser run ya iniciado.")
    draft = _draft_restart_precheck(repo, fixture)
    payload = {
        "status": "PASS",
        "step": "browser-resume-009",
        "timestamp": now(),
        "fixture_phase": state.get("fixture_phase"),
        "fixture_git_clean": True,
        "post_open_metadata": {
            "bootstrap_execution": state.get("bootstrap_execution"),
            "workspace_registration": state.get("workspace_registration"),
        },
        "preserved_browser_evidence": required,
        "observation_file": str(observation),
        "b2_source_unchanged": True,
        "draft_restart_precheck": draft,
        "resume_from": "B3-restart-runtime",
        "repeat_open_existing": False,
        "repeat_b1_b2": False,
        "source_mutations_performed": False,
        "pilot_workspace_accessed": False,
    }
    write_evidence(evidence, "14_browser_resume_009.json", payload)
    return payload


def runtime_recover(evidence: Path) -> dict[str, Any]:
    """Recover the known v1.0.3 failed joint-start orphan safely.

    v1.0.3 verified both ports were free immediately before starting API/UI. Its
    BLOCK evidence proves api_ready=False/ui_ready=True and api.log proves the API
    exited before bind because DEVPILOT_API_TOKEN was unset. Therefore a Node
    listener newly occupying 5173 with the expected Vite log can be attributed to
    that failed harness run. Any other listener remains fail-closed.
    """
    runtime = evidence / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    # If v1.0.4 launcher state already exists, use the guarded PID-first stop.
    if any(path.is_file() for path in _runtime_state_files(evidence)) and (_port_open("127.0.0.1", 8787) or _port_open("127.0.0.1", 5173)):
        runtime_stop(evidence)
    time.sleep(1)

    api_open = _port_open("127.0.0.1", 8787)
    ui_open = _port_open("127.0.0.1", 5173)
    actions: list[dict[str, Any]] = []
    if api_open:
        raise HarnessBlock("Port 8787 is occupied but v1.0.3 evidence proves its API never became ready. Refusing to kill an unknown listener.")
    if ui_open:
        block_files = sorted(evidence.glob("harness_runtime-start_BLOCK_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        api_log = runtime / "api.log"
        ui_log = runtime / "ui.log"
        proven = False
        if block_files and api_log.is_file() and ui_log.is_file():
            try:
                block = json.loads(block_files[0].read_text(encoding="utf-8"))
                msg = str(block.get("message", ""))
                api_text = api_log.read_text(encoding="utf-8", errors="replace")
                ui_text = ui_log.read_text(encoding="utf-8", errors="replace")
                proven = (
                    "api_ready=False ui_ready=True" in msg
                    and "API_EXECUTE_REQUIRES_EXPLICIT_TOKEN_BLOCK" in api_text
                    and "http://127.0.0.1:" in ui_text and "5173" in ui_text and "VITE" in ui_text.upper()
                )
            except Exception:
                proven = False
        if not proven:
            raise HarnessBlock("Port 5173 is occupied but evidence is insufficient to attribute it to the known v1.0.3 orphan. Refusing unsafe termination.")
        pid = _listener_pid_windows(5173)
        if not pid:
            raise HarnessBlock("Could not identify the PID listening on 5173; refusing unsafe termination.")
        image = (_task_image_windows(pid) or "").lower()
        if image not in {"node.exe", "node"}:
            raise HarnessBlock(f"Listener 5173 is PID {pid} image={image!r}, not the expected Node/Vite process. Refusing termination.")
        actions.append({"reason": "known-v1.0.3-vite-orphan", "image": image, **_stop_pid(pid)})
        time.sleep(1)
    if _port_open("127.0.0.1", 8787) or _port_open("127.0.0.1", 5173):
        raise HarnessBlock("Runtime recovery did not free both target ports.")
    payload = {"status": "PASS", "step": "runtime-recover", "timestamp": now(), "actions": actions, "ports_free": True, "unsafe_process_name_kill_used": False}
    write_evidence(evidence, f"runtime/runtime_recover_{int(time.time())}.json", payload)
    return payload

def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _git_content_equivalent(fixture: Path, rel: str) -> bool:
    # Git, not the physical Windows EOL representation, is the authority.
    # --quiet returns 0 when the worktree is semantically equivalent to HEAD,
    # including an LF/CRLF checkout representation accepted by Git attributes/config.
    unstaged = subprocess.run(
        ["git", "-C", str(fixture), "diff", "--quiet", "--", rel],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=60,
    )
    staged = subprocess.run(
        ["git", "-C", str(fixture), "diff", "--cached", "--quiet", "--", rel],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=60,
    )
    return unstaged.returncode == 0 and staged.returncode == 0


def _fixture_source_state(fixture: Path) -> dict[str, Any]:
    rels = ["docs/manual_authoring.md", "docs/manual_authoring.json"]
    state: dict[str, Any] = {}
    for rel in rels:
        path = fixture / rel
        if not path.is_file():
            raise HarnessBlock(f"Fixture source missing: {path}")
        raw_sha = sha256_file(path)
        canonical_sha = _canonical_lf_sha256(path)
        expected_blob = EXPECTED_BLOB_SHA256[rel]
        git_equivalent = _git_content_equivalent(fixture, rel)
        state[rel] = {
            "raw_sha256": raw_sha,
            "canonical_lf_sha256": canonical_sha,
            "expected_git_blob_sha256": expected_blob,
            "canonical_matches_git_blob": canonical_sha == expected_blob,
            "git_content_equivalent_to_head": git_equivalent,
            "eol_only_representation_difference": raw_sha != expected_blob and canonical_sha == expected_blob and git_equivalent,
            "restored_equivalent": canonical_sha == expected_blob and git_equivalent,
        }
    return state


def fixture_hash(fixture: Path, evidence: Path, label: str) -> dict[str, Any]:
    state = _fixture_source_state(fixture)
    raw_hashes = {rel: item["raw_sha256"] for rel, item in state.items()}
    canonical_hashes = {rel: item["canonical_lf_sha256"] for rel, item in state.items()}
    baseline_path = evidence / "11_fixture_source_hashes_before.json"

    if label == "before":
        ok = all(item["restored_equivalent"] for item in state.values())
        payload = {
            "status": "PASS" if ok else "BLOCK",
            "step": "fixture-hash",
            "label": label,
            "timestamp": now(),
            "hashes": raw_hashes,
            "canonical_lf_hashes": canonical_hashes,
            "authority": "git-blob+canonical-lf; raw SHA is diagnostic only on Windows",
            "source_state": state,
        }
        write_evidence(evidence, baseline_path.name, payload)
        if not ok:
            raise HarnessBlock(f"Fixture baseline is not equivalent to committed Git blobs: {state}")
        return payload

    if not baseline_path.is_file():
        raise HarnessBlock("Baseline fixture hashes are missing; run label=before first.")
    before = json.loads(baseline_path.read_text(encoding="utf-8"))

    if label == "during":
        md = state["docs/manual_authoring.md"]
        same = bool(md["restored_equivalent"])
        payload = {
            "status": "PASS" if same else "BLOCK",
            "step": "fixture-hash",
            "label": label,
            "timestamp": now(),
            "hashes": raw_hashes,
            "canonical_lf_hashes": canonical_hashes,
            "baseline_raw_hashes": before.get("hashes", {}),
            "markdown_source_unchanged": same,
            "authority": "git-blob+canonical-lf",
            "source_state": state,
        }
        write_evidence(evidence, "12_markdown_source_hash_during_draft.json", payload)
        if not same:
            raise HarnessBlock("Draft save/autosave changed approved Markdown source.")
        return payload

    if label == "after":
        same = all(item["restored_equivalent"] for item in state.values())
        eol_only = [rel for rel, item in state.items() if item["eol_only_representation_difference"]]
        payload = {
            "status": "PASS" if same else "BLOCK",
            "step": "fixture-hash",
            "label": label,
            "timestamp": now(),
            "hashes": raw_hashes,
            "canonical_lf_hashes": canonical_hashes,
            "baseline_raw_hashes": before.get("hashes", {}),
            "all_fixture_sources_restored": same,
            "authority": "git-blob+canonical-lf; physical LF/CRLF bytes are diagnostic only",
            "eol_only_representation_paths": eol_only,
            "source_state": state,
        }
        write_evidence(evidence, "13_fixture_source_hashes_after.json", payload)
        if not same:
            raise HarnessBlock(f"Fixture source content does not match committed Git authority after restore: {state}")
        return payload

    raise HarnessBlock("label must be before, during or after.")


def fixture_restore(fixture: Path, evidence: Path) -> dict[str, Any]:
    if "inventory-sales-local" in str(fixture).lower() or "DevPilot_Workspaces" in str(fixture):
        raise HarnessBlock("Refusing restore outside the disposable browser fixture.")
    result = run(["git", "-C", str(fixture), "restore", "--", "docs/manual_authoring.md"], cwd=fixture, timeout=60, check=False)
    if result.returncode != 0:
        raise HarnessBlock(f"Fixture restore BLOCK.\n{result.stdout[-4000:]}")
    state = _fixture_source_state(fixture)
    md = state["docs/manual_authoring.md"]
    if not md["restored_equivalent"]:
        raise HarnessBlock(f"Fixture restore completed but Markdown is not equivalent to committed Git blob: {md}")
    payload = {
        "status": "PASS",
        "step": "fixture-restore",
        "timestamp": now(),
        "path": "docs/manual_authoring.md",
        "authority": "git-blob+canonical-lf",
        "source_state": md,
    }
    write_evidence(evidence, "12b_fixture_restore.json", payload)
    return payload


def _section_between(text: str, begin: str, end: str) -> str:
    if begin not in text or end not in text:
        raise HarnessBlock(f"Observation contract markers missing: {begin} / {end}")
    body = text.split(begin, 1)[1].split(end, 1)[0]
    return body.strip("\n")


def _current_observation_path(evidence: Path) -> Path:
    pointer = evidence / OBSERVATION_POINTER_FILENAME
    if pointer.is_file():
        try:
            payload = json.loads(pointer.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HarnessBlock(f"Invalid observation pointer JSON: {pointer}") from exc
        name = str(payload.get("observation_filename") or "")
        if name != OBSERVATION_FILENAME:
            raise HarnessBlock(
                f"Observation pointer version mismatch: expected {OBSERVATION_FILENAME}, got {name!r}. "
                "Run browser-preflight again; older observations are preserved and must not be reused as current evidence."
            )
    return evidence / OBSERVATION_FILENAME


def prepare_observations(repo: Path, evidence: Path) -> dict[str, Any]:
    """Create/reuse a version-isolated observation file without inspecting older runs.

    Previous guide observation files are forensic evidence and are never parsed to
    decide whether the current file may be created. This removes the fragile
    heuristic that previously mistook instructional PASS examples for manual data.
    """
    browser = evidence / "browser"
    browser.mkdir(parents=True, exist_ok=True)
    src = repo / "docs" / "audits" / "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_TEMPLATE.md"
    dst = evidence / OBSERVATION_FILENAME
    if not src.is_file():
        raise HarnessBlock(f"Observation template missing: {src}")
    template_text = src.read_text(encoding="utf-8")
    for marker in (BROWSER_MATRIX_BEGIN, BROWSER_MATRIX_END, BROWSER_SUMMARY_BEGIN, BROWSER_SUMMARY_END):
        if marker not in template_text:
            raise HarnessBlock(f"Observation template missing contract marker: {marker}")

    action = "created-current-version"
    if dst.exists():
        # Never overwrite a current-version file: it may already contain manual data.
        action = "reused-current-version-preserved"
    else:
        shutil.copy2(src, dst)

    legacy = sorted(
        p.name for p in evidence.glob("DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS*.md")
        if p.name != OBSERVATION_FILENAME
    )
    pointer_payload = {
        "status": "PASS",
        "observation_version": OBSERVATION_VERSION,
        "observation_filename": OBSERVATION_FILENAME,
        "observation_file": str(dst),
        "template_sha256": sha256_file(src),
        "legacy_observations_preserved": legacy,
        "automatic_overwrite_performed": False,
        "updated_at": now(),
    }
    write_evidence(evidence, OBSERVATION_POINTER_FILENAME, pointer_payload)
    payload = {
        "status": "PASS",
        "step": "prepare-observations",
        "timestamp": now(),
        "observation_file": str(dst),
        "browser_dir": str(browser),
        "template_action": action,
        "legacy_observations_preserved": legacy,
        "manual_results_overwritten": False,
    }
    write_evidence(evidence, "10_browser_observation_workspace_v1_0_8.json", payload)
    return payload


def browser_preflight(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    """Single pre-browser gate: ports free + observations + hashes + fixture binding."""
    if _port_open("127.0.0.1", 8787) or _port_open("127.0.0.1", 5173):
        raise HarnessBlock("Browser preflight requires API/UI stopped and ports 8787/5173 free. Run runtime-stop first.")
    observations = prepare_observations(repo, evidence)
    hashes = fixture_hash(fixture, evidence, "before")
    binding = fixture_binding_precheck(repo, fixture, evidence)
    payload = {
        "status": "PASS",
        "step": "browser-preflight",
        "timestamp": now(),
        "ports_free": True,
        "observations": observations,
        "fixture_hash_before": hashes,
        "fixture_binding": binding,
        "browser_runtime_may_start": True,
        "pilot_workspace_accessed": False,
    }
    write_evidence(evidence, "10c_browser_preflight_v1_0_8.json", payload)
    return payload


def browser_evidence_validate(evidence: Path) -> dict[str, Any]:
    obs = _current_observation_path(evidence)
    if not obs.is_file():
        raise HarnessBlock(f"Current manual browser observations file is missing: {obs}")
    text = obs.read_text(encoding="utf-8")
    matrix = _section_between(text, BROWSER_MATRIX_BEGIN, BROWSER_MATRIX_END)
    summary = _section_between(text, BROWSER_SUMMARY_BEGIN, BROWSER_SUMMARY_END)

    expected_cases = [
        "Open Existing / PathGuard fixture",
        "Editor Markdown carga",
        "Autosave",
        "Recovery tras restart",
        "Version history",
        "Discard + recover",
        "JSON hints",
        "Conflict/stale preimage",
        "Project route guard",
        "Source no cambia al guardar draft",
        "Sesión/RBAC",
    ]
    expected_png = [
        "00_project_entry_fixture_open.png",
        "01_editor_markdown_loaded.png", "02_autosave_saved.png", "03_restart_recovery.png",
        "04_version_history.png", "05_discard_recover.png", "06_json_hint.png",
        "07_conflict_banner.png", "08_project_guard.png",
    ]
    missing_png = [name for name in expected_png if not (evidence / "browser" / name).is_file()]

    result_map: dict[str, str] = {}
    for line in matrix.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "Resultado PASS/BLOCK" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4 and cells[0]:
            result_map[cells[0]] = cells[1]
    missing_cases = [case for case in expected_cases if case not in result_map]
    nonpass = [(case, result_map.get(case, "")) for case in expected_cases if result_map.get(case, "").upper() != "PASS"]

    summary_values: dict[str, str] = {}
    expected_summary = {
        "browser_acceptance": "PASS",
        "S0_open": "0",
        "S1_open": "0",
        "secrets_exposed": "false",
        "network_runtime_used": "false",
        "external_api_used": "false",
        "pilot_workspace_accessed": "false",
    }
    for raw in summary.splitlines():
        stripped = raw.strip()
        for key in expected_summary:
            prefix = f"- `{key}`:"
            if stripped.startswith(prefix):
                summary_values[key] = stripped[len(prefix):].strip().strip("`")
    invalid_summary = [
        key for key, expected in expected_summary.items()
        if summary_values.get(key, "").lower() != expected.lower()
    ]
    blocked = bool(missing_png or missing_cases or nonpass or invalid_summary)
    payload = {
        "status": "BLOCK" if blocked else "PASS",
        "step": "browser-evidence-validate",
        "timestamp": now(),
        "observation_file": str(obs),
        "observation_version": OBSERVATION_VERSION,
        "rows_found": len(result_map),
        "missing_cases": missing_cases,
        "nonpass_rows": nonpass,
        "missing_screenshots": missing_png,
        "summary_values": summary_values,
        "invalid_summary_fields": invalid_summary,
        "instructional_examples_parsed": False,
    }
    write_evidence(evidence, "DEVPL_GSDLC_04_B_BROWSER_ACCEPTANCE_VALIDATION.json", payload)
    if blocked:
        raise HarnessBlock(f"Browser evidence incomplete/BLOCK: {payload}")
    return payload

def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "SOURCE_DELTA_MANIFEST.json"
    if not path.is_file():
        raise HarnessBlock(f"Missing SOURCE_DELTA_MANIFEST: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _status_path(line: str) -> str:
    if len(line) < 4:
        return line
    raw = line[3:]
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.replace("\\", "/")


def git_commit(repo: Path, package_root: Path, evidence: Path, message: str) -> dict[str, Any]:
    validation = evidence / "DEVPL_GSDLC_04_B_BROWSER_ACCEPTANCE_VALIDATION.json"
    if not validation.is_file() or json.loads(validation.read_text(encoding="utf-8")).get("status") != "PASS":
        raise HarnessBlock("Browser evidence validation must PASS before commit.")
    manifest = load_manifest(package_root)
    allowed = {str(item["path"]).replace("\\", "/") for item in manifest.get("files", [])}
    status_lines = run(["git", "status", "--porcelain=v1"], cwd=repo).stdout.splitlines()
    dirty_paths = sorted({_status_path(line) for line in status_lines if line.strip()})
    unexpected = [line for line in status_lines if _status_path(line) not in allowed]
    if unexpected:
        raise HarnessBlock(f"Unexpected Git paths before staging: {unexpected[:30]}")
    if not dirty_paths:
        raise HarnessBlock("No source delta is dirty; refusing to create an empty GSDLC-04-B commit.")
    diff_check = run(["git", "-c", "core.safecrlf=false", "diff", "--check", "--no-ext-diff"], cwd=repo, check=False)
    if diff_check.returncode != 0:
        raise HarnessBlock(f"git diff --check BLOCK.\n{diff_check.stdout[-4000:]}")
    run(["git", "add", "-A", "--", *dirty_paths], cwd=repo, timeout=300)
    staged = sorted(run(["git", "diff", "--cached", "--name-only"], cwd=repo).stdout.splitlines())
    if staged != dirty_paths:
        raise HarnessBlock(f"Staged path set does not match the actual declared dirty surface. expected={len(dirty_paths)} staged={len(staged)}")
    commit = run(["git", "commit", "-m", message], cwd=repo, timeout=300, check=False)
    if commit.returncode != 0:
        raise HarnessBlock(f"Git commit BLOCK.\n{commit.stdout[-6000:]}")
    head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    clean = run(["git", "status", "--porcelain=v1"], cwd=repo).stdout.strip() == ""
    if not clean:
        raise HarnessBlock("Commit completed but worktree is not clean.")
    payload = {"status": "PASS", "step": "git-commit", "timestamp": now(), "commit": head, "message": message, "staged_paths_total": len(staged), "staged_paths": staged, "worktree_clean": True}
    write_evidence(evidence, "19_git_commit.json", payload)
    return payload


def package_evidence(evidence: Path, artifacts: Path) -> dict[str, Any]:
    output_dir = artifacts / "evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "DEVPL_GSDLC_04_B_WINDOWS_EVIDENCE_v1_0_10.zip"
    if output.exists():
        raise HarnessBlock(f"Evidence ZIP already exists; refusing overwrite: {output}")
    forbidden_names = ("auth.db", "devpilot.db", ".env")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(evidence.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(evidence)
            lower = rel.as_posix().lower()
            if any(name in lower for name in forbidden_names) or "outputs/drafts" in lower:
                continue
            zf.write(path, rel.as_posix())
    with zipfile.ZipFile(output) as zf:
        bad = zf.testzip()
        if bad:
            raise HarnessBlock(f"Evidence ZIP CRC BLOCK: {bad}")
    digest = sha256_file(output)
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"status": "PASS", "step": "package-evidence", "timestamp": now(), "evidence_zip": str(output), "sha256": digest, "sidecar": str(sidecar)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GSDLC-04-B Windows harness with colored final PASS/BLOCK line.")
    parser.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    parser.add_argument("--package-root", default=None)
    parser.add_argument("--evidence-dir", default=DEFAULT_EVIDENCE)
    parser.add_argument("--browser-fixture-root", default=DEFAULT_FIXTURE)
    parser.add_argument("--artifacts-root", default=DEFAULT_ARTIFACTS)
    parser.add_argument("--step", required=True, choices=[
        "provision", "runtime-recover", "runtime-status", "runtime-stop", "browser-recovery-008", "browser-resume-009", "fixture-hash", "fixture-restore",
        "fixture-binding-precheck", "prepare-observations", "browser-preflight", "browser-evidence-validate", "git-commit", "package-evidence"
    ])
    parser.add_argument("--label", choices=["before", "during", "after"])
    parser.add_argument("--commit-message", default="feat(gsdlc-04-b): add governed manual artifact authoring")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    fixture = Path(args.browser_fixture_root).resolve()
    artifacts = Path(args.artifacts_root).resolve()
    package_root = Path(args.package_root).resolve() if args.package_root else None
    try:
        if args.step != "package-evidence" and not repo.is_dir():
            raise HarnessBlock(f"Repo root not found: {repo}")
        if args.step == "provision":
            payload = provision(repo, evidence)
        elif args.step == "runtime-recover":
            payload = runtime_recover(evidence)
        elif args.step == "runtime-status":
            payload = runtime_status(evidence, fixture)
        elif args.step == "runtime-stop":
            payload = runtime_stop(evidence)
        elif args.step == "browser-recovery-008":
            payload = browser_recovery_008(fixture, evidence)
        elif args.step == "browser-resume-009":
            payload = browser_resume_009(repo, fixture, evidence)
        elif args.step == "fixture-hash":
            if not args.label:
                raise HarnessBlock("--label before|during|after is required for fixture-hash.")
            payload = fixture_hash(fixture, evidence, args.label)
        elif args.step == "fixture-restore":
            payload = fixture_restore(fixture, evidence)
        elif args.step == "fixture-binding-precheck":
            payload = fixture_binding_precheck(repo, fixture, evidence)
        elif args.step == "prepare-observations":
            payload = prepare_observations(repo, evidence)
        elif args.step == "browser-preflight":
            payload = browser_preflight(repo, fixture, evidence)
        elif args.step == "browser-evidence-validate":
            payload = browser_evidence_validate(evidence)
        elif args.step == "git-commit":
            if package_root is None:
                raise HarnessBlock("--package-root is required for git-commit.")
            payload = git_commit(repo, package_root, evidence, args.commit_message)
        elif args.step == "package-evidence":
            payload = package_evidence(evidence, artifacts)
        else:
            raise HarnessBlock("Unknown step.")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        terminal_status("PASS", f"{args.step} completado")
        return 0
    except (HarnessBlock, subprocess.TimeoutExpired) as exc:
        payload = {"status": "BLOCK", "harness_id": HARNESS_ID, "version": HARNESS_VERSION, "step": args.step, "timestamp": now(), "message": str(exc)}
        try:
            write_evidence(evidence, f"harness_{args.step}_BLOCK_{int(time.time())}.json", payload)
        except Exception:
            pass
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        terminal_status("BLOCK", f"{args.step}: {str(exc).splitlines()[0]}")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
