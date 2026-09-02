from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.testing.temporal_shard_planner import TemporalShardPlanner

FULL_REGRESSION_VERSION = "2.1"
DEFAULT_RUNTIME_ROOT = Path("outputs/testing/full_regression")
DEFAULT_SHARD_SIZE = 50
DEFAULT_SHARD_TIMEOUT_SECONDS = 1200
DEFAULT_COLLECTION_TIMEOUT_SECONDS = 300

_EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "outputs", ".pytest_cache", "__pycache__", "node_modules", ".mypy_cache", ".ruff_cache"
}
_EXCLUDED_FILES = {".devpilot/devpilot.db", ".devpilot/auth/auth.db"}
_TERMINAL_COMPLETE = {"PASS", "FAIL", "ERROR", "SKIP_APPROVED"}


class TerminalOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP_APPROVED = "SKIP_APPROVED"
    INFRA_ABORT = "INFRA_ABORT"
    UNEXECUTED = "UNEXECUTED"


@dataclass(frozen=True)
class CollectedNode:
    nodeid: str
    ordinal: int


@dataclass(frozen=True)
class ShardDefinition:
    shard_id: str
    ordinal: int
    nodeids: tuple[str, ...]
    nodeids_sha256: str
    timeout_seconds: int


@dataclass(frozen=True)
class FullRegressionSession:
    session_id: str
    version: str
    created_at: str
    source_fingerprint: str
    source_descriptor: dict[str, Any]
    environment_fingerprint: str
    environment_descriptor: dict[str, Any]
    collection_sha256: str
    collection_total: int
    targets: tuple[str, ...]
    collection_duration_seconds: float = 0.0


@dataclass(frozen=True)
class ShardReceipt:
    session_id: str
    shard_id: str
    attempt: int
    mode: str
    started_at: str
    ended_at: str
    duration_seconds: float
    source_fingerprint_before: str
    source_fingerprint_after: str
    environment_fingerprint: str
    collection_sha256: str
    shard_plan_sha256: str
    planned_nodeids: tuple[str, ...]
    observed_nodeids: tuple[str, ...]
    outcomes: dict[str, str]
    returncode: int | None
    timed_out: bool
    infra_abort: bool
    source_mutation_detected: bool
    junit_path: str | None
    junit_sha256: str | None
    outcome_log_path: str | None
    outcome_log_sha256: str | None
    log_path: str | None = None
    log_sha256: str | None = None
    lifecycle_started_at: str | None = None
    lifecycle_ended_at: str | None = None
    lifecycle_duration_seconds: float | None = None
    source_guard_before_seconds: float | None = None
    source_guard_after_seconds: float | None = None
    orchestrator_overhead_seconds: float | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()




def _normalize_nodeid_path_only(nodeid: str) -> str:
    """Normalize only the filesystem path component of a pytest nodeid.

    Parameter ids may legitimately contain pytest escape sequences such as ``\\t``
    and ``\\x7f``. Replacing backslashes across the complete nodeid corrupts
    those ids and makes the collected nodeid impossible to re-select.
    """
    path_part, sep, suffix = str(nodeid).partition("::")
    normalized_path = path_part.replace("\\", "/")
    return normalized_path + (sep + suffix if sep else "")

def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _is_excluded(relative: Path) -> bool:
    parts = relative.parts
    if any(part in _EXCLUDED_DIR_NAMES for part in parts):
        return True
    normalized = str(relative).replace("\\", "/")
    if normalized in _EXCLUDED_FILES:
        return True
    # SQLite runtime sidecars are ephemeral state and must never invalidate a
    # sealed source fingerprint. This covers auth/devpilot DB WAL/SHM/journal
    # files created while API/UI are running during the single logical full.
    if any(normalized == f"{base}{suffix}" for base in _EXCLUDED_FILES for suffix in ("-wal", "-shm", "-journal", ".wal", ".shm", ".journal")):
        return True
    if normalized.endswith((".pyc", ".pyo")):
        return True
    return False


def _git_run(root: Path, args: Sequence[str], *, timeout: int = 15) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=timeout, shell=False, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_semantic_blob_hash(root: Path, relative: str) -> str | None:
    path = root / relative
    if not path.is_file():
        return None
    completed = _git_run(root, ["hash-object", f"--path={relative}", relative])
    if completed is None or completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value if len(value) == 40 else None


