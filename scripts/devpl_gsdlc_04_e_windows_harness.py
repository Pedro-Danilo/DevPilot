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
import http.cookiejar
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HARNESS_ID = "DEVPL-GSDLC-04-E-WINDOWS-HARNESS"
VERSION = "1.0.6"
CREDENTIAL_FIELD = "pass" + "word"
RUNTIME_CONSOLE_VERSION = "1.0.2"
CORRECTIVE_LEVEL = "GSDLC-04-E-RECOVERY-011"
DEFAULT_FIXTURE = r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER"
DEFAULT_INPUTS = r"D:\Projects\DevPilot_E2E_Evaluation\control\DEVPL-GSDLC-04-E\browser_inputs"
DEFAULT_EVIDENCE = r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E"
OBS_NAME = "DEVPL_GSDLC_04_E_MANUAL_BROWSER_OBSERVATIONS_v1_0_0.md"
TARGET_ARTIFACT = "docs/gsdlc04e_review_candidate.md"
INVALID_TARGET = "docs/gsdlc04e_invalid.md"
FULL_RUN_MARKER = "DEVPL_GSDLC_04_E_FULL_REGRESSION_RUN_MARKER.json"
FULL_CLOSURE = "DEVPL_GSDLC_04_E_FULL_REGRESSION_CLOSURE.json"
BROWSER_MARKER = "DEVPL_GSDLC_04_E_BROWSER_ACCEPTANCE_VALIDATION.json"
ROLLBACK_PREFLIGHT = "15_rollback_preflight_v1_0_11.json"
ROLLBACK_VERIFY = "15_rollback_verify_v1_0_11.json"
ROLLBACK_MARKER = "Temporary rollback proof 04-E."
REQUIRED_SCREENSHOTS = [
    "00_project_active_workbench.png",
    "01_project_context_guard.png",
    "02_manual_markdown_draft.png",
    "03_manual_autosave_recovery.png",
    "04_json_hints.png",
    "05_paste_provenance.png",
    "06_upload_import.png",
    "07_upload_negative.png",
    "08_findings_navigation.png",
    "09_plan_diff.png",
    "10_owner_approval.png",
    "11_wrong_role_denied.png",
    "12_apply_freeze.png",
    "13_stale_preimage.png",
    "14_external_revalidation.png",
    "15_rollback_recovery.png",
    "16_api_down_recovery.png",
    "17_accessibility.png",
]
EXPECTED_CASES = [
    "Project Home + active project + Artifact Workbench",
    "Direct project route guard without context",
    "MANUAL Markdown DRAFT",
    "MANUAL autosave/restart recovery",
    "JSON DRAFT validation hints",
    "PASTE provenance",
    "UPLOAD/IMPORT supported",
    "Upload traversal/unsupported blocked",
    "Validate/findings/navigation",
    "Immutable plan/diff",
    "Exact owner approval",
    "Wrong-role approval denied",
    "Apply + freeze",
    "Stale preimage invalidates plan/approval",
    "External edit FROZEN → REVALIDATION_REQUIRED",
    "Rollback/recovery",
    "API-down/timeout recovery",
    "Keyboard/focus/labels/accessibility",
]
SUMMARY_EXPECTED = {
    "browser_acceptance": "PASS",
    "S0_open": "0",
    "S1_open": "0",
    "secrets_exposed": "false",
    "network_runtime_used": "false",
    "external_api_used": "false",
    "pilot_workspace_accessed": "false",
    "normal_user_powershell_required": "0",
    "external_operator_project_writes": "0",
    "full_regression_runs_before_browser": "0",
}
BASELINE_TRACKED = [
    ".gitignore",
    ".devpilot/project.yaml",
    "docs/manual_authoring.md",
    "docs/manual_authoring.json",
    "docs/baseline.md",
]


class HarnessBlock(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def ansi() -> None:
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
    ansi()
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
    return value.strip('"').replace("\\", "/")


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
        ".gitignore": b".devpilot/auth/\noutputs/\n*.db\n*.db-*\n",
        ".devpilot/project.yaml": b"project_id: gsdlc04e-browser\nproject_name: GSDLC 04-E browser fixture\nproject_type: software\n",
        "docs/manual_authoring.md": b'''---\ndoc_id: "GSDLC-04-E-MANUAL"\ntitle: "GSDLC 04-E manual artifact"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# Manual artifact\n\nBaseline manual source.\n''',
        "docs/manual_authoring.json": b'{"doc_id":"GSDLC-04-E-JSON","title":"GSDLC 04-E JSON","status":"draft","version":"1.0.0"}\n',
        "docs/baseline.md": b'''---\ndoc_id: "GSDLC-04-E-ROLLBACK"\ntitle: "GSDLC 04-E rollback baseline"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# Rollback baseline\n\nOriginal baseline used only by the isolated browser fixture.\n''',
    }


def fixture_paths(fixture: Path) -> dict[str, Path]:
    return {rel: fixture / rel for rel in BASELINE_TRACKED}


def valid_review_bytes() -> bytes:
    return b'''---\ndoc_id: "GSDLC-04-E-BROWSER-CANDIDATE"\ntitle: "GSDLC 04-E browser candidate"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# GSDLC 04-E browser candidate\n\nThis artifact proves import, exact approval, atomic apply, freeze and external revalidation.\n'''


def _python(repo: Path) -> str:
    win = repo / ".venv/Scripts/python.exe"
    return str(win) if win.is_file() else sys.executable


def _fixture_identity_call(repo: Path, fixture: Path, inputs: Path, action: str) -> dict[str, Any]:
    script = repo / "scripts/devpl_gsdlc_04_e_fixture_identity.py"
    if not script.is_file():
        raise HarnessBlock("Synthetic wrong-role fixture identity helper is missing.")
    creds = inputs / "WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt"
    env = dict(os.environ); env["PYTHONPATH"] = "src"
    cp = run([_python(repo), str(script), "--action", action, "--repo-root", str(repo), "--fixture-root", str(fixture), "--credentials-output", str(creds)], cwd=repo, timeout=90, env=env, check=False)
    # Helper prints JSON first and a colored PASS/BLOCK line last. Parse the JSON
    # object only; never echo the credential handoff or any password.
    text = cp.stdout
    json_end = text.rfind("}\n")
    if json_end < 0:
        json_end = text.rfind("}")
    json_text = text[:json_end + 1] if json_end >= 0 else text
    if cp.returncode != 0:
        raise HarnessBlock(f"Synthetic wrong-role {action} failed.\n{text[-3000:]}")
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise HarnessBlock(f"Synthetic wrong-role helper returned invalid JSON for {action}.") from exc
    if payload.get("status") != "PASS":
        raise HarnessBlock(f"Synthetic wrong-role helper did not PASS for {action}: {payload}")
    return payload


def provision_wrong_role(repo: Path, fixture: Path, inputs: Path) -> dict[str, Any]:
    # Remove the superseded plaintext viewer handoff if it survived Recovery-004.
    (inputs / "VIEWER_LOGIN_DO_NOT_ATTACH.txt").unlink(missing_ok=True)
    payload = _fixture_identity_call(repo, fixture, inputs, "provision")
    creds = inputs / "WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt"
    if not creds.is_file() or not payload.get("roundtrip_login_verified") or payload.get("verified_roles") != ["developer"]:
        raise HarnessBlock("Synthetic wrong-role provisioning did not produce a verified canonical developer credential in the runtime API auth store.")
    return {
        "status": "PASS",
        "username": payload.get("username"),
        "role": payload.get("role"),
        "wrong_role_kind": payload.get("wrong_role_kind"),
        "credentials_file": str(creds),
        "credential_secret_in_evidence": False,
        "runtime_auth_store_only": True,
        "auth_store_scope": payload.get("auth_store_scope"),
        "roundtrip_login_verified": True,
        "legacy_runtime_viewer_removed": bool(payload.get("legacy_runtime_viewer_removed")),
        "legacy_fixture_viewer_removed": bool(payload.get("legacy_fixture_viewer_removed")),
    }


