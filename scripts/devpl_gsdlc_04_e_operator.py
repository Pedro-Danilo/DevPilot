from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPERATOR_ID = "DEVPL-GSDLC-04-E-OPERATOR"
OPERATOR_VERSION = "1.0.0"
BASELINE_REPO = "repo_DevPilot_Local_368_DEVPL_GSDLC_04_D_GOVERNED_ARTIFACT_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip"
BASELINE_COMMIT = "e1d9d1c722dc3fa389ce4cb7c3e18bc401d081cd"
BASELINE_SHA256 = "314c32d765fc2e4a2f470c4facc091b72d5951a3a9956c019d05561a885de8b9"
DEFAULT_BRANCH = "feat/devpl-gsdlc-04-e-artifact-workbench-browser-closure"
DEFAULT_CANDIDATE = "repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
BROWSER_MARKER = "DEVPL_GSDLC_04_E_BROWSER_ACCEPTANCE_VALIDATION.json"
FULL_CLOSURE_MARKER = "DEVPL_GSDLC_04_E_FULL_REGRESSION_CLOSURE.json"
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "outputs", ".pytest_cache", "__pycache__", "dist"}


class OperatorBlock(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_lf_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_lf_sha256(raw: bytes) -> str:
    return sha256_bytes(canonical_lf_bytes(raw))


def run(argv: list[str], *, cwd: Path, timeout: int = 180, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False, env=env)
    if check and cp.returncode != 0:
        raise OperatorBlock(f"Command failed ({cp.returncode}): {' '.join(argv)}\n{cp.stdout[-8000:]}")
    return cp


def git(repo: Path, *args: str, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, timeout=timeout, check=check)


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current").stdout.strip()


def git_status(repo: Path) -> list[str]:
    cp = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, shell=False)
    if cp.returncode != 0:
        raise OperatorBlock(cp.stderr.decode(errors="replace")[-3000:])
    return [x.decode("utf-8", errors="replace") for x in cp.stdout.split(b"\0") if x]


def dirty_path(entry: str) -> str:
    path = entry[3:] if len(entry) >= 4 else entry
    if " -> " in path:
        path = path.split(" -> ")[-1]
    return path.strip('"')


def git_path_clean(repo: Path, rel: str) -> bool:
    a = git(repo, "diff", "--quiet", "--", rel, check=False)
    b = git(repo, "diff", "--cached", "--quiet", "--", rel, check=False)
    return a.returncode == 0 and b.returncode == 0


def git_blob_bytes(repo: Path, commit: str, rel: str) -> bytes | None:
    cp = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, shell=False)
    return cp.stdout if cp.returncode == 0 else None


