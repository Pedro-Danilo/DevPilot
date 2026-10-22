"""MP132-R02-08: read-only, evidence-scoped Product Definition coverage.

Composes the canonical ArtifactProfileRegistry / ArtifactCoverageGate, instead
of introducing a second profile, approval, publication or model authority.
Source references are *presence proofs*, not semantic-equivalence judgments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import re
from typing import Literal

from .artifact_coverage_gate import CoverageRule

_FILE_TYPES = (
    ("product-vision", "docs/00_product/product_vision.md", "INTAKE"),
    ("mvp-scope", "docs/00_product/mvp_scope.md", "INTAKE"),
    ("requirements-specification", "docs/01_requirements/requirements_specification.md", "REQUIREMENTS"),
)
_HASH = re.compile(r"^[0-9a-f]{64}$")
_SCOPE_KEY = re.compile(r"\bSC-IN-\d{2,3}\b", re.I)
_PRIORITY = {"PASS": 0, "WARN": 1, "REVIEW_REQUIRED": 2, "BLOCK": 3}


def _content(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _hash(text: str) -> str:
    return sha256(_content(text).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FrozenProof:
    """Evidence from the *existing* authoritative lifecycle, not Markdown YAML."""
    sha256_lf: str
    receipt_ref: str
    lifecycle: str = "FROZEN"


@dataclass(frozen=True)
class GroundedLink:
    source_type: Literal["product-vision", "mvp-scope"]
    target_type: Literal["mvp-scope", "requirements-specification"]
    source_excerpt: str
    target_excerpt: str
    evidence_ref: str
    semantic_disposition: Literal["PASS", "REVIEW_REQUIRED", "FAIL"] = "REVIEW_REQUIRED"

    def __post_init__(self):
        if (self.source_type, self.target_type) not in {("product-vision", "mvp-scope"), ("mvp-scope", "requirements-specification")}:
            raise ValueError("R0208_LINK_DIRECTION_INVALID")


@dataclass(frozen=True)
class ProductDefinitionInput:
    frozen: dict[str, FrozenProof] = field(default_factory=dict)
    semantic_acceptance: dict[str, tuple[str, ...]] = field(default_factory=dict)
    links: tuple[GroundedLink, ...] = ()
    # Requested applicability is scoped to documented project facts, not an ID.
    product_has_ai: bool | None = None
    ai_fact_evidence: tuple[str, ...] = ()


def _finding(code: str, severity: str, source: str, detail: str, remediation: str) -> dict:
    return {"rule_id": code, "severity": severity, "source_ref": source,
            "observed": detail, "remediation": remediation}


def _rf_origins(text: str) -> dict[str, dict[str, str]]:
    """Only RF origins count as implementation traces; summary mentions do not."""
    found: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"(?ms)^###\s+(RF-\d+)\b([^\n]*)\n(.*?)(?=^###\s+RF-\d+\b|^##\s+|\Z)", text):
        rf_id, heading, block = match.groups()
        origin = re.search(r"(?im)^\s*[-*]?\s*Origen\s*:\s*([^\n]+)", block)
        if not origin:
            origin = re.search(r"(?im)^\s*Origen\s+(SC-IN-\d{2,3})", block)
        if not origin:
            continue
        description = re.search(r"(?im)^\s*[-*]?\s*Comportamiento\s*:\s*(.+)$", block)
        if not description:
            description = re.search(r"(?im)^\s*[-*]?\s*Criterio de aceptación\s*:\s*(.+)$", block)
        summary = (description.group(1) if description else block.strip().splitlines()[0] if block.strip() else '').strip()
        for cid in set(x.upper() for x in _SCOPE_KEY.findall(origin.group(1))):
            # Preserve the first (lowest) RF as a readable witness; multiple RFs
            # may reference the same Scope capability and must not overwrite it.
            found.setdefault(cid, {'rf_id':rf_id, 'requirement_excerpt':summary[:350], 'requirement_ref':f'docs/01_requirements/requirements_specification.md#{rf_id.lower()}'})
    return found


def _scope_excerpt(text: str, capability: str) -> str:
    # Markdown table row or exact-ID line. Keep the literal text: no paraphrase.
    for line in text.splitlines():
        if re.search(r"\b" + re.escape(capability) + r"\b", line, re.I):
            if re.match(r"\s*\|\s*" + re.escape(capability) + r"\s*\|",line,re.I):
                return line.strip()[:500]
    for line in text.splitlines():
        if re.search(r"\b" + re.escape(capability) + r"\b", line, re.I):
            return line.strip()[:500]
    return ''


def evaluate_product_definition(registry, documents_root: Path, inputs: ProductDefinitionInput) -> dict:
    """Return a bounded quality/coverage report; no source writes or model calls.

    A lack of semantic attestations is REVIEW_REQUIRED, never an invented PASS.
    An incorrectly attributed FROZEN snapshot is BLOCK. A missing upstream
    capability in Requirements is BLOCK, irrespective of stylistic differences.
    """
    root = Path(documents_root).resolve()
    documents = {}
    findings = []
    rules = []
    for typ, relative, stage in _FILE_TYPES:
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("R0208_UNSAFE_DOCUMENT_ROOT")
        text = _content(path.read_text(encoding="utf-8-sig")) if path.is_file() else ""
        documents[typ] = text
        proof = inputs.frozen.get(typ)
        if text and (not proof or not proof.receipt_ref.strip()):
            findings.append(_finding("FROZEN_AUTHORITY_UNVERIFIED", "REVIEW_REQUIRED", relative,
                "Falta recibo de lifecycle autoritativo", "Adjuntar recibo runtime FROZEN y hash verificado"))
        elif text and (proof.lifecycle != "FROZEN" or not _HASH.fullmatch(proof.sha256_lf) or _hash(text) != proof.sha256_lf):
            findings.append(_finding("FROZEN_HASH_OR_STATE_DRIFT", "BLOCK", relative,
                "Recibo FROZEN y Markdown no corresponden", "Conciliar autoridad runtime sin editar el artefacto FROZEN"))
        evidence = inputs.semantic_acceptance.get(typ, ())
        # Evidence is a reference to review, not a magic semantic certificate.
        rules.append(CoverageRule(artifact_type=typ, path=relative, stage=stage,
            obligation="REQUIRED", semantic_review="PASS" if evidence else "PENDING",
            semantic_evidence=tuple(evidence)))
    coverage = registry.evaluate_coverage(tuple(rules), stage="REQUIREMENTS", documents_root=root)
    for row in coverage["items"]:
        if row["result"] != "PASS":
            findings.append(_finding("PROFILE_OR_CONTENT_" + row["artifact_type"], row["result"], row["path"],
                ", ".join(row["reasons"]), "Verificar perfil, contenido y revisión semántica respaldada"))
    scope = documents["mvp-scope"]
    requirements = documents["requirements-specification"]
    ids = sorted(set(x.upper() for x in _SCOPE_KEY.findall(scope)))
    if not ids:
        findings.append(_finding("SCOPE_CAPABILITY_IDS_ABSENT", "REVIEW_REQUIRED", "mvp-scope",
            "No se reconocen IDs SC-IN para un control automático", "Revisar trazabilidad mediante perfil y pruebas específicas del proyecto"))
    origins = _rf_origins(requirements)
    missing = [code for code in ids if code not in origins]
    reference_evidence=[]
    for code in ids:
        rf=origins.get(code)
        reference_evidence.append({
            'capability_id':code, 'scope_ref':'docs/00_product/mvp_scope.md',
            'scope_excerpt':_scope_excerpt(scope,code),
            'requirement_rf':rf['rf_id'] if rf else None,
            'requirement_ref':rf['requirement_ref'] if rf else None,
            'requirement_excerpt':rf['requirement_excerpt'] if rf else '',
            'origin_verified':bool(rf), 'semantic_verified':False,
        })
    for code in missing:
        findings.append(_finding("SCOPE_CAPABILITY_NOT_TRACED", "BLOCK", "mvp-scope:" + code,
            "La capacidad Scope no consta como Origen de un RF (una mención en Alcance no es prueba)",
            "Revisar el RF correspondiente y proponer un sucesor gobernado si falta"))
    checked_links = []
    for link in inputs.links:
        source_text = documents[link.source_type]
        target_text = documents[link.target_type]
        source_ok = bool(link.source_excerpt.strip()) and _content(link.source_excerpt).strip() in source_text
        target_ok = bool(link.target_excerpt.strip()) and _content(link.target_excerpt).strip() in target_text
        founded = bool(link.evidence_ref.strip()) and source_ok and target_ok
        entry = {"from": link.source_type, "to": link.target_type, "evidence_ref": link.evidence_ref,
                 "source_present": source_ok, "target_present": target_ok, "semantic_disposition": link.semantic_disposition}
        checked_links.append(entry)
        if not founded:
            findings.append(_finding("GROUNDING_SOURCE_UNVERIFIED", "BLOCK", link.evidence_ref,
                "La cita o destino no aparece literalmente en los documentos declarados", "Aportar fragmentos exactos del origen y destino"))
        elif link.semantic_disposition == "FAIL":
            findings.append(_finding("CROSS_ARTIFACT_CONTRADICTION_REVIEWED", "BLOCK", link.evidence_ref,
                "Contradicción material corroborada", "Abrir análisis de impacto y sucesor gobernado"))
        elif link.semantic_disposition != "PASS":
            findings.append(_finding("CROSS_ARTIFACT_SEMANTICS_PENDING", "REVIEW_REQUIRED", link.evidence_ref,
                "Presencia verificada; equivalencia semántica pendiente", "Revisar coherencia sin afirmar equivalencia automática"))
    if not checked_links:
        findings.append(_finding("CROSS_ARTIFACT_SEMANTICS_UNPROVEN", "REVIEW_REQUIRED", "product-definition",
            "No existe prueba contextual Vision→Scope→Requirements", "Aportar al menos un enlace con fuente y dictamen revisable"))
    # A model helping to build the product does not make the delivered app AI-enabled.
    if inputs.product_has_ai is None or (inputs.product_has_ai is False and not inputs.ai_fact_evidence):
        miasi = "REVIEW_REQUIRED"
        findings.append(_finding("PRODUCT_AI_APPLICABILITY_UNVERIFIED", "REVIEW_REQUIRED", "project-facts",
            "No hay hechos suficientes para declarar MIASI requerido o N/A", "Verificar el alcance AI en el producto entregado"))
    else:
        miasi = "REQUIRED" if inputs.product_has_ai else "NOT_APPLICABLE"
        if inputs.product_has_ai and not inputs.ai_fact_evidence:
            miasi = "REVIEW_REQUIRED"
            findings.append(_finding("PRODUCT_AI_APPLICABILITY_UNVERIFIED", "REVIEW_REQUIRED", "project-facts",
                "AI declarado sin evidencia", "Vincular hechos de proyecto verificados"))
    result = max([coverage["result"], *(f["severity"] for f in findings)], key=lambda x: _PRIORITY[x])
    return {"contract": "MP132-R02-08-PRODUCT-DEFINITION-COVERAGE-v1", "result": result,
            "evaluation_only": True, "writes_performed": False, "model_calls": 0,
            "automatic_semantic_approval": False, "profile_registry": "ArtifactProfileRegistry",
            "coverage": coverage, "scope_capability_ids": ids, "untraced_scope_ids": missing,
            "reference_evidence":reference_evidence,
            "cross_artifact_links": checked_links, "miasi_applicability": miasi,
            "frozen_hashes": {typ: _hash(text) if text else None for typ, text in documents.items()},
            "findings": findings, "limitations": ["Las coincidencias literales no acreditan equivalencia semántica", "El estado FROZEN se acredita exclusivamente con recibos runtime"]}
