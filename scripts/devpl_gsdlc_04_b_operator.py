from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from typing import Any, Iterable

from devpl_gsdlc_04_b_fixture_state import repair_legacy_marker

OPERATOR_ID = "DEVPL-GSDLC-04-B-OPERATOR"
OPERATOR_VERSION = "1.0.10"
DEFAULT_BRANCH = "feat/devpl-gsdlc-04-b-manual-editor"
BASELINE_REPO = "repo_DevPilot_Local_365_DEVPL_GSDLC_04_A_ARTIFACT_LIFECYCLE_WINDOWS_VALIDATED_CANDIDATE.zip"
BASELINE_COMMIT = "6b6cb70eb16c94f4aa374fc74d9ff2f8f8b6c893"
BASELINE_SHA256 = "0359182b736d8cbb1f90ad92cf56fd02c7081fc357674597c02c2706fedb67a6"
DEFAULT_CANDIDATE_NAME = "repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip"
FORBIDDEN_PARTS = {".git", ".venv", "node_modules", "outputs", ".pytest_cache", "__pycache__"}
RUNTIME_DB_NAMES = {"devpilot.db", "auth.db"}


class OperatorBlock(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str], *, cwd: Path, timeout: int = 180, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False, env=env)
    if check and completed.returncode != 0:
        raise OperatorBlock(f"Command failed ({completed.returncode}): {' '.join(argv)}\n{completed.stdout[-6000:]}")
    return completed


def git(repo: Path, *args: str, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, timeout=timeout, check=check)


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
    """Always emit a short colored terminal verdict as the final console line."""
    _enable_windows_ansi()
    ok = status.upper() == "PASS"
    color = "\x1b[92m" if ok else "\x1b[91m"
    reset = "\x1b[0m"
    print(f"{color}{status.upper()} — {message}{reset}", flush=True)


