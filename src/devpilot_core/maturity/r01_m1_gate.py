"""R01-15 evidence maturity gate. This does not replace POST-H-002 maturity."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class R01M1EvidenceError(ValueError):
    """Invalid or untrusted maturity evidence; never grant broader authority."""


class R01M1Gate:
    REQUIRED_LEVELS = {
        "candidate": "DETERMINISTIC_SERVICE",
        "policy": "DETERMINISTIC_SERVICE",
        "docs": "GOVERNED_SERVICE",
        "settings": "WINDOWS_BROWSER_OWNER_PASS",
        "workflow_status": "WINDOWS_BROWSER_OWNER_PASS",
    }
    UNPROVEN = {
        "model_local_real": "NOT_TESTED",
        "model_external_real": "DENIED",
        "semantic_llm_judge": "NOT_TESTED",
        "rag_groundedness_real": "NOT_TESTED",
    }
    HASH = re.compile(r"^[0-9a-f]{40}$")
    SHA = re.compile(r"^[0-9a-f]{64}$")

    @classmethod
    def evaluate_file(cls, path: Path, *, expected_head: str) -> dict[str, Any]:
        return cls.evaluate(json.loads(Path(path).read_text(encoding="utf-8")), expected_head=expected_head)

    @classmethod
    def evaluate(cls, evidence: Mapping[str, Any], *, expected_head: str) -> dict[str, Any]:
        if not isinstance(evidence, Mapping) or evidence.get("schema") != "MP132.R01.M1.evidence.v1":
            raise R01M1EvidenceError("EVIDENCE_SCHEMA_INVALID")
        if not cls.HASH.fullmatch(expected_head) or evidence.get("baseline_head") != expected_head:
            raise R01M1EvidenceError("BASELINE_NOT_VERIFIED")
        rows=evidence.get("attestations")
        if not isinstance(rows,list) or len(rows)!=14:
            raise R01M1EvidenceError("R1_CHAIN_INCOMPLETE")
        prev=None
        for i,row in enumerate(rows,1):
            if not isinstance(row,dict) or row.get("sprint")!=f"R01-{i:02d}":
                raise R01M1EvidenceError("UNEXPECTED_SPRINT_ORDER")
            if not all(cls.HASH.fullmatch(str(row.get(x,""))) for x in ("base","head")):
                raise R01M1EvidenceError("INVALID_COMMIT_HASH")
            if not cls.SHA.fullmatch(str(row.get("evidence_zip_sha256",""))):
                raise R01M1EvidenceError("UNHASHED_RECEIPT")
            if not str(row.get("receipt_schema","")).startswith("MP132.R01."):
                raise R01M1EvidenceError("INVALID_RECEIPT_SCHEMA")
            if prev is not None and row["base"]!=prev:
                raise R01M1EvidenceError("CHAIN_BROKEN")
            if row["base"]==row["head"]:
                raise R01M1EvidenceError("NO_INCREMENT_COMMIT")
            prev=row["head"]
        if prev!=expected_head:
            raise R01M1EvidenceError("CHAIN_HEAD_DRIFT")
        levels=evidence.get("levels")
        if not isinstance(levels,Mapping) or set(levels)!=set(cls.REQUIRED_LEVELS)|set(cls.UNPROVEN):
            raise R01M1EvidenceError("CAPABILITY_MATRIX_INCOMPLETE")
        for cap, expected in (cls.REQUIRED_LEVELS | cls.UNPROVEN).items():
            if levels[cap]!=expected:
                raise R01M1EvidenceError("CAPABILITY_EVIDENCE_OVERCLAIM:"+cap)
        if any(row["browser"]!="WINDOWS_OWNER_PASS" for row in rows if row["sprint"] in {"R01-11","R01-12","R01-13"}):
            raise R01M1EvidenceError("BROWSER_ATTESTATION_ABSENT")
        if evidence.get("scope")!="R1_FIRST_VERTICAL_ONLY" or evidence.get("successor")!="R2_SEPARATE_OWNER_AUTHORITY_REQUIRED":
            raise R01M1EvidenceError("AUTHORITY_SCOPE_INVALID")
        findings=evidence.get("known_findings")
        if not isinstance(findings,list) or not findings or any(not isinstance(x,str) or not x for x in findings):
            raise R01M1EvidenceError("FINDINGS_NOT_DECLARED")
        digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        return {
            "schema":"MP132.R01.M1.gate.v1", "baseline_head":expected_head,
            "decision":"PASS_WITH_FINDINGS", "first_vertical":"VERTICAL_INTEGRATED_DETERMINISTIC_WITH_BROWSER",
            "multi_model_production":"FOUNDATION_PRESENT_NOT_VALIDATED",
            "receipt_count":14,"browser_owner_attestations":3,"known_findings":list(findings),
            "capability_levels":dict(levels),"evidence_sha256":digest,
            "full_regression_runs":0,"model_calls":0,"external_api_calls":0,
            "next":"R2_NOT_AUTHORIZED", "mp_1b":"NOT_AUTHORIZED",
            "note":"Historical Windows attestations are user-supplied; this gate validates their declared chain and levels, not Git signatures or the original browser sessions."
        }
