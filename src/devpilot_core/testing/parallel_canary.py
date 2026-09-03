from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.policy.secrets import SecretGuard

from .conflict_graph import ParallelShadowPlanner
from .full_regression import _git_semantic_clean_guard
from .isolation_registry import IsolationState, TestIsolationRegistry


DEFAULT_MANIFEST_PATH = Path(".devpilot/testing/frx_v2_3_d_canary_manifest.json")
DEFAULT_BR_MANIFEST_PATH = Path(".devpilot/testing/frx_v2_3_br_candidate_manifest.json")
DEFAULT_BR_SHADOW_PATH = Path("docs/audits/FRX_V2_3_BR_SUCCESSOR_SHADOW_PLAN.json")
REPORT_SCHEMA_ID = "devpilot.testing.parallel_canary_report.v1"
TERMINAL_OUTCOMES = {"PASS", "FAIL", "ERROR", "SKIP_APPROVED"}


class ParallelCanaryBlock(RuntimeError):
    """Deterministic bounded-canary BLOCK condition."""


@dataclass(frozen=True)
class CanaryJob:
    job_id: str
    nodeid: str
    contract_id: str
    br_candidate_id: str
    runtime_estimate_seconds: float
    resource_lock_keys: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CanaryJob":
        return cls(
            job_id=str(payload["job_id"]),
            nodeid=str(payload["nodeid"]),
            contract_id=str(payload["contract_id"]),
            br_candidate_id=str(payload["br_candidate_id"]),
            runtime_estimate_seconds=float(payload["runtime_estimate_seconds"]),
            resource_lock_keys=tuple(str(x) for x in payload.get("resource_lock_keys") or ()),
        )


@dataclass
class ActiveJob:
    mode: str
    job: CanaryJob
    clone_root: Path
    namespace_root: Path
    log_path: Path
    junit_path: Path
    outcomes_path: Path
    process: subprocess.Popen[Any]
    log_handle: Any
    launched_at: float
    lock_keys: tuple[str, ...]
    terminal_receipt_seen: bool = False
    terminal_receipt_seen_at: float | None = None


@dataclass
class ResourceLockTable:
    held_by: dict[str, str] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def acquire(self, job_id: str, keys: Iterable[str]) -> bool:
        ordered = tuple(sorted(set(str(k) for k in keys)))
        now = time.monotonic()
        conflicts = [key for key in ordered if key in self.held_by and self.held_by[key] != job_id]
        self.trace.append({"event": "lock-request", "job_id": job_id, "keys": list(ordered), "monotonic": now})
        if conflicts:
            self.trace.append({"event": "lock-blocked", "job_id": job_id, "keys": conflicts, "monotonic": time.monotonic()})
            return False
        for key in ordered:
            self.held_by[key] = job_id
        self.trace.append({"event": "lock-acquired", "job_id": job_id, "keys": list(ordered), "monotonic": time.monotonic()})
        return True

    def release(self, job_id: str, keys: Iterable[str]) -> None:
        ordered = tuple(sorted(set(str(k) for k in keys)))
        for key in ordered:
            if self.held_by.get(key) == job_id:
                del self.held_by[key]
        self.trace.append({"event": "lock-released", "job_id": job_id, "keys": list(ordered), "monotonic": time.monotonic()})


