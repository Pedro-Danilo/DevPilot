from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS_ID = "DEVPL-GSDLC-04-D-WINDOWS-HARNESS"
VERSION = "1.0.0"
DEFAULT_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER"
DEFAULT_INPUTS = r"D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-D\browser_inputs"
OBS_NAME = "DEVPL_GSDLC_04_D_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md"
TARGET_ARTIFACT = "docs/gsdlc04d_review_candidate.md"
INVALID_TARGET = "docs/gsdlc04d_invalid.md"
REQUIRED_SCREENSHOTS = [
    "00_project_review_ready.png",
    "01_findings_navigation.png",
    "02_plan_diff.png",
    "03_targeted_approval.png",
    "04_atomic_apply.png",
    "05_frozen_hash.png",
]
EXPECTED_CASES = [
    "Project context + review UI",
    "Invalid DRAFT findings + navigation",
    "Valid DRAFT immutable plan/diff",
    "Targeted Approval Center exact ID",
    "Approval verified + atomic apply",
    "FROZEN approved hash",
    "Source write bounded to declared artifact",
    "Session/RBAC guard",
]
SUMMARY_EXPECTED = {
    "browser_acceptance": "PASS",
    "S0_open": "0",
    "S1_open": "0",
    "secrets_exposed": "false",
    "network_runtime_used": "false",
    "external_api_used": "false",
    "pilot_workspace_accessed": "false",
    "full_regression_runs": "0",
}
BASELINE_TRACKED = [".devpilot/project.yaml", "docs/baseline.md", "docs/baseline.json"]


class HarnessBlock(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            k.SetConsoleMode(h, mode.value | 0x0004)
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


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, timeout=60, check=check)


def git_status(repo: Path) -> list[str]:
    cp = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
    if cp.returncode != 0:
        raise HarnessBlock(cp.stderr.decode(errors="replace")[-2500:])
    return [x.decode("utf-8", errors="replace") for x in cp.stdout.split(b"\0") if x]


def dirty_path(entry: str) -> str:
    value = entry[3:] if len(entry) >= 4 else entry
    if " -> " in value:
        value = value.split(" -> ")[-1]
    return value.strip('"')


def write_evidence(evidence: Path, name: str, payload: dict[str, Any], *, replace: bool = False) -> Path:
    path = evidence / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        stem, suffix, i = path.stem, path.suffix, 2
        while (path.parent / f"{stem}_{i:02d}{suffix}").exists():
            i += 1
        path = path.parent / f"{stem}_{i:02d}{suffix}"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def expected_fixture_bytes() -> dict[str, bytes]:
    return {
        ".devpilot/project.yaml": b"project_id: gsdlc04d-browser\nproject_name: GSDLC 04-D browser fixture\nproject_type: software\n",
        "docs/baseline.md": b"# GSDLC 04-D browser fixture\n\nBaseline approved source remains unchanged.\n",
        "docs/baseline.json": b'{"fixture":"GSDLC-04-D","version":1}\n',
    }


def fixture_paths(fixture: Path) -> dict[str, Path]:
    return {rel: fixture / rel for rel in BASELINE_TRACKED}


def valid_input_bytes() -> bytes:
    return b'''---\ndoc_id: "GSDLC-04-D-BROWSER-CANDIDATE"\ntitle: "GSDLC 04-D browser candidate"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# GSDLC 04-D browser candidate\n\nThis governed browser fixture proves validate, findings, immutable diff, exact approval, atomic apply and freeze.\n'''