def _git_semantic_source_descriptor(root: Path) -> dict[str, Any] | None:
    if not (root / ".git").exists():
        return None
    head = _git_run(root, ["rev-parse", "HEAD"])
    tracked = _git_run(root, ["ls-files", "-z"])
    untracked = _git_run(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    if head is None or tracked is None or untracked is None or head.returncode != 0 or tracked.returncode != 0 or untracked.returncode != 0:
        return None
    tracked_paths = [item for item in tracked.stdout.split("\0") if item]
    untracked_paths = [item for item in untracked.stdout.split("\0") if item]
    tracked_set = set(tracked_paths)
    digest = hashlib.sha256()
    files_total = bytes_total = tracked_total = untracked_total = 0
    for relative in sorted([*tracked_paths, *untracked_paths]):
        if _is_excluded(Path(relative)):
            continue
        blob = _git_semantic_blob_hash(root, relative) or "MISSING"
        digest.update(relative.replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob.encode("ascii"))
        digest.update(b"\n")
        files_total += 1
        file_path = root / relative
        if file_path.is_file():
            try:
                bytes_total += file_path.stat().st_size
            except OSError:
                pass
        if relative in tracked_set:
            tracked_total += 1
        else:
            untracked_total += 1
    return {
        "git_commit": head.stdout.strip() or None,
        "content_sha256": digest.hexdigest(),
        "files_total": files_total,
        "bytes_total": bytes_total,
        "tracked_files_total": tracked_total,
        "untracked_files_total": untracked_total,
        "fingerprint_mode": "git-semantic-working-tree-v1",
        "excluded_runtime_dirs": sorted(_EXCLUDED_DIR_NAMES),
    }


def _git_semantic_clean_guard(root: Path, *, expected_commit: str | None = None) -> dict[str, Any] | None:
    """Cheap Git-semantic mutation guard for a worktree sealed from a clean commit.

    Unlike the strong source descriptor, this performs a bounded number of Git
    commands and never launches ``git hash-object`` once per file.  Git itself
    applies attributes/eol normalization, so this intentionally compares Git
    content semantics rather than CRLF/LF physical bytes.
    """
    root = root.resolve()
    if not (root / ".git").exists():
        return None
    head = _git_run(root, ["rev-parse", "HEAD"])
    unstaged = _git_run(root, ["diff", "--name-only", "-z", "--no-ext-diff"])
    staged = _git_run(root, ["diff", "--cached", "--name-only", "-z", "--no-ext-diff"])
    untracked = _git_run(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    completed = (head, unstaged, staged, untracked)
    if any(item is None or item.returncode != 0 for item in completed):
        return None

    def visible_paths(stdout: str) -> list[str]:
        return sorted(
            path for path in (item for item in stdout.split("\0") if item)
            if not _is_excluded(Path(path))
        )

    current_commit = head.stdout.strip() or None
    unstaged_paths = visible_paths(unstaged.stdout)
    staged_paths = visible_paths(staged.stdout)
    untracked_paths = visible_paths(untracked.stdout)
    commit_matches = expected_commit is None or current_commit == expected_commit
    clean = commit_matches and not unstaged_paths and not staged_paths and not untracked_paths
    return {
        "available": True,
        "clean": clean,
        "git_commit": current_commit,
        "expected_commit": expected_commit,
        "commit_matches": commit_matches,
        "unstaged_total": len(unstaged_paths),
        "staged_total": len(staged_paths),
        "untracked_total": len(untracked_paths),
        "changed_paths": sorted(set(unstaged_paths + staged_paths + untracked_paths)),
        "fingerprint_mode": "git-semantic-clean-guard-v1",
    }


def _environment_runtime_guard(expected: dict[str, Any]) -> bool:
    try:
        pytest_version = importlib.metadata.version("pytest")
    except importlib.metadata.PackageNotFoundError:
        pytest_version = "not-installed"
    current = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable_name": Path(sys.executable).name,
        "pytest": pytest_version,
    }
    return all(current.get(key) == expected.get(key) for key in current)


def _source_descriptor(root: Path) -> dict[str, Any]:
    root = root.resolve()
    semantic = _git_semantic_source_descriptor(root)
    if semantic is not None:
        return semantic
    git_commit: str | None = None
    if (root / ".git").exists():
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                check=False,
            )
            if completed.returncode == 0:
                git_commit = completed.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            git_commit = None

    digest = hashlib.sha256()
    files_total = 0
    bytes_total = 0
    for path in sorted(root.rglob("*"), key=lambda item: str(item.relative_to(root)).replace("\\", "/")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _is_excluded(relative):
            continue
        normalized = str(relative).replace("\\", "/")
        data = path.read_bytes()
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
        digest.update(b"\n")
        files_total += 1
        bytes_total += len(data)
    return {
        "git_commit": git_commit,
        "content_sha256": digest.hexdigest(),
        "files_total": files_total,
        "bytes_total": bytes_total,
        "excluded_runtime_dirs": sorted(_EXCLUDED_DIR_NAMES),
    }


def _environment_descriptor(root: Path) -> dict[str, Any]:
    tracked = {}
    for name in ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "uv.lock", "poetry.lock"):
        path = root / name
        if path.exists() and path.is_file():
            tracked[name] = _git_semantic_blob_hash(root, name) or _sha256_file(path)
    try:
        pytest_version = importlib.metadata.version("pytest")
    except importlib.metadata.PackageNotFoundError:
        pytest_version = "not-installed"
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable_name": Path(sys.executable).name,
        "pytest": pytest_version,
        "config_hashes": tracked,
    }


def _fingerprint(payload: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_bytes(payload))


def _immutable_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            raise ValueError(f"immutable artifact mismatch: {path}")
        return
    path.write_text(content, encoding="utf-8", newline="\n")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _result(command: str, *, ok: bool, exit_code: ExitCode, message: str, summary: dict[str, Any], findings: list[Finding] | None = None, extra: dict[str, Any] | None = None) -> CommandResult:
    data: dict[str, Any] = {
        "summary": summary,
        "network_used": False,
        "external_api_used": False,
        "source_mutations_performed": False,
        "preliminary": True,
    }
    if extra:
        data.update(extra)
    return CommandResult(command=command, ok=ok, exit_code=exit_code, message=message, data=data, findings=findings or [])