def safe_rel(raw: str) -> Path:
    rel = Path(raw.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or any(part in FORBIDDEN_PARTS for part in rel.parts):
        raise OperatorBlock(f"Unsafe delta path: {raw}")
    low = rel.name.lower()
    if low.startswith("auth.db") or low.startswith("devpilot.db"):
        raise OperatorBlock(f"Runtime DB forbidden in source delta: {raw}")
    return rel


def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "SOURCE_DELTA_MANIFEST.json"
    if not path.is_file():
        raise OperatorBlock(f"Missing SOURCE_DELTA_MANIFEST.json: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    baseline = data.get("baseline") or {}
    expected = (BASELINE_REPO, BASELINE_COMMIT, BASELINE_SHA256)
    actual = (baseline.get("repo"), baseline.get("commit"), baseline.get("sha256"))
    if actual != expected:
        raise OperatorBlock(f"Package baseline mismatch. expected={expected} actual={actual}")
    return data


def preimage_equivalent(*, target_bytes: bytes, blob: bytes | None, raw_expected: str | None, canonical_expected: str | None, path_clean: bool) -> tuple[bool, bool]:
    if raw_expected and sha256_bytes(target_bytes) == raw_expected:
        return True, False
    if not path_clean or not canonical_expected or blob is None:
        return False, False
    target_can = canonical_lf_sha256(target_bytes)
    blob_can = canonical_lf_sha256(blob)
    ok = target_can == canonical_expected and blob_can == canonical_expected
    return ok, ok


def classify(repo: Path, package_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    pending: list[str] = []
    applied: list[str] = []
    conflicts: list[dict[str, Any]] = []
    eol_authority: list[str] = []
    for item in manifest["files"]:
        raw_path = item["path"]
        rel = safe_rel(raw_path)
        target = repo / rel
        op = item["operation"]
        exists = target.is_file()
        actual_sha = sha256_file(target) if exists else None
        post = item.get("postimage_sha256")
        if op == "create":
            if actual_sha == post:
                applied.append(raw_path)
            elif not exists:
                pending.append(raw_path)
            else:
                conflicts.append({"path": raw_path, "reason": "unexpected-existing-file", "actual": actual_sha})
            continue
        if op == "modify":
            if actual_sha == post:
                applied.append(raw_path)
                continue
            if not exists:
                conflicts.append({"path": raw_path, "reason": "missing-preimage"})
                continue
            raw = target.read_bytes()
            clean = git_path_clean(repo, raw_path)
            blob = git_blob_bytes(repo, BASELINE_COMMIT, raw_path) if clean else None
            equivalent, used_eol = preimage_equivalent(
                target_bytes=raw,
                blob=blob,
                raw_expected=item.get("preimage_sha256"),
                canonical_expected=item.get("preimage_canonical_lf_sha256"),
                path_clean=clean,
            )
            if equivalent:
                pending.append(raw_path)
                if used_eol:
                    eol_authority.append(raw_path)
            else:
                conflicts.append({
                    "path": raw_path,
                    "reason": "preimage-mismatch",
                    "actual": actual_sha,
                    "actual_canonical_lf_sha256": canonical_lf_sha256(raw),
                    "expected_raw_sha256": item.get("preimage_sha256"),
                    "expected_canonical_lf_sha256": item.get("preimage_canonical_lf_sha256"),
                    "git_path_clean": clean,
                    "git_blob_canonical_lf_sha256": canonical_lf_sha256(blob) if blob is not None else None,
                })
            continue
        if op == "delete":
            if not exists:
                applied.append(raw_path)
                continue
            raw = target.read_bytes()
            clean = git_path_clean(repo, raw_path)
            blob = git_blob_bytes(repo, BASELINE_COMMIT, raw_path) if clean else None
            equivalent, used_eol = preimage_equivalent(
                target_bytes=raw,
                blob=blob,
                raw_expected=item.get("preimage_sha256"),
                canonical_expected=item.get("preimage_canonical_lf_sha256"),
                path_clean=clean,
            )
            if equivalent:
                pending.append(raw_path)
                if used_eol:
                    eol_authority.append(raw_path)
            else:
                conflicts.append({"path": raw_path, "reason": "delete-preimage-mismatch", "actual": actual_sha})
            continue
        conflicts.append({"path": raw_path, "reason": f"unknown-operation:{op}"})
    return {
        "pending": pending,
        "already_applied": applied,
        "conflicts": conflicts,
        "gross_touched_surface_total": len(manifest["files"]),
        "net_diff_total": len(pending),
        "eol_equivalent_preimage_paths": eol_authority,
        "eol_equivalent_preimage_total": len(eol_authority),
        "preimage_authority": "raw-sha256-first; LF fallback only when Git path is clean and working tree + immutable predecessor Git blob canonicalize to the manifest preimage",
    }


def prepare_repo(repo: Path, branch_name: str) -> dict[str, Any]:
    if not (repo / ".git").exists():
        raise OperatorBlock("D:\\Projects\\DevPilot_Local must be a Git checkout.")
    if git_status(repo):
        raise OperatorBlock("Repo must be clean before 04-E branch preparation; no reset/clean is authorized.")
    if head(repo) != BASELINE_COMMIT:
        raise OperatorBlock(f"HEAD must be 04-D predecessor {BASELINE_COMMIT}; actual={head(repo)}")
    if not branch_name or branch_name.startswith("-") or any(ch.isspace() for ch in branch_name):
        raise OperatorBlock(f"Unsafe branch name: {branch_name!r}")
    ref = f"refs/heads/{branch_name}"
    probe = git(repo, "show-ref", "--verify", "--quiet", ref, check=False)
    if probe.returncode == 0:
        target = git(repo, "rev-parse", ref).stdout.strip()
        if target != BASELINE_COMMIT:
            raise OperatorBlock(f"Existing branch {branch_name} points to {target}; no reset/rebase/force authorized.")
        if branch(repo) != branch_name:
            git(repo, "switch", branch_name)
        action = "selected-existing"
    elif probe.returncode == 1:
        git(repo, "switch", "-c", branch_name)
        action = "created"
    else:
        raise OperatorBlock("git show-ref failed while inspecting 04-E branch.")
    if head(repo) != BASELINE_COMMIT or git_status(repo):
        raise OperatorBlock("Post-branch verification failed.")
    return {"status": "PASS", "branch": branch_name, "action": action, "head": head(repo), "worktree_clean": True, "destructive_git_used": False}


def preflight(repo: Path, package_root: Path, manifest: dict[str, Any], branch_name: str) -> dict[str, Any]:
    if head(repo) != BASELINE_COMMIT or branch(repo) != branch_name:
        raise OperatorBlock(f"04-E preflight requires HEAD={BASELINE_COMMIT} on {branch_name}; actual={head(repo)} {branch(repo)}")
    allowed = {x["path"] for x in manifest["files"]}
    unknown = [entry for entry in git_status(repo) if dirty_path(entry) not in allowed]
    if unknown:
        raise OperatorBlock(f"Unknown dirty paths outside governed 04-E delta: {unknown[:20]}")
    result = classify(repo, package_root, manifest)
    if result["conflicts"]:
        raise OperatorBlock(f"04-E preflight conflicts: {result['conflicts'][:12]}")
    cp = git(repo, "-c", "core.safecrlf=false", "diff", "--check", check=False)
    real_errors = [ln for ln in cp.stdout.splitlines() if ln.strip() and "LF will be replaced by CRLF" not in ln and "CRLF will be replaced by LF" not in ln and "original line endings" not in ln]
    if real_errors:
        raise OperatorBlock(f"Real whitespace defects detected: {real_errors[:20]}")
    return {"status": "PASS", "head": head(repo), "branch": branch(repo), "unknown_dirty_paths": [], **result, "full_regression_executed": False}


def replace_with_retry(src: Path, dst: Path, attempts: int = 5) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = dst.with_name(dst.name + ".devpilot04e.tmp")
    if temp.exists():
        temp.unlink()
    shutil.copyfile(src, temp)
    last: Exception | None = None
    for i in range(attempts):
        try:
            os.replace(temp, dst)
            return
        except (PermissionError, OSError) as exc:
            last = exc
            time.sleep(0.15 * (i + 1))
    if temp.exists():
        temp.unlink(missing_ok=True)
    raise OperatorBlock(f"Atomic file replacement failed after bounded retry: {dst}: {last}")


def apply_delta(repo: Path, package_root: Path, manifest: dict[str, Any], branch_name: str) -> dict[str, Any]:
    before = preflight(repo, package_root, manifest, branch_name)
    by_path = {x["path"]: x for x in manifest["files"]}
    applied_now: list[str] = []
    for raw in before["pending"]:
        item = by_path[raw]
        rel = safe_rel(raw)
        dst = repo / rel
        if item["operation"] == "delete":
            if dst.exists():
                dst.unlink()
            applied_now.append(raw)
            continue
        src = package_root / "source_delta" / rel
        if not src.is_file() or sha256_file(src) != item["postimage_sha256"]:
            raise OperatorBlock(f"Package postimage missing/invalid: {raw}")
        replace_with_retry(src, dst)
        if sha256_file(dst) != item["postimage_sha256"]:
            raise OperatorBlock(f"Post-write hash mismatch: {raw}")
        applied_now.append(raw)
    after = classify(repo, package_root, manifest)
    if after["pending"] or after["conflicts"]:
        raise OperatorBlock(f"Post-apply convergence failed: {after}")
    return {"status": "PASS", "applied_paths": applied_now, "post_apply": after}


def repo_review(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    entries = git_status(repo)
    allowed = {x["path"] for x in manifest["files"]}
    unexpected = [entry for entry in entries if dirty_path(entry) not in allowed]
    if unexpected:
        raise OperatorBlock(f"Unexpected Git paths outside 04-E source delta: {unexpected[:20]}")
    cp = git(repo, "-c", "core.safecrlf=false", "diff", "--check", check=False)
    real_errors = [ln for ln in cp.stdout.splitlines() if ln.strip() and "LF will be replaced by CRLF" not in ln and "CRLF will be replaced by LF" not in ln and "original line endings" not in ln]
    if real_errors:
        raise OperatorBlock(f"git diff --check found real whitespace defects: {real_errors[:20]}")
    tracked = git(repo, "ls-files").stdout.splitlines()
    forbidden = [p for p in tracked if any(part in FORBIDDEN_PARTS for part in Path(p).parts) or Path(p).name.lower().startswith(("auth.db", "devpilot.db"))]
    if forbidden:
        raise OperatorBlock(f"Forbidden tracked paths: {forbidden[:20]}")
    return {"head": head(repo), "branch": branch(repo), "status_entries": entries, "diff_check": "PASS", "unexpected_git_entries": [], "forbidden_tracked_total": 0, "tracked_files_total": len(tracked)}


def python_executable(repo: Path) -> str:
    win = repo / ".venv" / "Scripts" / "python.exe"
    return str(win) if win.is_file() else sys.executable


def validate(repo: Path, evidence: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    py = python_executable(repo)
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if os.name == "nt" and not (repo / ".venv" / "Scripts" / "python.exe").is_file():
        raise OperatorBlock(".venv\\Scripts\\python.exe missing; no implicit provisioning is authorized.")
    if not npm:
        raise OperatorBlock("npm.cmd/npm missing from PATH.")
    if not (repo / "ui/web/node_modules").is_dir():
        raise OperatorBlock("ui/web/node_modules missing; no silent network provisioning is authorized.")
    evidence.mkdir(parents=True, exist_ok=True)
    changed_paths_file = evidence / "DEVPL_GSDLC_04_E_TEST_IMPACT_CHANGED_PATHS.txt"
    changed_paths_file.write_text("\n".join(sorted(item["path"] for item in manifest["files"])) + "\n", encoding="utf-8")
    gates: list[tuple[str, list[str], int]] = [
        ("focused-04e", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_e_external_reconciliation.py"], 300),
        ("cumulative-04d", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_d_artifact_review_apply_freeze.py"], 300),
        ("cumulative-04c", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_c_artifact_import.py"], 300),
        ("cumulative-04b", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_b_manual_editor_draft_history.py"], 300),
        ("cumulative-04a", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_a_artifact_lifecycle.py"], 300),
        ("uoc-004", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_post_h_eval_002_uoc_004_contracts.py"], 300),
        ("uoc-005", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_post_h_eval_002_uoc_005_contracts.py"], 300),
        ("rbac", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_gsdlc_02_c_server_rbac.py"], 300),
        ("docs-source-registry", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_documentation_source_registry_schema.py"], 300),
        ("contract-reconciliation", [py, "-m", "pytest", "--assert=plain", "-q", "tests/test_devpl_documentation_contract_reconciliation_policy.py"], 300),
        ("test-impact-v2", [py, "-m", "devpilot_core", "test-impact", "analyze-v2", "--changed-paths-file", str(changed_paths_file), "--json"], 180),
        ("project-state", [py, "-m", "devpilot_core", "project-state", "validate", "--json"], 180),
        ("tcr-v1", [py, "-m", "devpilot_core", "test-contracts", "validate", "--json"], 180),
        ("tcr-v2", [py, "-m", "devpilot_core", "test-contracts", "validate-v2", "--json"], 180),
        ("docs-governance", [py, "-m", "devpilot_core", "docs-governance", "validate", "--json"], 300),
        ("api-contract-drift", [py, "-m", "devpilot_core", "api", "contract-drift", "--json"], 300),
        ("api-security", [py, "-m", "devpilot_core", "api", "security-hardening", "--json"], 300),
        ("ui-route-enforcement", [py, "-m", "devpilot_core", "api", "ui-route-enforcement", "--json"], 300),
        ("ui-static-04e", [npm, "--prefix", "ui/web", "run", "test:artifact-reconciliation"], 180),
        ("ui-build", [npm, "--prefix", "ui/web", "run", "build"], 600),
    ]
    evidence.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for name, argv, timeout in gates:
        cp = run(argv, cwd=repo, timeout=timeout, env=env, check=False)
        record = {"status": "PASS" if cp.returncode == 0 else "BLOCK", "gate": name, "returncode": cp.returncode, "output_tail": cp.stdout[-12000:], "timestamp": now()}
        checkpoint(evidence, f"validate_{name}", {"status": record["status"], "result": record, "full_regression_executed": False, "pilot_workspace_accessed": False})
        out.append(record)
        if cp.returncode != 0:
            raise OperatorBlock(f"Validation gate {name} BLOCK.\n{cp.stdout[-8000:]}")
    return {"status": "PASS", "gates": out, "validation_scope": "GSDLC-04-E focal + cumulative A-E + deterministic governance/API/UI; full regression intentionally deferred until Windows browser PASS", "full_regression_runs": 0, "full_regression_executed": False, "network_used": False, "external_api_used": False, "pilot_workspace_accessed": False}

def git_commit(repo: Path, manifest: dict[str, Any], evidence: Path, message: str) -> dict[str, Any]:
    marker = evidence / BROWSER_MARKER
    if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")).get("status") != "PASS":
        raise OperatorBlock("Browser evidence PASS marker missing; 04-E commit is blocked.")
    full_marker = evidence / FULL_CLOSURE_MARKER
    if not full_marker.is_file():
        raise OperatorBlock("Full regression closure marker missing; 04-E commit is blocked.")
    full_payload = json.loads(full_marker.read_text(encoding="utf-8"))
    if full_payload.get("status") not in {"PASS", "COMPOSITE-PASS"} or int(full_payload.get("full_regression_runs", -1)) != 1:
        raise OperatorBlock(f"Full regression closure is not authoritative PASS/composite with exactly one run: {full_payload}")
    review = repo_review(repo, manifest)
    dirty = sorted({dirty_path(x) for x in review["status_entries"]})
    if not dirty:
        raise OperatorBlock("No 04-E source changes are dirty; refusing empty commit.")
    allowed = {x["path"] for x in manifest["files"]}
    if not set(dirty) <= allowed:
        raise OperatorBlock("Dirty paths exceed governed 04-E delta.")
    for rel in dirty:
        git(repo, "add", "--", rel)
    cp = git(repo, "-c", "core.safecrlf=false", "diff", "--cached", "--check", check=False)
    if cp.returncode != 0:
        raise OperatorBlock(f"Staged diff whitespace BLOCK: {cp.stdout[-5000:]}")
    git(repo, "commit", "-m", message, timeout=180)
    if git_status(repo):
        raise OperatorBlock("Worktree not clean after 04-E commit.")
    return {"status": "PASS", "commit": head(repo), "message": message, "staged_paths_total": len(dirty), "worktree_clean": True}


def package_head(repo: Path, artifacts_root: Path, name: str) -> dict[str, Any]:
    if git_status(repo):
        raise OperatorBlock("Worktree must be clean before Windows candidate packaging.")
    tracked = git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
    bad = [p for p in tracked if any(part in FORBIDDEN_PARTS for part in Path(p).parts) or Path(p).name.lower().startswith(("auth.db", "devpilot.db"))]
    if bad:
        raise OperatorBlock(f"Forbidden tracked paths in HEAD: {bad[:20]}")
    outdir = artifacts_root / "baselines" / "gsdlc_04_e"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / name
    if out.exists():
        raise OperatorBlock(f"Candidate already exists; refusing overwrite: {out}")
    run(["git", "archive", "--format=zip", f"--output={out}", "HEAD"], cwd=repo, timeout=300)
    digest = sha256_file(out)
    out.with_suffix(out.suffix + ".sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    return {"status": "PASS", "candidate": str(out), "sha256": digest, "git_head": head(repo), "tracked_files_total": len(tracked), "forbidden_tracked_total": 0, "full_regression_executed": False}


def checkpoint(evidence: Path, phase: str, payload: dict[str, Any]) -> Path:
    evidence.mkdir(parents=True, exist_ok=True)
    path = evidence / f"operator_{phase}.json"
    if path.exists():
        i = 2
        while (evidence / f"operator_{phase}_{i:02d}.json").exists():
            i += 1
        path = evidence / f"operator_{phase}_{i:02d}.json"
    path.write_text(json.dumps({"operator_id": OPERATOR_ID, "operator_version": OPERATOR_VERSION, "phase": phase, "timestamp": now(), **payload}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed GSDLC-04-E source operator; state-aware and dry-run by default.")
    parser.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    parser.add_argument("--package-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--evidence-dir", default=r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E")
    parser.add_argument("--artifacts-root", default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002")
    parser.add_argument("--branch-name", default=DEFAULT_BRANCH)
    parser.add_argument("--candidate-name", default=DEFAULT_CANDIDATE)
    parser.add_argument("--commit-message", default="feat(gsdlc-04-e): close governed artifact workbench")
    parser.add_argument("--phase", choices=["prepare-repo", "preflight", "converge-source", "repo-review", "validate", "git-commit", "package-git-head"], required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    package = Path(args.package_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    try:
        low = str(repo).lower()
        if "inventory-sales-local" in low or "devpilot_workspaces" in low:
            raise OperatorBlock("Pilot workspace access forbidden during GSDLC-04-E.")
        if not repo.is_dir():
            raise OperatorBlock(f"Repo missing: {repo}")
        manifest = load_manifest(package)
        if args.phase in {"prepare-repo", "converge-source", "git-commit", "package-git-head"} and not args.execute:
            raise OperatorBlock(f"Phase {args.phase} mutates governed state and requires --execute.")
        if args.phase == "prepare-repo":
            result = prepare_repo(repo, args.branch_name)
        elif args.phase == "preflight":
            result = preflight(repo, package, manifest, args.branch_name)
        elif args.phase == "converge-source":
            result = {"status": "PASS", "apply": apply_delta(repo, package, manifest, args.branch_name), "repo_review": repo_review(repo, manifest), "full_regression_executed": False}
        elif args.phase == "repo-review":
            result = {"status": "PASS", **repo_review(repo, manifest), "full_regression_executed": False}
        elif args.phase == "validate":
            result = validate(repo, evidence, manifest)
        elif args.phase == "git-commit":
            result = git_commit(repo, manifest, evidence, args.commit_message)
        else:
            result = package_head(repo, Path(args.artifacts_root).resolve(), args.candidate_name)
        payload = {"status": "PASS", "result": result, "pilot_workspace_accessed": False, "full_regression_executed": False}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        checkpoint(evidence, args.phase, payload)
        verdict("PASS", f"{args.phase} completado")
        return 0
    except (OperatorBlock, subprocess.TimeoutExpired, PermissionError, OSError, json.JSONDecodeError) as exc:
        payload = {"status": "BLOCK", "operator_id": OPERATOR_ID, "version": OPERATOR_VERSION, "phase": args.phase, "timestamp": now(), "message": str(exc), "full_regression_executed": False, "pilot_workspace_accessed": False}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        try:
            checkpoint(evidence, args.phase, payload)
        except Exception:
            pass
        verdict("BLOCK", f"{args.phase}: {exc}")
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
