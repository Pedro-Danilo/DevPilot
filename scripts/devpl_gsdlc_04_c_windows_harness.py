from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS_ID = "DEVPL-GSDLC-04-C-WINDOWS-HARNESS"
VERSION = "1.0.0"
DEFAULT_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER"
DEFAULT_INPUTS = r"D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-C\browser_inputs"
OBS_NAME = "DEVPL_GSDLC_04_C_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md"
REQUIRED_SCREENSHOTS = [
    "00_project_entry_fixture_open.png",
    "01_paste_preview.png",
    "02_paste_draft_provenance.png",
    "03_upload_draft_provenance.png",
    "04_import_json_provenance.png",
    "05_secret_warning_redacted.png",
    "06_project_guard.png",
]
EXPECTED_CASES = [
    "Open Existing / project context",
    "PASTE preview",
    "PASTE DRAFT + provenance",
    "UPLOAD Markdown DRAFT",
    "IMPORT JSON DRAFT",
    "Original/normalized hashes + provenance",
    "Secret warning/redaction",
    "Project route guard",
    "Source/workspace files unchanged",
    "Sesión/RBAC",
]
SUMMARY_EXPECTED = {
    "browser_acceptance": "PASS",
    "S0_open": "0",
    "S1_open": "0",
    "secrets_exposed": "false",
    "network_runtime_used": "false",
    "external_api_used": "false",
    "pilot_workspace_accessed": "false",
}


class HarnessBlock(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        m = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(m)):
            k.SetConsoleMode(h, m.value | 0x0004)
    except Exception:
        pass


def verdict(status: str, message: str) -> None:
    _ansi()
    color = "\x1b[92m" if status == "PASS" else "\x1b[91m"
    print(f"{color}{status} — {message}\x1b[0m", flush=True)


def run(argv: list[str], *, cwd: Path, timeout: int = 120, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False, env=env)
    if check and cp.returncode != 0:
        raise HarnessBlock(f"Command failed ({cp.returncode}): {' '.join(argv)}\n{cp.stdout[-6000:]}")
    return cp


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def write_evidence(evidence: Path, name: str, payload: dict[str, Any]) -> Path:
    path = evidence / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stem, suffix, i = path.stem, path.suffix, 2
        while (path.parent / f"{stem}_{i:02d}{suffix}").exists():
            i += 1
        path = path.parent / f"{stem}_{i:02d}{suffix}"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, timeout=60, check=check)


def git_status(repo: Path) -> list[str]:
    cp = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
    if cp.returncode != 0:
        raise HarnessBlock(cp.stderr.decode(errors="replace")[-2500:])
    return [x.decode("utf-8", errors="replace") for x in cp.stdout.split(b"\0") if x]


def fixture_paths(fixture: Path) -> dict[str, Path]:
    return {
        ".devpilot/project.yaml": fixture / ".devpilot" / "project.yaml",
        "docs/baseline.md": fixture / "docs" / "baseline.md",
        "docs/baseline.json": fixture / "docs" / "baseline.json",
    }


def expected_fixture_bytes() -> dict[str, bytes]:
    return {
        ".devpilot/project.yaml": b"project_id: gsdlc-04-c-browser-fixture\nproject_name: GSDLC 04 C Browser Fixture\nproject_type: software\n",
        "docs/baseline.md": b"# GSDLC 04-C browser fixture\n\nApproved source remains unchanged.\n",
        "docs/baseline.json": b'{"fixture":"GSDLC-04-C","version":1}\n',
    }