def git_blob_oid(repo: Path, commit: str, rel: Path) -> str | None:
    spec = f"{commit}:{rel.as_posix()}"
    completed = git(repo, "rev-parse", spec, check=False)
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def git_blob_bytes(repo: Path, commit: str, rel: Path) -> bytes | None:
    spec = f"{commit}:{rel.as_posix()}"
    completed = subprocess.run(
        ["git", "show", spec],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        shell=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def git_path_clean(repo: Path, rel: Path) -> bool:
    worktree = git(repo, "diff", "--quiet", "--", rel.as_posix(), check=False)
    index = git(repo, "diff", "--cached", "--quiet", "--", rel.as_posix(), check=False)
    return worktree.returncode == 0 and index.returncode == 0


def git_index_flag(repo: Path, rel: Path) -> str | None:
    completed = git(repo, "ls-files", "-v", "--", rel.as_posix(), check=False)
    line = completed.stdout.strip()
    return line[:1] if line else None


def canonical_lf_sha256(data: bytes) -> str:
    return sha256_bytes(data.replace(b"\r\n", b"\n"))


def safe_relative(path: str) -> Path:
    rel = Path(path.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or any(part in FORBIDDEN_PARTS for part in rel.parts):
        raise OperatorBlock(f"Unsafe delta path: {path}")
    if rel.name in RUNTIME_DB_NAMES or rel.name.startswith("auth.db") or rel.name.startswith("devpilot.db"):
        raise OperatorBlock(f"Runtime DB cannot be part of source delta: {path}")
    return rel


def read_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "SOURCE_DELTA_MANIFEST.json"
    if not path.is_file():
        raise OperatorBlock(f"Missing package manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("baseline", {}).get("repo") != BASELINE_REPO or payload.get("baseline", {}).get("commit") != BASELINE_COMMIT:
        raise OperatorBlock("SOURCE_DELTA_MANIFEST baseline does not match the owner-adjudicated repo365 authority.")
    return payload


def git_identity(repo: Path) -> dict[str, Any]:
    if not (repo / ".git").exists():
        return {"git_present": False, "head": None, "status_entries": []}
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    status_raw = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, timeout=60).stdout
    entries = [item.decode("utf-8", errors="replace") for item in status_raw.split(b"\x00") if item]
    return {"git_present": True, "head": head, "status_entries": entries}




def current_branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current").stdout.strip()


def prepare_repo_branch(repo: Path, branch_name: str) -> dict[str, Any]:
    """Verify the immutable predecessor and safely create/select the 04-B branch.

    This phase intentionally replaces the former PowerShell `git branch --list ... .Trim()`
    expression. Git return codes are used directly, so a missing branch is normal state,
    never a null-string error. No reset/rebase/force operation is used.
    """
    identity = git_identity(repo)
    if not identity["git_present"]:
        raise OperatorBlock("Git repository is required before preparing the GSDLC-04-B branch.")
    if identity["status_entries"]:
        raise OperatorBlock(f"Repository must be clean before branch preparation. Dirty entries: {identity['status_entries'][:20]}")
    if identity["head"] != BASELINE_COMMIT:
        raise OperatorBlock(f"Git HEAD {identity['head']} is not the owner-adjudicated predecessor {BASELINE_COMMIT}.")
    if not branch_name or branch_name.startswith("-") or any(ch.isspace() for ch in branch_name):
        raise OperatorBlock(f"Unsafe/invalid branch name: {branch_name!r}")
    ref = f"refs/heads/{branch_name}"
    probe = git(repo, "show-ref", "--verify", "--quiet", ref, check=False)
    before_branch = current_branch(repo)
    if probe.returncode == 0:
        branch_head = git(repo, "rev-parse", ref).stdout.strip()
        if branch_head != BASELINE_COMMIT:
            raise OperatorBlock(
                f"Existing branch {branch_name} points to {branch_head}, not predecessor {BASELINE_COMMIT}. "
                "No reset/rebase/force is authorized; preserve the branch and request review."
            )
        if before_branch == branch_name:
            action = "already-selected"
        else:
            git(repo, "switch", branch_name)
            action = "switched-existing"
    elif probe.returncode == 1:
        git(repo, "switch", "-c", branch_name)
        action = "created-and-switched"
    else:
        raise OperatorBlock(f"Could not inspect branch {branch_name}; git show-ref returned {probe.returncode}.")
    post = git_identity(repo)
    after_branch = current_branch(repo)
    if post["head"] != BASELINE_COMMIT or post["status_entries"] or after_branch != branch_name:
        raise OperatorBlock(
            f"Post-branch verification failed: head={post['head']} branch={after_branch!r} status={post['status_entries'][:20]}"
        )
    return {
        "branch": branch_name,
        "action": action,
        "branch_before": before_branch,
        "branch_after": after_branch,
        "head": post["head"],
        "status_entries": post["status_entries"],
        "baseline_commit_verified": True,
        "destructive_git_used": False,
    }


def _classify_diff_check_output(output: str) -> tuple[list[str], list[str]]:
    """Separate benign EOL diagnostics from actual whitespace errors."""
    warnings: list[str] = []
    errors: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("warning:") or low.startswith("the file will have its original line endings"):
            warnings.append(line)
        else:
            errors.append(line)
    return warnings, errors


def _text_hygiene_errors(repo: Path, manifest: dict[str, Any]) -> list[str]:
    """Check declared current files, including untracked new files, for EOF/path hygiene."""
    errors: list[str] = []
    text_suffixes = {".py", ".json", ".md", ".ts", ".tsx", ".css", ".mjs", ".yaml", ".yml"}
    for item in manifest.get("files", []):
        # `git diff --check` already evaluates tracked modifications relative to the
        # baseline and correctly ignores historical whitespace that was not introduced
        # by 04-B. This supplemental check is only for create/untracked files, which
        # `git diff --check` cannot see before staging.
        if item.get("operation") != "create":
            continue
        rel = safe_relative(str(item["path"]))
        target = repo / rel
        if not target.is_file() or target.suffix.lower() not in text_suffixes:
            continue
        data = target.read_bytes()
        if data and data.endswith((b"\n\n", b"\r\n\r\n")):
            errors.append(f"{rel.as_posix()}: multiple terminal newlines / blank line at EOF in new file")
        if data and not data.endswith((b"\n", b"\r\n")):
            errors.append(f"{rel.as_posix()}: missing terminal newline in new file")
    return errors


def repo_review(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    identity = git_identity(repo)
    if not identity["git_present"]:
        raise OperatorBlock("Git repository is required for repo-review.")
    unexpected = unexpected_git_status_entries(identity, manifest)
    if unexpected:
        raise OperatorBlock(f"Unexpected Git paths outside SOURCE_DELTA_MANIFEST: {unexpected[:20]}")
    # core.safecrlf=false suppresses checkout-normalization warnings. Real whitespace
    # failures still produce a non-zero return code and are reported separately.
    diff_check = git(repo, "-c", "core.safecrlf=false", "diff", "--check", "--no-ext-diff", check=False)
    warnings, diff_errors = _classify_diff_check_output(diff_check.stdout)
    hygiene_errors = _text_hygiene_errors(repo, manifest)
    diff_stat = git(repo, "diff", "--stat", check=False).stdout
    tracked = git(repo, "ls-files").stdout.splitlines()
    violations: list[str] = []
    for raw in tracked:
        rel = Path(raw)
        if any(part in FORBIDDEN_PARTS for part in rel.parts) or rel.name in RUNTIME_DB_NAMES or rel.name.startswith("auth.db") or rel.name.startswith("devpilot.db"):
            violations.append(raw)
    if diff_errors or hygiene_errors or (diff_check.returncode != 0 and not diff_errors):
        details = {"diff_errors": diff_errors, "hygiene_errors": hygiene_errors, "unclassified_returncode": diff_check.returncode if diff_check.returncode != 0 and not diff_errors else None}
        raise OperatorBlock(f"Repository whitespace/hygiene review failed: {json.dumps(details, ensure_ascii=False)}")
    if violations:
        raise OperatorBlock(f"Forbidden runtime/cache paths are tracked: {violations[:20]}")
    return {
        "head": identity["head"],
        "branch": current_branch(repo),
        "status_entries": identity["status_entries"],
        "diff_stat": diff_stat,
        "diff_check": "PASS",
        "diff_check_warnings": warnings,
        "diff_check_warnings_total": len(warnings),
        "text_hygiene": "PASS",
        "forbidden_tracked_total": 0,
        "tracked_files_total": len(tracked),
        "unexpected_git_entries": [],
    }


def unexpected_git_status_entries(identity: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    """Return dirty Git entries outside the declared source delta.

    `git status --porcelain=v1 -z` is already the operator authority. GSDLC-04-B
    does not contain renames, so a rename/copy record or any unparseable status
    entry is treated conservatively as unexpected and blocks preflight.
    """
    if not identity.get("git_present"):
        return []
    allowed = {safe_relative(str(item["path"])).as_posix() for item in manifest.get("files", [])}
    unexpected: list[str] = []
    for entry in identity.get("status_entries", []):
        if len(entry) < 4:
            unexpected.append(entry)
            continue
        status = entry[:2]
        raw_path = entry[3:].replace("\\", "/")
        if "R" in status or "C" in status or raw_path not in allowed:
            unexpected.append(entry)
    return unexpected


def inspect_delta(repo: Path, package_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Inspect the package delta without mutating source.

    Exact worktree SHA-256 remains the fastest path. When Windows checkout filters
    (especially CRLF/LF conversion) make the worktree bytes differ while Git still
    reports a clean path, the owner-adjudicated Git commit/blob is authoritative.
    This avoids false preimage conflicts without accepting a dirty or divergent
    file. Special index flags (skip-worktree / assume-unchanged) are rejected.
    """
    delta_root = package_root / "source_delta"
    if not delta_root.is_dir():
        raise OperatorBlock(f"Missing source_delta directory: {delta_root}")

    identity = git_identity(repo)
    git_authority_available = bool(identity.get("git_present") and identity.get("head") == BASELINE_COMMIT)
    pending: list[str] = []
    already: list[str] = []
    conflicts: list[dict[str, Any]] = []
    git_blob_authority_paths: list[dict[str, Any]] = []

    for entry in manifest.get("files", []):
        rel = safe_relative(str(entry["path"]))
        target = repo / rel
        operation = str(entry.get("operation", "modify"))
        expected_pre = entry.get("preimage_sha256")
        expected_post = entry.get("postimage_sha256")
        accepted_preimages = [str(v) for v in entry.get("accepted_preimage_sha256s", []) if v]
        if expected_pre and expected_pre not in accepted_preimages:
            accepted_preimages.insert(0, str(expected_pre))
        expected_blob_oid = entry.get("preimage_git_blob_oid_sha1")
        expected_lf = entry.get("preimage_canonical_lf_sha256")

        if operation == "delete":
            if not target.exists():
                already.append(rel.as_posix())
                continue
            if accepted_preimages and sha256_file(target) in accepted_preimages:
                pending.append(rel.as_posix())
                continue
        else:
            source = delta_root / rel
            if not source.is_file() or sha256_file(source) != expected_post:
                raise OperatorBlock(f"Delta payload/hash mismatch: {rel.as_posix()}")
            if target.is_file() and expected_post and sha256_file(target) == expected_post:
                already.append(rel.as_posix())
                continue
            if expected_pre is None and not target.exists():
                pending.append(rel.as_posix())
                continue
            if target.is_file() and accepted_preimages and sha256_file(target) in accepted_preimages:
                pending.append(rel.as_posix())
                continue

        # Windows checkout filters can legitimately change worktree bytes while
        # leaving the path clean. In that case verify the immutable Git baseline
        # blob instead of trusting the smudged worktree byte representation.
        if accepted_preimages and target.is_file() and git_authority_available:
            flag = git_index_flag(repo, rel)
            if flag == "S" or (flag is not None and flag.islower()):
                conflicts.append({
                    "path": rel.as_posix(),
                    "reason": "unsafe-git-index-flag",
                    "git_index_flag": flag,
                })
                continue

            clean = git_path_clean(repo, rel)
            actual_blob_oid = git_blob_oid(repo, BASELINE_COMMIT, rel)
            blob = git_blob_bytes(repo, BASELINE_COMMIT, rel)
            actual_blob_lf = canonical_lf_sha256(blob) if blob is not None else None
            blob_matches = bool(expected_blob_oid and actual_blob_oid == expected_blob_oid)
            canonical_matches = bool(expected_lf and actual_blob_lf == expected_lf)

            if clean and (blob_matches or canonical_matches):
                pending.append(rel.as_posix())
                git_blob_authority_paths.append({
                    "path": rel.as_posix(),
                    "authority": "git-blob",
                    "git_blob_oid": actual_blob_oid,
                    "match_mode": "exact-blob-oid" if blob_matches else "canonical-lf",
                    "worktree_sha256": sha256_file(target),
                    "manifest_preimage_sha256": expected_pre,
                })
                continue

            conflicts.append({
                "path": rel.as_posix(),
                "reason": "preimage-mismatch-after-git-blob-check",
                "target_exists": True,
                "git_path_clean": clean,
                "git_blob_oid": actual_blob_oid,
                "expected_git_blob_oid": expected_blob_oid,
                "git_blob_canonical_lf_sha256": actual_blob_lf,
                "expected_canonical_lf_sha256": expected_lf,
                "worktree_sha256": sha256_file(target),
                "accepted_preimage_sha256s": accepted_preimages,
            })
            continue

        conflicts.append({
            "path": rel.as_posix(),
            "reason": "preimage-mismatch-or-unexpected-file",
            "target_exists": target.exists(),
            "worktree_sha256": sha256_file(target) if target.is_file() else None,
            "accepted_preimage_sha256s": accepted_preimages,
        })

    return {
        "pending": pending,
        "already_applied": already,
        "conflicts": conflicts,
        "net_diff_total": len(pending),
        "gross_touched_surface_total": len(manifest.get("files", [])),
        "git_blob_authority_paths": git_blob_authority_paths,
        "git_blob_authority_total": len(git_blob_authority_paths),
    }


def replace_with_retry(source: Path, target: Path, attempts: int = 5) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".devpilot-04b-tmp")
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            shutil.copyfile(source, tmp)
            os.replace(tmp, target)
            return
        except OSError as exc:
            last = exc
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.2 * (attempt + 1))
    raise OperatorBlock(f"Could not replace {target} after {attempts} bounded retries: {last}")


def apply_delta(repo: Path, package_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    state = inspect_delta(repo, package_root, manifest)
    if state["conflicts"]:
        raise OperatorBlock(f"Preimage conflicts BLOCK apply: {json.dumps(state['conflicts'], ensure_ascii=False)}")
    delta_root = package_root / "source_delta"
    changed: list[str] = []
    for entry in manifest.get("files", []):
        rel = safe_relative(str(entry["path"]))
        if rel.as_posix() not in state["pending"]:
            continue
        target = repo / rel
        if entry.get("operation") == "delete":
            target.unlink()
        else:
            replace_with_retry(delta_root / rel, target)
        changed.append(rel.as_posix())
    post = inspect_delta(repo, package_root, manifest)
    if post["pending"] or post["conflicts"]:
        raise OperatorBlock(f"Post-apply verification BLOCK: {post}")
    return {"applied_paths": changed, "already_applied": post["already_applied"], "post_apply": post}


def validation_commands(repo: Path) -> list[tuple[str, list[str], int]]:
    venv_python = repo / ".venv" / "Scripts" / "python.exe"
    py = str(venv_python) if venv_python.is_file() else sys.executable
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise OperatorBlock("npm is not available in PATH for Windows validation.")
    return [
        ("focused-04b", [py, "-m", "pytest", "-p", "no:ddtrace", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_b_manual_editor_draft_history.py"], 300),
        ("cumulative-a-b-uoc", [py, "-m", "pytest", "-p", "no:ddtrace", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_a_artifact_lifecycle.py", "tests/test_post_h_eval_002_uoc_004_contracts.py", "tests/test_post_h_eval_002_uoc_005_contracts.py", "tests/test_devpl_gsdlc_04_b_manual_editor_draft_history.py"], 600),
        ("security-api-ui-impact", [py, "-m", "pytest", "-p", "no:ddtrace", "--assert=plain", "-q", "tests/test_devpl_gsdlc_02_c_server_rbac.py", "tests/test_devpl_gsdlc_02_c_api_rbac.py", "tests/test_api_workspace_documents.py", "tests/test_web_ui_workspace_documents.py", "tests/test_post_h_014_api_route_contracts.py", "tests/test_post_h_028_ui_route_registry_enforcement.py"], 900),
        ("schema-list", [py, "-m", "devpilot_core", "schema", "list", "--json"], 180),
        ("artifact-profiles-and-readiness", [py, "-m", "devpilot_core", "validate", "docs", "--json"], 240),
        ("project-state", [py, "-m", "devpilot_core", "project-state", "validate", "--json"], 180),
        ("tcr-v1", [py, "-m", "devpilot_core", "test-contracts", "validate", "--json"], 240),
        ("tcr-v2", [py, "-m", "devpilot_core", "test-contracts", "validate-v2", "--json"], 240),
        ("docs-governance", [py, "-m", "devpilot_core", "docs-governance", "validate", "--json"], 300),
        ("api-contract-drift", [py, "-m", "devpilot_core", "api", "contract-drift", "--json"], 300),
        ("api-security-hardening", [py, "-m", "devpilot_core", "api", "security-hardening", "--json"], 300),
        ("ui-static-04b", [npm, "--prefix", "ui/web", "run", "test:artifact-manual-editor"], 180),
        ("ui-build", [npm, "--prefix", "ui/web", "run", "build"], 600),
    ]


def validate(repo: Path) -> dict[str, Any]:
    if not (repo / "ui" / "web" / "node_modules").is_dir():
        raise OperatorBlock("ui/web/node_modules is missing. Run the guide's npm ci provisioning command before validation; the operator will not silently use network.")
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    results: list[dict[str, Any]] = []
    for name, argv, timeout in validation_commands(repo):
        completed = run(argv, cwd=repo, timeout=timeout, env=env, check=False)
        results.append({"name": name, "argv": argv, "returncode": completed.returncode, "output_tail": completed.stdout[-8000:]})
        if completed.returncode != 0:
            raise OperatorBlock(f"Validation gate {name} BLOCK.\n{completed.stdout[-8000:]}")
    return {"gates": results, "full_regression_runs": 0, "full_regression_executed": False}


def validate_corrective(repo: Path) -> dict[str, Any]:
    """Only the gates directly impacted by recovery-010 final fixture equivalence handling.

    Product UI/API behavior was already validated in v1.0.7. This corrective
    touches fixture/harness/documentation only, so do not repeat cumulative,
    API-security, UI-build or unrelated registries.
    """
    venv_python = repo / ".venv" / "Scripts" / "python.exe"
    py = str(venv_python) if venv_python.is_file() else sys.executable
    env = dict(os.environ); env["PYTHONPATH"] = "src"
    commands = [
        ("focused-04b", [py, "-m", "pytest", "-p", "no:ddtrace", "--assert=plain", "-q", "tests/test_devpl_gsdlc_04_b_manual_editor_draft_history.py"], 300),
        ("source-registry", [py, "-m", "pytest", "-p", "no:ddtrace", "--assert=plain", "-q", "tests/test_documentation_source_registry_schema.py"], 240),
        ("docs-governance", [py, "-m", "devpilot_core", "docs-governance", "validate", "--json"], 300),
    ]
    results=[]
    for name, argv, timeout in commands:
        completed=run(argv,cwd=repo,timeout=timeout,env=env,check=False)
        results.append({"name":name,"argv":argv,"returncode":completed.returncode,"output_tail":completed.stdout[-8000:]})
        if completed.returncode != 0:
            raise OperatorBlock(f"Corrective validation gate {name} BLOCK.\n{completed.stdout[-8000:]}")
    return {"gates":results,"validation_scope":"recovery-010-strictly-impacted-only","full_regression_runs":0,"full_regression_executed":False}


def prepare_browser_fixture(target: Path, evidence_dir: Path) -> dict[str, Any]:
    """Create or converge the disposable 04-B fixture without dirtying Git.

    v1.0.7 wrote an ownership marker *after* the baseline commit, leaving the
    fixture permanently dirty and causing ProjectBootstrapExecutor verification
    to fail with ``verification-failed:git-not-clean``. v1.0.8 stores ownership
    only in the external evidence directory and migrates exactly that legacy
    untracked marker when it is the sole dirty path.
    """
    target = target.resolve()
    if "DevPilot_Workspaces" in str(target) or "inventory-sales-local" in str(target).lower():
        raise OperatorBlock("Pilot workspace access is forbidden during GSDLC-04.")
    evidence_dir = evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if target.exists() and any(target.iterdir()):
        try:
            repaired = repair_legacy_marker(target, evidence_dir=evidence_dir)
        except Exception as exc:
            raise OperatorBlock(str(exc)) from exc
        state = repaired["fixture_state"]
        return {
            "fixture_id": "DEVPL-GSDLC-04-B-BROWSER-FIXTURE",
            "created_at": now(),
            "target": str(target),
            "git_head": state["head"],
            "fixture_reused": True,
            "repair_action": repaired["repair_action"],
            "git_clean": True,
            "ownership_marker_location": "external-evidence-only",
            "pilot_workspace_accessed": False,
            "network_used": False,
            "external_api_used": False,
            "files": {
                "docs/manual_authoring.md": sha256_file(target / "docs" / "manual_authoring.md"),
                "docs/manual_authoring.json": sha256_file(target / "docs" / "manual_authoring.json"),
            },
        }

    (target / "docs").mkdir(parents=True, exist_ok=True)
    (target / ".devpilot").mkdir(parents=True, exist_ok=True)
    (target / "docs" / "manual_authoring.md").write_text("# Manual authoring fixture\n\nApproved source v1.\n", encoding="utf-8", newline="\n")
    (target / "docs" / "manual_authoring.json").write_text('{"title":"Manual authoring fixture","version":1}\n', encoding="utf-8", newline="\n")
    (target / ".devpilot" / "project.yaml").write_text("project_id: gsdlc-04-b-browser-fixture\nproject_name: GSDLC 04 B Browser Fixture\nproject_type: software\n", encoding="utf-8", newline="\n")
    if not shutil.which("git"):
        raise OperatorBlock("Git is required for the disposable 04-B browser fixture.")
    git(target, "init")
    git(target, "config", "user.name", "DevPilot GSDLC 04-B Fixture")
    git(target, "config", "user.email", "devpilot-gsdlc04b@local.invalid")
    git(target, "add", "docs/manual_authoring.md", "docs/manual_authoring.json", ".devpilot/project.yaml")
    git(target, "commit", "-m", "test(gsdlc-04-b): browser fixture baseline")
    try:
        repaired = repair_legacy_marker(target, evidence_dir=evidence_dir)
    except Exception as exc:
        raise OperatorBlock(str(exc)) from exc
    state = repaired["fixture_state"]
    return {
        "fixture_id": "DEVPL-GSDLC-04-B-BROWSER-FIXTURE",
        "created_at": now(),
        "target": str(target),
        "git_head": state["head"],
        "fixture_reused": False,
        "repair_action": repaired["repair_action"],
        "git_clean": True,
        "ownership_marker_location": "external-evidence-only",
        "pilot_workspace_accessed": False,
        "network_used": False,
        "external_api_used": False,
        "files": {
            "docs/manual_authoring.md": sha256_file(target / "docs" / "manual_authoring.md"),
            "docs/manual_authoring.json": sha256_file(target / "docs" / "manual_authoring.json"),
        },
    }


def package_git_head(repo: Path, output_dir: Path, candidate_name: str) -> dict[str, Any]:
    identity = git_identity(repo)
    if not identity["git_present"]:
        raise OperatorBlock("Git repository is required to produce the clean successor ZIP from HEAD.")
    if identity["status_entries"]:
        raise OperatorBlock(f"Git worktree must be clean before package-git-head. Dirty entries: {identity['status_entries'][:20]}")
    tracked = git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines()
    violations = []
    for raw in tracked:
        rel = Path(raw)
        if any(part in FORBIDDEN_PARTS for part in rel.parts) or rel.name in RUNTIME_DB_NAMES or rel.name.startswith("auth.db") or rel.name.startswith("devpilot.db"):
            violations.append(raw)
    if violations:
        raise OperatorBlock(f"Forbidden runtime/cache paths are tracked in HEAD: {violations[:20]}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / candidate_name
    if output.exists():
        raise OperatorBlock(f"Refusing to overwrite existing candidate: {output}")
    run(["git", "archive", "--format=zip", f"--output={output}", "HEAD"], cwd=repo, timeout=300)
    digest = sha256_file(output)
    (output.with_suffix(output.suffix + ".sha256")).write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"candidate":str(output),"sha256":digest,"git_head":identity["head"],"tracked_files_total":len(tracked),"forbidden_tracked_total":0}


def write_checkpoint(repo: Path, phase: str, payload: dict[str, Any], evidence_dir: Path | None = None) -> Path:
    folder = repo / "outputs" / "gsdlc04b_operator" / "checkpoints"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{phase}.json"
    body = {"operator_id":OPERATOR_ID,"operator_version":OPERATOR_VERSION,"phase":phase,"timestamp":now(),**payload}
    serialized = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    path.write_text(serialized, encoding="utf-8")
    if evidence_dir is not None:
        evidence_text = str(evidence_dir)
        if "DevPilot_Workspaces" in evidence_text or "inventory-sales-local" in evidence_text.lower():
            raise OperatorBlock("Evidence directory cannot point to the real pilot workspace.")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / f"operator_{phase}.json"
        if evidence_path.exists():
            counter = 2
            while True:
                candidate = evidence_dir / f"operator_{phase}_{counter:02d}.json"
                if not candidate.exists():
                    evidence_path = candidate
                    break
                counter += 1
        evidence_path.write_text(serialized, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="State-aware GSDLC-04-B Windows operator. Dry-run/preflight by default.")
    parser.add_argument("--repo-root", default=r"D:\Projects\DevPilot_Local")
    parser.add_argument("--package-root", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--phase", choices=["prepare-repo", "preflight", "apply", "converge-source", "validate", "validate-corrective", "prepare-browser", "repo-review", "package-git-head"], default="preflight")
    parser.add_argument("--execute", action="store_true", help="Required for mutating phases prepare-repo/apply/prepare-browser/package-git-head.")
    parser.add_argument("--browser-fixture-root", default=r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_B_BROWSER")
    parser.add_argument("--output-dir", default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002\baselines\gsdlc_04_b")
    parser.add_argument("--candidate-name", default=DEFAULT_CANDIDATE_NAME)
    parser.add_argument("--branch-name", default=DEFAULT_BRANCH)
    parser.add_argument("--evidence-dir", default=None, help="Optional external evidence directory; JSON checkpoints are written here even when Git status is empty.")
    return parser.parse_args()


def main() -> int:
    args = parse_args(); repo = Path(args.repo_root).resolve(); package_root = Path(args.package_root).resolve(); evidence_dir = Path(args.evidence_dir).resolve() if args.evidence_dir else None
    try:
        if not repo.is_dir(): raise OperatorBlock(f"Repository root not found: {repo}")
        manifest = read_manifest(package_root)
        identity = git_identity(repo)
        inspection = inspect_delta(repo, package_root, manifest)
        unexpected_git = unexpected_git_status_entries(identity, manifest)
        if args.phase == "prepare-repo":
            if not args.execute:
                raise OperatorBlock("Phase prepare-repo changes only the Git branch pointer/working branch and requires explicit --execute. Nothing was changed.")
            result = prepare_repo_branch(repo, args.branch_name)
            payload={"status":"PASS","result":result,"mutations_performed":True,"source_mutations_performed":False,"full_regression_executed":False,"pilot_workspace_accessed":False}
            print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"prepare-repo",payload,evidence_dir); terminal_status("PASS", "prepare-repo completado"); return 0
        if args.phase == "preflight":
            missing_git = not identity['git_present']
            head_mismatch = bool(identity['git_present'] and identity['head'] != BASELINE_COMMIT and inspection['pending'])
            blocked = bool(inspection['conflicts'] or unexpected_git or head_mismatch or missing_git)
            payload={"status":"BLOCK" if blocked else "PASS","baseline":{"repo":BASELINE_REPO,"commit":BASELINE_COMMIT,"sha256":BASELINE_SHA256},"git":identity,"delta":inspection,"unexpected_git_entries":unexpected_git,"git_required":True,"git_missing":missing_git,"head_mismatch_with_pending_delta":head_mismatch,"mutations_performed":False,"full_regression_executed":False,"pilot_workspace_accessed":False}
            print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"preflight",payload,evidence_dir); terminal_status("BLOCK" if blocked else "PASS", "preflight bloqueado; deténgase y preserve evidencia" if blocked else "preflight completado sin conflictos"); return 20 if blocked else 0
        if args.phase in {"apply","converge-source","prepare-browser","package-git-head"} and not args.execute:
            raise OperatorBlock(f"Phase {args.phase} is mutating and requires explicit --execute. Nothing was changed.")
        if args.phase == "apply":
            if identity['git_present'] and identity['head'] != BASELINE_COMMIT and inspection['pending']:
                raise OperatorBlock(f"Git HEAD {identity['head']} is not the owner-adjudicated baseline {BASELINE_COMMIT}; apply is blocked before source mutation.")
            result=apply_delta(repo,package_root,manifest); payload={"status":"PASS","result":result,"full_regression_executed":False,"pilot_workspace_accessed":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"apply",payload,evidence_dir); terminal_status("PASS", "apply completado y verificado"); return 0
        if args.phase == "converge-source":
            if not identity['git_present']:
                raise OperatorBlock("Git repository is required for converge-source.")
            if identity['head'] != BASELINE_COMMIT:
                raise OperatorBlock(f"Git HEAD {identity['head']} is not predecessor {BASELINE_COMMIT}; no reset/rebase/force is authorized.")
            branch = current_branch(repo)
            if branch != args.branch_name:
                raise OperatorBlock(f"Current branch {branch!r} is not required branch {args.branch_name!r}; run prepare-repo only if the branch checkpoint was not previously completed.")
            if unexpected_git:
                raise OperatorBlock(f"Unexpected Git paths outside manifest before convergence: {unexpected_git[:20]}")
            if inspection['conflicts']:
                raise OperatorBlock(f"Preimage conflicts before convergence: {json.dumps(inspection['conflicts'], ensure_ascii=False)}")
            applied = apply_delta(repo, package_root, manifest)
            review = repo_review(repo, manifest)
            post = inspect_delta(repo, package_root, manifest)
            if post['pending'] or post['conflicts']:
                raise OperatorBlock(f"Convergence post-check failed: {post}")
            payload={"status":"PASS","result":{"apply":applied,"repo_review":review,"post_delta":post},"full_regression_executed":False,"pilot_workspace_accessed":False}
            print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"converge-source",payload,evidence_dir); terminal_status("PASS", "source convergido y repo-review PASS"); return 0
        if args.phase == "validate":
            if inspection['pending'] or inspection['conflicts']: raise OperatorBlock("Candidate does not match the full source delta; apply/reconcile before validation.")
            result=validate(repo); payload={"status":"PASS","result":result,"pilot_workspace_accessed":False,"network_used":False,"external_api_used":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"validate",payload,evidence_dir); terminal_status("PASS", "validación focal/acumulativa completada"); return 0
        if args.phase == "validate-corrective":
            if inspection['pending'] or inspection['conflicts']: raise OperatorBlock("Candidate does not match the full source delta; converge-source before corrective validation.")
            result=validate_corrective(repo); payload={"status":"PASS","result":result,"pilot_workspace_accessed":False,"network_used":False,"external_api_used":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"validate-corrective",payload,evidence_dir); terminal_status("PASS", "validación correctiva mínima recovery-010 completada"); return 0
        if args.phase == "repo-review":
            result=repo_review(repo, manifest); payload={"status":"PASS","result":result,"full_regression_executed":False,"pilot_workspace_accessed":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"repo-review",payload,evidence_dir); terminal_status("PASS", "repo-review completado"); return 0
        if args.phase == "prepare-browser":
            
            if evidence_dir is None:
                raise OperatorBlock("prepare-browser requires --evidence-dir so fixture ownership remains outside the Git fixture.")
            result=prepare_browser_fixture(Path(args.browser_fixture_root), evidence_dir); payload={"status":"PASS","result":result,"full_regression_executed":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"prepare-browser",payload,evidence_dir); terminal_status("PASS", "fixture browser preparado"); return 0
        if args.phase == "package-git-head":
            if inspection['pending'] or inspection['conflicts']: raise OperatorBlock("Source delta is not fully present; packaging blocked.")
            result=package_git_head(repo,Path(args.output_dir),args.candidate_name); payload={"status":"PASS","result":result,"full_regression_executed":False,"pilot_workspace_accessed":False}; print(json.dumps(payload,ensure_ascii=False,indent=2)); write_checkpoint(repo,"package-git-head",payload,evidence_dir); terminal_status("PASS", "candidate Git HEAD empaquetado"); return 0
        raise OperatorBlock("Unknown phase")
    except OperatorBlock as exc:
        payload={"status":"BLOCK","operator_id":OPERATOR_ID,"phase":args.phase,"message":str(exc),"full_regression_executed":False,"pilot_workspace_accessed":False}
        print(json.dumps(payload,ensure_ascii=False,indent=2),file=sys.stderr)
        try: write_checkpoint(repo,args.phase,payload,evidence_dir)
        except Exception: pass
        terminal_status("BLOCK", f"{args.phase}: {str(exc).splitlines()[0]}")
        return 20
    except subprocess.TimeoutExpired as exc:
        print(json.dumps({"status":"BLOCK","operator_id":OPERATOR_ID,"phase":args.phase,"message":f"Bounded timeout: {exc}","full_regression_executed":False},ensure_ascii=False,indent=2),file=sys.stderr); terminal_status("BLOCK", f"{args.phase}: timeout acotado"); return 21


if __name__ == "__main__":
    raise SystemExit(main())
