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

OPERATOR_ID = "DEVPL-GSDLC-04-C-OPERATOR"
OPERATOR_VERSION = "1.0.3"
BASELINE_REPO = "repo_DevPilot_Local_366_DEVPL_GSDLC_04_B_MANUAL_EDITOR_DRAFT_HISTORY_WINDOWS_VALIDATED_CANDIDATE.zip"
BASELINE_COMMIT = "b095bf5b75259c9c7c4a9a5c1b5d546cfe049d6f"
BASELINE_SHA256 = "3cfe97a376ee269b6c6fb3465e9549c2eea1e2160ecf5ff4848fd351a776ad92"
DEFAULT_BRANCH = "feat/devpl-gsdlc-04-c-artifact-import"
DEFAULT_CANDIDATE = "repo_DevPilot_Local_367_DEVPL_GSDLC_04_C_EXTERNAL_SOURCE_IMPORT_WINDOWS_VALIDATED_CANDIDATE.zip"
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], *, cwd: Path, timeout: int = 180, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(argv, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False, env=env)
    if check and cp.returncode != 0:
        raise OperatorBlock(f"Command failed ({cp.returncode}): {' '.join(argv)}\n{cp.stdout[-8000:]}")
    return cp


def git(repo: Path, *args: str, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, timeout=timeout, check=check)


def git_status(repo: Path) -> list[str]:
    cp = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, shell=False)
    if cp.returncode != 0:
        raise OperatorBlock(cp.stderr.decode(errors="replace")[-3000:])
    return [x.decode("utf-8", errors="replace") for x in cp.stdout.split(b"\0") if x]


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current").stdout.strip()


def git_blob_bytes(repo: Path, commit: str, rel: str) -> bytes | None:
    cp = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, shell=False)
    if cp.returncode != 0:
        return None
    return cp.stdout


def canonical_lf_bytes(raw: bytes) -> bytes:
    # Only EOL representation is normalized. Content bytes remain otherwise unchanged.
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_lf_sha256(raw: bytes) -> str:
    return hashlib.sha256(canonical_lf_bytes(raw)).hexdigest()


def preimage_equivalent_with_git_authority(*, target_bytes: bytes, git_blob: bytes | None, expected_raw_sha256: str | None, expected_canonical_lf_sha256: str | None, path_clean: bool) -> tuple[bool, bool]:
    """Return (equivalent, used_git_eol_authority).

    Raw SHA is preferred. If Windows checkout/archive EOL representation differs,
    a fallback is allowed only for a Git-clean path and only when BOTH the current
    working-tree bytes and the immutable predecessor Git blob canonicalize to the
    manifest's canonical-LF preimage hash. This cannot mask a real content edit.
    """
    raw_sha = hashlib.sha256(target_bytes).hexdigest()
    if expected_raw_sha256 and raw_sha == expected_raw_sha256:
        return True, False
    if not path_clean or not expected_canonical_lf_sha256 or git_blob is None:
        return False, False
    target_canonical = canonical_lf_sha256(target_bytes)
    blob_canonical = canonical_lf_sha256(git_blob)
    ok = target_canonical == expected_canonical_lf_sha256 and blob_canonical == expected_canonical_lf_sha256
    return ok, ok


def git_path_clean(repo: Path, rel: str) -> bool:
    a = git(repo, "diff", "--quiet", "--", rel, check=False)
    b = git(repo, "diff", "--cached", "--quiet", "--", rel, check=False)
    return a.returncode == 0 and b.returncode == 0