def prepare_browser(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if fixture.resolve() != Path(DEFAULT_FIXTURE).resolve():
        raise HarnessBlock(f"Fixture debe ser exactamente {DEFAULT_FIXTURE}.")
    if "inventory-sales-local" in str(fixture).lower() or "devpilot_workspaces" in str(fixture).lower():
        raise HarnessBlock("Workspace piloto real prohibido.")
    expected = expected_fixture_bytes()
    reused = False
    if fixture.exists() and any(fixture.iterdir()):
        if not (fixture / ".git").exists():
            raise HarnessBlock("Fixture existente no es Git; no se sobrescribirá.")
        rows = git_status(fixture)
        if rows:
            raise HarnessBlock(f"Fixture existente Git-dirty; preserve evidencia y no use git clean/reset: {rows}")
        tracked = set(git(fixture, "ls-files").stdout.splitlines())
        if tracked != set(expected):
            raise HarnessBlock(f"Fixture existente tiene tracked set inesperado: {sorted(tracked)}")
        for rel, body in expected.items():
            if canonical((fixture / rel).read_bytes()) != canonical(body):
                raise HarnessBlock(f"Fixture existente no coincide con baseline controlado: {rel}")
        reused = True
    else:
        for rel, body in expected.items():
            p = fixture / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body)
        git(fixture, "init")
        git(fixture, "config", "user.name", "DevPilot GSDLC 04-C Fixture")
        git(fixture, "config", "user.email", "devpilot-gsdlc04c@local.invalid")
        git(fixture, "add", ".devpilot/project.yaml", "docs/baseline.md", "docs/baseline.json")
        git(fixture, "commit", "-m", "test(gsdlc-04-c): browser fixture baseline")
    if git_status(fixture):
        raise HarnessBlock("Fixture no quedó Git clean después de preparación.")

    inputs.mkdir(parents=True, exist_ok=True)
    secret_key = "pass" + "word"
    secret_value = "demo" + "_only_" + "gsdlc04c"
    input_bytes = {
        "upload_source.md": b"# External upload\r\n\r\nMarkdown from a local file.\r\n",
        "import_source.json": b"\xff\xfe" + '{"title":"External JSON","version":1}\r\n'.encode("utf-16le"),
        "secret_warning_source.md": f"# Synthetic warning case\n\n{secret_key}={secret_value}\n".encode("utf-8"),
    }
    for name, body in input_bytes.items():
        p = inputs / name
        if p.exists() and p.read_bytes() != body:
            raise HarnessBlock(f"Input controlado existente difiere; no se sobrescribirá: {p}")
        p.write_bytes(body)

    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "browser").mkdir(parents=True, exist_ok=True)
    template = repo / "docs" / "audits" / "DEVPL_GSDLC_04_C_MANUAL_BROWSER_OBSERVATIONS_TEMPLATE.md"
    obs = evidence / OBS_NAME
    if not obs.exists():
        shutil.copyfile(template, obs)
        observation_action = "created"
    else:
        observation_action = "preserved-existing"
    source = {
        rel: {
            "raw_sha256": sha(path),
            "canonical_lf_sha256": hashlib.sha256(canonical(path.read_bytes())).hexdigest(),
        }
        for rel, path in fixture_paths(fixture).items()
    }
    payload = {
        "status": "PASS",
        "step": "prepare-browser",
        "timestamp": now(),
        "fixture": str(fixture),
        "fixture_reused": reused,
        "fixture_git_head": git(fixture, "rev-parse", "HEAD").stdout.strip(),
        "fixture_git_clean": True,
        "source_baseline": source,
        "browser_inputs": str(inputs),
        "input_hashes": {name: hashlib.sha256(body).hexdigest() for name, body in input_bytes.items()},
        "observation_file": str(obs),
        "observation_action": observation_action,
        "pilot_workspace_accessed": False,
        "runtime_db_copied": False,
    }
    write_evidence(evidence, "10_prepare_browser.json", payload)
    return payload


def provision_check(repo: Path, evidence: Path) -> dict[str, Any]:
    py = repo / ".venv" / "Scripts" / "python.exe"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    payload = {
        "status": "PASS",
        "step": "provision-check",
        "timestamp": now(),
        "venv_python": str(py),
        "venv_python_exists": py.is_file(),
        "npm": npm,
        "node_modules_exists": (repo / "ui" / "web" / "node_modules").is_dir(),
    }
    if os.name == "nt" and not py.is_file():
        raise HarnessBlock("Falta .venv\\Scripts\\python.exe.")
    if not npm:
        raise HarnessBlock("npm.cmd/npm no está disponible.")
    if not (repo / "ui" / "web" / "node_modules").is_dir():
        raise HarnessBlock("ui/web/node_modules no existe. No se hará provisioning de red automáticamente; use el fallback npm ci indicado en la guía.")
    write_evidence(evidence, "09_provision_check.json", payload)
    return payload


def source_hash(fixture: Path, evidence: Path, label: str) -> dict[str, Any]:
    rows = git_status(fixture)
    state: dict[str, Any] = {}
    all_ok = True
    for rel, path in fixture_paths(fixture).items():
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(fixture), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
        if blob.returncode != 0:
            raise HarnessBlock(f"No se pudo leer Git blob: {rel}")
        raw = path.read_bytes()
        current = canonical(raw)
        expected = canonical(blob.stdout)
        equivalent = current == expected
        state[rel] = {
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_lf_sha256": hashlib.sha256(current).hexdigest(),
            "expected_git_blob_sha256": hashlib.sha256(expected).hexdigest(),
            "git_content_equivalent_to_head": equivalent,
            "eol_only_representation_difference": raw != blob.stdout and equivalent,
        }
        all_ok = all_ok and equivalent
    if rows or not all_ok:
        raise HarnessBlock(f"Fixture source no equivale a Git baseline. git_status={rows} source_state={state}")
    payload = {
        "status": "PASS",
        "step": "source-hash",
        "label": label,
        "timestamp": now(),
        "authority": "git-blob+canonical-lf",
        "all_workspace_sources_unchanged": True,
        "git_clean": True,
        "source_state": state,
    }
    write_evidence(evidence, "11_fixture_source_hashes_before.json" if label == "before" else "13_fixture_source_hashes_after.json", payload)
    return payload