def prepare_browser(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if fixture.resolve() != Path(DEFAULT_FIXTURE).resolve():
        raise HarnessBlock(f"Fixture must be exactly {DEFAULT_FIXTURE}.")
    low = str(fixture).lower()
    if "inventory-sales-local" in low or "devpilot_workspaces" in low:
        raise HarnessBlock("Real pilot workspace is forbidden during GSDLC-04-D.")
    expected = expected_fixture_bytes()
    reused = False
    if fixture.exists() and any(fixture.iterdir()):
        if not (fixture / ".git").exists():
            raise HarnessBlock("Existing browser fixture is not Git; refusing overwrite.")
        rows = git_status(fixture)
        if rows:
            raise HarnessBlock(f"Existing fixture has surviving browser/source state: {rows}. Do not reset/clean; continue from the corresponding later guide step or preserve evidence for diagnosis.")
        tracked = set(git(fixture, "ls-files").stdout.splitlines())
        if tracked != set(expected):
            raise HarnessBlock(f"Existing fixture tracked set differs from controlled baseline: {sorted(tracked)}")
        for rel, body in expected.items():
            if canonical((fixture / rel).read_bytes()) != canonical(body):
                raise HarnessBlock(f"Existing fixture baseline differs: {rel}")
        reused = True
    else:
        for rel, body in expected.items():
            path = fixture / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        git(fixture, "init")
        git(fixture, "config", "user.name", "DevPilot GSDLC 04-D Fixture")
        git(fixture, "config", "user.email", "devpilot-gsdlc04d@local.invalid")
        git(fixture, "add", *BASELINE_TRACKED)
        git(fixture, "commit", "-m", "test(gsdlc-04-d): browser fixture baseline")
    if git_status(fixture):
        raise HarnessBlock("Fixture is not Git-clean after preparation.")

    inputs.mkdir(parents=True, exist_ok=True)
    controlled = {
        "invalid_review_source.md": b"# Missing frontmatter\n\nBrowser finding navigation case.\n",
        "valid_review_source.md": valid_input_bytes(),
    }
    for name, body in controlled.items():
        path = inputs / name
        if path.exists() and path.read_bytes() != body:
            raise HarnessBlock(f"Controlled browser input differs; refusing overwrite: {path}")
        path.write_bytes(body)

    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "browser").mkdir(parents=True, exist_ok=True)
    template = repo / "docs/audits/DEVPL_GSDLC_04_D_MANUAL_BROWSER_OBSERVATIONS_TEMPLATE.md"
    obs = evidence / OBS_NAME
    if not obs.exists():
        shutil.copyfile(template, obs)
        observation_action = "created"
    else:
        observation_action = "preserved-existing"
    baseline = {rel: {"raw_sha256": sha(path), "canonical_lf_sha256": sha_bytes(canonical(path.read_bytes()))} for rel, path in fixture_paths(fixture).items()}
    payload = {
        "status": "PASS",
        "step": "prepare-browser",
        "timestamp": now(),
        "fixture": str(fixture),
        "fixture_reused": reused,
        "fixture_git_head": git(fixture, "rev-parse", "HEAD").stdout.strip(),
        "fixture_git_clean": True,
        "baseline_sources": baseline,
        "browser_inputs": str(inputs),
        "input_hashes": {name: sha_bytes(body) for name, body in controlled.items()},
        "expected_declared_source_write": TARGET_ARTIFACT,
        "invalid_target_must_not_exist": INVALID_TARGET,
        "observation_file": str(obs),
        "observation_action": observation_action,
        "pilot_workspace_accessed": False,
        "runtime_db_copied": False,
    }
    write_evidence(evidence, "10_prepare_browser.json", payload)
    return payload


def provision_check(repo: Path, evidence: Path) -> dict[str, Any]:
    py = repo / ".venv/Scripts/python.exe"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    payload = {"status": "PASS", "step": "provision-check", "timestamp": now(), "venv_python": str(py), "venv_python_exists": py.is_file(), "npm": npm, "node_modules_exists": (repo / "ui/web/node_modules").is_dir(), "network_used": False}
    if os.name == "nt" and not py.is_file():
        raise HarnessBlock("Missing .venv\\Scripts\\python.exe.")
    if not npm:
        raise HarnessBlock("npm.cmd/npm is unavailable.")
    if not (repo / "ui/web/node_modules").is_dir():
        raise HarnessBlock("ui/web/node_modules is missing. Harness will not silently use network; follow the explicit provisioning fallback in the guide if needed.")
    write_evidence(evidence, "09_provision_check.json", payload)
    return payload