def safe_rel(raw: str) -> Path:
    rel = Path(raw.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or any(part in FORBIDDEN_PARTS for part in rel.parts):
        raise OperatorBlock(f"Unsafe delta path: {raw}")
    low = rel.name.lower()
    if low.startswith("auth.db") or low.startswith("devpilot.db"):
        raise OperatorBlock(f"Runtime DB is forbidden in source delta: {raw}")
    return rel


def load_manifest(package_root: Path) -> dict[str, Any]:
    path = package_root / "SOURCE_DELTA_MANIFEST.json"
    if not path.is_file():
        raise OperatorBlock(f"Missing SOURCE_DELTA_MANIFEST.json: {path}")
    d = json.loads(path.read_text(encoding="utf-8"))
    b = d.get("baseline", {})
    if b.get("repo") != BASELINE_REPO or b.get("commit") != BASELINE_COMMIT or b.get("sha256") != BASELINE_SHA256:
        raise OperatorBlock("Package baseline does not match owner-adjudicated repo366 authority.")
    return d


def prepare_repo(repo: Path, branch_name: str) -> dict[str, Any]:
    if not (repo / ".git").exists():
        raise OperatorBlock("D:\\Projects\\DevPilot_Local must be a Git checkout.")
    if git_status(repo):
        raise OperatorBlock("Repo must be clean before 04-C branch preparation.")
    if head(repo) != BASELINE_COMMIT:
        raise OperatorBlock(f"HEAD must be predecessor {BASELINE_COMMIT}; actual={head(repo)}")
    if not branch_name or branch_name.startswith("-") or any(ch.isspace() for ch in branch_name):
        raise OperatorBlock(f"Unsafe branch name: {branch_name!r}")
    ref = f"refs/heads/{branch_name}"
    probe = git(repo, "show-ref", "--verify", "--quiet", ref, check=False)
    if probe.returncode == 0:
        target = git(repo, "rev-parse", ref).stdout.strip()
        if target != BASELINE_COMMIT:
            raise OperatorBlock(f"Existing branch {branch_name} points to {target}; no reset/rebase/force is authorized.")
        if branch(repo) != branch_name:
            git(repo, "switch", branch_name)
        action = "selected-existing"
    elif probe.returncode == 1:
        git(repo, "switch", "-c", branch_name)
        action = "created"
    else:
        raise OperatorBlock("git show-ref failed while inspecting 04-C branch.")
    if head(repo) != BASELINE_COMMIT or git_status(repo):
        raise OperatorBlock("Post-branch verification failed.")
    return {"status":"PASS","branch":branch_name,"action":action,"head":head(repo),"worktree_clean":True,"destructive_git_used":False}


def classify(repo: Path, package_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    pending=[]; applied=[]; conflicts=[]; blob_authority=[]; eol_equivalent=[]
    for item in manifest["files"]:
        rel = safe_rel(item["path"]); target = repo / rel; op=item["operation"]
        pre=item.get("preimage_sha256"); pre_canonical=item.get("preimage_canonical_lf_sha256"); post=item.get("postimage_sha256")
        exists=target.is_file()
        raw=sha256_file(target) if exists else None
        if op == "create":
            if raw == post: applied.append(item["path"])
            elif not exists: pending.append(item["path"])
            else: conflicts.append({"path":item["path"],"reason":"unexpected-existing-file","actual":raw})
        elif op == "modify":
            if raw == post: applied.append(item["path"]); continue
            if not exists:
                conflicts.append({"path":item["path"],"reason":"missing-preimage"}); continue
            target_bytes=target.read_bytes()
            clean=git_path_clean(repo,item["path"])
            blob=git_blob_bytes(repo,BASELINE_COMMIT,item["path"]) if clean else None
            equivalent, used_eol = preimage_equivalent_with_git_authority(
                target_bytes=target_bytes, git_blob=blob, expected_raw_sha256=pre,
                expected_canonical_lf_sha256=pre_canonical, path_clean=clean
            )
            if equivalent:
                pending.append(item["path"]);
                if used_eol:
                    blob_authority.append(item["path"]); eol_equivalent.append(item["path"])
                continue
            conflicts.append({
                "path":item["path"],"reason":"preimage-mismatch","actual":raw,"expected_preimage":pre,
                "actual_canonical_lf_sha256":canonical_lf_sha256(target_bytes),
                "expected_canonical_lf_sha256":pre_canonical,
                "git_path_clean":clean,
                "git_blob_canonical_lf_sha256":canonical_lf_sha256(blob) if blob is not None else None,
            })
        elif op == "delete":
            if not exists: applied.append(item["path"]); continue
            target_bytes=target.read_bytes(); clean=git_path_clean(repo,item["path"]); blob=git_blob_bytes(repo,BASELINE_COMMIT,item["path"]) if clean else None
            equivalent, used_eol = preimage_equivalent_with_git_authority(
                target_bytes=target_bytes, git_blob=blob, expected_raw_sha256=pre,
                expected_canonical_lf_sha256=pre_canonical, path_clean=clean
            )
            if equivalent:
                pending.append(item["path"]);
                if used_eol:
                    blob_authority.append(item["path"]); eol_equivalent.append(item["path"])
            else:
                conflicts.append({"path":item["path"],"reason":"delete-preimage-mismatch","actual":raw,"expected_canonical_lf_sha256":pre_canonical})
        else:
            conflicts.append({"path":item["path"],"reason":f"unknown-operation:{op}"})
    return {
        "pending":pending,"already_applied":applied,"conflicts":conflicts,
        "gross_touched_surface_total":len(manifest["files"]),"net_diff_total":len(pending),
        "git_blob_authority_paths":blob_authority,"git_blob_authority_total":len(blob_authority),
        "eol_equivalent_preimage_paths":eol_equivalent,"eol_equivalent_preimage_total":len(eol_equivalent),
        "preimage_authority":"raw-sha256-first; fallback requires Git-clean path + canonical-LF equality for working tree and immutable predecessor Git blob",
    }




def _latest_checkpoint(evidence: Path, prefix: str) -> dict[str, Any] | None:
    candidates=sorted(evidence.glob(prefix+"*.json"), key=lambda p:p.stat().st_mtime)
    for p in reversed(candidates):
        try:
            d=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") in {"PASS","BLOCK"}:
            return d
    return None


def _dirty_path(entry: str) -> str:
    path=entry[3:] if len(entry)>=4 else entry
    if " -> " in path: path=path.split(" -> ")[-1]
    return path.strip('"')


def _semantic_recovery_003_ok(repo: Path, rel: str) -> bool:
    p=repo/Path(rel)
    if rel=="ui/web/scripts/gsdlc04c-artifact-import-smoke.mjs" and p.is_file():
        t=p.read_text(encoding="utf-8",errors="replace")
        return "new URL(import.meta.url).pathname" in t or "fileURLToPath(import.meta.url)" in t
    if rel==".devpilot/docs_governance/source_registry.json" and p.is_file():
        try: d=json.loads(p.read_text(encoding="utf-8"))
        except Exception: return False
        guides=[x for x in d.get("documents",[]) if x.get("doc_id")=="DEVPL-GSDLC-04-C-UNIQUE-WINDOWS-GUIDE"]
        return len(guides)==1 and guides[0].get("path") in {
            "GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_1.md",
            "GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_2.md",
            "GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_3.md",
        }
    if rel=="scripts/devpl_gsdlc_04_c_operator.py" and p.is_file():
        t=p.read_text(encoding="utf-8",errors="replace")
        return "DEVPL-GSDLC-04-C-OPERATOR" in t and any(f'OPERATOR_VERSION = "{v}"' in t for v in ("1.0.1","1.0.2","1.0.3"))
    if rel=="scripts/devpl_gsdlc_04_c_operator_config.json" and p.is_file():
        try: d=json.loads(p.read_text(encoding="utf-8"))
        except Exception: return False
        return d.get("operator_id")==OPERATOR_ID and str(d.get("version")) in {"1.0.1","1.0.2","1.0.3"}
    return False


def recovery_preflight_003(repo: Path, package_root: Path, manifest: dict[str, Any], evidence: Path, branch_name: str) -> dict[str, Any]:
    if head(repo)!=BASELINE_COMMIT or branch(repo)!=branch_name:
        raise OperatorBlock(f"Recovery-003 requires HEAD={BASELINE_COMMIT} on {branch_name}; actual={head(repo)} {branch(repo)}")
    conv=_latest_checkpoint(evidence,"operator_converge-source")
    review=_latest_checkpoint(evidence,"operator_repo-review")
    static=_latest_checkpoint(evidence,"operator_validate_ui-static-04c")
    if not conv or conv.get("status")!="PASS": raise OperatorBlock("Recovery-003 requires prior v1.0.2 converge-source PASS evidence.")
    if not review or review.get("status")!="PASS": raise OperatorBlock("Recovery-003 requires prior repo-review PASS evidence.")
    if not static or static.get("status")!="BLOCK": raise OperatorBlock("Recovery-003 requires the preserved ui-static-04c BLOCK checkpoint.")
    msg=json.dumps(static,ensure_ascii=False)
    if re.search(r"D:\\+D:\\+Projects", msg) is None:
        raise OperatorBlock("Preserved ui-static BLOCK is not the recognized D:\\D:\\ Windows URL-path defect.")
    allowed={x["path"] for x in manifest["files"]}
    allowed.add("GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_2.md")
    unknown=[e for e in git_status(repo) if _dirty_path(e) not in allowed]
    if unknown: raise OperatorBlock(f"Unknown dirty paths outside governed Recovery-003 surface: {unknown[:20]}")
    cp=git(repo,"-c","core.safecrlf=false","diff","--check",check=False)
    errors=[ln for ln in cp.stdout.splitlines() if ln.strip() and "LF will be replaced by CRLF" not in ln and "CRLF will be replaced by LF" not in ln and "original line endings" not in ln]
    if cp.returncode!=0 or errors: raise OperatorBlock(f"Recovery-003 refuses a tree with real whitespace defects: {errors[:20]}")
    special=[".devpilot/docs_governance/source_registry.json","scripts/devpl_gsdlc_04_c_operator.py","scripts/devpl_gsdlc_04_c_operator_config.json","ui/web/scripts/gsdlc04c-artifact-import-smoke.mjs"]
    bad=[x for x in special if (repo/x).exists() and not _semantic_recovery_003_ok(repo,x)]
    if bad: raise OperatorBlock(f"Recovery-003 semantic state mismatch in superseded paths: {bad}")
    old=repo/"GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_2.md"
    if old.exists():
        t=old.read_text(encoding="utf-8",errors="replace")
        if 'doc_id: "DEVPL-GSDLC-04-C-UNIQUE-WINDOWS-GUIDE"' not in t or 'version: "1.0.2"' not in t:
            raise OperatorBlock("Existing v1.0.2 guide is not the recognized superseded 04-C guide; refusing removal.")
    return {"status":"PASS","head":head(repo),"branch":branch(repo),"prior_converge_pass":True,"prior_repo_review_pass":True,"recognized_ui_static_block":True,"unknown_dirty_paths":[],"safe_recovery_removals":[old.name] if old.exists() else [],"semantic_superseded_paths":[x for x in special if (repo/x).exists()],"source_mutations_performed":False,"full_regression_executed":False}


def classify_recovery_003(repo: Path, package_root: Path, manifest: dict[str, Any], evidence: Path, branch_name: str) -> dict[str, Any]:
    recovery_preflight_003(repo,package_root,manifest,evidence,branch_name)
    base=classify(repo,package_root,manifest)
    by={x["path"]:x for x in manifest["files"]}
    special={".devpilot/docs_governance/source_registry.json","scripts/devpl_gsdlc_04_c_operator.py","scripts/devpl_gsdlc_04_c_operator_config.json","ui/web/scripts/gsdlc04c-artifact-import-smoke.mjs"}
    remaining=[]; pending=list(base["pending"]); applied=list(base["already_applied"])
    for c in base["conflicts"]:
        rel=c.get("path")
        if rel in special and _semantic_recovery_003_ok(repo,rel):
            if rel not in pending: pending.append(rel)
        else: remaining.append(c)
    base["pending"]=pending; base["already_applied"]=applied; base["conflicts"]=remaining; base["net_diff_total"]=len(pending)
    base["superseded_recovery_003_paths"]=sorted([x for x in pending if x in special])
    return base


def apply_recovery_003(repo: Path, package_root: Path, manifest: dict[str, Any], evidence: Path, branch_name: str) -> dict[str, Any]:
    before=classify_recovery_003(repo,package_root,manifest,evidence,branch_name)
    if before["conflicts"]: raise OperatorBlock(f"Recovery-003 conflicts before apply: {before['conflicts'][:12]}")
    old=repo/"GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_C_v1_0_2.md"
    removed=[]
    if old.exists(): old.unlink(); removed.append(old.name)
    by={x["path"]:x for x in manifest["files"]}; applied_now=[]
    for raw in before["pending"]:
        item=by[raw]; rel=safe_rel(raw); dst=repo/rel
        if item["operation"]=="delete":
            if dst.exists(): dst.unlink()
            applied_now.append(raw); continue
        src=package_root/"source_delta"/rel
        if not src.is_file() or sha256_file(src)!=item["postimage_sha256"]: raise OperatorBlock(f"Package postimage invalid/missing: {raw}")
        _replace(src,dst)
        if sha256_file(dst)!=item["postimage_sha256"]: raise OperatorBlock(f"Post-write hash mismatch: {raw}")
        applied_now.append(raw)
    after=classify(repo,package_root,manifest)
    if after["pending"] or after["conflicts"]: raise OperatorBlock(f"Recovery-003 post-apply verification failed: {after}")
    return {"applied_paths":applied_now,"recovery_removed_paths":removed,"post_apply":after}


def windows_path_portability_audit(repo: Path) -> dict[str, Any]:
    scripts=repo/"ui/web/scripts"; findings=[]; scanned=0
    unsafe=re.compile(r"new\s+URL\(\s*import\.meta\.url\s*\)\.pathname|import\.meta\.url\s*\)\.pathname")
    for p in sorted(list(scripts.rglob("*.mjs"))+list(scripts.rglob("*.js"))):
        scanned+=1; t=p.read_text(encoding="utf-8",errors="replace")
        if unsafe.search(t): findings.append(str(p.relative_to(repo)).replace("\\\\","/"))
    target=repo/"ui/web/scripts/gsdlc04c-artifact-import-smoke.mjs"; tt=target.read_text(encoding="utf-8")
    if "fileURLToPath(import.meta.url)" not in tt: findings.append("04-C smoke missing fileURLToPath(import.meta.url)")
    if findings: raise OperatorBlock(f"Windows path portability audit BLOCK: {findings[:20]}")
    return {"status":"PASS","scripts_scanned":scanned,"unsafe_url_pathname_total":0,"gsdlc04c_file_url_to_path":True,"historical_regression_class":"POST-H-028 D:\\\\D:\\\\ path duplication","full_regression_executed":False}


def validate_corrective_003(repo: Path, evidence: Path) -> dict[str, Any]:
    py=_py(repo); env=dict(os.environ); env["PYTHONPATH"]="src"; env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
    npm=shutil.which("npm.cmd") or shutil.which("npm")
    if not npm: raise OperatorBlock("npm.cmd/npm missing from PATH.")
    if os.name=="nt" and not (repo/".venv"/"Scripts"/"python.exe").is_file(): raise OperatorBlock(".venv\\Scripts\\python.exe missing.")
    if not (repo/"ui/web/node_modules").is_dir(): raise OperatorBlock("ui/web/node_modules missing; no silent network provisioning authorized.")
    evidence.mkdir(parents=True,exist_ok=True); out=[]
    audit=windows_path_portability_audit(repo); rec={"status":"PASS","gate":"windows-path-portability-audit",**audit,"timestamp":now()}; (evidence/"operator_validate_windows-path-portability-audit.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\\n",encoding="utf-8"); out.append(rec)
    gates=[
      ("docs-registry-policy",[py,"-m","pytest","--assert=plain","-q","tests/test_documentation_source_registry_schema.py","tests/test_devpl_documentation_contract_reconciliation_policy.py"],300),
      ("docs-governance",[py,"-m","devpilot_core","docs-governance","validate","--json"],300),
      ("ui-static-04c",[npm,"--prefix","ui/web","run","test:artifact-import"],180),
      ("ui-build",[npm,"--prefix","ui/web","run","build"],600),
    ]
    for name,argv,timeout in gates:
        cp=run(argv,cwd=repo,timeout=timeout,env=env,check=False)
        rec={"status":"PASS" if cp.returncode==0 else "BLOCK","gate":name,"returncode":cp.returncode,"output_tail":cp.stdout[-12000:],"timestamp":now()}
        (evidence/f"operator_validate_{name}.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\\n",encoding="utf-8"); out.append(rec)
        if cp.returncode!=0: raise OperatorBlock(f"Corrective validation gate {name} BLOCK.\\n{cp.stdout[-8000:]}")
    return {"gates":out,"validation_scope":"Recovery-003 forward-only: path portability + affected docs + ui-static + ui-build","prior_v102_pass_gates_reused":True,"full_regression_runs":0,"full_regression_executed":False,"network_used":False,"external_api_used":False}

def _replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".devpl04c.tmp")
    for attempt in range(5):
        try:
            shutil.copyfile(src,tmp); os.replace(tmp,dst); return
        except PermissionError:
            if tmp.exists(): tmp.unlink(missing_ok=True)
            if attempt == 4: raise
            time.sleep(0.35*(attempt+1))


def apply(repo: Path, package_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    before=classify(repo,package_root,manifest)
    if before["conflicts"]:
        raise OperatorBlock(f"Delta conflicts before apply: {before['conflicts'][:12]}")
    applied_now=[]
    by={x["path"]:x for x in manifest["files"]}
    for raw in before["pending"]:
        item=by[raw]; rel=safe_rel(raw); dst=repo/rel
        if item["operation"] == "delete":
            dst.unlink(); applied_now.append(raw); continue
        src=package_root/"source_delta"/rel
        if not src.is_file() or sha256_file(src) != item["postimage_sha256"]:
            raise OperatorBlock(f"Package postimage invalid/missing: {raw}")
        _replace(src,dst)
        if sha256_file(dst) != item["postimage_sha256"]:
            raise OperatorBlock(f"Post-write hash mismatch: {raw}")
        applied_now.append(raw)
    after=classify(repo,package_root,manifest)
    if after["pending"] or after["conflicts"]:
        raise OperatorBlock(f"Post-apply verification failed: {after}")
    return {"applied_paths":applied_now,"post_apply":after}


def repo_review(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    allowed=set(x["path"] for x in manifest["files"])
    status=git_status(repo)
    unexpected=[]
    for entry in status:
        path=entry[3:] if len(entry)>=4 else entry
        if " -> " in path: path=path.split(" -> ")[-1]
        path=path.strip('"')
        if path not in allowed: unexpected.append(entry)
    if unexpected:
        raise OperatorBlock(f"Unexpected Git paths outside source delta: {unexpected[:20]}")
    cp=git(repo,"-c","core.safecrlf=false","diff","--check",check=False)
    errors=[ln for ln in cp.stdout.splitlines() if ln.strip() and "LF will be replaced by CRLF" not in ln and "CRLF will be replaced by LF" not in ln and "original line endings" not in ln]
    if cp.returncode != 0 or errors:
        raise OperatorBlock(f"git diff --check found real whitespace defects: {errors[:30]}")
    tracked=git(repo,"ls-files").stdout.splitlines(); forbidden=[]
    for raw in tracked:
        rel=Path(raw)
        if any(x in FORBIDDEN_PARTS for x in rel.parts) or rel.name.lower().startswith(("auth.db","devpilot.db")):
            forbidden.append(raw)
    if forbidden: raise OperatorBlock(f"Forbidden runtime/cache tracked paths: {forbidden[:20]}")
    return {"head":head(repo),"branch":branch(repo),"status_entries":status,"diff_check":"PASS","unexpected_git_entries":[],"forbidden_tracked_total":0,"tracked_files_total":len(tracked)}


def _py(repo: Path) -> str:
    win=repo/".venv"/"Scripts"/"python.exe"
    return str(win) if win.is_file() else sys.executable


def validate(repo: Path, evidence: Path) -> dict[str, Any]:
    py=_py(repo); env=dict(os.environ); env["PYTHONPATH"]="src"; env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
    npm=shutil.which("npm.cmd") or shutil.which("npm")
    if not npm: raise OperatorBlock("npm.cmd/npm missing from PATH.")
    if os.name == "nt" and not (repo/".venv"/"Scripts"/"python.exe").is_file():
        raise OperatorBlock(".venv\\Scripts\\python.exe missing; preserve repo and provision the existing DevPilot venv before validation.")
    if not (repo/"ui/web/node_modules").is_dir():
        raise OperatorBlock("ui/web/node_modules missing. Operator refuses silent network provisioning; preserve the BLOCK and stop. Do not improvise npm install/npm ci outside the guide.")
    gates=[
      ("focused-04c",[py,"-m","pytest","--assert=plain","-q","tests/test_devpl_gsdlc_04_c_artifact_import.py"],300),
      ("cumulative-a-b-c-uoc",[py,"-m","pytest","--assert=plain","-q","tests/test_devpl_gsdlc_04_a_artifact_lifecycle.py","tests/test_devpl_gsdlc_04_b_manual_editor_draft_history.py","tests/test_devpl_gsdlc_04_c_artifact_import.py","tests/test_post_h_eval_002_uoc_004_contracts.py","tests/test_post_h_eval_002_uoc_005_contracts.py"],600),
      ("impact-rbac-api-ui-docs",[py,"-m","pytest","--assert=plain","-q","tests/test_devpl_gsdlc_02_c_server_rbac.py","tests/test_devpl_gsdlc_02_c_api_rbac.py","tests/test_api_workspace_documents.py","tests/test_web_ui_workspace_documents.py","tests/test_post_h_014_api_route_contracts.py","tests/test_post_h_028_ui_route_registry_enforcement.py","tests/test_documentation_source_registry_schema.py","tests/test_devpl_documentation_contract_reconciliation_policy.py"],600),
      ("project-state",[py,"-m","devpilot_core","project-state","validate","--json"],180),
      ("tcr-v1",[py,"-m","devpilot_core","test-contracts","validate","--json"],180),
      ("tcr-v2",[py,"-m","devpilot_core","test-contracts","validate-v2","--json"],180),
      ("schema-list",[py,"-m","devpilot_core","schema","list","--json"],180),
      ("docs-governance",[py,"-m","devpilot_core","docs-governance","validate","--json"],300),
      ("api-contract-drift",[py,"-m","devpilot_core","api","contract-drift","--json"],300),
      ("api-security",[py,"-m","devpilot_core","api","security-hardening","--json"],300),
      ("ui-route-enforcement",[py,"-m","devpilot_core","api","ui-route-enforcement","--json"],240),
      ("ui-static-04c",[npm,"--prefix","ui/web","run","test:artifact-import"],180),
      ("ui-build",[npm,"--prefix","ui/web","run","build"],600),
    ]
    evidence.mkdir(parents=True,exist_ok=True); out=[]
    for name,argv,timeout in gates:
        cp=run(argv,cwd=repo,timeout=timeout,env=env,check=False)
        rec={"status":"PASS" if cp.returncode==0 else "BLOCK","gate":name,"returncode":cp.returncode,"output_tail":cp.stdout[-12000:],"timestamp":now()}
        (evidence/f"operator_validate_{name}.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        out.append(rec)
        if cp.returncode != 0: raise OperatorBlock(f"Validation gate {name} BLOCK.\n{cp.stdout[-8000:]}")
    return {"gates":out,"validation_scope":"04-C focal+cumulative+impact+deterministic","full_regression_runs":0,"full_regression_executed":False,"network_used":False,"external_api_used":False}


def git_commit(repo: Path, manifest: dict[str, Any], evidence: Path, message: str) -> dict[str, Any]:
    marker=evidence/"DEVPL_GSDLC_04_C_BROWSER_ACCEPTANCE_VALIDATION.json"
    if not marker.is_file(): raise OperatorBlock("Browser evidence validation PASS marker missing; commit is blocked.")
    m=json.loads(marker.read_text(encoding="utf-8"))
    if m.get("status") != "PASS": raise OperatorBlock("Browser evidence validation is not PASS.")
    review=repo_review(repo,manifest)
    dirty=[]
    for entry in review["status_entries"]:
        p=entry[3:] if len(entry)>=4 else entry
        if " -> " in p: p=p.split(" -> ")[-1]
        dirty.append(p.strip('"'))
    if not dirty: raise OperatorBlock("No 04-C source changes are dirty; refusing empty commit.")
    allowed=set(x["path"] for x in manifest["files"])
    if not set(dirty)<=allowed: raise OperatorBlock("Dirty paths exceed governed delta.")
    for p in sorted(set(dirty)): git(repo,"add","--",p)
    cp=git(repo,"-c","core.safecrlf=false","diff","--cached","--check",check=False)
    if cp.returncode != 0: raise OperatorBlock(f"Staged diff whitespace BLOCK: {cp.stdout[-5000:]}")
    git(repo,"commit","-m",message,timeout=180)
    if git_status(repo): raise OperatorBlock("Worktree not clean after commit.")
    return {"status":"PASS","commit":head(repo),"message":message,"staged_paths_total":len(set(dirty)),"worktree_clean":True}


def package_head(repo: Path, artifacts_root: Path, name: str) -> dict[str, Any]:
    if git_status(repo): raise OperatorBlock("Worktree must be clean before candidate packaging.")
    tracked=git(repo,"ls-tree","-r","--name-only","HEAD").stdout.splitlines(); bad=[]
    for raw in tracked:
        rel=Path(raw)
        if any(x in FORBIDDEN_PARTS for x in rel.parts) or rel.name.lower().startswith(("auth.db","devpilot.db")): bad.append(raw)
    if bad: raise OperatorBlock(f"Forbidden tracked paths in HEAD: {bad[:20]}")
    outdir=artifacts_root/"baselines"/"gsdlc_04_c"; outdir.mkdir(parents=True,exist_ok=True); out=outdir/name
    if out.exists(): raise OperatorBlock(f"Candidate already exists; refusing overwrite: {out}")
    run(["git","archive","--format=zip",f"--output={out}","HEAD"],cwd=repo,timeout=300)
    digest=sha256_file(out); out.with_suffix(out.suffix+".sha256").write_text(f"{digest}  {out.name}\n",encoding="utf-8")
    return {"status":"PASS","candidate":str(out),"sha256":digest,"git_head":head(repo),"tracked_files_total":len(tracked),"forbidden_tracked_total":0,"full_regression_executed":False}


def checkpoint(evidence: Path, phase: str, payload: dict[str, Any]) -> None:
    evidence.mkdir(parents=True,exist_ok=True)
    path=evidence/f"operator_{phase}.json"
    if path.exists():
        i=2
        while (evidence/f"operator_{phase}_{i:02d}.json").exists(): i+=1
        path=evidence/f"operator_{phase}_{i:02d}.json"
    path.write_text(json.dumps({"operator_id":OPERATOR_ID,"operator_version":OPERATOR_VERSION,"phase":phase,"timestamp":now(),**payload},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def main() -> int:
    p=argparse.ArgumentParser(description="Governed GSDLC-04-C source operator; dry-run by default.")
    p.add_argument("--repo-root",default=r"D:\Projects\DevPilot_Local")
    p.add_argument("--package-root",default=str(Path(__file__).resolve().parents[1]))
    p.add_argument("--evidence-dir",default=r"D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-C")
    p.add_argument("--artifacts-root",default=r"D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002")
    p.add_argument("--branch-name",default=DEFAULT_BRANCH)
    p.add_argument("--candidate-name",default=DEFAULT_CANDIDATE)
    p.add_argument("--commit-message",default="feat(gsdlc-04-c): add governed paste and artifact import")
    p.add_argument("--phase",choices=["prepare-repo","preflight","recovery-preflight-003","converge-source","validate","validate-corrective-003","repo-review","git-commit","package-git-head"],default="recovery-preflight-003")
    p.add_argument("--execute",action="store_true")
    a=p.parse_args(); repo=Path(a.repo_root).resolve(); pkg=Path(a.package_root).resolve(); evidence=Path(a.evidence_dir).resolve()
    try:
        if "inventory-sales-local" in str(repo).lower() or "devpilot_workspaces" in str(repo).lower(): raise OperatorBlock("Pilot workspace access forbidden.")
        if not repo.is_dir(): raise OperatorBlock(f"Repo missing: {repo}")
        manifest=load_manifest(pkg)
        if a.phase in {"prepare-repo","converge-source","git-commit","package-git-head"} and not a.execute:
            raise OperatorBlock(f"Phase {a.phase} mutates state and requires --execute.")
        if a.phase=="prepare-repo": result=prepare_repo(repo,a.branch_name)
        elif a.phase=="preflight":
            if not (repo/".git").exists(): raise OperatorBlock("Git repo required.")
            if head(repo)!=BASELINE_COMMIT and branch(repo)!=a.branch_name:
                raise OperatorBlock(f"Unexpected HEAD/branch before preflight: {head(repo)} {branch(repo)}")
            result=classify(repo,pkg,manifest)
            if result["conflicts"]: raise OperatorBlock(f"Preflight conflicts: {result['conflicts'][:12]}")
            result={"status":"PASS",**result,"full_regression_executed":False}
        elif a.phase=="recovery-preflight-003": result=recovery_preflight_003(repo,pkg,manifest,evidence,a.branch_name)
        elif a.phase=="converge-source":
            # Recovery-003 is state-aware for the known v1.0.2 partial state; clean baseline still uses normal apply.
            try:
                applied=apply_recovery_003(repo,pkg,manifest,evidence,a.branch_name)
            except OperatorBlock as recovery_exc:
                if not git_status(repo): applied=apply(repo,pkg,manifest)
                else: raise recovery_exc
            review=repo_review(repo,manifest); result={"status":"PASS","apply":applied,"repo_review":review,"full_regression_executed":False}
        elif a.phase=="validate": result={"status":"PASS",**validate(repo,evidence)}
        elif a.phase=="validate-corrective-003": result={"status":"PASS",**validate_corrective_003(repo,evidence)}
        elif a.phase=="repo-review": result={"status":"PASS",**repo_review(repo,manifest),"full_regression_executed":False}
        elif a.phase=="git-commit": result=git_commit(repo,manifest,evidence,a.commit_message)
        else: result=package_head(repo,Path(a.artifacts_root).resolve(),a.candidate_name)
        payload={"status":"PASS","result":result,"pilot_workspace_accessed":False}; print(json.dumps(payload,indent=2,ensure_ascii=False)); checkpoint(evidence,a.phase,payload); verdict("PASS",f"{a.phase} completado"); return 0
    except (OperatorBlock,subprocess.TimeoutExpired,PermissionError,OSError,json.JSONDecodeError) as exc:
        payload={"status":"BLOCK","operator_id":OPERATOR_ID,"version":OPERATOR_VERSION,"phase":a.phase,"timestamp":now(),"message":str(exc),"source_mutations_performed":False if a.phase in {"prepare-repo","preflight","recovery-preflight-003","validate","validate-corrective-003","repo-review"} else None,"full_regression_executed":False,"pilot_workspace_accessed":False}
        print(json.dumps(payload,indent=2,ensure_ascii=False));
        try: checkpoint(evidence,a.phase,payload)
        except Exception: pass
        verdict("BLOCK",f"{a.phase}: {exc}"); return 20


if __name__ == "__main__":
    raise SystemExit(main())
