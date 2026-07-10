from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evidence_graph.models import EvidenceGraphOptions, EvidenceGraphSourceSpec

POST_H_031_A_CREATED_BY = "POST-H-031-A"
EVIDENCE_GRAPH_SCHEMA_ID = "SCHEMA-DEVPL-EVIDENCE-GRAPH-V1"
EVIDENCE_GRAPH_CONTRACT = "EvidenceGraph"
EVIDENCE_GRAPH_REPORT_ID = "devpilot-evidence-graph"
DEFAULT_EVIDENCE_GRAPH_SOURCES = Path(".devpilot/evidence/evidence_graph_sources.json")
DEFAULT_EVIDENCE_GRAPH_OUTPUT_JSON = Path("outputs/reports/evidence_graph.json")
DEFAULT_EVIDENCE_GRAPH_OUTPUT_MARKDOWN = Path("outputs/reports/evidence_graph.md")

_FORBIDDEN_PATH_PARTS = {".env", ".env.local", ".env.production", "devpilot.db"}
_FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
_RUNTIME_PREFIXES = ("outputs/", "outputs\\")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _display_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _stable_sha256(path: Path, *, max_bytes: int = 2_000_000) -> str | None:
    if not path.is_file() or path.stat().st_size > max_bytes:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json_if_safe(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.suffix.lower() != ".json" or path.stat().st_size > 3_000_000:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _is_runtime_path(path: str) -> bool:
    normalized = _display_path(path)
    return normalized.startswith("outputs/")


def _is_forbidden_source_path(path: str) -> bool:
    normalized = _display_path(path).lower()
    parts = set(Path(normalized).parts)
    if parts.intersection(_FORBIDDEN_PATH_PARTS):
        return True
    if normalized.endswith(".devpilot/devpilot.db") or normalized.endswith(".devpilot/devpilot.sqlite"):
        return True
    if Path(normalized).suffix in _FORBIDDEN_SUFFIXES:
        return True
    return False


class EvidenceGraphBuilder:
    """Build a local, read-only evidence graph for operator consumption.

    POST-H-031-A deliberately models evidence, claims, gaps and no-go gates; it
    does not execute verification commands and does not issue readiness claims.
    Formal PASS/BLOCK declarations remain owned by dedicated gates such as
    POST-H-025 production-ready-local and quality-gate profiles.
    """

    def __init__(self, root: Path, options: EvidenceGraphOptions | None = None) -> None:
        self.root = Path(root)
        self.options = options or EvidenceGraphOptions()

    @property
    def sources_path(self) -> Path:
        return self.root / self.options.sources_path

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        try:
            specs = self._load_sources()
        except Exception as exc:
            findings.append(
                Finding(
                    "EVIDENCE_GRAPH_SOURCES_INVALID",
                    f"Evidence graph source config could not be loaded: {exc}",
                    Severity.ERROR,
                    path=_display_path(self.options.sources_path),
                )
            )
            return CommandResult(
                command="evidence graph",
                ok=False,
                exit_code=ExitCode.ERROR,
                message="Evidence graph source configuration is invalid.",
                data={"summary": self._empty_summary()},
                findings=findings,
            )

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        source_nodes: list[dict[str, Any]] = []
        for spec in specs:
            node, node_edges, node_findings = self._node_from_source(spec)
            nodes.append(node)
            source_nodes.append(node)
            edges.extend(node_edges)
            findings.extend(node_findings)

        state = self._load_project_state()
        criteria = self._load_criteria()
        nodes.extend(self._claim_nodes(state, criteria))
        nodes.extend(self._no_go_gate_nodes(state, criteria))
        nodes.extend(self._derived_gap_nodes(source_nodes))
        edges.extend(self._derived_edges(source_nodes, state, criteria))

        blocking_findings = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        graph = {
            "schema_version": "1.0",
            "schema_id": EVIDENCE_GRAPH_SCHEMA_ID,
            "graph_id": EVIDENCE_GRAPH_REPORT_ID,
            "created_by": POST_H_031_A_CREATED_BY,
            "status": "pass" if not blocking_findings else "blocked",
            "generated_at_utc": _utc_now(),
            "summary": self._summary(nodes, edges, findings),
            "nodes": nodes,
            "edges": edges,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "source_mutations_performed": False,
                "commands_executed": False,
                "secrets_read": False,
                "raw_payloads_exported": False,
                "devpilot_db_read": False,
                "reports_written": bool(self.options.write_report),
            },
            "limitations": [
                "EvidenceGraph is an operator model and does not declare readiness by itself.",
                "Missing expected evidence is represented as missing_expected, never as PASS.",
                "Runtime evidence under outputs/ is regenerable and not a versioned source of truth.",
                "Formal PASS/BLOCK declarations remain owned by dedicated gates such as production-ready-local and quality-gate.",
            ],
            "findings": [finding.to_dict() for finding in findings] or [
                Finding(
                    "EVIDENCE_GRAPH_MODEL_READY",
                    "Evidence graph was built from local metadata without executing commands.",
                    Severity.INFO,
                    metadata={"sources_total": len(specs)},
                ).to_dict()
            ],
            "notes": [
                "POST-H-031-A creates the graph model only; operator health, gap actions, claims dashboard and redacted export UX remain future micro-sprints.",
                "The builder is read-only unless --write-report is explicitly used, and report writes are limited to outputs/reports.",
            ],
        }

        if self.options.write_report:
            self._write_reports(graph)

        return CommandResult(
            command="evidence graph",
            ok=not blocking_findings,
            exit_code=ExitCode.PASS if not blocking_findings else self._exit_code_from_findings(blocking_findings),
            message="Evidence graph model built." if not blocking_findings else "Evidence graph model has blocking findings.",
            data={"summary": graph["summary"], "graph": graph},
            findings=findings or [Finding("EVIDENCE_GRAPH_MODEL_READY", "Evidence graph model is available.", Severity.INFO)],
        )

    def _load_sources(self) -> list[EvidenceGraphSourceSpec]:
        payload = json.loads(self.sources_path.read_text(encoding="utf-8"))
        raw_sources = payload.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ValueError("evidence_graph_sources.json must contain a non-empty sources list")
        specs = [EvidenceGraphSourceSpec.from_dict(item) for item in raw_sources if isinstance(item, dict)]
        missing_ids = [spec.path for spec in specs if not spec.source_id or not spec.path]
        if missing_ids:
            raise ValueError(f"source declarations with missing source_id/path: {missing_ids}")
        return specs

    def _node_from_source(self, spec: EvidenceGraphSourceSpec) -> tuple[dict[str, Any], list[dict[str, Any]], list[Finding]]:
        findings: list[Finding] = []
        edges: list[dict[str, Any]] = []
        display_path = _display_path(spec.path)
        path = spec.resolved(self.root)
        forbidden = _is_forbidden_source_path(display_path)
        exists = path.exists() if not forbidden else False
        runtime = _is_runtime_path(display_path)
        evidence_class = "runtime_generated" if runtime else spec.evidence_class
        if forbidden:
            evidence_class = "blocked_or_forbidden"
            status = "blocked"
            findings.append(Finding("EVIDENCE_GRAPH_FORBIDDEN_SOURCE", "Forbidden evidence source was blocked from inspection.", Severity.BLOCK, path=display_path))
        elif exists:
            status = "available"
        else:
            evidence_class = "missing_expected"
            status = "missing"
            severity = Severity.BLOCK if spec.required else Severity.WARNING
            findings.append(Finding("EVIDENCE_GRAPH_SOURCE_MISSING", "Expected evidence source is missing.", severity, path=display_path, metadata={"required": spec.required, "source_id": spec.source_id}))

        payload = None if forbidden or not exists else _load_json_if_safe(path)
        metadata: dict[str, Any] = {
            "exists": exists,
            "required": spec.required,
            "runtime_generated": runtime,
            "versioned_source": bool(exists and not runtime and not forbidden),
            "blocked_from_reading": forbidden,
            "size_bytes": path.stat().st_size if exists and path.is_file() else None,
            "sha256": None if forbidden or not exists else _stable_sha256(path),
        }
        if isinstance(payload, dict):
            metadata["schema_id"] = payload.get("schema_id")
            metadata["status_field"] = payload.get("status")
            metadata["created_by"] = payload.get("created_by")
            metadata["summary_keys"] = sorted(payload.get("summary", {}).keys()) if isinstance(payload.get("summary"), dict) else []

        node = {
            "node_id": f"source:{spec.source_id}",
            "node_type": spec.node_type,
            "title": spec.title,
            "status": status,
            "evidence_class": evidence_class,
            "path": display_path,
            "source_id": spec.source_id,
            "category": spec.category,
            "required": spec.required,
            "expected_schema_id": spec.expected_schema_id,
            "metadata": metadata,
            "tags": list(spec.tags),
            "notes": list(spec.notes),
        }
        if spec.generated_by:
            edges.append(self._edge(f"command:{spec.generated_by}", node["node_id"], "generated_by", "Configured source declares producer command."))
        if spec.validates_against:
            edges.append(self._edge(node["node_id"], f"schema:{spec.validates_against}", "validates_against", "Configured source declares expected schema."))
        for claim_id in spec.supports_claims:
            edges.append(self._edge(node["node_id"], f"claim:{claim_id}", "supports", "Configured evidence supports this claim."))
        for gate_id in spec.relates_to_gates:
            edges.append(self._edge(node["node_id"], f"gate:{gate_id}", "supports", "Configured evidence relates to this gate."))
        return node, edges, findings

    def _load_project_state(self) -> dict[str, Any]:
        path = self.root / ".devpilot/project_state.json"
        payload = _load_json_if_safe(path)
        return payload or {}

    def _load_criteria(self) -> dict[str, Any]:
        path = self.root / ".devpilot/production/production_ready_local_criteria.json"
        payload = _load_json_if_safe(path)
        return payload or {}

    def _claim_nodes(self, state: dict[str, Any], criteria: dict[str, Any]) -> list[dict[str, Any]]:
        claims_allowed = criteria.get("claims_allowed") if isinstance(criteria.get("claims_allowed"), dict) else {}
        claim_defs = {
            "production-ready-local": bool(claims_allowed.get("production_ready_local", state.get("post_h_025_production_ready_local_declared", False))),
            "enterprise-ready": bool(claims_allowed.get("enterprise_ready", False)),
            "remote-ready": bool(claims_allowed.get("remote_ready", False)),
            "compliance-certified": bool(claims_allowed.get("compliance_certified", False)),
            "saas-ready": bool(claims_allowed.get("saas_ready", False)),
        }
        nodes: list[dict[str, Any]] = []
        for claim_id, allowed in claim_defs.items():
            nodes.append(
                {
                    "node_id": f"claim:{claim_id}",
                    "node_type": "claim",
                    "title": claim_id,
                    "status": "allowed" if allowed else "prohibited",
                    "evidence_class": "derived_summary",
                    "path": None,
                    "metadata": {
                        "allowed": allowed,
                        "source": ".devpilot/production/production_ready_local_criteria.json",
                        "graph_declares_readiness": False,
                    },
                    "tags": ["claim", "no-overclaim"],
                    "notes": ["EvidenceGraph models claim status but does not issue the claim."],
                }
            )
        return nodes

    def _no_go_gate_nodes(self, state: dict[str, Any], criteria: dict[str, Any]) -> list[dict[str, Any]]:
        no_go = criteria.get("no_go_gates") if isinstance(criteria.get("no_go_gates"), dict) else {}
        keys = [
            "remote_execution_enabled",
            "connector_write_enabled",
            "plugin_execution_enabled",
            "external_apis_required",
            "compliance_certification_claim",
            "enterprise_ready_claim",
            "remote_ready_claim",
            "saas_ready_claim",
        ]
        nodes: list[dict[str, Any]] = []
        for key in keys:
            expected = no_go.get(key, False)
            actual = state.get(key, expected)
            safe = actual is False and expected is False
            nodes.append(
                {
                    "node_id": f"gate:{key}",
                    "node_type": "gate",
                    "title": key,
                    "status": "active_blocking" if safe else "violated",
                    "evidence_class": "derived_summary",
                    "path": ".devpilot/production/production_ready_local_criteria.json",
                    "metadata": {"expected": expected, "actual": actual, "safe": safe},
                    "tags": ["no-go-gate"],
                    "notes": ["No-go gate is represented for operator visibility; enforcement remains in dedicated validators/gates."],
                }
            )
        return nodes

    def _derived_gap_nodes(self, source_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for node in source_nodes:
            if node["status"] in {"missing", "blocked"}:
                nodes.append(
                    {
                        "node_id": f"gap:{node['source_id']}",
                        "node_type": "gap",
                        "title": f"Gap for {node['source_id']}",
                        "status": "blocking" if node.get("required") else "advisory",
                        "evidence_class": "derived_summary",
                        "path": node.get("path"),
                        "metadata": {
                            "source_id": node.get("source_id"),
                            "reason": node["status"],
                            "required": node.get("required"),
                        },
                        "tags": ["gap", "operator-action-future"],
                        "notes": ["POST-H-031-C will map this gap to concrete actions; POST-H-031-A only models the gap."],
                    }
                )
        return nodes

    def _derived_edges(self, source_nodes: list[dict[str, Any]], state: dict[str, Any], criteria: dict[str, Any]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        for node in source_nodes:
            if node["status"] in {"missing", "blocked"}:
                edges.append(self._edge(f"gap:{node['source_id']}", node["node_id"], "requires", "Gap requires expected evidence source."))
        for gate in ["remote_execution_enabled", "connector_write_enabled", "plugin_execution_enabled", "external_apis_required"]:
            edges.append(self._edge(f"gate:{gate}", "claim:production-ready-local", "supports", "Safe disabled capability supports bounded local claim."))
        for gate, claim in [
            ("enterprise_ready_claim", "enterprise-ready"),
            ("remote_ready_claim", "remote-ready"),
            ("compliance_certification_claim", "compliance-certified"),
            ("saas_ready_claim", "saas-ready"),
        ]:
            edges.append(self._edge(f"gate:{gate}", f"claim:{claim}", "blocks", "No-go gate blocks overclaim."))
        return edges

    def _edge(self, source: str, target: str, edge_type: str, rationale: str) -> dict[str, Any]:
        return {
            "edge_id": f"{edge_type}:{source}->{target}".replace(" ", "-"),
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "rationale": rationale,
        }

    def _summary(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_class: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for node in nodes:
            by_type[node.get("node_type", "unknown")] = by_type.get(node.get("node_type", "unknown"), 0) + 1
            by_class[node.get("evidence_class", "unknown")] = by_class.get(node.get("evidence_class", "unknown"), 0) + 1
            by_status[node.get("status", "unknown")] = by_status.get(node.get("status", "unknown"), 0) + 1
        blocking = [f for f in findings if f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        return {
            "created_by": POST_H_031_A_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if not blocking else "BLOCK",
            "nodes_total": len(nodes),
            "edges_total": len(edges),
            "nodes_by_type": by_type,
            "nodes_by_evidence_class": by_class,
            "nodes_by_status": by_status,
            "missing_evidence_total": by_status.get("missing", 0),
            "blocking_gaps_total": sum(1 for node in nodes if node.get("node_type") == "gap" and node.get("status") == "blocking"),
            "no_go_gates_total": by_type.get("gate", 0),
            "claims_total": by_type.get("claim", 0),
            "findings_total": len(findings),
            "blocking_findings_total": len(blocking),
            "graph_declares_readiness": False,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": bool(self.options.write_report),
            "preliminary": True,
        }

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "created_by": POST_H_031_A_CREATED_BY,
            "status": "implemented-initial",
            "decision": "BLOCK",
            "nodes_total": 0,
            "edges_total": 0,
            "missing_evidence_total": 0,
            "blocking_gaps_total": 0,
            "no_go_gates_total": 0,
            "claims_total": 0,
            "findings_total": 1,
            "blocking_findings_total": 1,
            "graph_declares_readiness": False,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "reports_written": False,
            "preliminary": True,
        }

    def _exit_code_from_findings(self, findings: list[Finding]) -> ExitCode:
        if any(f.severity == Severity.ERROR for f in findings):
            return ExitCode.ERROR
        if any(f.severity == Severity.BLOCK for f in findings):
            return ExitCode.BLOCK
        return ExitCode.FAIL

    def _write_reports(self, graph: dict[str, Any]) -> None:
        json_path = self.root / self.options.output_json
        markdown_path = self.root / self.options.output_markdown
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(render_evidence_graph_markdown(graph), encoding="utf-8")


def render_evidence_graph_markdown(graph: dict[str, Any]) -> str:
    summary = graph.get("summary", {}) if isinstance(graph.get("summary"), dict) else {}
    lines = [
        "# DevPilot Evidence Graph",
        "",
        f"- Graph ID: `{graph.get('graph_id')}`",
        f"- Created by: `{graph.get('created_by')}`",
        f"- Status: `{graph.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Nodes: `{summary.get('nodes_total')}`",
        f"- Edges: `{summary.get('edges_total')}`",
        f"- Missing evidence: `{summary.get('missing_evidence_total')}`",
        f"- Blocking gaps: `{summary.get('blocking_gaps_total')}`",
        "",
        "## Safety",
        "",
    ]
    for key, value in (graph.get("safety") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Limitations", ""])
    for item in graph.get("limitations", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Node counts by type", ""])
    for key, value in sorted((summary.get("nodes_by_type") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Findings", ""])
    for finding in graph.get("findings", []):
        lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}`: {finding.get('message')}")
    lines.append("")
    return "\n".join(lines)