def baseline_equivalence(fixture: Path) -> dict[str, Any]:
    state: dict[str, Any] = {}
    all_ok = True
    for rel, path in fixture_paths(fixture).items():
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(fixture), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
        if blob.returncode != 0:
            raise HarnessBlock(f"Unable to read immutable fixture Git blob: {rel}")
        raw = path.read_bytes()
        current = canonical(raw)
        expected = canonical(blob.stdout)
        equivalent = current == expected
        state[rel] = {
            "raw_sha256": sha_bytes(raw),
            "canonical_lf_sha256": sha_bytes(current),
            "expected_git_blob_canonical_lf_sha256": sha_bytes(expected),
            "git_content_equivalent_to_head": equivalent,
            "eol_only_representation_difference": raw != blob.stdout and equivalent,
        }
        all_ok = all_ok and equivalent
    return {"all_baseline_sources_unchanged": all_ok, "source_state": state, "authority": "git-blob+canonical-lf"}


def browser_preflight(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if port_open(8787) or port_open(5173):
        raise HarnessBlock("Ports 8787/5173 must be free before browser-preflight.")
    if not (evidence / OBS_NAME).is_file():
        raise HarnessBlock("Manual observations file missing; run prepare-browser first.")
    for name in ["invalid_review_source.md", "valid_review_source.md"]:
        if not (inputs / name).is_file():
            raise HarnessBlock(f"Missing controlled browser input: {inputs / name}")
    rows = git_status(fixture)
    eq = baseline_equivalence(fixture)
    if rows or not eq["all_baseline_sources_unchanged"]:
        raise HarnessBlock(f"Fixture must be Git-clean and baseline-equivalent before browser runtime. status={rows} equivalence={eq}")
    payload = {"status": "PASS", "step": "browser-preflight", "timestamp": now(), "ports_free": True, "fixture_git_clean": True, **eq, "fixture_binding_required": str(fixture), "pilot_workspace_accessed": False}
    write_evidence(evidence, "12_browser_preflight.json", payload)
    return payload


def runtime_status(evidence: Path, fixture: Path) -> dict[str, Any]:
    if not port_open(8787) or not port_open(5173):
        raise HarnessBlock(f"Runtime is not ready. api_8787={port_open(8787)} ui_5173={port_open(5173)}")
    runtime = evidence / "runtime"
    states: dict[str, Any] = {}
    for role in ["api", "ui"]:
        path = runtime / f"{role}_console_state.json"
        if not path.is_file():
            raise HarnessBlock(f"Missing runtime console state: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "PASS" or data.get("version") != VERSION:
            raise HarnessBlock(f"Invalid runtime state for {role}: {data}")
        states[role] = data
    binding = states["api"].get("workspace_binding") or {}
    if Path(str(binding.get("active_workspace_root", ""))).resolve() != fixture.resolve() or binding.get("scope") != "gsdlc-04-d-browser-fixture-only":
        raise HarnessBlock("API runtime is not bound exclusively to the 04-D browser fixture.")
    payload = {"status": "PASS", "step": "runtime-status", "timestamp": now(), "api_ready": True, "ui_ready": True, "api_url": "http://127.0.0.1:8787/api/v1/health", "ui_url": "http://127.0.0.1:5173/", "three_console_runtime_required": True, "workspace_binding": binding}
    write_evidence(evidence, "runtime/runtime_status.json", payload)
    return payload


def latest_frozen_review(repo: Path, relative_path: str) -> dict[str, Any] | None:
    root = repo / "outputs/artifact_reviews/gsdlc_04_d"
    candidates: list[tuple[float, dict[str, Any]]] = []
    if not root.is_dir():
        return None
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("relative_path") == relative_path and data.get("status") == "FROZEN":
            candidates.append((path.stat().st_mtime, data))
    return sorted(candidates, key=lambda item: item[0])[-1][1] if candidates else None


def source_scope_after(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    rows = git_status(fixture)
    paths = sorted(dirty_path(x) for x in rows)
    if paths != [TARGET_ARTIFACT]:
        raise HarnessBlock(f"Browser apply must mutate exactly {TARGET_ARTIFACT}; actual Git paths={paths}")
    target = fixture / TARGET_ARTIFACT
    invalid = fixture / INVALID_TARGET
    if not target.is_file():
        raise HarnessBlock("Declared target file is missing after atomic apply.")
    if invalid.exists():
        raise HarnessBlock("Invalid FINDINGS-only target was unexpectedly written to workspace source.")
    eq = baseline_equivalence(fixture)
    if not eq["all_baseline_sources_unchanged"]:
        raise HarnessBlock("Baseline fixture sources changed unexpectedly.")
    review = latest_frozen_review(repo, TARGET_ARTIFACT)
    if not review:
        raise HarnessBlock("No FROZEN 04-D review evidence found for declared target.")
    current_sha = sha(target)
    if review.get("approved_sha256") != current_sha or review.get("approval_valid") is not True:
        raise HarnessBlock("FROZEN review hash/approval does not match the actual declared source.")
    if not review.get("approval_id") or not review.get("execution_id") or not (review.get("plan") or {}).get("plan_hash"):
        raise HarnessBlock("FROZEN review lacks exact approval/execution/plan binding.")
    payload = {
        "status": "PASS",
        "step": "source-scope-after",
        "timestamp": now(),
        "authority": "git-status-v1-z + immutable baseline Git blobs + FROZEN review record",
        "expected_mutated_path": TARGET_ARTIFACT,
        "actual_mutated_paths": paths,
        "unexpected_source_writes_total": 0,
        "invalid_findings_target_written": False,
        "all_baseline_sources_unchanged": True,
        "declared_source_sha256": current_sha,
        "review_id": review.get("review_id"),
        "approval_id": review.get("approval_id"),
        "execution_id": review.get("execution_id"),
        "plan_id": (review.get("plan") or {}).get("plan_id"),
        "plan_hash": (review.get("plan") or {}).get("plan_hash"),
        "review_status": review.get("status"),
        "approval_valid": review.get("approval_valid"),
        "approved_sha256": review.get("approved_sha256"),
        "source_mutations_performed": True,
        "source_mutation_scope": "exactly-one-declared-browser-fixture-artifact",
        "pilot_workspace_accessed": False,
        "full_regression_executed": False,
        **eq,
    }
    write_evidence(evidence, "06_source_scope_after.json", payload, replace=True)
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
        path = runtime / f"{role}_console_state.json"
        if not path.is_file():
            if port_open(port):
                raise HarnessBlock(f"Port {port} occupied without trusted 04-D PID state; unknown process will not be killed.")
            results.append({"role": role, "stopped": True, "already_stopped": True})
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        child = int(data.get("child_pid") or 0)
        launcher = int(data.get("launcher_pid") or 0)
        if not port_open(port):
            results.append({"role": role, "child_pid": child, "stopped": True, "already_stopped": True})
            continue
        if os.name != "nt":
            raise HarnessBlock("PID-safe runtime-stop is designed for Windows.")
        image = (_task_image(launcher) or "").lower()
        if image not in {"python.exe", "pythonw.exe", "py.exe"}:
            raise HarnessBlock(f"Stale/unsafe launcher PID for {role}: {launcher}")
        if child <= 0:
            raise HarnessBlock(f"Invalid child PID for {role}.")
        cp = subprocess.run(["taskkill", "/PID", str(child), "/T", "/F"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30, shell=False)
        if cp.returncode != 0 and port_open(port):
            raise HarnessBlock(f"Unable to stop {role} PID {child}: {cp.stdout}")
        results.append({"role": role, "launcher_pid": launcher, "child_pid": child, "stopped": True, "output": cp.stdout[-2000:]})
    time.sleep(1)
    if port_open(8787) or port_open(5173):
        raise HarnessBlock("Ports remain occupied after runtime-stop.")
    payload = {"status": "PASS", "step": "runtime-stop", "timestamp": now(), "results": results, "ports_free": True, "stale_pid_kill_allowed": False}
    write_evidence(evidence, f"runtime/runtime_stop_{int(time.time())}.json", payload)
    return payload


def parse_observations(path: Path) -> tuple[dict[str, tuple[str, str]], dict[str, str], str, str]:
    text = path.read_text(encoding="utf-8")
    required = ["<!-- BEGIN_BROWSER_MATRIX -->", "<!-- END_BROWSER_MATRIX -->", "<!-- BEGIN_BROWSER_SUMMARY -->", "<!-- END_BROWSER_SUMMARY -->"]
    if any(marker not in text for marker in required):
        raise HarnessBlock("Observation delimiters missing.")
    matrix = text.split("<!-- BEGIN_BROWSER_MATRIX -->", 1)[1].split("<!-- END_BROWSER_MATRIX -->", 1)[0]
    rows: dict[str, tuple[str, str]] = {}
    for line in matrix.splitlines():
        if not line.strip().startswith("|") or "---" in line or "Caso" in line:
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            rows[cells[0]] = (cells[1], cells[3])
    summary = text.split("<!-- BEGIN_BROWSER_SUMMARY -->", 1)[1].split("<!-- END_BROWSER_SUMMARY -->", 1)[0]
    values: dict[str, str] = {}
    for line in summary.splitlines():
        match = re.match(r"\s*-\s*`([^`]+)`:\s*(\S+)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    decision_match = re.search(r"^- Decisión:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    justification_match = re.search(r"^- Justificación:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return rows, values, (decision_match.group(1).strip() if decision_match else ""), (justification_match.group(1).strip() if justification_match else "")


def browser_evidence_validate(evidence: Path) -> dict[str, Any]:
    obs = evidence / OBS_NAME
    if not obs.is_file():
        raise HarnessBlock(f"Observation file missing: {obs}")
    rows, values, decision, justification = parse_observations(obs)
    missing = [case for case in EXPECTED_CASES if case not in rows]
    nonpass = [case for case in EXPECTED_CASES if rows.get(case, ("", ""))[0] != "PASS"]
    blank_observations = [case for case in EXPECTED_CASES if not rows.get(case, ("", ""))[1].strip()]
    browser = evidence / "browser"
    missing_shots = [name for name in REQUIRED_SCREENSHOTS if not (browser / name).is_file() or (browser / name).stat().st_size < 1000]
    invalid_summary = {k: (values.get(k), expected) for k, expected in SUMMARY_EXPECTED.items() if values.get(k) != expected}
    scope_path = evidence / "06_source_scope_after.json"
    if not scope_path.is_file():
        raise HarnessBlock("Missing 06_source_scope_after.json; run source-scope-after before evidence validation.")
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    if scope.get("status") != "PASS" or scope.get("unexpected_source_writes_total") != 0 or scope.get("review_status") != "FROZEN":
        raise HarnessBlock("Source-scope evidence does not prove exact declared apply + FROZEN state.")
    if decision != "PASS-CANDIDATE" or not justification:
        raise HarnessBlock("Manual owner execution decision must be PASS-CANDIDATE with non-empty justification.")
    if missing or nonpass or blank_observations or missing_shots or invalid_summary:
        raise HarnessBlock(f"Browser evidence incomplete: missing={missing} nonpass={nonpass} blank_observations={blank_observations} missing_screenshots={missing_shots} invalid_summary={invalid_summary}")
    payload = {
        "status": "PASS",
        "step": "browser-evidence-validate",
        "timestamp": now(),
        "rows_found": len(rows),
        "missing_cases": [],
        "nonpass_rows": [],
        "blank_observations": [],
        "missing_screenshots": [],
        "summary_values": values,
        "decision": decision,
        "justification_present": True,
        "declared_source_scope_pass": True,
        "source_write_expected_and_bounded": True,
        "review_status": "FROZEN",
        "full_regression_runs": 0,
        "pilot_workspace_accessed": False,
    }
    write_evidence(evidence, "DEVPL_GSDLC_04_D_BROWSER_ACCEPTANCE_VALIDATION.json", payload, replace=True)
    return payload


def redaction_scan(evidence: Path) -> dict[str, Any]:
    patterns = [
        re.compile(r"sk-proj-[A-Za-z0-9_-]{12,}"),
        re.compile(r"github_pat_[A-Za-z0-9_-]{12,}"),
        re.compile(r"AKIA[0-9A-Z]{8,}"),
        re.compile(r"(?i)(password|api[_-]?key|token|secret)\s*[:=]\s*[^\s,;`]+"),
    ]
    findings = []
    for path in evidence.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for idx, pattern in enumerate(patterns):
            if pattern.search(text):
                findings.append({"path": str(path.relative_to(evidence)), "pattern_id": idx})
    return {"status": "PASS" if not findings else "BLOCK", "findings": findings, "secrets_exposed": bool(findings)}


def package_evidence(evidence: Path, artifacts: Path) -> dict[str, Any]:
    marker = evidence / "DEVPL_GSDLC_04_D_BROWSER_ACCEPTANCE_VALIDATION.json"
    if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")).get("status") != "PASS":
        raise HarnessBlock("Browser evidence validation PASS is required before evidence packaging.")
    scan = redaction_scan(evidence)
    if scan["status"] != "PASS":
        raise HarnessBlock(f"Redaction scan BLOCK; preserve evidence and inspect paths only: {scan['findings'][:12]}")
    write_evidence(evidence, "DEVPL_GSDLC_04_D_REDACTION_SCAN_WINDOWS.json", scan, replace=True)
    outdir = artifacts / "evidence"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "DEVPL_GSDLC_04_D_WINDOWS_EVIDENCE_v1_0_0.zip"
    if out.exists():
        raise HarnessBlock(f"Refusing overwrite of sealed evidence package: {out}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(evidence.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(evidence).as_posix())
    with zipfile.ZipFile(out) as zf:
        bad = zf.testzip()
        if bad:
            raise HarnessBlock(f"Evidence ZIP CRC failed at {bad}")
    digest = sha(out)
    sidecar = out.with_suffix(out.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    return {"status": "PASS", "step": "package-evidence", "timestamp": now(), "evidence_zip": str(out), "sha256": digest, "sidecar": str(sidecar), "redaction_scan": "PASS", "full_regression_runs": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="GSDLC-04-D Windows/browser evidence harness.")
    parser.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    parser.add_argument("--evidence-dir", default=r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D")
    parser.add_argument("--browser-fixture-root", default=DEFAULT_FIXTURE)
    parser.add_argument("--browser-input-root", default=DEFAULT_INPUTS)
    parser.add_argument("--artifacts-root", default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002")
    parser.add_argument("--step", choices=["provision-check", "prepare-browser", "browser-preflight", "runtime-status", "source-scope-after", "runtime-stop", "browser-evidence-validate", "package-evidence"], required=True)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    fixture = Path(args.browser_fixture_root).resolve()
    inputs = Path(args.browser_input_root).resolve()
    try:
        low = str(repo).lower()
        if "inventory-sales-local" in low or "devpilot_workspaces" in low:
            raise HarnessBlock("Repo root points to forbidden pilot workspace.")
        if args.step == "provision-check":
            result = provision_check(repo, evidence)
        elif args.step == "prepare-browser":
            result = prepare_browser(repo, fixture, inputs, evidence)
        elif args.step == "browser-preflight":
            result = browser_preflight(repo, fixture, inputs, evidence)
        elif args.step == "runtime-status":
            result = runtime_status(evidence, fixture)
        elif args.step == "source-scope-after":
            result = source_scope_after(repo, fixture, evidence)
        elif args.step == "runtime-stop":
            result = runtime_stop(evidence)
        elif args.step == "browser-evidence-validate":
            result = browser_evidence_validate(evidence)
        else:
            result = package_evidence(evidence, Path(args.artifacts_root).resolve())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        verdict("PASS", f"{args.step} completado")
        return 0
    except (HarnessBlock, subprocess.TimeoutExpired, PermissionError, OSError, json.JSONDecodeError) as exc:
        payload = {"status": "BLOCK", "harness_id": HARNESS_ID, "version": VERSION, "step": args.step, "timestamp": now(), "message": str(exc), "full_regression_executed": False, "pilot_workspace_accessed": False}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        try:
            write_evidence(evidence, f"harness_{args.step}_BLOCK_{int(time.time())}.json", payload)
        except Exception:
            pass
        verdict("BLOCK", f"{args.step}: {exc}")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