class BoundedParallelCanaryRunner:
    """FRX-v2.3-D two-job serial/parallel canary.

    The runner intentionally has no generic scheduler.  It launches the two
    owner-authorized atomic pytest jobs directly with ``subprocess.Popen`` and
    polls their process lifecycle from one coordinator thread.  This avoids
    nested process supervisors, xdist, shell semantics and thread-pool shutdown
    ambiguity while retaining live per-node terminal receipts and hard worker
    bounds.
    """

    version = "1.0.0"

    def __init__(self, root: Path, *, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
        self.root = Path(root).resolve()
        self.manifest_path = self.root / manifest_path
        self.registry = TestIsolationRegistry(self.root)
        self.secret_guard = SecretGuard(self.root)

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _json_write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _run_git(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )

    def _source_commit(self) -> str | None:
        if not (self.root / ".git").exists():
            return None
        completed = self._run_git(self.root, "rev-parse", "HEAD")
        return completed.stdout.strip() if completed.returncode == 0 else None

    def _load_and_validate_inputs(self) -> tuple[dict[str, Any], list[CanaryJob], dict[str, Any]]:
        if not self.manifest_path.is_file():
            raise ParallelCanaryBlock(f"canary manifest is missing: {self.manifest_path}")
        manifest_raw = self.manifest_path.read_bytes()
        manifest = json.loads(manifest_raw.decode("utf-8"))
        jobs = [CanaryJob.from_dict(item) for item in manifest.get("jobs") or []]
        policy = manifest.get("policy") or {}
        if manifest.get("schema_id") != "devpilot.testing.frx_v2_3_d_canary_manifest.v1":
            raise ParallelCanaryBlock("unexpected canary manifest schema_id")
        if len(jobs) != 2 or len({j.nodeid for j in jobs}) != 2 or len({j.contract_id for j in jobs}) != 2:
            raise ParallelCanaryBlock("FRX-v2.3-D requires exactly two unique nodeids from two distinct contracts")
        if int(policy.get("max_workers", -1)) != 2 or int(policy.get("full_regression_runs", -1)) != 0:
            raise ParallelCanaryBlock("canary policy must remain workers=2 and full_regression_runs=0")
        for false_key in ("shell_allowed", "xdist_allowed", "network_runtime_allowed"):
            if policy.get(false_key) is not False:
                raise ParallelCanaryBlock(f"{false_key} must remain false")
        for true_key in (
            "parallel_safe_required",
            "same_subset_serial_then_parallel",
            "separate_worker_namespaces",
            "resource_locks_required",
            "live_terminal_receipts_required",
            "source_clean_required",
            "incremental_speedup_required",
        ):
            if policy.get(true_key) is not True:
                raise ParallelCanaryBlock(f"{true_key} must remain true")

        registry = self.registry.load()
        semantics = TestIsolationRegistry.validate_semantics(registry)
        if semantics.get("ok") is not True:
            raise ParallelCanaryBlock("test isolation registry semantic validation did not PASS")
        by_nodeid = {str(e["nodeid"]): e for e in registry.get("entries") or []}
        selected_entries: list[dict[str, Any]] = []
        for job in jobs:
            entry = by_nodeid.get(job.nodeid)
            if not entry:
                raise ParallelCanaryBlock(f"selected nodeid is absent from TestIsolationRegistry: {job.nodeid}")
            if entry.get("state") != IsolationState.PROVEN_PARALLEL_SAFE.value or entry.get("parallel_safe") is not True:
                raise ParallelCanaryBlock(f"selected nodeid is not PROVEN_PARALLEL_SAFE: {job.nodeid}")
            selected_entries.append(entry)

        br_manifest = self._load_json(self.root / DEFAULT_BR_MANIFEST_PATH)
        br_by_nodeid = {str(item["nodeid"]): item for item in br_manifest.get("candidates") or []}
        for job in jobs:
            candidate = br_by_nodeid.get(job.nodeid)
            if not candidate:
                raise ParallelCanaryBlock(f"selected nodeid lacks FRX-v2.3-BR candidate evidence: {job.nodeid}")
            if str(candidate.get("candidate_id")) != job.br_candidate_id or str(candidate.get("contract_id")) != job.contract_id:
                raise ParallelCanaryBlock(f"BR candidate/contract mismatch for {job.nodeid}")

        graph = ParallelShadowPlanner.build_conflict_graph(selected_entries)
        if graph.edges:
            raise ParallelCanaryBlock(f"selected canary has {len(graph.edges)} conflict edge(s)")

        shadow_path = self.root / DEFAULT_BR_SHADOW_PATH
        shadow = self._load_json(shadow_path) if shadow_path.exists() else {}
        if shadow:
            decision = ((shadow.get("amdahl_feasibility") or {}).get("decision") or shadow.get("amdahl_decision"))
            authorized = shadow.get("frx_v2_3_d_authorized")
            if decision != "GO" or authorized is not True:
                raise ParallelCanaryBlock("FRX-v2.3-BR successor feasibility no longer authorizes D")

        return manifest, jobs, {
            "manifest_sha256": self._sha256_bytes(manifest_raw),
            "isolation_registry_status": semantics,
            "conflict_graph": graph.to_dict(),
            "br_shadow_checked": bool(shadow),
        }

    def preview(self) -> dict[str, Any]:
        try:
            manifest, jobs, validation = self._load_and_validate_inputs()
            source_commit = self._source_commit()
            source_guard = _git_semantic_clean_guard(self.root, expected_commit=source_commit) if source_commit else None
            return {
                "schema_id": REPORT_SCHEMA_ID,
                "version": self.version,
                "status": "PREVIEW",
                "decision": "PREVIEW",
                "source_commit": source_commit,
                "manifest_sha256": validation["manifest_sha256"],
                "jobs_total": len(jobs),
                "jobs": [job.__dict__ for job in jobs],
                "max_workers": int((manifest.get("policy") or {}).get("max_workers", 2)),
                "full_regression_runs": 0,
                "source_clean": bool(source_guard and source_guard.get("clean")) if source_commit else False,
                "conflict_violations": len((validation["conflict_graph"] or {}).get("edges") or []),
                "serial": {},
                "parallel": {},
                "outcome_parity": False,
                "secret_leakage": False,
                "incremental_parallel_speedup_percent": None,
                "frx_v2_3_e_authorized": False,
                "validation": validation,
            }
        except Exception as exc:
            return self._block_report(str(exc), manifest_sha256="0" * 64)

    def run(self, *, output_dir: Path, clone_root: Path, timeout_seconds: int = 45) -> dict[str, Any]:
        started = time.monotonic()
        output_dir = Path(output_dir).resolve()
        clone_root = Path(clone_root).resolve()
        if timeout_seconds < 5 or timeout_seconds > 180:
            return self._block_report("timeout_seconds must be between 5 and 180", manifest_sha256="0" * 64)
        try:
            manifest, jobs, validation = self._load_and_validate_inputs()
            manifest_sha = validation["manifest_sha256"]
            if not (self.root / ".git").exists():
                raise ParallelCanaryBlock("FRX-v2.3-D execute requires a Git worktree; ZIP-only trees are preview/focal-validation only")
            source_commit = self._source_commit()
            if not source_commit:
                raise ParallelCanaryBlock("cannot resolve source commit")
            before_guard = _git_semantic_clean_guard(self.root, expected_commit=source_commit)
            if not before_guard or before_guard.get("clean") is not True:
                raise ParallelCanaryBlock(f"source worktree is not Git-semantically clean: {before_guard}")
            output_dir.mkdir(parents=True, exist_ok=True)
            clone_root.mkdir(parents=True, exist_ok=True)
            serial = self._run_mode("serial", jobs, source_commit, output_dir, clone_root, timeout_seconds, max_live=1)
            if serial.get("status") != "PASS":
                raise ParallelCanaryBlock(f"serial canary BLOCK: {serial.get('block_reason')}")
            parallel = self._run_mode("parallel", jobs, source_commit, output_dir, clone_root, timeout_seconds, max_live=2)
            if parallel.get("status") != "PASS":
                raise ParallelCanaryBlock(f"parallel canary BLOCK: {parallel.get('block_reason')}")

            serial_outcomes = {r["nodeid"]: r["terminal_outcome"] for r in serial["jobs"]}
            parallel_outcomes = {r["nodeid"]: r["terminal_outcome"] for r in parallel["jobs"]}
            outcome_parity = serial_outcomes == parallel_outcomes and all(v == "PASS" for v in serial_outcomes.values())
            artifact_parity = self._artifact_shape(serial) == self._artifact_shape(parallel)
            after_guard = _git_semantic_clean_guard(self.root, expected_commit=source_commit)
            source_clean = bool(after_guard and after_guard.get("clean") is True)
            leakage = any(bool(item.get("secret_leakage")) for item in serial.get("jobs") or []) or any(bool(item.get("secret_leakage")) for item in parallel.get("jobs") or [])
            serial_wall = float(serial["wall_seconds"])
            parallel_wall = float(parallel["wall_seconds"])
            speedup = ((serial_wall - parallel_wall) / serial_wall * 100.0) if serial_wall > 0 else 0.0
            conflict_violations = int(serial.get("conflict_violations", 0)) + int(parallel.get("conflict_violations", 0))
            safety_pass = outcome_parity and artifact_parity and source_clean and not leakage and conflict_violations == 0
            performance_pass = speedup > 0.0
            status = "PASS" if safety_pass and performance_pass else "BLOCK"
            decision = "GO-E" if status == "PASS" else "BLOCK"
            report = {
                "schema_id": REPORT_SCHEMA_ID,
                "version": self.version,
                "status": status,
                "decision": decision,
                "source_commit": source_commit,
                "manifest_sha256": manifest_sha,
                "full_regression_runs": 0,
                "max_workers": 2,
                "jobs_total": 2,
                "serial": serial,
                "parallel": parallel,
                "outcome_parity": outcome_parity,
                "runtime_artifact_shape_parity": artifact_parity,
                "source_clean": source_clean,
                "source_guard_before": before_guard,
                "source_guard_after": after_guard,
                "conflict_violations": conflict_violations,
                "secret_leakage": leakage,
                "incremental_parallel_speedup_percent": round(speedup, 6),
                "wall_clock_decomposition": {
                    "serial_wall_seconds": round(serial_wall, 6),
                    "parallel_wall_seconds": round(parallel_wall, 6),
                    "incremental_parallel_seconds_saved": round(serial_wall - parallel_wall, 6),
                    "coordinator_total_seconds": round(time.monotonic() - started, 6),
                    "comparison_basis": "same two-nodeid canary on D code; excludes v2.3-A de-dup attribution",
                },
                "safety_pass": safety_pass,
                "performance_pass": performance_pass,
                "frx_v2_3_e_authorized": status == "PASS",
                "validation": validation,
                "risk_limits": {
                    "generic_scheduler": False,
                    "thread_pool": False,
                    "xdist": False,
                    "shell": False,
                    "full_regression": False,
                    "browser": False,
                    "api_ui": False,
                },
            }
            if status != "PASS":
                report["block_reason"] = self._why_blocked(report)
            self._json_write(output_dir / "parallel_canary_report.json", report)
            return report
        except Exception as exc:
            manifest_sha = "0" * 64
            try:
                manifest_sha = self._sha256_bytes(self.manifest_path.read_bytes())
            except OSError:
                pass
            report = self._block_report(str(exc), manifest_sha256=manifest_sha, source_commit=self._source_commit())
            output_dir.mkdir(parents=True, exist_ok=True)
            self._json_write(output_dir / "parallel_canary_report.json", report)
            return report

    def _run_mode(
        self,
        mode: str,
        jobs: list[CanaryJob],
        source_commit: str,
        output_dir: Path,
        clone_root: Path,
        timeout_seconds: int,
        *,
        max_live: int,
    ) -> dict[str, Any]:
        mode_dir = output_dir / mode
        receipt_path = mode_dir / "mode_receipt.json"
        if receipt_path.is_file():
            existing = self._load_json(receipt_path)
            if existing.get("status") == "PASS" and existing.get("source_commit") == source_commit and existing.get("jobs_total") == 2:
                existing["reused_terminal_receipt"] = True
                return existing
        if mode_dir.exists() and any(mode_dir.iterdir()):
            raise ParallelCanaryBlock(f"non-terminal surviving state exists for {mode}; use a new output_dir rather than overwriting evidence")
        mode_dir.mkdir(parents=True, exist_ok=True)
        locks = ResourceLockTable()
        queue = list(jobs)
        active: list[ActiveJob] = []
        finished: list[dict[str, Any]] = []
        mode_started = time.monotonic()
        max_observed = 0
        conflict_violations = 0

        while queue or active:
            while queue and len(active) < max_live:
                job = queue[0]
                if not locks.acquire(job.job_id, job.resource_lock_keys):
                    conflict_violations += 1
                    raise ParallelCanaryBlock(f"resource lock conflict blocked {job.job_id}")
                queue.pop(0)
                active.append(self._launch_job(mode, job, source_commit, mode_dir, clone_root, locks))
                max_observed = max(max_observed, len(active))
                if mode == "serial":
                    break

            progressed = False
            for item in list(active):
                if not item.terminal_receipt_seen and self._terminal_receipt(item.outcomes_path, item.job.nodeid) is not None:
                    item.terminal_receipt_seen = True
                    item.terminal_receipt_seen_at = time.monotonic()
                return_code = item.process.poll()
                elapsed = time.monotonic() - item.launched_at
                if return_code is None and elapsed > timeout_seconds:
                    self._kill_process_tree(item.process)
                    return_code = item.process.wait(timeout=10)
                    item.log_handle.close()
                    locks.release(item.job.job_id, item.lock_keys)
                    raise ParallelCanaryBlock(f"watchdog timeout after {timeout_seconds}s for {item.job.nodeid}; process tree terminated")
                if return_code is None:
                    continue
                item.log_handle.close()
                locks.release(item.job.job_id, item.lock_keys)
                record = self._finalize_job(item, return_code, source_commit)
                finished.append(record)
                active.remove(item)
                progressed = True
            if not progressed and active:
                time.sleep(0.05)

        mode_wall = time.monotonic() - mode_started
        by_node = {item["nodeid"]: item for item in finished}
        ordered = [by_node[j.nodeid] for j in jobs]
        pass_mode = (
            len(ordered) == len(jobs)
            and all(item["status"] == "PASS" and item["terminal_outcome"] == "PASS" and item["source_clean_after"] for item in ordered)
            and max_observed <= max_live
            and conflict_violations == 0
        )
        receipt = {
            "schema_id": "devpilot.testing.parallel_canary_mode_receipt.v1",
            "status": "PASS" if pass_mode else "BLOCK",
            "mode": mode,
            "source_commit": source_commit,
            "jobs_total": len(ordered),
            "max_workers_allowed": max_live,
            "max_workers_observed": max_observed,
            "wall_seconds": round(mode_wall, 6),
            "jobs": ordered,
            "lock_trace": locks.trace,
            "conflict_violations": conflict_violations,
            "full_regression_runs": 0,
            "reused_terminal_receipt": False,
        }
        if not pass_mode:
            receipt["block_reason"] = "one or more atomic jobs failed lifecycle/outcome/source checks"
        self._json_write(receipt_path, receipt)
        return receipt

    def _launch_job(
        self,
        mode: str,
        job: CanaryJob,
        source_commit: str,
        mode_dir: Path,
        clone_root: Path,
        locks: ResourceLockTable,
    ) -> ActiveJob:
        job_root = mode_dir / job.job_id
        namespace_root = job_root / "namespace"
        log_path = job_root / "pytest.log"
        junit_path = job_root / "junit.xml"
        outcomes_path = job_root / "outcomes.jsonl"
        clone_path = clone_root / mode / job.job_id
        for path in (job_root, namespace_root, clone_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        if clone_path.exists():
            raise ParallelCanaryBlock(f"worker clone already exists and will not be overwritten: {clone_path}")
        clone_started = time.monotonic()
        clone = subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", str(self.root), str(clone_path)],
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
            check=False,
        )
        if clone.returncode != 0:
            locks.release(job.job_id, job.resource_lock_keys)
            raise ParallelCanaryBlock(f"fresh worker clone failed for {job.job_id}: {clone.stderr.strip()[:500]}")
        checkout = self._run_git(clone_path, "checkout", "--quiet", source_commit)
        if checkout.returncode != 0:
            locks.release(job.job_id, job.resource_lock_keys)
            raise ParallelCanaryBlock(f"worker clone checkout failed for {job.job_id}: {checkout.stderr.strip()[:500]}")
        clone_guard = _git_semantic_clean_guard(clone_path, expected_commit=source_commit)
        if not clone_guard or clone_guard.get("clean") is not True:
            locks.release(job.job_id, job.resource_lock_keys)
            raise ParallelCanaryBlock(f"worker clone is not source-clean before pytest: {job.job_id}")

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["DEVPILOT_FULL_SESSION_OUTCOMES"] = str(outcomes_path)
        env["TMP"] = str(namespace_root / "tmp")
        env["TEMP"] = str(namespace_root / "tmp")
        env["TMPDIR"] = str(namespace_root / "tmp")
        Path(env["TMP"]).mkdir(parents=True, exist_ok=True)
        clone_src = str(clone_path / "src")
        existing_pp = env.get("PYTHONPATH")
        env["PYTHONPATH"] = clone_src if not existing_pp else os.pathsep.join((clone_src, existing_pp))
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "-p",
            "devpilot_core.testing.full_regression_plugin",
            job.nodeid,
            f"--junitxml={junit_path}",
        ]
        log_handle = log_path.open("w", encoding="utf-8", newline="\n")
        popen_kwargs: dict[str, Any] = {
            "cwd": str(clone_path),
            "env": env,
            "stdout": log_handle,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.DEVNULL,
            "shell": False,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["start_new_session"] = True
        launched_at = time.monotonic()
        process = subprocess.Popen(command, **popen_kwargs)
        metadata = {
            "mode": mode,
            "job_id": job.job_id,
            "nodeid": job.nodeid,
            "contract_id": job.contract_id,
            "source_commit": source_commit,
            "pid": process.pid,
            "clone_seconds": round(launched_at - clone_started, 6),
            "command_shape": [sys.executable, "-m", "pytest", "<atomic-nodeid>", "--junitxml=<worker-path>"],
            "shell": False,
        }
        self._json_write(job_root / "launch.json", metadata)
        return ActiveJob(
            mode=mode,
            job=job,
            clone_root=clone_path,
            namespace_root=namespace_root,
            log_path=log_path,
            junit_path=junit_path,
            outcomes_path=outcomes_path,
            process=process,
            log_handle=log_handle,
            launched_at=launched_at,
            lock_keys=job.resource_lock_keys,
        )

    @staticmethod
    def _terminal_receipt(path: Path, nodeid: str) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        terminal: dict[str, Any] | None = None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("nodeid") == nodeid and payload.get("outcome") in TERMINAL_OUTCOMES:
                terminal = payload
        return terminal

    def _finalize_job(self, item: ActiveJob, return_code: int, source_commit: str) -> dict[str, Any]:
        terminal = self._terminal_receipt(item.outcomes_path, item.job.nodeid)
        clone_guard = _git_semantic_clean_guard(item.clone_root, expected_commit=source_commit)
        source_clean = bool(clone_guard and clone_guard.get("clean") is True)
        junit_exists = item.junit_path.is_file() and item.junit_path.stat().st_size > 0
        log_exists = item.log_path.is_file()
        elapsed = time.monotonic() - item.launched_at
        outcome = str((terminal or {}).get("outcome") or "MISSING")
        log_text = item.log_path.read_text(encoding="utf-8", errors="replace") if item.log_path.is_file() else ""
        secret_leakage = self.secret_guard.redact(log_text).changed
        status = "PASS" if return_code == 0 and outcome == "PASS" and junit_exists and source_clean and not secret_leakage else "BLOCK"
        return {
            "status": status,
            "job_id": item.job.job_id,
            "nodeid": item.job.nodeid,
            "contract_id": item.job.contract_id,
            "pid": item.process.pid,
            "return_code": return_code,
            "terminal_outcome": outcome,
            "terminal_receipt_seen_before_parent_exit": item.terminal_receipt_seen,
            "wall_seconds": round(elapsed, 6),
            "junit_exists": junit_exists,
            "outcomes_exists": item.outcomes_path.is_file(),
            "log_exists": log_exists,
            "source_clean_after": source_clean,
            "source_guard_after": clone_guard,
            "secret_leakage": secret_leakage,
            "runtime_estimate_seconds": item.job.runtime_estimate_seconds,
        }

    @staticmethod
    def _kill_process_tree(process: subprocess.Popen[Any]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                    check=False,
                )
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass

    @staticmethod
    def _artifact_shape(mode: dict[str, Any]) -> dict[str, tuple[bool, bool, bool]]:
        return {
            str(item["nodeid"]): (
                bool(item.get("junit_exists")),
                bool(item.get("outcomes_exists")),
                bool(item.get("log_exists")),
            )
            for item in mode.get("jobs") or []
        }

    @staticmethod
    def _why_blocked(report: dict[str, Any]) -> str:
        failures = []
        if not report.get("outcome_parity"):
            failures.append("outcome parity failed")
        if not report.get("runtime_artifact_shape_parity"):
            failures.append("runtime artifact shape parity failed")
        if not report.get("source_clean"):
            failures.append("source drift detected")
        if report.get("secret_leakage"):
            failures.append("secret-like content detected")
        if int(report.get("conflict_violations") or 0):
            failures.append("resource conflict violation detected")
        if float(report.get("incremental_parallel_speedup_percent") or 0.0) <= 0.0:
            failures.append("parallel overhead eliminated the canary benefit")
        return "; ".join(failures) or "bounded canary acceptance criteria not met"

    def _block_report(self, reason: str, *, manifest_sha256: str, source_commit: str | None = None) -> dict[str, Any]:
        return {
            "schema_id": REPORT_SCHEMA_ID,
            "version": self.version,
            "status": "BLOCK",
            "decision": "BLOCK",
            "source_commit": source_commit,
            "manifest_sha256": manifest_sha256,
            "full_regression_runs": 0,
            "max_workers": 0,
            "jobs_total": 2,
            "serial": {},
            "parallel": {},
            "outcome_parity": False,
            "source_clean": False,
            "conflict_violations": 0,
            "secret_leakage": False,
            "incremental_parallel_speedup_percent": None,
            "frx_v2_3_e_authorized": False,
            "block_reason": reason,
        }
