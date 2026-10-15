"""R01-02: persistent, provider-neutral candidate lifecycle.

This store owns *candidate evidence only*. It cannot approve, publish, execute a
provider, or apply source patches. One SQLite database serializes concurrent
writers; existing GenerationRequest / ArtifactCandidateEnvelope remain canonical.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

from .contracts import (
    ArtifactCandidateEnvelope, CandidateStatus, GenerationRequest,
    canonical_json, canonical_sha256, transition_candidate,
)


class CandidateLifecycleConflict(ValueError):
    """An idempotency key, immutable candidate, or expected state disagrees."""


def _fingerprint(candidate: ArtifactCandidateEnvelope[Any], request: GenerationRequest) -> str:
    immutable = candidate.to_dict()
    for key in ("status", "evaluation_summary", "unsupported_claims", "questions"):
        immutable.pop(key, None)
    return canonical_sha256({"request": request.to_dict(), "candidate": immutable})


class CandidateLifecycleStore:
    """SQLite store with transaction-bound idempotency and optimistic status CAS.

    The db path is explicitly supplied by the operator/application; never put it
    in source-controlled directories or use a mutable global singleton.
    """

    def __init__(self, db_path: Path, *, timeout_seconds: float = 5.0) -> None:
        self.path = Path(db_path)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._open() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL UNIQUE,
                    request_json TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    proof_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    parent_id TEXT,
                    root_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    FOREIGN KEY(parent_id) REFERENCES candidates(candidate_id)
                );
                CREATE TABLE IF NOT EXISTS replay_keys (
                    replay_key TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id)
                );
            """)

    @contextmanager
    def _open(self):
        db = sqlite3.connect(self.path, timeout=self.timeout_seconds, isolation_level=None)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
            yield db
        finally:
            db.close()

    @staticmethod
    def _envelope(raw: str) -> ArtifactCandidateEnvelope[Any]:
        envelope = ArtifactCandidateEnvelope.from_dict(json.loads(raw))
        if not envelope.content_integrity_ok():
            raise CandidateLifecycleConflict("PERSISTED_CONTENT_DRIFT")
        return envelope

    def get(self, candidate_id: str) -> ArtifactCandidateEnvelope[Any] | None:
        with self._open() as db:
            row = db.execute("SELECT envelope_json FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
        return self._envelope(row[0]) if row else None

    def receipt(self, candidate_id: str) -> dict[str, Any]:
        with self._open() as db:
            row = db.execute("SELECT proof_json, status FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
        if not row:
            raise KeyError("CANDIDATE_NOT_FOUND")
        return {**json.loads(row[0]), "status": row[1]}

    def put(self, *, request: GenerationRequest, candidate: ArtifactCandidateEnvelope[Any],
            idempotency_key: str) -> ArtifactCandidateEnvelope[Any]:
        """Persist once. Retries return the same candidate, even after terminal state.

        A replay key cannot silently bind to a changed request/provider/prompt.
        The same immutable fingerprint never yields a second candidate record.
        """
        key = str(idempotency_key or "").strip()
        if not key or len(key) > 256:
            raise ValueError("INVALID_IDEMPOTENCY_KEY")
        if candidate.request_id != request.request_id or candidate.artifact_type != request.artifact_type:
            raise CandidateLifecycleConflict("REQUEST_BINDING_DRIFT")
        if candidate.canonical_input_sha256 != request.canonical_input_sha256:
            raise CandidateLifecycleConflict("INPUT_HASH_DRIFT")
        if not candidate.content_integrity_ok():
            raise CandidateLifecycleConflict("CONTENT_HASH_DRIFT")
        proof = {
            "candidate_id": candidate.candidate_id,
            "request_id": request.request_id,
            "input_sha256": request.canonical_input_sha256,
            "context_sha256": canonical_sha256({"reference": request.context_reference,
                                                "upstream_hashes": dict(request.upstream_hashes)}),
            "output_sha256": candidate.content_sha256,
            "provider_sha256": canonical_sha256(candidate.origin.to_dict()),
            "prompt_sha256": canonical_sha256({"ref": candidate.provenance.prompt_ref,
                                               "profile_ref": candidate.provenance.profile_ref}),
            "version": candidate.version,
            "profile_version": request.profile_version,
            "dependency_profile_version": request.dependency_profile_version,
            "parent_id": candidate.lineage.parent_candidate_id,
            "root_id": candidate.lineage.root_candidate_id,
        }
        fp = _fingerprint(candidate, request)
        with self._open() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                old_key = db.execute("SELECT candidate_id FROM replay_keys WHERE replay_key=?", (key,)).fetchone()
                if old_key:
                    row = db.execute("SELECT fingerprint, envelope_json FROM candidates WHERE candidate_id=?",
                                     (old_key[0],)).fetchone()
                    if not row or row[0] != fp:
                        raise CandidateLifecycleConflict("IDEMPOTENCY_CONTEXT_CONFLICT")
                    db.commit()
                    return self._envelope(row[1])
                old_candidate = db.execute(
                    "SELECT fingerprint, envelope_json FROM candidates WHERE candidate_id=? OR fingerprint=?",
                    (candidate.candidate_id, fp)).fetchone()
                if old_candidate:
                    if old_candidate[0] != fp:
                        raise CandidateLifecycleConflict("IMMUTABLE_CANDIDATE_COLLISION")
                    saved = self._envelope(old_candidate[1])
                    if saved.candidate_id != candidate.candidate_id:
                        raise CandidateLifecycleConflict("FINGERPRINT_ID_COLLISION")
                else:
                    parent_id = candidate.lineage.parent_candidate_id
                    if parent_id:
                        row = db.execute("SELECT envelope_json FROM candidates WHERE candidate_id=?", (parent_id,)).fetchone()
                        if not row:
                            raise CandidateLifecycleConflict("MISSING_LINEAGE_PARENT")
                        parent = self._envelope(row[0])
                        if (parent.version + 1 != candidate.version or
                            candidate.lineage.parent_version != parent.version or
                            candidate.lineage.root_candidate_id != parent.lineage.root_candidate_id or
                            candidate.artifact_type != parent.artifact_type):
                            raise CandidateLifecycleConflict("LINEAGE_INCONSISTENT")
                    db.execute(
                        "INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?)",
                        (candidate.candidate_id, fp, canonical_json(request.to_dict()),
                         canonical_json(candidate.to_dict()), canonical_json(proof),
                         candidate.status.value, parent_id, candidate.lineage.root_candidate_id, candidate.version),
                    )
                    saved = candidate
                db.execute("INSERT INTO replay_keys VALUES(?,?)", (key, saved.candidate_id))
                db.commit()
                return saved
            except BaseException:
                db.rollback()
                raise

    def transition(self, *, candidate_id: str, expected_status: CandidateStatus,
                   target_status: CandidateStatus) -> ArtifactCandidateEnvelope[Any]:
        """Atomic status transition. Repeated completion is a read-only no-op."""
        with self._open() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT envelope_json FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
                if not row:
                    raise KeyError("CANDIDATE_NOT_FOUND")
                current = self._envelope(row[0])
                if current.status == target_status:
                    db.commit()
                    return current
                if current.status != expected_status:
                    raise CandidateLifecycleConflict("CONCURRENT_STATUS_CONFLICT")
                updated = transition_candidate(current, target_status)
                written = db.execute(
                    "UPDATE candidates SET envelope_json=?, status=? WHERE candidate_id=? AND status=?",
                    (canonical_json(updated.to_dict()), target_status.value, candidate_id, expected_status.value),
                ).rowcount
                if written != 1:
                    raise CandidateLifecycleConflict("CONCURRENT_STATUS_CONFLICT")
                db.commit()
                return updated
            except BaseException:
                db.rollback()
                raise