def _read_wrong_role_credentials(inputs: Path) -> tuple[str, str]:
    path = inputs / "WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt"
    if not path.is_file():
        raise HarnessBlock("Synthetic wrong-role credential handoff is missing.")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1); values[key.strip()] = value
    username = values.get("username", "").strip().lower(); credential_value = values.get(CREDENTIAL_FIELD, "")
    if username != "developer04e.local" or not credential_value:
        raise HarnessBlock("Synthetic wrong-role credential handoff is malformed.")
    return username, credential_value


def _live_wrong_role_login_probe(repo: Path, inputs: Path) -> dict[str, Any]:
    if not port_open(8787):
        raise HarnessBlock("API must be running before the live wrong-role credential probe.")
    username, credential_value = _read_wrong_role_credentials(inputs)
    jar = http.cookiejar.CookieJar(); opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    body = json.dumps({"username": username, CREDENTIAL_FIELD: credential_value}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8787/api/v1/auth/login", data=body, method="POST", headers={"Content-Type":"application/json","Origin":"http://127.0.0.1:5173"})
    try:
        with opener.open(req, timeout=5) as response:
            status = int(response.status); payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HarnessBlock(f"Live API wrong-role login probe failed HTTP {exc.code}; credential/runtime auth-store parity is not proven.") from exc
    if status != 200:
        raise HarnessBlock(f"Live API wrong-role login probe expected HTTP 200, got {status}.")
    session = payload.get("session") or {}; principal = session.get("principal") or {}
    if principal.get("username") != "developer04e.local" or principal.get("roles") != ["developer"]:
        raise HarnessBlock(f"Live API wrong-role login authenticated unexpected principal/roles: {principal}")
    csrf = next((c.value for c in jar if c.name == "devpilot_csrf"), "")
    if not csrf:
        raise HarnessBlock("Live API wrong-role probe did not receive the CSRF cookie needed for the RBAC probe.")
    # Critical Recovery-005 check: the canonical wrong-role must be able to
    # inspect its own safe session envelope, otherwise the UI cannot render the
    # authenticated shell and B11 degenerates into an auth-bootstrap failure.
    session_req = urllib.request.Request("http://127.0.0.1:8787/api/v1/auth/session", method="GET", headers={"Origin":"http://127.0.0.1:5173"})
    try:
        with opener.open(session_req, timeout=5) as response:
            session_status = int(response.status); session_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        session_status = int(exc.code); session_payload = {}
    if session_status != 200:
        raise HarnessBlock(f"Canonical wrong-role must inspect its authenticated session before browser B11; GET /auth/session returned HTTP {session_status}.")
    safe_principal = ((session_payload.get("session") or {}).get("principal") or {}) if isinstance(session_payload, dict) else {}
    if safe_principal.get("username") != "developer04e.local" or safe_principal.get("roles") != ["developer"]:
        raise HarnessBlock(f"Safe session envelope returned unexpected wrong-role principal: {safe_principal}")
    approval_probe = urllib.request.Request("http://127.0.0.1:8787/api/v1/approvals/APPROVAL-GSDLC04E-RBAC-PROBE/approve", data=b"{}", method="POST", headers={"Content-Type":"application/json","Origin":"http://127.0.0.1:5173","X-DevPilot-CSRF":csrf})
    try:
        with opener.open(approval_probe, timeout=5) as response:
            approval_status = int(response.status); approval_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        approval_status = int(exc.code)
        try: approval_payload = json.loads(exc.read().decode("utf-8"))
        except Exception: approval_payload = {}
    if approval_status != 403:
        raise HarnessBlock(f"Wrong-role approval RBAC probe expected HTTP 403, got {approval_status}.")
    findings = approval_payload.get("findings") if isinstance(approval_payload, dict) else None
    finding_id = ""
    if isinstance(findings, list) and findings and isinstance(findings[0], dict):
        finding_id = str(findings[0].get("id") or "")
    if not finding_id:
        finding_id = str(((approval_payload.get("error") or {}).get("finding_id") or (approval_payload.get("error") or {}).get("code") or approval_payload.get("finding_id") or ""))
    if finding_id != "RBAC_ROLE_DENY":
        raise HarnessBlock(f"Canonical wrong-role approval probe must return RBAC_ROLE_DENY, got {finding_id or 'missing'}.")
    session_token = next((c.value for c in jar if c.name == "devpilot_session"), "")
    if not session_token:
        raise HarnessBlock("Live API wrong-role probe did not receive the opaque session cookie needed for safe local revocation.")
    try:
        from devpilot_core.application.auth_service import AuthApplicationService
        revocation = AuthApplicationService(repo).logout(token=session_token, csrf_token=csrf)
    except Exception as exc:
        raise HarnessBlock(f"Live API wrong-role verification session could not be revoked through runtime AuthApplicationService: {type(exc).__name__}.") from exc
    if not getattr(revocation, "revoked", False):
        raise HarnessBlock("Live API wrong-role verification session was not revoked cleanly.")
    return {
        "live_api_login_verified": True,
        "http_status": 200,
        "username": "developer04e.local",
        "roles": ["developer"],
        "auth_session_http_status": session_status,
        "auth_session_renderable": True,
        "wrong_role_approval_http_status": approval_status,
        "wrong_role_approval_denied": True,
        "wrong_role_finding_id": finding_id,
        "verification_session_revoked": True,
        "verification_session_revocation_authority": "runtime-auth-application-service",
        "password_exposed": False,
    }


def wrong_role_auth_prepare(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if not port_open(8787) or not port_open(5173):
        raise HarnessBlock("API/UI must remain READY before wrong-role-auth-prepare.")
    provisioned = provision_wrong_role(repo, fixture, inputs)
    live = _live_wrong_role_login_probe(repo, inputs)
    payload={"status":"PASS","step":"wrong-role-auth-prepare","timestamp":now(),"corrective_level":CORRECTIVE_LEVEL,"wrong_role_identity":{k:v for k,v in provisioned.items() if k!="credentials_file"},"live_api_probe":live,"credentials_file_present":True,"credentials_secret_in_evidence":False,"runtime_auth_store_root":str(repo),"full_regression_runs":0,"pilot_workspace_accessed":False}
    write_evidence(evidence,"13_wrong_role_auth_prepare_v1_0_5.json",payload,replace=True); return payload


def wrong_role_auth_cleanup(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    payload = _fixture_identity_call(repo, fixture, inputs, "cleanup")
    (inputs / "VIEWER_LOGIN_DO_NOT_ATTACH.txt").unlink(missing_ok=True)
    if (inputs / "WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt").exists():
        raise HarnessBlock("Synthetic wrong-role credential handoff still exists after cleanup.")
    result={"status":"PASS","step":"wrong-role-auth-cleanup","timestamp":now(),"corrective_level":CORRECTIVE_LEVEL,"username":"developer04e.local","role":"developer","runtime_identity_removed":bool(payload.get("runtime_identity_removed")),"legacy_runtime_viewer_removed":bool(payload.get("legacy_runtime_viewer_removed")),"credentials_removed":bool(payload.get("credentials_removed")),"secret_exposed":False,"full_regression_runs":0,"pilot_workspace_accessed":False}
    write_evidence(evidence,"14_wrong_role_auth_cleanup_v1_0_5.json",result,replace=True); return result

def prepare_browser(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if fixture.resolve() != Path(DEFAULT_FIXTURE).resolve():
        raise HarnessBlock(f"Fixture must be exactly {DEFAULT_FIXTURE}.")
    low = str(fixture).lower()
    if "inventory-sales-local" in low or "devpilot_workspaces" in low:
        raise HarnessBlock("Real pilot workspace is forbidden during GSDLC-04-E.")
    expected = expected_fixture_bytes(); reused = False
    if fixture.exists() and any(fixture.iterdir()):
        if not (fixture / ".git").exists():
            raise HarnessBlock("Existing browser fixture is not Git; refusing overwrite.")
        rows = git_status(fixture)
        if rows:
            raise HarnessBlock(f"Existing fixture has surviving source state: {rows}. Do not reset/clean; resume later or preserve for diagnosis.")
        tracked = set(git(fixture, "ls-files").stdout.splitlines())
        if tracked != set(expected):
            raise HarnessBlock(f"Existing fixture tracked set differs from controlled baseline: {sorted(tracked)}")
        for rel, body in expected.items():
            if canonical((fixture / rel).read_bytes()) != canonical(body):
                raise HarnessBlock(f"Existing fixture baseline differs: {rel}")
        reused = True
    else:
        for rel, body in expected.items():
            path = fixture / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
        git(fixture, "init")
        git(fixture, "config", "user.name", "DevPilot GSDLC 04-E Fixture")
        git(fixture, "config", "user.email", "devpilot-gsdlc04e@local.invalid")
        git(fixture, "add", *BASELINE_TRACKED)
        git(fixture, "commit", "-m", "test(gsdlc-04-e): browser fixture baseline")
    if git_status(fixture):
        raise HarnessBlock("Fixture is not Git-clean after preparation.")

    inputs.mkdir(parents=True, exist_ok=True)
    controlled = {
        "valid_review_source.md": valid_review_bytes(),
        "invalid_review_source.md": b"# Missing governed frontmatter\n\nBrowser finding navigation case.\n",
        "upload_source.md": b'''---\ndoc_id: "GSDLC-04-E-UPLOAD"\ntitle: "Upload source"\nstatus: "draft"\nversion: "1.0.0"\nowner: "owner.local"\nupdated: "2026-08-22"\napproval: "pending"\n---\n# Upload source\n\nSupported Markdown upload.\n''',
        "import_source.json": b'{"doc_id":"GSDLC-04-E-IMPORT","title":"Import JSON","status":"draft","version":"1.0.0"}\n',
        "unsupported_payload.exe": b"MZ synthetic-non-executable-browser-fixture-only\x00\x01",
        "external_edit_append.txt": b"\nExternal editor drift accepted only for GSDLC-04-E browser fixture.\n",
    }
    for name, body in controlled.items():
        path = inputs / name
        if path.exists() and path.read_bytes() != body:
            raise HarnessBlock(f"Controlled browser input differs; refusing overwrite: {path}")
        path.write_bytes(body)

    wrong_role = provision_wrong_role(repo, fixture, inputs)
    evidence.mkdir(parents=True, exist_ok=True); (evidence / "browser").mkdir(parents=True, exist_ok=True)
    template = repo / "docs/audits/DEVPL_GSDLC_04_E_MANUAL_BROWSER_OBSERVATIONS_TEMPLATE.md"
    obs = evidence / OBS_NAME
    if not obs.exists():
        shutil.copyfile(template, obs); observation_action = "created"
    else:
        observation_action = "preserved-existing"
    baseline = {rel: {"raw_sha256": sha(path), "canonical_lf_sha256": sha_bytes(canonical(path.read_bytes()))} for rel, path in fixture_paths(fixture).items()}
    payload = {
        "status": "PASS", "step": "prepare-browser", "timestamp": now(), "fixture": str(fixture), "fixture_reused": reused,
        "fixture_git_head": git(fixture, "rev-parse", "HEAD").stdout.strip(), "fixture_git_clean": True,
        "baseline_sources": baseline, "browser_inputs": str(inputs), "input_hashes": {name: sha_bytes(body) for name, body in controlled.items()},
        "wrong_role_identity": wrong_role, "expected_final_dirty_path": TARGET_ARTIFACT, "invalid_target_must_not_exist": INVALID_TARGET,
        "observation_file": str(obs), "observation_action": observation_action, "pilot_workspace_accessed": False, "runtime_db_copied": False,
    }
    write_evidence(evidence, "10_prepare_browser.json", payload, replace=True)
    return payload


def provision_check(repo: Path, evidence: Path) -> dict[str, Any]:
    py = repo / ".venv/Scripts/python.exe"; npm = shutil.which("npm.cmd") or shutil.which("npm")
    payload = {"status": "PASS", "step": "provision-check", "timestamp": now(), "venv_python": str(py), "venv_python_exists": py.is_file(), "npm": npm, "node_modules_exists": (repo / "ui/web/node_modules").is_dir(), "network_used": False}
    if os.name == "nt" and not py.is_file(): raise HarnessBlock("Missing .venv\\Scripts\\python.exe.")
    if not npm: raise HarnessBlock("npm.cmd/npm is unavailable.")
    if not (repo / "ui/web/node_modules").is_dir(): raise HarnessBlock("ui/web/node_modules is missing; no silent network provisioning is authorized.")
    write_evidence(evidence, "09_provision_check.json", payload, replace=True); return payload


def baseline_equivalence(fixture: Path) -> dict[str, Any]:
    state: dict[str, Any] = {}; all_ok = True
    for rel, path in fixture_paths(fixture).items():
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(fixture), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
        if blob.returncode != 0: raise HarnessBlock(f"Unable to read immutable fixture Git blob: {rel}")
        raw = path.read_bytes(); current = canonical(raw); expected = canonical(blob.stdout); equivalent = current == expected
        state[rel] = {"raw_sha256": sha_bytes(raw), "canonical_lf_sha256": sha_bytes(current), "expected_git_blob_canonical_lf_sha256": sha_bytes(expected), "git_content_equivalent_to_head": equivalent, "eol_only_representation_difference": raw != blob.stdout and equivalent}
        all_ok = all_ok and equivalent
    return {"all_baseline_sources_unchanged": all_ok, "source_state": state, "authority": "git-blob+canonical-lf"}


def browser_preflight(repo: Path, fixture: Path, inputs: Path, evidence: Path) -> dict[str, Any]:
    if port_open(8787) or port_open(5173): raise HarnessBlock("Ports 8787/5173 must be free before browser-preflight.")
    if not (evidence / OBS_NAME).is_file(): raise HarnessBlock("Manual observations file missing; run prepare-browser first.")
    for name in ["valid_review_source.md","invalid_review_source.md","upload_source.md","import_source.json","unsupported_payload.exe","WRONG_ROLE_LOGIN_DO_NOT_ATTACH.txt"]:
        if not (inputs / name).is_file(): raise HarnessBlock(f"Missing controlled browser input: {inputs/name}")
    rows = git_status(fixture); eq = baseline_equivalence(fixture)
    if rows or not eq["all_baseline_sources_unchanged"]: raise HarnessBlock(f"Fixture must be Git-clean and baseline-equivalent before browser runtime. status={rows}")
    payload={"status":"PASS","step":"browser-preflight","timestamp":now(),"ports_free":True,"fixture_git_clean":True,**eq,"fixture_binding_required":str(fixture),"pilot_workspace_accessed":False,"full_regression_runs":0}
    write_evidence(evidence,"12_browser_preflight.json",payload,replace=True); return payload


def runtime_status(evidence: Path, fixture: Path) -> dict[str, Any]:
    if not port_open(8787) or not port_open(5173): raise HarnessBlock(f"Runtime is not ready. api_8787={port_open(8787)} ui_5173={port_open(5173)}")
    states={}
    for role in ["api","ui"]:
        path=evidence/"runtime"/f"{role}_console_state.json"
        if not path.is_file(): raise HarnessBlock(f"Missing runtime console state: {path}")
        data=json.loads(path.read_text(encoding="utf-8"));
        if data.get("status")!="PASS" or data.get("version")!=RUNTIME_CONSOLE_VERSION: raise HarnessBlock(f"Invalid runtime state for {role}: expected runtime version={RUNTIME_CONSOLE_VERSION} actual={data.get('version')} state={data}")
        states[role]=data
    binding=states["api"].get("workspace_binding") or {}
    if Path(str(binding.get("active_workspace_root", ""))).resolve()!=fixture.resolve() or binding.get("scope")!="gsdlc-04-e-browser-fixture-only": raise HarnessBlock("API runtime is not bound exclusively to 04-E browser fixture.")
    payload={"status":"PASS","step":"runtime-status","timestamp":now(),"api_ready":True,"ui_ready":True,"api_url":"http://127.0.0.1:8787/api/v1/health","ui_url":"http://127.0.0.1:5173/","three_console_runtime_required":True,"workspace_binding":binding}
    write_evidence(evidence,"runtime/runtime_status.json",payload); return payload


def _task_image(pid: int) -> str | None:
    if os.name != "nt": return None
    cp=subprocess.run(["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20,shell=False)
    if cp.returncode!=0 or "No tasks are running" in cp.stdout:return None
    line=cp.stdout.strip().splitlines()[0] if cp.stdout.strip() else ""; return line.split(",")[0].strip('"') if line else None


def stop_role(evidence: Path, role: str) -> dict[str, Any]:
    port=8787 if role=="api" else 5173; path=evidence/"runtime"/f"{role}_console_state.json"
    if not path.is_file():
        if port_open(port): raise HarnessBlock(f"Port {port} occupied without trusted 04-E PID state; unknown process will not be killed.")
        return {"role":role,"stopped":True,"already_stopped":True}
    data=json.loads(path.read_text(encoding="utf-8")); child=int(data.get("child_pid") or 0); launcher=int(data.get("launcher_pid") or 0)
    if not port_open(port): return {"role":role,"child_pid":child,"stopped":True,"already_stopped":True}
    if os.name!="nt": raise HarnessBlock("PID-safe runtime stop is Windows-authoritative.")
    image=(_task_image(launcher) or "").lower()
    if image not in {"python.exe","pythonw.exe","py.exe"}: raise HarnessBlock(f"Stale/unsafe launcher PID for {role}: {launcher}")
    if child<=0: raise HarnessBlock(f"Invalid child PID for {role}.")
    cp=subprocess.run(["taskkill","/PID",str(child),"/T","/F"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30,shell=False)
    if cp.returncode!=0 and port_open(port): raise HarnessBlock(f"Unable to stop {role} PID {child}: {cp.stdout}")
    time.sleep(.7); return {"role":role,"launcher_pid":launcher,"child_pid":child,"stopped":not port_open(port),"output":cp.stdout[-2000:]}


def runtime_stop_api(evidence: Path) -> dict[str, Any]:
    result=stop_role(evidence,"api")
    if port_open(8787): raise HarnessBlock("API port remains occupied after stop-api.")
    if not port_open(5173): raise HarnessBlock("UI must remain running during API-down recovery scenario.")
    payload={"status":"PASS","step":"runtime-stop-api","timestamp":now(),"result":result,"api_port_free":True,"ui_still_ready":True}
    write_evidence(evidence,"runtime/runtime_stop_api.json",payload,replace=True); return payload


def runtime_stop(evidence: Path) -> dict[str, Any]:
    results=[stop_role(evidence,"api"),stop_role(evidence,"ui")]; time.sleep(.8)
    if port_open(8787) or port_open(5173): raise HarnessBlock("Ports remain occupied after runtime-stop.")
    payload={"status":"PASS","step":"runtime-stop","timestamp":now(),"results":results,"ports_free":True,"stale_pid_kill_allowed":False}
    write_evidence(evidence,f"runtime/runtime_stop_{int(time.time())}.json",payload); return payload


def latest_review(repo: Path, relative_path: str, statuses: set[str]) -> dict[str, Any] | None:
    root=repo/"outputs/artifact_reviews/gsdlc_04_d"; candidates=[]
    if not root.is_dir(): return None
    for path in root.rglob("*.json"):
        try:data=json.loads(path.read_text(encoding="utf-8"))
        except Exception:continue
        if data.get("relative_path")==relative_path and data.get("status") in statuses:candidates.append((path.stat().st_mtime,data))
    return sorted(candidates,key=lambda x:x[0])[-1][1] if candidates else None


def state_file_git_parity(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    rows=git_status(fixture); paths=sorted(dirty_path(x) for x in rows)
    if paths != [TARGET_ARTIFACT]: raise HarnessBlock(f"Final browser fixture must have exactly external-drift target dirty; actual={paths}")
    target=fixture/TARGET_ARTIFACT
    if not target.is_file(): raise HarnessBlock("External-drift target missing.")
    if (fixture/INVALID_TARGET).exists(): raise HarnessBlock("Invalid findings-only target was written unexpectedly.")
    eq=baseline_equivalence(fixture)
    if not eq["all_baseline_sources_unchanged"]: raise HarnessBlock("Tracked baseline files do not match immutable Git blobs after browser closure.")
    review=latest_review(repo,TARGET_ARTIFACT,{"REVALIDATION_REQUIRED"})
    if not review: raise HarnessBlock("No REVALIDATION_REQUIRED review found for final external-edit target.")
    rec=review.get("reconciliation") or {}
    if review.get("approval_valid") is not False or rec.get("status")!="REVALIDATION_REQUIRED" or rec.get("change_kind")!="modified": raise HarnessBlock(f"Review reconciliation does not prove modified drift + stale approval invalidation: {rec}")
    if rec.get("auto_reverted") is not False or rec.get("hidden_merge") is not False: raise HarnessBlock("External drift was auto-reverted or hidden-merged, which is forbidden.")
    if not str(rec.get("git_diff") or "").strip(): raise HarnessBlock("Git diff is missing from reconciliation evidence.")
    provenance=rec.get("source_provenance") or {}
    if provenance.get("source_type")!="EXTERNAL_EDITOR": raise HarnessBlock("Reconciled provenance did not record EXTERNAL_EDITOR.")
    payload={"status":"PASS","step":"state-file-git-parity","timestamp":now(),"actual_dirty_paths":paths,"unexpected_source_writes_total":0,"review_id":review.get("review_id"),"review_status":review.get("status"),"approval_valid":review.get("approval_valid"),"approved_sha256":review.get("approved_sha256"),"current_source_sha256":sha(target),"change_kind":rec.get("change_kind"),"auto_reverted":rec.get("auto_reverted"),"hidden_merge":rec.get("hidden_merge"),"git_branch_at_freeze":rec.get("git_branch_at_freeze"),"git_branch_current":rec.get("git_branch_current"),"git_diff_present":True,"source_type":provenance.get("source_type"),"external_operator_project_writes":0,"pilot_workspace_accessed":False,**eq}
    write_evidence(evidence,"18_state_file_git_parity.json",payload,replace=True); return payload



def _api_log_lines(evidence: Path) -> list[str]:
    path = evidence / "runtime" / "api_console.log"
    if not path.is_file():
        raise HarnessBlock(f"API console log missing: {path}")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _last_match(lines: list[str], pattern: re.Pattern[str], *, start: int = 0) -> tuple[int, re.Match[str]] | None:
    found: tuple[int, re.Match[str]] | None = None
    for index in range(max(0, start), len(lines)):
        match = pattern.search(lines[index])
        if match:
            found = (index, match)
    return found


def _execution_record(repo: Path, execution_id: str) -> tuple[Path, dict[str, Any]]:
    candidates = [repo / "outputs" / "uoc005_control" / "records" / f"{execution_id}.json"]
    outputs = repo / "outputs"
    if outputs.is_dir():
        for path in outputs.glob(f"**/records/{execution_id}.json"):
            if path not in candidates:
                candidates.append(path)
    for path in candidates:
        if path.is_file():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise HarnessBlock(f"Unable to parse UOC-005 execution record {path}: {exc}") from exc
            return path, payload
    raise HarnessBlock(f"UOC-005 execution record not found for {execution_id}; expected under repo outputs/uoc005_control.")


def _latest_b15_execution(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    baseline = fixture / "docs/baseline.md"
    if not baseline.is_file():
        raise HarnessBlock("B15 baseline source is missing.")
    blob = subprocess.run(["git", "show", "HEAD:docs/baseline.md"], cwd=str(fixture), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
    if blob.returncode != 0:
        raise HarnessBlock("Unable to read immutable Git preimage for docs/baseline.md.")
    pre_raw = blob.stdout
    current_raw = baseline.read_bytes()
    lines = _api_log_lines(evidence)
    apply_re = re.compile(r'POST /api/v1/workspace/edit-plans/(?P<plan>eplan_[A-Za-z0-9_-]+)/apply HTTP/1\.1" 200 OK')
    applied = _last_match(lines, apply_re)
    if not applied:
        raise HarnessBlock("No successful B15 workspace apply was found in API evidence.")
    apply_index, apply_match = applied
    exec_re = re.compile(r'GET /api/v1/workspace/edit-executions/(?P<execution>uedit_[A-Za-z0-9_-]+) HTTP/1\.1" 200 OK')
    execution = _last_match(lines, exec_re, start=apply_index)
    if not execution:
        raise HarnessBlock("Successful B15 apply exists but no recoverable execution ID was observed.")
    execution_index, execution_match = execution
    execution_id = execution_match.group("execution")
    record_path, record = _execution_record(repo, execution_id)
    if str(record.get("relative_path") or "") != "docs/baseline.md":
        raise HarnessBlock(f"Latest UOC-005 execution is not B15 baseline.md: {record.get('relative_path')!r}")
    rollback_req = re.compile(rf'POST /api/v1/workspace/edit-executions/{re.escape(execution_id)}/rollback-approval-request HTTP/1\.1" 200 OK')
    rollback_request_seen = _last_match(lines, rollback_req, start=execution_index) is not None
    current_sha = sha(baseline)
    pre_sha = str(record.get("pre_sha256") or "")
    post_sha = str(record.get("post_sha256") or "")
    record_status = str(record.get("status") or "")
    git_pre_raw_sha = sha_bytes(pre_raw)
    current_git_equivalent = canonical(current_raw) == canonical(pre_raw)
    marker_present = ROLLBACK_MARKER.encode("utf-8") in canonical(current_raw)
    dirty = sorted(dirty_path(row) for row in git_status(fixture))
    return {
        "plan_id": apply_match.group("plan"),
        "execution_id": execution_id,
        "execution_record_path": str(record_path),
        "execution_status": record_status,
        "record_pre_sha256": pre_sha,
        "record_post_sha256": post_sha,
        "git_preimage_raw_sha256": git_pre_raw_sha,
        "current_raw_sha256": current_sha,
        "current_git_equivalent": current_git_equivalent,
        "temporary_marker_present": marker_present,
        "rollback_approval_started": rollback_request_seen,
        "actual_dirty_paths": dirty,
        "api_log_lines": len(lines),
        "record": record,
    }


def classify_b15_resume(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    state = _latest_b15_execution(repo, fixture, evidence)
    if state["rollback_approval_started"]:
        raise HarnessBlock("B15 rollback approval has already started; preserve evidence and diagnose before replaying any B15 operation.")
    expected_applied_dirty = sorted([TARGET_ARTIFACT, "docs/baseline.md"])
    expected_clean_baseline_dirty = [TARGET_ARTIFACT]
    if state["execution_status"] == "applied" and state["current_raw_sha256"] == state["record_post_sha256"]:
        if state["actual_dirty_paths"] != expected_applied_dirty:
            raise HarnessBlock(f"B15 applied execution exists but dirty scope is unexpected: {state['actual_dirty_paths']}")
        mode = "ROLLBACK_ONLY"
        reason = "Persisted UOC-005 execution is applied and the current source still equals its exact post SHA."
    elif state["execution_status"] == "applied" and state["current_git_equivalent"]:
        if state["actual_dirty_paths"] != expected_clean_baseline_dirty:
            raise HarnessBlock(f"B15 source is Git-preimage-equivalent but dirty scope is unexpected: {state['actual_dirty_paths']}")
        mode = "REPLAY_B15"
        reason = "The previous execution record remains applied, but the source has already returned to the immutable Git preimage without a recorded rollback request; the old execution is stale for rollback and B15 must be replayed once from the clean preimage."
    elif state["execution_status"] == "rolled-back-manual" and state["current_git_equivalent"]:
        if state["actual_dirty_paths"] != expected_clean_baseline_dirty:
            raise HarnessBlock(f"B15 is already rolled back but dirty scope is unexpected: {state['actual_dirty_paths']}")
        mode = "ALREADY_ROLLED_BACK"
        reason = "Execution record already proves rolled-back-manual and source equals immutable Git preimage."
    else:
        raise HarnessBlock(
            "B15 state is neither rollback-eligible nor safely replayable: "
            f"execution_status={state['execution_status']} current_sha={state['current_raw_sha256']} "
            f"pre_sha={state['record_pre_sha256']} post_sha={state['record_post_sha256']} "
            f"git_equivalent={state['current_git_equivalent']} marker={state['temporary_marker_present']} dirty={state['actual_dirty_paths']}"
        )
    return {**{k:v for k,v in state.items() if k != "record"}, "resume_mode": mode, "resume_reason": reason}


def b15_state(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    state = classify_b15_resume(repo, fixture, evidence)
    payload = {"status":"PASS", "step":"b15-state", "timestamp":now(), **state, "full_regression_runs":0, "pilot_workspace_accessed":False}
    write_evidence(evidence, "15_b15_state_v1_0_11.json", payload, replace=True)
    return payload


def _http_log_count(lines: list[str], method: str, path: str, status_code: int, *, start: int = 0) -> int:
    pattern = re.compile(rf'(?:^|[\"\s]){re.escape(method.upper())} {re.escape(path)} HTTP/1\.[01]\" {int(status_code)}(?:\s|$)')
    return sum(1 for line in lines[start:] if pattern.search(line))


def _http_log_any(lines: list[str], method: str, path: str, status_code: int, *, start: int = 0) -> bool:
    return _http_log_count(lines, method, path, status_code, start=start) > 0


def rollback_preflight(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    state = classify_b15_resume(repo, fixture, evidence)
    if state["resume_mode"] != "ROLLBACK_ONLY":
        raise HarnessBlock(f"B15 is not rollback-ready; resume_mode={state['resume_mode']}. If REPLAY_B15, replay only B15 from the clean preimage and run rollback-preflight immediately after the new apply.")
    if not port_open(8787) or not port_open(5173):
        raise HarnessBlock(f"B15 rollback continuation requires fresh API/UI runtime. api_8787={port_open(8787)} ui_5173={port_open(5173)}")
    lines = _api_log_lines(evidence)
    execution_id = state["execution_id"]
    execution_index = next((i for i,line in enumerate(lines) if f"/workspace/edit-executions/{execution_id}" in line), 0)
    draft_conflict = any("/workspace/artifact-drafts/" in line and ' 403 ' in line for line in lines[execution_index + 1:])
    rollback_endpoint = f"/api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request"
    rollback_post_endpoint = f"/api/v1/workspace/edit-executions/{execution_id}/rollback"
    start_index = execution_index + 1
    prior_unauthorized = _http_log_count(lines, "POST", rollback_endpoint, 401, start=start_index)
    prior_success = _http_log_count(lines, "POST", rollback_endpoint, 200, start=start_index)
    prior_options_success = _http_log_count(lines, "OPTIONS", rollback_endpoint, 200, start=start_index)
    prior_rollback_success = _http_log_count(lines, "POST", rollback_post_endpoint, 200, start=start_index)
    if prior_success:
        raise HarnessBlock("B15 rollback approval POST HTTP 200 already exists in prior evidence; do not create another approval until that exact approval is adjudicated.")
    if prior_rollback_success:
        raise HarnessBlock("B15 rollback POST HTTP 200 already exists; preserve evidence for exact execution adjudication.")
    doc_id = ""
    doc_re = re.compile(r'GET /api/v1/workspace/documents/(?P<document>doc_[A-Za-z0-9_-]+) HTTP/1\.1" 200 OK')
    for index in range(len(lines)-1, -1, -1):
        match = doc_re.search(lines[index])
        if match:
            doc_id = match.group("document")
            break
    resume_url = f"http://127.0.0.1:5173/workspace/documents?execution={execution_id}"
    if doc_id:
        resume_url += f"&document={doc_id}"
    payload = {
        "status":"PASS", "step":"rollback-preflight", "timestamp":now(),
        "corrective_level": CORRECTIVE_LEVEL,
        "execution_id":execution_id, "plan_id":state["plan_id"], "document_id":doc_id or None,
        "execution_record_path":state["execution_record_path"], "execution_status":state["execution_status"],
        "baseline_pre_sha256":state["record_pre_sha256"], "baseline_applied_sha256":state["record_post_sha256"],
        "current_source_sha256":state["current_raw_sha256"], "temporary_marker_present":state["temporary_marker_present"],
        "actual_dirty_paths":state["actual_dirty_paths"], "manual_draft_preimage_conflict_observed":draft_conflict,
        "manual_draft_conflict_interpretation":"expected-post-apply-runtime-draft-conflict; does not invalidate persisted UOC-005 execution",
        "prior_rollback_post_401_total": prior_unauthorized,
        "prior_rollback_post_200_total": prior_success,
        "prior_rollback_options_200_total": prior_options_success,
        "prior_rollback_http_200_total": prior_rollback_success,
        "http_log_method_aware": True,
        "prior_rollback_unauthorized_total": prior_unauthorized,
        "prior_rollback_success_total": prior_success,
        "owner_reauthentication_required": prior_unauthorized > 0,
        "approval_ui_mode":"inline-rollback-approval-card",
        "approval_center_required":False,
        "approval_center_navigation_for_rollback":"PROHIBITED_BY_RECOVERY_GUIDE",
        "browser_session_fresh_required":True,
        "runtime_console_version_expected":RUNTIME_CONSOLE_VERSION,
        "rollback_approval_started":False, "api_log_lines_at_preflight":len(lines), "resume_url":resume_url,
        "full_regression_runs":0, "pilot_workspace_accessed":False,
    }
    write_evidence(evidence, ROLLBACK_PREFLIGHT, payload, replace=True)
    return payload

def rollback_verify(repo: Path, fixture: Path, evidence: Path) -> dict[str, Any]:
    preflight_path = evidence / ROLLBACK_PREFLIGHT
    if not preflight_path.is_file():
        raise HarnessBlock("B15 rollback preflight evidence is missing.")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS":
        raise HarnessBlock("B15 rollback preflight did not PASS.")
    execution_id = str(preflight.get("execution_id") or "")
    start = int(preflight.get("api_log_lines_at_preflight") or 0)
    if not execution_id:
        raise HarnessBlock("B15 rollback preflight has no execution ID.")
    lines = _api_log_lines(evidence)
    tail = lines[start:]
    request_re = re.compile(rf'POST /api/v1/workspace/edit-executions/{re.escape(execution_id)}/rollback-approval-request HTTP/1\.1" 200 OK')
    rollback_re = re.compile(rf'POST /api/v1/workspace/edit-executions/{re.escape(execution_id)}/rollback HTTP/1\.1" 200 OK')
    request_index = next((i for i,line in enumerate(tail) if request_re.search(line)), -1)
    rollback_index = next((i for i,line in enumerate(tail) if rollback_re.search(line)), -1)
    if request_index < 0:
        raise HarnessBlock("B15 rollback approval request HTTP 200 was not observed.")
    if rollback_index < 0 or rollback_index <= request_index:
        raise HarnessBlock("B15 governed rollback HTTP 200 was not observed after its approval request.")
    approval_re = re.compile(r'POST /api/v1/approvals/(?P<approval>APPROVAL-[A-Za-z0-9_-]+)/approve HTTP/1\.1" 200 OK')
    approval = next((approval_re.search(tail[i]) for i in range(request_index+1,rollback_index) if approval_re.search(tail[i])), None)
    if not approval:
        raise HarnessBlock("B15 separate human rollback approval HTTP 200 was not observed.")
    record_path, record = _execution_record(repo, execution_id)
    if str(record.get("status") or "") != "rolled-back-manual":
        raise HarnessBlock(f"B15 rollback endpoint returned 200 but execution record status is {record.get('status')!r}, not rolled-back-manual.")
    baseline = fixture / "docs/baseline.md"
    blob = subprocess.run(["git","show","HEAD:docs/baseline.md"],cwd=str(fixture),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,shell=False)
    if blob.returncode != 0 or not baseline.is_file():
        raise HarnessBlock("B15 restored baseline cannot be read.")
    expected = canonical(blob.stdout); actual = canonical(baseline.read_bytes())
    if actual != expected:
        raise HarnessBlock("B15 rollback endpoint returned 200 but docs/baseline.md does not equal its immutable Git preimage.")
    if ROLLBACK_MARKER.encode("utf-8") in actual:
        raise HarnessBlock("B15 temporary rollback marker remains in source after rollback.")
    dirty = sorted(dirty_path(row) for row in git_status(fixture))
    if dirty != [TARGET_ARTIFACT]:
        raise HarnessBlock(f"B15 rollback left partial/unexpected fixture writes: {dirty}")
    partials = [str(path.relative_to(fixture)).replace("\\","/") for path in (fixture/"docs").glob("*tmp*") if path.is_file()]
    if partials:
        raise HarnessBlock(f"B15 rollback left temporary/partial files: {partials}")
    restored = sha(baseline)
    if restored != str(record.get("pre_sha256") or ""):
        raise HarnessBlock("B15 restored source SHA does not equal the persisted UOC-005 execution pre SHA.")
    if restored != str(record.get("rollback",{}).get("restored_sha256") or ""):
        raise HarnessBlock("B15 execution record rollback restored SHA does not match the actual restored source.")
    payload = {
        "status":"PASS", "step":"rollback-verify", "timestamp":now(), "corrective_level":CORRECTIVE_LEVEL, "execution_id":execution_id,
        "execution_record_path":str(record_path), "execution_status":"rolled-back-manual", "rollback_approval_id":approval.group("approval"),
        "rollback_http_status":200, "baseline_pre_sha256":record.get("pre_sha256"), "baseline_post_sha256":record.get("post_sha256"),
        "restored_sha256":restored, "restored_preimage":True, "temporary_marker_present":False,
        "partial_writes_total":0, "actual_dirty_paths":dirty, "unexpected_source_writes_total":0,
        "full_regression_runs":0, "pilot_workspace_accessed":False,
    }
    write_evidence(evidence, ROLLBACK_VERIFY, payload, replace=True)
    return payload


def parse_observations(path: Path) -> tuple[dict[str, tuple[str,str]],dict[str,str],str,str]:
    text=path.read_text(encoding="utf-8"); required=["<!-- BEGIN_BROWSER_MATRIX -->","<!-- END_BROWSER_MATRIX -->","<!-- BEGIN_BROWSER_SUMMARY -->","<!-- END_BROWSER_SUMMARY -->"]
    if any(m not in text for m in required): raise HarnessBlock("Observation delimiters missing.")
    matrix=text.split(required[0],1)[1].split(required[1],1)[0]; rows={}
    for line in matrix.splitlines():
        if not line.strip().startswith("|") or "---" in line or "Caso" in line: continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells)>=4: rows[cells[0]]=(cells[1],cells[3])
    summary=text.split(required[2],1)[1].split(required[3],1)[0]; values={}
    for line in summary.splitlines():
        m=re.match(r"\s*-\s*`([^`]+)`:\s*(\S+)\s*$",line)
        if m: values[m.group(1)]=m.group(2)
    dm=re.search(r"^- Decisión:\s*(.+?)\s*$",text,flags=re.MULTILINE); jm=re.search(r"^- Justificación:\s*(.+?)\s*$",text,flags=re.MULTILINE)
    return rows,values,dm.group(1).strip() if dm else "",jm.group(1).strip() if jm else ""


def browser_evidence_validate(evidence: Path) -> dict[str, Any]:
    obs=evidence/OBS_NAME
    if not obs.is_file(): raise HarnessBlock(f"Observation file missing: {obs}")
    rows,values,decision,justification=parse_observations(obs)
    missing=[x for x in EXPECTED_CASES if x not in rows]; nonpass=[x for x in EXPECTED_CASES if rows.get(x,("",""))[0]!="PASS"]; blank=[x for x in EXPECTED_CASES if not rows.get(x,("",""))[1].strip()]
    browser=evidence/"browser"; missing_shots=[x for x in REQUIRED_SCREENSHOTS if not (browser/x).is_file() or (browser/x).stat().st_size<1000]
    invalid_summary={k:(values.get(k),v) for k,v in SUMMARY_EXPECTED.items() if values.get(k)!=v}
    parity=evidence/"18_state_file_git_parity.json"
    if not parity.is_file() or json.loads(parity.read_text(encoding="utf-8")).get("status")!="PASS": raise HarnessBlock("Final state/file/Git parity PASS is required before browser evidence validation.")
    wrong_prepare=evidence/"13_wrong_role_auth_prepare_v1_0_5.json"; wrong_cleanup=evidence/"14_wrong_role_auth_cleanup_v1_0_5.json"
    if not wrong_prepare.is_file() or not wrong_cleanup.is_file(): raise HarnessBlock("Wrong-role browser evidence requires canonical-role auth prepare + cleanup machine evidence.")
    wp=json.loads(wrong_prepare.read_text(encoding="utf-8")); wc=json.loads(wrong_cleanup.read_text(encoding="utf-8")); probe=wp.get("live_api_probe") or {}
    if wp.get("status")!="PASS" or not probe.get("live_api_login_verified") or probe.get("roles")!=["developer"] or probe.get("auth_session_http_status")!=200 or not probe.get("auth_session_renderable") or not probe.get("wrong_role_approval_denied") or probe.get("wrong_role_approval_http_status")!=403 or probe.get("wrong_role_finding_id")!="RBAC_ROLE_DENY": raise HarnessBlock("Canonical developer wrong-role login/session + exact approval RBAC_ROLE_DENY proof is missing or invalid.")
    if wc.get("status")!="PASS" or not wc.get("credentials_removed"): raise HarnessBlock("Synthetic wrong-role credential cleanup PASS is required before browser evidence validation.")
    rollback_proof=evidence/ROLLBACK_VERIFY
    if not rollback_proof.is_file(): raise HarnessBlock("B15 machine-readable rollback verification PASS is required before browser evidence validation.")
    rv=json.loads(rollback_proof.read_text(encoding="utf-8"))
    if rv.get("status")!="PASS" or not rv.get("restored_preimage") or rv.get("temporary_marker_present") is not False or int(rv.get("partial_writes_total",-1))!=0 or int(rv.get("unexpected_source_writes_total",-1))!=0: raise HarnessBlock("B15 rollback evidence does not prove restored preimage + zero partial writes.")
    if decision!="PASS-CANDIDATE" or not justification or justification=="PENDIENTE": raise HarnessBlock("Manual decision must be PASS-CANDIDATE with non-empty real justification.")
    if missing or nonpass or blank or missing_shots or invalid_summary: raise HarnessBlock(f"Browser evidence incomplete: missing={missing} nonpass={nonpass} blank={blank} missing_screenshots={missing_shots} invalid_summary={invalid_summary}")
    payload={"status":"PASS","step":"browser-evidence-validate","timestamp":now(),"rows_found":len(rows),"missing_cases":[],"nonpass_rows":[],"blank_observations":[],"missing_screenshots":[],"summary_values":values,"decision":decision,"justification_present":True,"state_file_git_parity":"PASS","rollback_verification":"PASS","external_drift_detected":True,"stale_approval_invalidated":True,"full_regression_runs_before_browser":0,"pilot_workspace_accessed":False}
    write_evidence(evidence,BROWSER_MARKER,payload,replace=True); return payload


def load_manifest(package_root: Path) -> dict[str,Any]:
    p=package_root/"SOURCE_DELTA_MANIFEST.json"
    if not p.is_file(): raise HarnessBlock(f"Missing source delta manifest: {p}")
    d=json.loads(p.read_text(encoding="utf-8")); b=d.get("baseline") or {}
    expected=("repo_DevPilot_Local_368_DEVPL_GSDLC_04_D_GOVERNED_ARTIFACT_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip","e1d9d1c722dc3fa389ce4cb7c3e18bc401d081cd","314c32d765fc2e4a2f470c4facc091b72d5951a3a9956c019d05561a885de8b9")
    actual=(b.get("repo"),b.get("commit"),b.get("sha256"))
    if actual!=expected: raise HarnessBlock(f"Package baseline mismatch: {actual}")
    return d


def source_fingerprint(repo: Path, manifest: dict[str,Any]) -> str:
    h=hashlib.sha256()
    for item in sorted(manifest["files"],key=lambda x:x["path"]):
        rel=item["path"].replace("\\","/"); path=repo/rel; op=item["operation"]
        if op=="delete":
            if path.exists(): raise HarnessBlock(f"Expected deleted source path still exists: {rel}")
            digest="ABSENT"
        else:
            if not path.is_file(): raise HarnessBlock(f"Expected postimage missing before full regression: {rel}")
            raw=path.read_bytes(); raw_digest=sha_bytes(raw); canonical_digest=sha_bytes(canonical(raw))
            expected_raw=item.get("postimage_sha256"); expected_canonical=item.get("postimage_canonical_lf_sha256")
            if raw_digest==expected_raw:
                digest=expected_canonical or expected_raw
            elif expected_canonical and canonical_digest==expected_canonical:
                digest=expected_canonical
            else:
                raise HarnessBlock(f"Postimage content mismatch before full regression: {rel}; raw={raw_digest} canonical_lf={canonical_digest}")
        h.update(f"{rel}\0{op}\0{digest}\n".encode())
    return h.hexdigest()


def pre_full_marker(repo: Path, evidence: Path, package_root: Path) -> dict[str,Any]:
    browser=evidence/BROWSER_MARKER
    if not browser.is_file() or json.loads(browser.read_text(encoding="utf-8")).get("status")!="PASS": raise HarnessBlock("Browser PASS is required before preparing the one full regression.")
    manifest=load_manifest(package_root); fp=source_fingerprint(repo,manifest); path=evidence/FULL_RUN_MARKER
    if path.exists():
        existing=json.loads(path.read_text(encoding="utf-8"))
        if existing.get("source_fingerprint")!=fp: raise HarnessBlock("Existing durable full-regression marker belongs to a different source fingerprint.")
        if existing.get("status")=="PREPARED": return existing
        raise HarnessBlock(f"Full regression attempt is already consumed/status={existing.get('status')}; never rerun it.")
    payload={"status":"PREPARED","marker_id":"DEVPL-GSDLC-04-E-FULL-RUN-1","timestamp":now(),"full_regression_runs":0,"maximum_runs":1,"rerun_allowed":False,"browser_validation_sha256":sha(browser),"source_fingerprint":fp,"source_delta_files_total":len(manifest["files"]),"policy":"exactly-once-after-browser-pass"}
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return payload


def _summary_counts(text:str)->dict[str,int]:
    out={}
    for key in ["passed","failed","error","errors","skipped","xfailed","xpassed"]:
        matches=re.findall(rf"(\d+)\s+{key}\b",text)
        if matches: out["errors" if key=="error" else key]=int(matches[-1])
    return out


def full_regression_once(repo: Path, evidence: Path, package_root: Path) -> dict[str,Any]:
    marker_path=evidence/FULL_RUN_MARKER
    if not marker_path.is_file(): raise HarnessBlock("Durable PREPARED marker missing; run pre-full-marker first.")
    marker=json.loads(marker_path.read_text(encoding="utf-8")); manifest=load_manifest(package_root); fp=source_fingerprint(repo,manifest)
    if marker.get("source_fingerprint")!=fp: raise HarnessBlock("Source fingerprint changed after full marker; full run blocked.")
    if marker.get("status")=="PASS":
        closure=evidence/FULL_CLOSURE
        if closure.is_file(): return json.loads(closure.read_text(encoding="utf-8"))
        raise HarnessBlock("Marker says PASS but closure evidence is missing; preserve state for diagnosis.")
    if marker.get("status")!="PREPARED": raise HarnessBlock(f"Full regression attempt already consumed/status={marker.get('status')}; never rerun it.")
    full=evidence/"full_regression"; full.mkdir(parents=True,exist_ok=True); log=full/"full_regression_run_01.log"; junit=full/"full_regression_run_01.junit.xml"
    if log.exists() or junit.exists(): raise HarnessBlock("Full run evidence already exists while marker is PREPARED; inconsistent state, do not rerun.")
    marker.update({"status":"RUNNING","full_regression_runs":1,"started_at":now()}); marker_path.write_text(json.dumps(marker,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    py=_python(repo); env=dict(os.environ); env["PYTHONPATH"]="src"; env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
    argv=[py,"-m","pytest","--assert=plain","-q","tests",f"--junitxml={junit}"]
    timed_out=False; rc=124
    with log.open("w",encoding="utf-8",errors="replace") as stream:
        stream.write(f"DEVPL_GSDLC_04_E_FULL_REGRESSION_RUN=1\nstarted_at={marker['started_at']}\nsource_fingerprint={fp}\n")
        stream.flush()
        try:
            cp=subprocess.run(argv,cwd=str(repo),stdout=stream,stderr=subprocess.STDOUT,text=True,timeout=14400,shell=False,env=env)
            rc=cp.returncode
        except subprocess.TimeoutExpired:
            timed_out=True; stream.write("\nBLOCK: full regression timed out; the single attempt is consumed and MUST NOT be rerun.\n")
    text=log.read_text(encoding="utf-8",errors="replace")
    failed=sorted(set(re.findall(r"^(?:FAILED|ERROR)\s+(tests/[^\s]+::[^\s]+)",text,flags=re.MULTILINE)))
    counts=_summary_counts(text); status="PASS" if rc==0 and not timed_out else "FAIL"
    marker.update({"status":status,"completed_at":now(),"returncode":rc,"timed_out":timed_out,"full_regression_runs":1,"log":str(log),"log_sha256":sha(log),"junit":str(junit) if junit.is_file() else None,"junit_sha256":sha(junit) if junit.is_file() else None,"counts":counts,"failed_nodeids":failed,"failed_nodeids_total":len(failed),"rerun_allowed":False})
    marker_path.write_text(json.dumps(marker,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    closure={"status":"PASS" if status=="PASS" else "FAIL/COMPOSITE-RECOVERY-REQUIRED","closure_mode":"full-regression-pass" if status=="PASS" else "full-failed-no-rerun","full_regression_runs":1,"full_regression_rerun_allowed":False,"source_fingerprint":fp,"browser_acceptance":"PASS","log_sha256":marker["log_sha256"],"junit_sha256":marker.get("junit_sha256"),"counts":counts,"failed_nodeids":failed,"completed_at":marker["completed_at"]}
    (evidence/FULL_CLOSURE).write_text(json.dumps(closure,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if status!="PASS": raise HarnessBlock(f"The one full regression FAILED and is consumed. Do NOT rerun. failed_nodeids_total={len(failed)}. Return evidence for root-cause/selective composite recovery.")
    return closure


def redaction_scan(evidence: Path) -> dict[str,Any]:
    patterns=[re.compile(r"sk-proj-[A-Za-z0-9_-]{12,}"),re.compile(r"github_pat_[A-Za-z0-9_-]{12,}"),re.compile(r"AKIA[0-9A-Z]{8,}"),re.compile(r"(?i)(password|api[_-]?key|token|secret)\s*[:=]\s*[^\s,;`]+")]
    findings=[]
    for path in evidence.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png",".jpg",".jpeg",".zip"}:continue
        try:text=path.read_text(encoding="utf-8",errors="replace")
        except Exception:continue
        for i,p in enumerate(patterns):
            if p.search(text): findings.append({"path":str(path.relative_to(evidence)),"pattern_id":i})
    return {"status":"PASS" if not findings else "BLOCK","findings":findings,"secrets_exposed":bool(findings)}


def package_evidence(evidence: Path, artifacts: Path) -> dict[str,Any]:
    browser=evidence/BROWSER_MARKER; closure=evidence/FULL_CLOSURE
    if not browser.is_file() or json.loads(browser.read_text(encoding="utf-8")).get("status")!="PASS": raise HarnessBlock("Browser PASS marker is required before final evidence packaging.")
    if not closure.is_file(): raise HarnessBlock("Full regression closure evidence is missing.")
    c=json.loads(closure.read_text(encoding="utf-8"))
    if c.get("status") not in {"PASS","COMPOSITE-PASS"} or int(c.get("full_regression_runs",-1))!=1: raise HarnessBlock(f"Full closure is not valid: {c}")
    scan=redaction_scan(evidence)
    if scan["status"]!="PASS": raise HarnessBlock(f"Redaction scan BLOCK: {scan['findings'][:12]}")
    write_evidence(evidence,"DEVPL_GSDLC_04_E_REDACTION_SCAN_WINDOWS.json",scan,replace=True)
    outdir=artifacts/"evidence"; outdir.mkdir(parents=True,exist_ok=True); out=outdir/"DEVPL_GSDLC_04_E_WINDOWS_EVIDENCE_v1_0_0.zip"
    if out.exists(): raise HarnessBlock(f"Refusing overwrite of sealed evidence package: {out}")
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(evidence.rglob("*")):
            if path.is_file(): zf.write(path,path.relative_to(evidence).as_posix())
    with zipfile.ZipFile(out) as zf:
        bad=zf.testzip()
        if bad: raise HarnessBlock(f"Evidence ZIP CRC failed at {bad}")
    digest=sha(out); side=out.with_suffix(out.suffix+".sha256"); side.write_text(f"{digest}  {out.name}\n",encoding="utf-8")
    return {"status":"PASS","step":"package-evidence","timestamp":now(),"evidence_zip":str(out),"sha256":digest,"sidecar":str(side),"redaction_scan":"PASS","full_regression_runs":1,"full_closure_status":c.get("status")}


def main()->int:
    ap=argparse.ArgumentParser(description="GSDLC-04-E Windows/browser/full-regression evidence harness.")
    ap.add_argument("--repo-root",default=r"D:\Projects\DevPilot_Local"); ap.add_argument("--package-root",default=str(Path(__file__).resolve().parents[1])); ap.add_argument("--evidence-dir",default=DEFAULT_EVIDENCE); ap.add_argument("--browser-fixture-root",default=DEFAULT_FIXTURE); ap.add_argument("--browser-input-root",default=DEFAULT_INPUTS); ap.add_argument("--artifacts-root",default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002")
    ap.add_argument("--step",choices=["provision-check","prepare-browser","browser-preflight","runtime-status","wrong-role-auth-prepare","wrong-role-auth-cleanup","b15-state","rollback-preflight","rollback-verify","runtime-stop-api","state-file-git-parity","runtime-stop","browser-evidence-validate","pre-full-marker","full-regression-once","package-evidence"],required=True)
    a=ap.parse_args(); repo=Path(a.repo_root).resolve(); package=Path(a.package_root).resolve(); evidence=Path(a.evidence_dir).resolve(); fixture=Path(a.browser_fixture_root).resolve(); inputs=Path(a.browser_input_root).resolve()
    try:
        low=str(repo).lower()
        if "inventory-sales-local" in low or "devpilot_workspaces" in low: raise HarnessBlock("Repo root points to forbidden pilot workspace.")
        if a.step=="provision-check": result=provision_check(repo,evidence)
        elif a.step=="prepare-browser": result=prepare_browser(repo,fixture,inputs,evidence)
        elif a.step=="browser-preflight": result=browser_preflight(repo,fixture,inputs,evidence)
        elif a.step=="runtime-status": result=runtime_status(evidence,fixture)
        elif a.step=="wrong-role-auth-prepare": result=wrong_role_auth_prepare(repo,fixture,inputs,evidence)
        elif a.step=="wrong-role-auth-cleanup": result=wrong_role_auth_cleanup(repo,fixture,inputs,evidence)
        elif a.step=="b15-state": result=b15_state(repo,fixture,evidence)
        elif a.step=="rollback-preflight": result=rollback_preflight(repo,fixture,evidence)
        elif a.step=="rollback-verify": result=rollback_verify(repo,fixture,evidence)
        elif a.step=="runtime-stop-api": result=runtime_stop_api(evidence)
        elif a.step=="state-file-git-parity": result=state_file_git_parity(repo,fixture,evidence)
        elif a.step=="runtime-stop": result=runtime_stop(evidence)
        elif a.step=="browser-evidence-validate": result=browser_evidence_validate(evidence)
        elif a.step=="pre-full-marker": result=pre_full_marker(repo,evidence,package)
        elif a.step=="full-regression-once": result=full_regression_once(repo,evidence,package)
        else: result=package_evidence(evidence,Path(a.artifacts_root).resolve())
        print(json.dumps(result,indent=2,ensure_ascii=False)); verdict("PASS",f"{a.step} completado"); return 0
    except (HarnessBlock,subprocess.TimeoutExpired,PermissionError,OSError,json.JSONDecodeError) as exc:
        payload={"status":"BLOCK","harness_id":HARNESS_ID,"version":VERSION,"step":a.step,"timestamp":now(),"message":str(exc),"pilot_workspace_accessed":False}
        print(json.dumps(payload,indent=2,ensure_ascii=False))
        try:write_evidence(evidence,f"harness_{a.step}_BLOCK_{int(time.time())}.json",payload)
        except Exception:pass
        verdict("BLOCK",f"{a.step}: {exc}"); return 20

if __name__=="__main__": raise SystemExit(main())