def browser_preflight(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if port_open(8787) or port_open(5173):
        raise HarnessBlock("8787/5173 deben estar libres antes de browser-preflight.")
    if not (evidence / OBS_NAME).is_file():
        raise HarnessBlock("Falta archivo de observaciones 04-C; ejecute prepare-browser.")
    for name in ["upload_source.md", "import_source.json", "secret_warning_source.md"]:
        if not (inputs / name).is_file():
            raise HarnessBlock(f"Falta input browser controlado: {inputs / name}")
    before = source_hash(fixture, evidence, "before")
    py = repo / ".venv" / "Scripts" / "python.exe"
    executable = str(py) if py.is_file() else sys.executable
    probe = repo / "scripts" / "devpl_gsdlc_04_c_fixture_binding_probe.py"
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    cp = run([executable, str(probe), "--repo-root", str(repo), "--browser-fixture-root", str(fixture)], cwd=repo, timeout=180, check=False, env=env)
    if cp.returncode != 0:
        raise HarnessBlock(f"fixture-binding-precheck BLOCK:\n{cp.stdout[-6000:]}")
    payload = {
        "status": "PASS",
        "step": "browser-preflight",
        "timestamp": now(),
        "ports_free": True,
        "source_hash_before": before,
        "fixture_binding_prechecked": True,
        "browser_runtime_may_start": True,
        "pilot_workspace_accessed": False,
    }
    write_evidence(evidence, "12_browser_preflight.json", payload)
    return payload


def runtime_status(evidence: Path, fixture: Path) -> dict[str, Any]:
    if not port_open(8787) or not port_open(5173):
        raise HarnessBlock(f"Runtime no está listo. api_8787={port_open(8787)} ui_5173={port_open(5173)}")
    runtime = evidence / "runtime"
    states: dict[str, Any] = {}
    for role in ["api", "ui"]:
        p = runtime / f"{role}_console_state.json"
        if not p.is_file():
            raise HarnessBlock(f"Falta state de Consola {role}: {p}")
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("status") != "PASS" or d.get("version") != VERSION:
            raise HarnessBlock(f"Runtime state inválido para {role}: {d}")
        states[role] = d
    binding = states["api"].get("workspace_binding", {})
    if Path(str(binding.get("active_workspace_root", ""))).resolve() != fixture.resolve() or binding.get("scope") != "gsdlc-04-c-browser-fixture-only":
        raise HarnessBlock("API runtime no está ligado exclusivamente al fixture 04-C.")
    payload = {
        "status": "PASS",
        "step": "runtime-status",
        "timestamp": now(),
        "api_ready": True,
        "ui_ready": True,
        "api_url": "http://127.0.0.1:8787/api/v1/health",
        "ui_url": "http://127.0.0.1:5173/",
        "three_console_runtime_required": True,
        "fixture_binding_ready": True,
        "workspace_binding": binding,
    }
    write_evidence(evidence, "runtime/runtime_status.json", payload)
    return payload


def _task_image(pid: int) -> str | None:
    if os.name != "nt":
        return None
    cp = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20, shell=False)
    if cp.returncode != 0 or "No tasks are running" in cp.stdout:
        return None
    line = cp.stdout.strip().splitlines()[0] if cp.stdout.strip() else ""
    return line.split(",")[0].strip('"') if line else None