class FullRegressionSessionManager:
    """Resumable, completion-first pytest full-regression session manager.

    v2.1 intentionally remains sequential. Runtime receipts live under outputs/
    and are never source authority. Source and environment fingerprints are
    checked before any execution and source content is checked after every
    shard. `run` and `resume` require explicit execute=True from the CLI.
    """

    def __init__(self, root: Path, *, runtime_root: Path | None = None) -> None:
        self.root = Path(root).resolve()
        configured = runtime_root or DEFAULT_RUNTIME_ROOT
        self.runtime_root = configured if configured.is_absolute() else (self.root / configured)

    def collect(self, *, session_id: str | None = None, targets: Sequence[str] = (), timeout_seconds: int = DEFAULT_COLLECTION_TIMEOUT_SECONDS) -> CommandResult:
        if timeout_seconds <= 0 or timeout_seconds > 1800:
            return self._block("tests full-session collect", "FRX2_COLLECTION_TIMEOUT_INVALID", "Collection timeout must be between 1 and 1800 seconds.")
        normalized_targets = tuple(str(item).replace("\\", "/") for item in targets if str(item).strip())
        resolved_session_id = session_id or f"frx2-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        if not self._valid_session_id(resolved_session_id):
            return self._block("tests full-session collect", "FRX2_SESSION_ID_INVALID", "Session id contains unsupported characters.")
        session_dir = self._session_dir(resolved_session_id)
        if session_dir.exists():
            return self._block("tests full-session collect", "FRX2_SESSION_EXISTS", "Session id already exists; immutable sessions cannot be overwritten.")
        source = _source_descriptor(self.root)
        environment = _environment_descriptor(self.root)
        source_fp = _fingerprint(source)
        env_fp = _fingerprint(environment)
        collection_capture = self.runtime_root / ".collect" / f"{resolved_session_id}.json"
        collection_capture.parent.mkdir(parents=True, exist_ok=True)
        if collection_capture.exists():
            collection_capture.unlink()
        args = [sys.executable, "-m", "pytest", "--collect-only", "-q", "--disable-warnings", "-p", "devpilot_core.testing.full_regression_collect_plugin", *normalized_targets]
        collection_started = time.monotonic()
        completed, timed_out = self._run_subprocess(args, timeout_seconds=timeout_seconds, extra_env={"DEVPILOT_FULL_SESSION_COLLECTION": str(collection_capture)})
        collection_duration_seconds = round(time.monotonic() - collection_started, 6)
        if timed_out:
            return self._block("tests full-session collect", "FRX2_COLLECTION_TIMEOUT", "Pytest collection timed out; no session was created.")
        if completed is None or completed.returncode != 0:
            return _result(
                "tests full-session collect",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Pytest collection failed; no session was created.",
                summary={"collected": False, "returncode": None if completed is None else completed.returncode},
                findings=[Finding(id="FRX2_COLLECTION_FAILED", message=(completed.stderr[-4000:] if completed else "subprocess failed to start"), severity=Severity.BLOCK)],
            )
        nodeids: list[str] = []
        if collection_capture.exists():
            try:
                captured = json.loads(collection_capture.read_text(encoding="utf-8"))
                if isinstance(captured, list):
                    nodeids = [_normalize_nodeid_path_only(str(item)) for item in captured if str(item).strip()]
            except (OSError, json.JSONDecodeError):
                nodeids = []
            finally:
                try:
                    collection_capture.unlink()
                except OSError:
                    pass
        if not nodeids:
            nodeids = self._parse_collection(completed.stdout)
        if not nodeids:
            return self._block("tests full-session collect", "FRX2_COLLECTION_EMPTY", "Collection produced zero test nodeids.")
        if len(nodeids) != len(set(nodeids)):
            return self._block("tests full-session collect", "FRX2_COLLECTION_DUPLICATE_NODEIDS", "Collection contains duplicate nodeids.")
        collection_payload = {
            "schema_id": "devpilot.testing.full_regression_collection.v2_1",
            "version": FULL_REGRESSION_VERSION,
            "nodes": [asdict(CollectedNode(nodeid=nodeid, ordinal=index)) for index, nodeid in enumerate(nodeids, start=1)],
            "nodeids_total": len(nodeids),
        }
        collection_sha = _sha256_bytes(_canonical_bytes(collection_payload))
        session = FullRegressionSession(
            session_id=resolved_session_id,
            version=FULL_REGRESSION_VERSION,
            created_at=_utc_now(),
            source_fingerprint=source_fp,
            source_descriptor=source,
            environment_fingerprint=env_fp,
            environment_descriptor=environment,
            collection_sha256=collection_sha,
            collection_total=len(nodeids),
            targets=normalized_targets,
            collection_duration_seconds=collection_duration_seconds,
        )
        session_payload = {"schema_id": "devpilot.testing.full_regression_session.v2_1", **asdict(session)}
        try:
            _immutable_write(session_dir / "collection.json", collection_payload)
            _immutable_write(session_dir / "session.json", session_payload)
        except ValueError as exc:
            return self._block("tests full-session collect", "FRX2_IMMUTABILITY_VIOLATION", str(exc))
        return _result(
            "tests full-session collect",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Full regression collection sealed successfully.",
            summary={
                "session_id": resolved_session_id,
                "nodeids_total": len(nodeids),
                "collection_sha256": collection_sha,
                "source_fingerprint": source_fp,
                "environment_fingerprint": env_fp,
                "tests_executed": False,
                "collection_duration_seconds": collection_duration_seconds,
            },
            findings=[Finding(id="FRX2_COLLECTION_SEALED", message="Collection is unique, deterministic for this invocation and sealed under the session.", severity=Severity.INFO)],
        )

    def plan(self, *, session_id: str, shard_size: int = DEFAULT_SHARD_SIZE, shard_timeout_seconds: int = DEFAULT_SHARD_TIMEOUT_SECONDS) -> CommandResult:
        config_path = self.root / ".devpilot" / "testing" / "temporal_planner_config.json"
        if config_path.is_file():
            try:
                temporal_config = json.loads(config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return self._block("tests full-session plan", "FRX2_TEMPORAL_DEFAULT_CONFIG_INVALID", f"Temporal planner config is invalid: {exc}")
            if bool(temporal_config.get("scheduler_enabled")):
                if int(temporal_config.get("parallel_workers", 1)) != 1:
                    return self._block("tests full-session plan", "FRX2_TEMPORAL_PARALLEL_WORKERS_FORBIDDEN", "FRX-v2.2 temporal scheduling is sequential and requires parallel_workers=1.")
                registry_environment = str(temporal_config.get("registry_environment_fingerprint") or "").strip()
                if not registry_environment:
                    return self._block("tests full-session plan", "FRX2_TEMPORAL_REGISTRY_ENVIRONMENT_REQUIRED", "Enabled temporal scheduling requires registry_environment_fingerprint.")
                return self.plan_temporal(
                    session_id=session_id,
                    registry_environment_fingerprint=registry_environment,
                    target_shard_seconds=float(temporal_config.get("target_shard_seconds", 300.0)),
                    max_nodeids=int(temporal_config.get("max_nodeids", 50)),
                    max_command_chars=int(temporal_config.get("max_command_chars", 7000)),
                    shard_timeout_seconds=shard_timeout_seconds,
                )
        loaded = self._load_session(session_id, command="tests full-session plan")
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection = loaded
        integrity = self._validate_identity(session, collection, require_environment=True)
        if integrity is not None:
            return integrity
        if shard_size <= 0 or shard_size > 500:
            return self._block("tests full-session plan", "FRX2_SHARD_SIZE_INVALID", "Shard size must be between 1 and 500 nodeids.")
        if shard_timeout_seconds <= 0 or shard_timeout_seconds > 3600:
            return self._block("tests full-session plan", "FRX2_SHARD_TIMEOUT_INVALID", "Shard timeout must be between 1 and 3600 seconds.")
        nodeids = [item["nodeid"] for item in collection["nodes"]]
        shards: list[dict[str, Any]] = []
        for index in range(0, len(nodeids), shard_size):
            chunk = tuple(nodeids[index : index + shard_size])
            definition = ShardDefinition(
                shard_id=f"shard-{len(shards)+1:04d}",
                ordinal=len(shards) + 1,
                nodeids=chunk,
                nodeids_sha256=_sha256_bytes(_canonical_bytes(list(chunk))),
                timeout_seconds=shard_timeout_seconds,
            )
            shards.append({**asdict(definition), "nodeids": list(definition.nodeids)})
        flattened = [nodeid for shard in shards for nodeid in shard["nodeids"]]
        if flattened != nodeids or len(flattened) != len(set(flattened)):
            return self._block("tests full-session plan", "FRX2_PLAN_COVERAGE_INVALID", "Plan does not preserve the collection exactly once.")
        core = {
            "schema_id": "devpilot.testing.full_regression_shard_plan.v2_1",
            "version": FULL_REGRESSION_VERSION,
            "session_id": session_id,
            "collection_sha256": session["collection_sha256"],
            "collection_total": len(nodeids),
            "shard_size": shard_size,
            "shard_timeout_seconds": shard_timeout_seconds,
            "shards": shards,
            "shards_total": len(shards),
        }
        plan_sha = _sha256_bytes(_canonical_bytes(core))
        payload = {**core, "shard_plan_sha256": plan_sha}
        try:
            _immutable_write(self._session_dir(session_id) / "plan.json", payload)
        except ValueError as exc:
            return self._block("tests full-session plan", "FRX2_PLAN_IMMUTABILITY_VIOLATION", str(exc))
        return _result(
            "tests full-session plan",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Sequential immutable shard plan sealed successfully.",
            summary={"session_id": session_id, "shards_total": len(shards), "nodeids_total": len(nodeids), "shard_plan_sha256": plan_sha, "tests_executed": False},
            findings=[Finding(id="FRX2_PLAN_SEALED", message="Every collected nodeid appears exactly once in the immutable sequential plan.", severity=Severity.INFO)],
        )

    def plan_temporal(
        self,
        *,
        session_id: str,
        registry_environment_fingerprint: str,
        target_shard_seconds: float = 300.0,
        max_nodeids: int = 50,
        max_command_chars: int = 7000,
        shard_timeout_seconds: int = DEFAULT_SHARD_TIMEOUT_SECONDS,
    ) -> CommandResult:
        command = "tests full-session temporal-plan"
        loaded = self._load_session(session_id, command=command)
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection = loaded
        integrity = self._validate_identity(session, collection, require_environment=True)
        if integrity is not None:
            return integrity
        if shard_timeout_seconds <= 0 or shard_timeout_seconds > 3600:
            return self._block(command, "FRX2_TEMPORAL_TIMEOUT_INVALID", "Shard timeout must be between 1 and 3600 seconds.")
        nodeids = [item["nodeid"] for item in collection["nodes"]]
        planner = TemporalShardPlanner(self.root, target_shard_seconds=target_shard_seconds, max_nodeids=max_nodeids, max_command_chars=max_command_chars)
        try:
            temporal = planner.plan(nodeids, environment_fingerprint=registry_environment_fingerprint, collection_sha256=session["collection_sha256"], expected_collection_sha256=session["collection_sha256"])
        except Exception as exc:
            return self._block(command, "FRX2_TEMPORAL_PLAN_FAILED", str(exc))
        shards: list[dict[str, Any]] = []
        for shard in temporal["shards"]:
            estimate = float(shard.get("estimated_seconds") or 0.0)
            adaptive_timeout = max(600, min(shard_timeout_seconds, int(estimate * 2 + 120) if estimate > 0 else shard_timeout_seconds))
            shards.append({
                "shard_id": shard["shard_id"],
                "ordinal": shard["ordinal"],
                "nodeids": list(shard["nodeids"]),
                "nodeids_sha256": shard["nodeids_sha256"],
                "timeout_seconds": adaptive_timeout,
                "estimated_seconds": estimate,
                "known_count": int(shard.get("known_count") or 0),
                "unknown_count": int(shard.get("unknown_count") or 0),
                "confidence_counts": dict(shard.get("confidence_counts") or {}),
                "command_chars": int(shard.get("command_chars") or 0),
                "slow_singleton": bool(shard.get("slow_singleton")),
            })
        flattened = [nodeid for shard in shards for nodeid in shard["nodeids"]]
        if len(flattened) != len(nodeids) or set(flattened) != set(nodeids) or len(flattened) != len(set(flattened)):
            return self._block(command, "FRX2_TEMPORAL_PLAN_COVERAGE_INVALID", "Temporal plan does not preserve the collection exactly once.")
        core = {
            "schema_id": "devpilot.testing.full_regression_temporal_shard_plan.v2_2",
            "version": "2.2",
            "session_id": session_id,
            "collection_sha256": session["collection_sha256"],
            "collection_total": len(nodeids),
            "planner": "deterministic-lpt-sequential",
            "mode": "windows-one-full-benchmark",
            "scheduler_enabled_for_session": True,
            "parallel_workers": 1,
            "registry_environment_fingerprint": registry_environment_fingerprint,
            "target_shard_seconds": float(target_shard_seconds),
            "max_nodeids": int(max_nodeids),
            "max_command_chars": int(max_command_chars),
            "shard_timeout_seconds": int(shard_timeout_seconds),
            "registry_provenance": temporal.get("registry_provenance"),
            "known_nodeids": temporal.get("known_nodeids"),
            "unknown_nodeids": temporal.get("unknown_nodeids"),
            "slow_singletons": temporal.get("slow_singletons"),
            "shards": shards,
            "shards_total": len(shards),
        }
        plan_sha = _sha256_bytes(_canonical_bytes(core))
        payload = {**core, "shard_plan_sha256": plan_sha}
        try:
            _immutable_write(self._session_dir(session_id) / "plan.json", payload)
        except ValueError as exc:
            return self._block(command, "FRX2_TEMPORAL_PLAN_IMMUTABILITY_VIOLATION", str(exc))
        return _result(command, ok=True, exit_code=ExitCode.PASS, message="Temporal sequential shard plan sealed for the single v2.2 full benchmark.", summary={
            "session_id": session_id, "collection_total": len(nodeids), "shards_total": len(shards), "shard_plan_sha256": plan_sha,
            "parallel_workers": 1, "scheduler_enabled_for_session": True, "tests_executed": False})

    def run(self, *, session_id: str, execute: bool, max_shards: int | None = None, timeout_seconds: int | None = None, mode: str = "run") -> CommandResult:
        command = f"tests full-session {mode}"
        if not execute:
            status = self.status(session_id=session_id)
            if status.exit_code == ExitCode.ERROR:
                return status
            return _result(
                command,
                ok=True,
                exit_code=ExitCode.PASS,
                message="Execution preview only. Add --execute to run pending shards.",
                summary={**(status.data.get("summary", {}) if status.data else {}), "execute": False, "tests_executed": False},
                findings=[Finding(id="FRX2_EXECUTION_PREVIEW", message="No tests executed because --execute was not supplied.", severity=Severity.INFO)],
            )
        if max_shards is not None and (max_shards <= 0 or max_shards > 10000):
            return self._block(command, "FRX2_MAX_SHARDS_INVALID", "max_shards must be positive when supplied.")
        loaded = self._load_session_with_plan(session_id, command=command)
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection, plan = loaded
        integrity = self._validate_identity(session, collection, plan=plan, require_environment=True)
        if integrity is not None:
            return integrity
        effective_timeout_override = timeout_seconds
        if effective_timeout_override is not None and (effective_timeout_override <= 0 or effective_timeout_override > 3600):
            return self._block(command, "FRX2_RUN_TIMEOUT_INVALID", "Timeout override must be between 1 and 3600 seconds.")
        state = self._accounting(session_id, collection, plan)
        executed_shards = 0
        new_receipts: list[str] = []
        for shard in plan["shards"]:
            pending = [nodeid for nodeid in shard["nodeids"] if state["outcomes"].get(nodeid, TerminalOutcome.UNEXECUTED.value) not in _TERMINAL_COMPLETE]
            if not pending:
                continue
            if max_shards is not None and executed_shards >= max_shards:
                break
            attempt = self._next_attempt(session_id, shard["shard_id"])
            receipt, runtime_block = self._execute_shard(
                session=session,
                plan=plan,
                shard=shard,
                nodeids=pending,
                attempt=attempt,
                timeout_seconds=effective_timeout_override or int(shard["timeout_seconds"]),
                mode=mode,
            )
            receipt_path = self._receipt_path(session_id, shard["shard_id"], attempt)
            try:
                _immutable_write(receipt_path, {"schema_id": "devpilot.testing.full_regression_shard_receipt.v2_1", **asdict(receipt)})
            except ValueError as exc:
                return self._block(command, "FRX2_RECEIPT_IMMUTABILITY_VIOLATION", str(exc))
            new_receipts.append(_relative(receipt_path, self.root))
            executed_shards += 1
            state = self._accounting(session_id, collection, plan)
            if runtime_block:
                return _result(
                    command,
                    ok=False,
                    exit_code=ExitCode.BLOCK,
                    message="Shard execution stopped on infrastructure or source-integrity block; the logical session remains resumable when fingerprints are unchanged.",
                    summary={**state["summary"], "executed_shards_this_call": executed_shards, "new_receipts": new_receipts, "tests_executed": True},
                    findings=[Finding(id="FRX2_SHARD_INFRA_BLOCK", message=runtime_block, severity=Severity.BLOCK)],
                )
        state = self._accounting(session_id, collection, plan)
        complete = state["summary"]["unexecuted_total"] == 0
        functional_failures = state["summary"]["fail_total"] + state["summary"]["error_total"]
        if complete and functional_failures:
            return _result(
                command,
                ok=False,
                exit_code=ExitCode.FAIL,
                message="All planned nodeids have terminal accounting; functional failures/errors were preserved without fail-fast abort.",
                summary={**state["summary"], "executed_shards_this_call": executed_shards, "new_receipts": new_receipts, "tests_executed": executed_shards > 0},
                findings=[Finding(id="FRX2_COMPLETION_WITH_FUNCTIONAL_FAILURES", message="Completion-first accounting finished with functional failures/errors.", severity=Severity.FAIL)],
            )
        return _result(
            command,
            ok=True,
            exit_code=ExitCode.PASS,
            message="Shard execution completed for the requested bounded scope." if not complete else "All planned nodeids have terminal accounting.",
            summary={**state["summary"], "executed_shards_this_call": executed_shards, "new_receipts": new_receipts, "tests_executed": executed_shards > 0},
            findings=[Finding(id="FRX2_RUN_PROGRESS", message="Logical session progress is persisted in immutable receipts; completed nodeids will not be rerun by resume.", severity=Severity.INFO)],
        )

    def resume(self, *, session_id: str, execute: bool, max_shards: int | None = None, timeout_seconds: int | None = None) -> CommandResult:
        return self.run(session_id=session_id, execute=execute, max_shards=max_shards, timeout_seconds=timeout_seconds, mode="resume")

    def status(self, *, session_id: str) -> CommandResult:
        loaded = self._load_session_with_plan(session_id, command="tests full-session status")
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection, plan = loaded
        integrity = self._validate_sealed_artifacts(session, collection, plan)
        if integrity is not None:
            return integrity
        state = self._accounting(session_id, collection, plan)
        return _result(
            "tests full-session status",
            ok=True,
            exit_code=ExitCode.PASS,
            message="Full regression logical session status computed from immutable receipts.",
            summary=state["summary"],
            findings=[],
            extra={"outcomes": state["outcomes"], "receipts": state["receipts"]},
        )

    def adjudicate(self, *, session_id: str) -> CommandResult:
        command = "tests full-session adjudicate"
        loaded = self._load_session_with_plan(session_id, command=command)
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection, plan = loaded
        integrity = self._validate_identity(session, collection, plan=plan, require_environment=True)
        if integrity is not None:
            return integrity
        state = self._accounting(session_id, collection, plan)
        summary = state["summary"]
        if summary["unexecuted_total"] > 0:
            return _result(
                command,
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Final adjudication blocked because nodeids remain UNEXECUTED.",
                summary=summary,
                findings=[Finding(id="FRX2_ADJUDICATION_INCOMPLETE", message="A final coverage claim requires 100% terminal accounting.", severity=Severity.BLOCK)],
            )
        decision = "PASS"
        exit_code = ExitCode.PASS
        findings: list[Finding] = []
        if summary["fail_total"] or summary["error_total"]:
            decision = "FAIL"
            exit_code = ExitCode.FAIL
            findings.append(Finding(id="FRX2_ADJUDICATION_FUNCTIONAL_FAILURES", message="Coverage is complete but functional failures/errors remain.", severity=Severity.FAIL))
        payload_core = {
            "schema_id": "devpilot.testing.full_regression_adjudication.v2_1",
            "version": FULL_REGRESSION_VERSION,
            "session_id": session_id,
            "decision": decision,
            "collection_sha256": session["collection_sha256"],
            "shard_plan_sha256": plan["shard_plan_sha256"],
            "source_fingerprint": session["source_fingerprint"],
            "environment_fingerprint": session["environment_fingerprint"],
            "terminal_accounting": summary,
            "coverage_complete": True,
            "receipts": state["receipts"],
        }
        payload = {**payload_core, "adjudication_sha256": _sha256_bytes(_canonical_bytes(payload_core))}
        try:
            _immutable_write(self._session_dir(session_id) / "adjudication.json", payload)
        except ValueError as exc:
            return self._block(command, "FRX2_ADJUDICATION_IMMUTABILITY_VIOLATION", str(exc))
        return _result(
            command,
            ok=decision == "PASS",
            exit_code=exit_code,
            message="Full regression session adjudicated with complete terminal accounting.",
            summary={**summary, "decision": decision, "coverage_complete": True, "adjudication_sha256": payload["adjudication_sha256"]},
            findings=findings or [Finding(id="FRX2_ADJUDICATION_PASS", message="All collected nodeids are terminal and no functional failures/errors remain.", severity=Severity.INFO)],
        )

    def _execute_shard(self, *, session: dict[str, Any], plan: dict[str, Any], shard: dict[str, Any], nodeids: Sequence[str], attempt: int, timeout_seconds: int, mode: str) -> tuple[ShardReceipt, str | None]:
        session_id = session["session_id"]
        session_dir = self._session_dir(session_id)
        runtime_dir = session_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        receipt_stem = f"{shard['shard_id']}-attempt-{attempt:03d}"
        junit_path = runtime_dir / f"{receipt_stem}.junit.xml"
        outcomes_path = runtime_dir / f"{receipt_stem}.outcomes.jsonl"
        if junit_path.exists():
            junit_path.unlink()
        if outcomes_path.exists():
            outcomes_path.unlink()

        lifecycle_started_at = _utc_now()
        lifecycle_start = time.monotonic()
        expected_commit = (session.get("source_descriptor") or {}).get("git_commit")

        guard_before_start = time.monotonic()
        source_guard_before = _git_semantic_clean_guard(self.root, expected_commit=expected_commit)
        source_guard_before_seconds = round(time.monotonic() - guard_before_start, 6)
        if source_guard_before is not None and source_guard_before.get("clean"):
            source_before = str(session["source_fingerprint"])
        else:
            source_before = _fingerprint(_source_descriptor(self.root))

        environment_matches = _environment_runtime_guard(session.get("environment_descriptor") or {})
        if environment_matches:
            env_fp = str(session["environment_fingerprint"])
        else:
            env_fp = _fingerprint(_environment_descriptor(self.root))

        started_at = _utc_now()
        start = time.monotonic()
        env = self._subprocess_env(extra={"DEVPILOT_FULL_SESSION_OUTCOMES": str(outcomes_path)})
        args = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "-p",
            "devpilot_core.testing.full_regression_plugin",
            f"--junitxml={junit_path}",
            *nodeids,
        ]
        completed: subprocess.CompletedProcess[str] | None = None
        timed_out = False
        timeout_stdout = ""
        timeout_stderr = ""
        try:
            completed = subprocess.run(args, cwd=self.root, capture_output=True, text=True, timeout=timeout_seconds, shell=False, check=False, env=env)
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            timeout_stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            timeout_stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        except OSError as exc:
            completed = None
            timeout_stderr = f"os-error: {exc}"
        duration = round(time.monotonic() - start, 6)
        log_path = runtime_dir / f"{receipt_stem}.log"
        stdout_text = completed.stdout if completed is not None else timeout_stdout
        stderr_text = completed.stderr if completed is not None else timeout_stderr
        log_path.write_text((stdout_text or "") + ("\nSTDERR:\n" + stderr_text if stderr_text else "") + ("\nINFRA: TIMEOUT\n" if timed_out else ""), encoding="utf-8", newline="\n")
        ended_at = _utc_now()
        outcome_records = self._read_outcome_log(outcomes_path)
        outcomes = {nodeid: outcome_records.get(nodeid, TerminalOutcome.UNEXECUTED.value) for nodeid in nodeids}
        observed = tuple(nodeid for nodeid in nodeids if outcomes[nodeid] != TerminalOutcome.UNEXECUTED.value)
        returncode = None if completed is None else int(completed.returncode)
        infra_abort = timed_out or completed is None or (returncode not in {0, 1})

        guard_after_start = time.monotonic()
        source_guard_after = _git_semantic_clean_guard(self.root, expected_commit=expected_commit)
        source_guard_after_seconds = round(time.monotonic() - guard_after_start, 6)
        if source_guard_after is not None and source_guard_after.get("clean"):
            source_after = str(session["source_fingerprint"])
        else:
            source_after = _fingerprint(_source_descriptor(self.root))
        source_mutation = source_before != session["source_fingerprint"] or source_after != session["source_fingerprint"]

        runtime_block: str | None = None
        if source_mutation:
            runtime_block = "Git-semantic source guard detected source mutation during shard execution. Resume is blocked until a new logical session is created from the intended source."
        elif env_fp != session["environment_fingerprint"]:
            runtime_block = "Environment fingerprint changed before shard execution."
        elif infra_abort:
            runtime_block = "Shard infrastructure aborted or timed out; observed outcomes are preserved and remaining nodeids stay UNEXECUTED for same-session resume."

        lifecycle_duration = round(time.monotonic() - lifecycle_start, 6)
        lifecycle_ended_at = _utc_now()
        receipt = ShardReceipt(
            session_id=session_id,
            shard_id=shard["shard_id"],
            attempt=attempt,
            mode=mode,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration,
            source_fingerprint_before=source_before,
            source_fingerprint_after=source_after,
            environment_fingerprint=env_fp,
            collection_sha256=session["collection_sha256"],
            shard_plan_sha256=plan["shard_plan_sha256"],
            planned_nodeids=tuple(nodeids),
            observed_nodeids=observed,
            outcomes=outcomes,
            returncode=returncode,
            timed_out=timed_out,
            infra_abort=infra_abort,
            source_mutation_detected=source_mutation,
            junit_path=_relative(junit_path, self.root) if junit_path.exists() else None,
            junit_sha256=_sha256_file(junit_path),
            outcome_log_path=_relative(outcomes_path, self.root) if outcomes_path.exists() else None,
            outcome_log_sha256=_sha256_file(outcomes_path),
            log_path=_relative(log_path, self.root) if log_path.exists() else None,
            log_sha256=_sha256_file(log_path),
            lifecycle_started_at=lifecycle_started_at,
            lifecycle_ended_at=lifecycle_ended_at,
            lifecycle_duration_seconds=lifecycle_duration,
            source_guard_before_seconds=source_guard_before_seconds,
            source_guard_after_seconds=source_guard_after_seconds,
            orchestrator_overhead_seconds=round(max(0.0, lifecycle_duration - duration), 6),
        )
        return receipt, runtime_block

    def _load_session(self, session_id: str, *, command: str) -> tuple[dict[str, Any], dict[str, Any]] | CommandResult:
        if not self._valid_session_id(session_id):
            return self._block(command, "FRX2_SESSION_ID_INVALID", "Session id contains unsupported characters.")
        session_dir = self._session_dir(session_id)
        session_path = session_dir / "session.json"
        collection_path = session_dir / "collection.json"
        if not session_path.exists() or not collection_path.exists():
            return self._error(command, "FRX2_SESSION_NOT_FOUND", "Session or collection artifact does not exist.")
        try:
            return _load_json(session_path), _load_json(collection_path)
        except (OSError, json.JSONDecodeError) as exc:
            return self._error(command, "FRX2_SESSION_READ_ERROR", str(exc))

    def _load_session_with_plan(self, session_id: str, *, command: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | CommandResult:
        loaded = self._load_session(session_id, command=command)
        if isinstance(loaded, CommandResult):
            return loaded
        session, collection = loaded
        plan_path = self._session_dir(session_id) / "plan.json"
        if not plan_path.exists():
            return self._error(command, "FRX2_PLAN_NOT_FOUND", "Immutable shard plan does not exist; run plan first.")
        try:
            plan = _load_json(plan_path)
        except (OSError, json.JSONDecodeError) as exc:
            return self._error(command, "FRX2_PLAN_READ_ERROR", str(exc))
        return session, collection, plan

    def _validate_sealed_artifacts(self, session: dict[str, Any], collection: dict[str, Any], plan: dict[str, Any] | None = None) -> CommandResult | None:
        collection_copy = dict(collection)
        actual_collection_sha = _sha256_bytes(_canonical_bytes(collection_copy))
        if actual_collection_sha != session.get("collection_sha256"):
            return self._block("tests full-session integrity", "FRX2_COLLECTION_HASH_MISMATCH", "Collection hash no longer matches the sealed session.")
        if collection.get("nodeids_total") != session.get("collection_total"):
            return self._block("tests full-session integrity", "FRX2_COLLECTION_TOTAL_MISMATCH", "Collection count no longer matches the sealed session.")
        nodeids = [item.get("nodeid") for item in collection.get("nodes", [])]
        if len(nodeids) != len(set(nodeids)) or any(not item for item in nodeids):
            return self._block("tests full-session integrity", "FRX2_COLLECTION_INVALID", "Collection contains duplicate or empty nodeids.")
        if plan is not None:
            plan_copy = {key: value for key, value in plan.items() if key != "shard_plan_sha256"}
            actual_plan_sha = _sha256_bytes(_canonical_bytes(plan_copy))
            if actual_plan_sha != plan.get("shard_plan_sha256"):
                return self._block("tests full-session integrity", "FRX2_PLAN_HASH_MISMATCH", "Shard plan hash no longer matches its sealed content.")
            flattened = [nodeid for shard in plan.get("shards", []) for nodeid in shard.get("nodeids", [])]
            if len(flattened) != len(nodeids) or set(flattened) != set(nodeids) or len(flattened) != len(set(flattened)):
                return self._block("tests full-session integrity", "FRX2_PLAN_COVERAGE_INVALID", "Shard plan no longer maps the collection exactly once.")
        return None

    def _validate_identity(self, session: dict[str, Any], collection: dict[str, Any], *, plan: dict[str, Any] | None = None, require_environment: bool) -> CommandResult | None:
        sealed = self._validate_sealed_artifacts(session, collection, plan)
        if sealed is not None:
            return sealed
        expected_commit = (session.get("source_descriptor") or {}).get("git_commit")
        source_guard = _git_semantic_clean_guard(self.root, expected_commit=expected_commit)
        if source_guard is not None and source_guard.get("clean"):
            current_source = session.get("source_fingerprint")
        else:
            current_source = _fingerprint(_source_descriptor(self.root))
        if current_source != session.get("source_fingerprint"):
            return self._block("tests full-session identity", "FRX2_SOURCE_FINGERPRINT_MISMATCH", "Current Git-semantic source differs from the logical session. Start a new session; do not merge receipts.")
        if require_environment:
            if _environment_runtime_guard(session.get("environment_descriptor") or {}):
                current_env = session.get("environment_fingerprint")
            else:
                current_env = _fingerprint(_environment_descriptor(self.root))
            if current_env != session.get("environment_fingerprint"):
                return self._block("tests full-session identity", "FRX2_ENVIRONMENT_FINGERPRINT_MISMATCH", "Current environment fingerprint differs from the logical session. Start a new session; do not merge receipts.")
        return None

    def _accounting(self, session_id: str, collection: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        nodeids = [item["nodeid"] for item in collection["nodes"]]
        outcomes: dict[str, str] = {nodeid: TerminalOutcome.UNEXECUTED.value for nodeid in nodeids}
        receipts: list[str] = []
        infra_abort_receipts = 0
        receipt_dir = self._session_dir(session_id) / "receipts"
        if receipt_dir.exists():
            for path in sorted(receipt_dir.glob("*.json")):
                payload = _load_json(path)
                if payload.get("collection_sha256") != plan.get("collection_sha256") or payload.get("shard_plan_sha256") != plan.get("shard_plan_sha256"):
                    continue
                receipts.append(_relative(path, self.root))
                if payload.get("infra_abort"):
                    infra_abort_receipts += 1
                for nodeid, outcome in (payload.get("outcomes") or {}).items():
                    if nodeid not in outcomes:
                        continue
                    # Completed functional outcomes are sticky. UNEXECUTED may later be replaced by a resume receipt.
                    if outcomes[nodeid] in _TERMINAL_COMPLETE:
                        continue
                    if outcome in {item.value for item in TerminalOutcome}:
                        outcomes[nodeid] = outcome
        counts = {outcome.value: 0 for outcome in TerminalOutcome}
        for outcome in outcomes.values():
            counts[outcome] = counts.get(outcome, 0) + 1
        summary = {
            "session_id": session_id,
            "collection_total": len(nodeids),
            "accounted_total": len(nodeids) - counts[TerminalOutcome.UNEXECUTED.value],
            "pass_total": counts[TerminalOutcome.PASS.value],
            "fail_total": counts[TerminalOutcome.FAIL.value],
            "error_total": counts[TerminalOutcome.ERROR.value],
            "skip_approved_total": counts[TerminalOutcome.SKIP_APPROVED.value],
            "infra_abort_nodeids_total": counts[TerminalOutcome.INFRA_ABORT.value],
            "unexecuted_total": counts[TerminalOutcome.UNEXECUTED.value],
            "coverage_percent": round(((len(nodeids) - counts[TerminalOutcome.UNEXECUTED.value]) / len(nodeids)) * 100, 4) if nodeids else 0.0,
            "receipts_total": len(receipts),
            "infra_abort_receipts_total": infra_abort_receipts,
            "shards_total": plan.get("shards_total", 0),
            "shard_plan_sha256": plan.get("shard_plan_sha256"),
            "collection_sha256": plan.get("collection_sha256"),
            "logical_attempts": 1,
            "parallel_workers": 1,
            "completion_first": True,
            "planner": plan.get("planner", "count-based-sequential"),
            "scheduler_enabled_for_session": bool(plan.get("scheduler_enabled_for_session", False)),
        }
        return {"summary": summary, "outcomes": outcomes, "receipts": receipts}

    def _read_outcome_log(self, path: Path) -> dict[str, str]:
        outcomes: dict[str, str] = {}
        if not path.exists():
            return outcomes
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            nodeid = str(payload.get("nodeid") or "")
            outcome = str(payload.get("outcome") or "")
            if nodeid and outcome in {item.value for item in TerminalOutcome}:
                outcomes[nodeid] = outcome
        return outcomes

    def _run_subprocess(self, args: Sequence[str], *, timeout_seconds: int, extra_env: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str] | None, bool]:
        try:
            completed = subprocess.run(list(args), cwd=self.root, capture_output=True, text=True, timeout=timeout_seconds, shell=False, check=False, env=self._subprocess_env(extra=extra_env))
            return completed, False
        except subprocess.TimeoutExpired:
            return None, True
        except OSError:
            return None, False

    def _subprocess_env(self, *, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ)
        target_src = str(self.root / "src")
        devpilot_src = str(Path(__file__).resolve().parents[2])
        existing_parts = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
        pythonpath_parts: list[str] = []
        for part in (target_src, devpilot_src, *existing_parts):
            if part not in pythonpath_parts:
                pythonpath_parts.append(part)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if extra:
            env.update(extra)
        return env

    @staticmethod
    def _parse_collection(stdout: str) -> list[str]:
        nodeids: list[str] = []
        for raw in stdout.splitlines():
            line = raw.strip()
            if not line or line.startswith(("=", "<", "warnings summary")):
                continue
            if "::" not in line:
                continue
            if line.startswith(("tests/", "test/")) or ".py::" in line:
                nodeids.append(_normalize_nodeid_path_only(line))
        return nodeids

    def _receipt_path(self, session_id: str, shard_id: str, attempt: int) -> Path:
        return self._session_dir(session_id) / "receipts" / f"{shard_id}-attempt-{attempt:03d}.json"

    def _next_attempt(self, session_id: str, shard_id: str) -> int:
        receipt_dir = self._session_dir(session_id) / "receipts"
        if not receipt_dir.exists():
            return 1
        existing = list(receipt_dir.glob(f"{shard_id}-attempt-*.json"))
        return len(existing) + 1

    def _session_dir(self, session_id: str) -> Path:
        return self.runtime_root / session_id

    @staticmethod
    def _valid_session_id(session_id: str) -> bool:
        return bool(session_id) and len(session_id) <= 96 and all(ch.isalnum() or ch in {"-", "_", "."} for ch in session_id)

    @staticmethod
    def _block(command: str, finding_id: str, message: str) -> CommandResult:
        return _result(command, ok=False, exit_code=ExitCode.BLOCK, message=message, summary={"blocked": True}, findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK)])

    @staticmethod
    def _error(command: str, finding_id: str, message: str) -> CommandResult:
        return _result(command, ok=False, exit_code=ExitCode.ERROR, message=message, summary={"error": True}, findings=[Finding(id=finding_id, message=message, severity=Severity.ERROR)])