def runtime_stop(evidence: Path) -> dict[str, Any]:
    runtime = evidence / "runtime"
    results = []
    for role, port in [("api", 8787), ("ui", 5173)]:
        p = runtime / f"{role}_console_state.json"
        if not p.is_file():
            if port_open(port):
                raise HarnessBlock(f"Puerto {port} ocupado sin PID state 04-C; no se matará proceso desconocido.")
            results.append({"role": role, "stopped": True, "already_stopped": True})
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        child = int(d.get("child_pid") or 0)
        launcher = int(d.get("launcher_pid") or 0)
        if not port_open(port):
            results.append({"role": role, "child_pid": child, "stopped": True, "already_stopped": True})
            continue
        if os.name != "nt":
            raise HarnessBlock("runtime-stop PID-safe está diseñado para Windows.")
        image = (_task_image(launcher) or "").lower()
        if image not in {"python.exe", "pythonw.exe", "py.exe"}:
            raise HarnessBlock(f"Stale/unsafe PID state para {role}; launcher PID {launcher} no es Python dedicado.")
        if child <= 0:
            raise HarnessBlock(f"child_pid inválido para {role}.")
        cp = subprocess.run(["taskkill", "/PID", str(child), "/T", "/F"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30, shell=False)
        if cp.returncode != 0 and port_open(port):
            raise HarnessBlock(f"No se pudo cerrar {role} PID {child}: {cp.stdout}")
        results.append({"role": role, "launcher_pid": launcher, "child_pid": child, "stopped": True, "output": cp.stdout[-2000:]})
    time.sleep(1)
    if port_open(8787) or port_open(5173):
        raise HarnessBlock("Puertos 8787/5173 siguen ocupados tras runtime-stop.")
    payload = {"status": "PASS", "step": "runtime-stop", "timestamp": now(), "results": results, "ports_free": True, "stale_pid_kill_allowed": False}
    write_evidence(evidence, f"runtime/runtime_stop_{int(time.time())}.json", payload)
    return payload


def parse_observations(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    if "<!-- BEGIN_BROWSER_MATRIX -->" not in text or "<!-- END_BROWSER_MATRIX -->" not in text or "<!-- BEGIN_BROWSER_SUMMARY -->" not in text or "<!-- END_BROWSER_SUMMARY -->" not in text:
        raise HarnessBlock("Observation delimiters missing.")
    matrix = text.split("<!-- BEGIN_BROWSER_MATRIX -->", 1)[1].split("<!-- END_BROWSER_MATRIX -->", 1)[0]
    rows: dict[str, str] = {}
    for line in matrix.splitlines():
        if not line.strip().startswith("|") or "---" in line or "Caso" in line:
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            rows[cells[0]] = cells[1]
    summary = text.split("<!-- BEGIN_BROWSER_SUMMARY -->", 1)[1].split("<!-- END_BROWSER_SUMMARY -->", 1)[0]
    values: dict[str, str] = {}
    for line in summary.splitlines():
        match = re.match(r"\s*-\s*`([^`]+)`:\s*(\S+)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return rows, values


def browser_evidence_validate(evidence: Path) -> dict[str, Any]:
    obs = evidence / OBS_NAME
    if not obs.is_file():
        raise HarnessBlock(f"Observation file missing: {obs}")
    rows, values = parse_observations(obs)
    missing = [case for case in EXPECTED_CASES if case not in rows]
    nonpass = [case for case in EXPECTED_CASES if rows.get(case) != "PASS"]
    browser = evidence / "browser"
    missing_shots = [name for name in REQUIRED_SCREENSHOTS if not (browser / name).is_file() or (browser / name).stat().st_size < 1000]
    invalid = {k: (values.get(k), expected) for k, expected in SUMMARY_EXPECTED.items() if values.get(k) != expected}
    after = evidence / "13_fixture_source_hashes_after.json"
    if not after.is_file():
        raise HarnessBlock("Falta 13_fixture_source_hashes_after.json; ejecute source-hash --label after primero.")
    after_data = json.loads(after.read_text(encoding="utf-8"))
    if after_data.get("status") != "PASS" or after_data.get("all_workspace_sources_unchanged") is not True:
        raise HarnessBlock("Final source hash no demuestra source/workspace unchanged.")
    if missing or nonpass or missing_shots or invalid:
        raise HarnessBlock(f"Browser evidence incomplete: missing_cases={missing} nonpass={nonpass} missing_screenshots={missing_shots} invalid_summary={invalid}")
    payload = {
        "status": "PASS",
        "step": "browser-evidence-validate",
        "timestamp": now(),
        "observation_file": str(obs),
        "rows_found": len(rows),
        "missing_cases": [],
        "nonpass_rows": [],
        "missing_screenshots": [],
        "summary_values": values,
        "invalid_summary_fields": [],
        "source_workspace_unchanged": True,
    }
    write_evidence(evidence, "DEVPL_GSDLC_04_C_BROWSER_ACCEPTANCE_VALIDATION.json", payload)
    return payload


def redaction_scan(evidence: Path) -> dict[str, Any]:
    patterns = [
        re.compile(r"sk-proj-[A-Za-z0-9_-]{12,}"),
        re.compile(r"github_pat_[A-Za-z0-9_-]{12,}"),
        re.compile(r"AKIA[0-9A-Z]{8,}"),
        re.compile(r"(?i)(password|api[_-]?key|token|secret)\s*[:=]\s*[^\s,;`]+"),
    ]
    findings = []
    for p in evidence.rglob("*"):
        if not p.is_file() or p.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pattern in patterns:
            if pattern.search(text):
                findings.append({"path": str(p.relative_to(evidence)), "pattern_id": patterns.index(pattern)})
    return {"status": "PASS" if not findings else "BLOCK", "findings": findings, "secrets_exposed": bool(findings)}


def package_evidence(evidence: Path, artifacts: Path) -> dict[str, Any]:
    marker = evidence / "DEVPL_GSDLC_04_C_BROWSER_ACCEPTANCE_VALIDATION.json"
    if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")).get("status") != "PASS":
        raise HarnessBlock("Browser evidence validation PASS required before evidence packaging.")
    scan = redaction_scan(evidence)
    if scan["status"] != "PASS":
        raise HarnessBlock(f"Redaction scan BLOCK; preserve evidence and review paths only: {scan['findings'][:12]}")
    write_evidence(evidence, "DEVPL_GSDLC_04_C_REDACTION_SCAN_WINDOWS.json", scan)
    outdir = artifacts / "evidence"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "DEVPL_GSDLC_04_C_WINDOWS_EVIDENCE_v1_0_0.zip"
    if out.exists():
        raise HarnessBlock(f"Refusing overwrite of sealed evidence package: {out}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(evidence.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(evidence).as_posix())
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        if bad:
            raise HarnessBlock(f"Evidence ZIP CRC failed at {bad}")
    digest = sha(out)
    sidecar = out.with_suffix(out.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    return {"status": "PASS", "step": "package-evidence", "timestamp": now(), "evidence_zip": str(out), "sha256": digest, "sidecar": str(sidecar), "redaction_scan": "PASS"}


def main() -> int:
    p = argparse.ArgumentParser(description="GSDLC-04-C Windows/browser evidence harness.")
    p.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    p.add_argument("--evidence-dir", default=r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C")
    p.add_argument("--browser-fixture-root", default=DEFAULT_FIXTURE)
    p.add_argument("--browser-input-root", default=DEFAULT_INPUTS)
    p.add_argument("--artifacts-root", default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002")
    p.add_argument("--step", choices=["provision-check", "prepare-browser", "browser-preflight", "runtime-status", "source-hash", "browser-evidence-validate", "runtime-stop", "package-evidence"], required=True)
    p.add_argument("--label", choices=["before", "after"])
    a = p.parse_args()
    repo = Path(a.repo_root).resolve()
    evidence = Path(a.evidence_dir).resolve()
    fixture = Path(a.browser_fixture_root).resolve()
    inputs = Path(a.browser_input_root).resolve()
    try:
        if "inventory-sales-local" in str(repo).lower() or "devpilot_workspaces" in str(repo).lower():
            raise HarnessBlock("Repo root points at forbidden pilot workspace.")
        if a.step == "provision-check":
            result = provision_check(repo, evidence)
        elif a.step == "prepare-browser":
            result = prepare_browser(repo, fixture, inputs, evidence)
        elif a.step == "browser-preflight":
            result = browser_preflight(repo, fixture, inputs, evidence)
        elif a.step == "runtime-status":
            result = runtime_status(evidence, fixture)
        elif a.step == "source-hash":
            if not a.label:
                raise HarnessBlock("--label before|after is required for source-hash.")
            result = source_hash(fixture, evidence, a.label)
        elif a.step == "browser-evidence-validate":
            result = browser_evidence_validate(evidence)
        elif a.step == "runtime-stop":
            result = runtime_stop(evidence)
        else:
            result = package_evidence(evidence, Path(a.artifacts_root).resolve())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        verdict("PASS", f"{a.step} completado")
        return 0
    except (HarnessBlock, subprocess.TimeoutExpired, PermissionError, OSError, json.JSONDecodeError) as exc:
        payload = {"status": "BLOCK", "harness_id": HARNESS_ID, "version": VERSION, "step": a.step, "timestamp": now(), "message": str(exc), "full_regression_executed": False, "pilot_workspace_accessed": False}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        try:
            write_evidence(evidence, f"harness_{a.step}_BLOCK_{int(time.time())}.json", payload)
        except Exception:
            pass
        verdict("BLOCK", f"{a.step}: {exc}")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
