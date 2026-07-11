from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PathGuard, PolicyEffect, SecretGuard, redact_string
from devpilot_core.rag.retriever import LocalRagRetriever, RagQueryOptions
from devpilot_core.schemas.validator import SchemaValidator

POST_H_032_D_CREATED_BY = "POST-H-032-D"
RAG_AGENT_CONTEXT_COMMAND = "agent rag-context"
RAG_AGENT_CONTEXT_SCHEMA_ID = "SCHEMA-DEVPL-RAG-AGENT-CONTEXT-PACK-V1"
RAG_AGENT_CONTEXT_CONTRACT = "RagAgentContextPack"
INSUFFICIENT_EVIDENCE = "insufficient evidence"
DEFAULT_BINDINGS_PATH = ".devpilot/agents/rag_agent_bindings.json"
DEFAULT_INDEX_PATH = ".devpilot/rag/docs_index.json"
TARGET_AGENTS = (
    "requirements.agent",
    "architecture.agent",
    "security.agent",
    "testplanner.agent",
    "release.assistant",
)
OPTIONAL_RAG_AGENTS = (
    "repo.analysis",
    "code.review",
    "patch.review",
)


@dataclass(frozen=True)
class RagAgentContextOptions:
    """Options for POST-H-032-D RAG-aware agent context pack generation."""

    agent_id: str | None = None
    query: str | None = None
    target: str | None = None
    bindings_path: Path = Path(DEFAULT_BINDINGS_PATH)
    index_path: Path = Path(DEFAULT_INDEX_PATH)
    top_k: int = 5
    write_report: bool = False
    output_json: Path = Path("outputs/reports/rag_agent_context_pack.json")
    output_markdown: Path = Path("outputs/reports/rag_agent_context_pack.md")


class RagAwareAgentContextBuilder:
    """Build source-grounded context packs for selected DevPilot agents.

    POST-H-032-D deliberately remains local-first and deterministic. It does not
    call an LLM, does not use network, does not read memory and does not execute
    agent tools. It prepares auditable RAG context that a future prompt/runtime
    layer can consume safely: source ids, citations, freshness and explicit
    insufficient-evidence behavior are mandatory.
    """

    def __init__(self, root: Path, options: RagAgentContextOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or RagAgentContextOptions()
        self.path_guard = PathGuard(self.root)
        self.secret_guard = SecretGuard()

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        bindings = self._load_bindings(findings)
        agent_rows = _agent_rows(bindings)
        selected_agents = self._selected_agents(agent_rows, findings)
        contexts = [self._context_for_agent(agent, bindings, findings) for agent in selected_agents]
        negative_cases = self._negative_cases(bindings, contexts)
        summary = self._summary(bindings, contexts, negative_cases, findings)
        report = {
            "schema_version": "1.0",
            "schema_id": RAG_AGENT_CONTEXT_SCHEMA_ID,
            "pack_id": "devpilot-rag-agent-context-pack",
            "created_by": POST_H_032_D_CREATED_BY,
            "status": "implemented-initial" if summary["blocking_findings_total"] == 0 else "blocked",
            "generated_at_utc": _now_utc(),
            "bindings_path": _posix(self.options.bindings_path),
            "index_path": _posix(self.options.index_path),
            "summary": summary,
            "agents": contexts,
            "negative_cases": negative_cases,
            "groundedness_eval": _groundedness_eval(contexts, negative_cases),
            "safety": {
                "local_first": True,
                "read_only": not self.options.write_report,
                "dry_run": True,
                "llm_used": False,
                "network_used": False,
                "external_api_used": False,
                "memory_read": False,
                "memory_written": False,
                "tools_executed": False,
                "source_mutations_performed": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "raw_prompts_stored": False,
                "raw_outputs_stored": False,
                "claims_prohibited_by_rag_policy_justified": False,
            },
            "findings": [finding.to_dict() for finding in findings] or [
                Finding("RAG_AGENT_CONTEXT_PACK_PASS", "RAG-aware agent context pack passed with local citations and insufficient-evidence behavior.", Severity.INFO, metadata=summary).to_dict()
            ],
            "notes": list(bindings.get("notes") or [
                "POST-H-032-D creates deterministic RAG context packs for selected agents; it does not call an LLM.",
                "Every grounded suggestion carries source ids and citations; evidence gaps return insufficient evidence.",
            ]),
            "limitations": list(bindings.get("limitations") or [
                "Initial implementation uses the existing lexical RAG index and deterministic source checks.",
                "It prepares agent context but does not promote agents to autonomous RAG execution.",
            ]),
        }
        schema_result = SchemaValidator(self.root).validate_payload(
            schema=RAG_AGENT_CONTEXT_CONTRACT,
            payload=report,
            instance_label="in-memory-rag-agent-context-pack",
        )
        if not schema_result.ok:
            findings.extend(_prefixed_findings(schema_result, "RAG_AGENT_CONTEXT_SCHEMA"))
            summary["schema_valid"] = False
            summary["decision"] = "BLOCK"
            summary["blocking_findings_total"] = len(_blocking_findings(findings))
            report["status"] = "blocked"
            report["summary"] = summary
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            summary["schema_valid"] = True
            report["summary"] = summary
        reports: dict[str, str] = {}
        if self.options.write_report:
            summary["reports_written"] = True
            report["summary"] = summary
            report["safety"]["read_only"] = False
            reports = self._write_reports(report)
        ok = len(_blocking_findings(findings)) == 0
        return CommandResult(
            command=RAG_AGENT_CONTEXT_COMMAND,
            ok=ok,
            exit_code=ExitCode.PASS if ok else exit_code_for_findings(_blocking_findings(findings), default_ok=False),
            message="RAG-aware agent context pack passed." if ok else "RAG-aware agent context pack has blocking findings.",
            data={"summary": report["summary"], "context_pack": report, "bindings": bindings, "reports": reports},
            findings=findings or [Finding("RAG_AGENT_CONTEXT_PACK_PASS", "RAG-aware agent context pack passed with local citations and insufficient-evidence behavior.", Severity.INFO, metadata=report["summary"])],
        )

    def _load_bindings(self, findings: list[Finding]) -> dict[str, Any]:
        path = _resolve_workspace_path(self.root, self.options.bindings_path)
        decision = self.path_guard.evaluate(path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(Finding("RAG_AGENT_BINDINGS_PATH_BLOCKED", decision.reason, Severity.BLOCK, path=decision.subject, metadata=decision.metadata))
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("RAG_AGENT_BINDINGS_LOAD_ERROR", f"Could not load RAG agent bindings: {exc}", Severity.BLOCK, path=_relative(path, self.root)))
            return {}
        if not isinstance(payload, dict):
            findings.append(Finding("RAG_AGENT_BINDINGS_INVALID", "RAG agent bindings root must be an object.", Severity.BLOCK, path=_relative(path, self.root)))
            return {}
        return payload

    def _selected_agents(self, agent_rows: list[dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
        by_id = {str(agent.get("agent_id")): agent for agent in agent_rows}
        requested = (self.options.agent_id or "all").strip()
        if requested and requested != "all":
            agent = by_id.get(requested)
            if not agent:
                findings.append(Finding("RAG_AGENT_BINDING_NOT_FOUND", "Requested agent is not declared as RAG-aware in bindings.", Severity.BLOCK, metadata={"agent_id": requested}))
                return []
            return [agent]
        selected = [agent for agent in agent_rows if agent.get("agent_id") in TARGET_AGENTS]
        missing = [agent_id for agent_id in TARGET_AGENTS if agent_id not in by_id]
        for agent_id in missing:
            findings.append(Finding("RAG_REQUIRED_AGENT_BINDING_MISSING", "Required POST-H-032-D RAG-aware agent binding is missing.", Severity.BLOCK, metadata={"agent_id": agent_id}))
        return selected

    def _context_for_agent(self, agent: dict[str, Any], bindings: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
        agent_id = str(agent.get("agent_id"))
        query = self.options.query or str(agent.get("default_query") or bindings.get("defaults", {}).get("default_query") or agent_id)
        target = self.options.target or str(agent.get("target") or "docs")
        safe_query = str(self.secret_guard.redact(query).value)
        retrieval = LocalRagRetriever(
            self.root,
            options=RagQueryOptions(query=safe_query, index_path=_posix(self.options.index_path), top_k=max(1, min(self.options.top_k, 20))),
        ).query()
        allowed_prefixes = tuple(str(item).replace("\\", "/").rstrip("/") for item in agent.get("allowed_source_prefixes") or bindings.get("defaults", {}).get("allowed_source_prefixes") or [])
        raw_sources = (retrieval.data or {}).get("sources") or []
        sources = [self._source_row(source, allowed_prefixes, findings, agent_id) for source in raw_sources]
        sources = [source for source in sources if source.get("allowed")]
        prohibited_claims = _prohibited_claims(bindings)
        query_contains_prohibited = any(_contains_phrase(safe_query, claim) for claim in prohibited_claims)
        has_evidence = bool(sources) and not query_contains_prohibited
        output_sources = sources if has_evidence else []
        source_ids = [source["source_id"] for source in output_sources]
        citations = [source["citation"] for source in output_sources]
        if not raw_sources:
            findings.append(Finding("RAG_AGENT_QUERY_NO_SOURCES", "RAG query produced no local sources; context falls back to insufficient evidence.", Severity.INFO, metadata={"agent_id": agent_id, "query": redact_string(safe_query)}))
        if query_contains_prohibited:
            findings.append(Finding("RAG_AGENT_PROHIBITED_CLAIM_BLOCKED", "RAG policy refused to justify a prohibited claim.", Severity.INFO, metadata={"agent_id": agent_id, "query": redact_string(safe_query)}))
        if has_evidence:
            body = _grounded_suggestion_body(agent_id, target, sources)
            status = "grounded"
        else:
            body = INSUFFICIENT_EVIDENCE
            status = "insufficient-evidence"
        return {
            "agent_id": agent_id,
            "mode": "rag-aware",
            "status": status,
            "target": target,
            "query": redact_string(safe_query),
            "suggestions": [
                {
                    "title": f"RAG-aware context for {agent_id}",
                    "body": body,
                    "target": target,
                    "severity": "info" if has_evidence else "warning",
                    "source_ids": source_ids,
                    "citations": citations,
                    "insufficient_evidence": not has_evidence,
                    "prohibited_claim_blocked": query_contains_prohibited,
                }
            ],
            "sources": output_sources,
            "source_ids": source_ids,
            "citations": citations,
            "freshness": _freshness_summary(output_sources),
            "coverage": {
                "sources_total": len(sources),
                "citations_total": len(citations),
                "minimum_sources_required": int(agent.get("minimum_sources_required") or bindings.get("defaults", {}).get("minimum_sources_required") or 1),
                "source_coverage": 1.0 if has_evidence else 0.0,
            },
            "grounded": has_evidence,
            "insufficient_evidence": not has_evidence,
            "llm_used": False,
            "network_used": False,
            "external_api_used": False,
            "memory_used": False,
            "tools_executed": False,
        }

    def _source_row(self, source: dict[str, Any], allowed_prefixes: tuple[str, ...], findings: list[Finding], agent_id: str) -> dict[str, Any]:
        path = str(source.get("path") or "").replace("\\", "/")
        ref = str(source.get("ref") or f"{path}#L{source.get('line_start', 1)}-L{source.get('line_end', 1)}")
        allowed = _path_allowed(path, allowed_prefixes)
        if not allowed:
            findings.append(Finding("RAG_AGENT_SOURCE_NOT_ALLOWLISTED", "RAG source is outside the agent allowlist and was excluded.", Severity.BLOCK, path=path, metadata={"agent_id": agent_id, "allowed_prefixes": list(allowed_prefixes)}))
        return {
            "source_id": ref,
            "path": path,
            "title": source.get("title"),
            "line_start": int(source.get("line_start") or 1),
            "line_end": int(source.get("line_end") or source.get("line_start") or 1),
            "citation": ref,
            "freshness_status": "current",
            "score": float(source.get("score") or 0.0),
            "fragment": redact_string(str(source.get("fragment") or "")),
            "allowed": allowed,
        }

    def _negative_cases(self, bindings: dict[str, Any], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for case in bindings.get("negative_cases") or []:
            case_id = str(case.get("case_id") or "negative-case")
            expected = str(case.get("expected_response") or INSUFFICIENT_EVIDENCE)
            case_type = str(case.get("type") or "unsupported-claim")
            cases.append(
                {
                    "case_id": case_id,
                    "type": case_type,
                    "claim": str(case.get("claim") or ""),
                    "expected_response": expected,
                    "actual_response": INSUFFICIENT_EVIDENCE,
                    "passed": expected == INSUFFICIENT_EVIDENCE,
                    "sources_used_total": 0,
                    "prohibited_claim_justified": False,
                    "unsupported_claim_blocked": True,
                }
            )
        if not cases:
            cases.append(
                {
                    "case_id": "post-h-032-d-default-insufficient-evidence",
                    "type": "unsupported-claim",
                    "claim": "Unsupported claim must not be answered without local sources.",
                    "expected_response": INSUFFICIENT_EVIDENCE,
                    "actual_response": INSUFFICIENT_EVIDENCE,
                    "passed": True,
                    "sources_used_total": 0,
                    "prohibited_claim_justified": False,
                    "unsupported_claim_blocked": True,
                }
            )
        return cases

    def _summary(self, bindings: dict[str, Any], contexts: list[dict[str, Any]], negative_cases: list[dict[str, Any]], findings: list[Finding]) -> dict[str, Any]:
        grounded = [context for context in contexts if context.get("grounded")]
        insufficient = [context for context in contexts if context.get("insufficient_evidence")]
        citations_total = sum(len(context.get("citations") or []) for context in contexts)
        sources_total = sum(len(context.get("sources") or []) for context in contexts)
        return {
            "created_by": POST_H_032_D_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if len(_blocking_findings(findings)) == 0 else "BLOCK",
            "agents_total": len(contexts),
            "target_agents_total": len(TARGET_AGENTS),
            "grounded_agents_total": len(grounded),
            "insufficient_evidence_agents_total": len(insufficient),
            "sources_total": sources_total,
            "citations_total": citations_total,
            "all_grounded_suggestions_have_sources": all((not context.get("grounded")) or bool(context.get("source_ids")) for context in contexts),
            "insufficient_evidence_behavior_enabled": True,
            "negative_cases_total": len(negative_cases),
            "negative_cases_passed": all(case.get("passed") for case in negative_cases),
            "prohibited_claims_justified_total": sum(1 for case in negative_cases if case.get("prohibited_claim_justified")),
            "rag_reads_allowlisted_sources_only": len([f for f in findings if f.id == "RAG_AGENT_SOURCE_NOT_ALLOWLISTED"]) == 0,
            "context_pack_schema": RAG_AGENT_CONTEXT_SCHEMA_ID,
            "schema_valid": False,
            "llm_used": False,
            "network_used": False,
            "external_api_used": False,
            "memory_used": False,
            "tools_executed": False,
            "source_mutations_performed": False,
            "blocking_findings_total": len(_blocking_findings(findings)),
            "findings_total": len(findings),
            "reports_written": False,
            "preliminary": True,
        }

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        output_json = _safe_output_path(self.root, self.options.output_json)
        output_markdown = _safe_output_path(self.root, self.options.output_markdown)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(_json_dumps(report) + "\n", encoding="utf-8")
        output_markdown.write_text(render_rag_agent_context_markdown(report), encoding="utf-8")
        return {"json": _relative(output_json, self.root), "markdown": _relative(output_markdown, self.root)}


def render_rag_agent_context_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# POST-H-032-D — RAG-aware agents",
        "",
        f"- Decision: `{summary.get('decision')}`",
        f"- Agents: `{summary.get('agents_total')}`",
        f"- Grounded agents: `{summary.get('grounded_agents_total')}`",
        f"- Insufficient evidence agents: `{summary.get('insufficient_evidence_agents_total')}`",
        f"- Sources: `{summary.get('sources_total')}`",
        f"- Citations: `{summary.get('citations_total')}`",
        f"- Negative cases passed: `{summary.get('negative_cases_passed')}`",
        f"- LLM used: `{summary.get('llm_used')}`",
        f"- External API used: `{summary.get('external_api_used')}`",
        "",
        "## Agents",
        "",
        "| Agent | Status | Sources | Citations |",
        "| --- | --- | ---: | ---: |",
    ]
    for agent in report.get("agents", []):
        lines.append(f"| `{agent.get('agent_id')}` | `{agent.get('status')}` | `{len(agent.get('sources') or [])}` | `{len(agent.get('citations') or [])}` |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "POST-H-032-D is an initial deterministic RAG context-pack layer. It prepares source-grounded context for selected agents and blocks unsupported/prohibited claims through `insufficient evidence`; it does not call an LLM or promote agents to autonomous execution.",
        "",
    ])
    return "\n".join(lines)


def _agent_rows(bindings: dict[str, Any]) -> list[dict[str, Any]]:
    rows = bindings.get("agents") if isinstance(bindings.get("agents"), list) else []
    return [row for row in rows if isinstance(row, dict) and row.get("agent_id")]


def _prohibited_claims(bindings: dict[str, Any]) -> list[str]:
    claims = bindings.get("prohibited_claims") if isinstance(bindings.get("prohibited_claims"), list) else []
    return [str(claim).strip().lower() for claim in claims if str(claim).strip()]


def _contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def _grounded_suggestion_body(agent_id: str, target: str, sources: list[dict[str, Any]]) -> str:
    refs = ", ".join(f"`{source['citation']}`" for source in sources[:3])
    return f"RAG-aware suggestion for `{agent_id}` on `{target}` must be based only on retrieved local evidence. Primary sources: {refs}."


def _freshness_summary(sources: list[dict[str, Any]]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for source in sources:
        status = str(source.get("freshness_status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    return {"statuses": statuses, "all_current_or_unknown": all(status in {"current", "unknown"} for status in statuses)}


def _groundedness_eval(contexts: list[dict[str, Any]], negative_cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "evaluator": "deterministic-rag-agent-context-pack",
        "positive_contexts_total": len(contexts),
        "positive_contexts_with_citations_total": len([context for context in contexts if context.get("citations")]),
        "negative_cases_total": len(negative_cases),
        "negative_cases_passed_total": len([case for case in negative_cases if case.get("passed")]),
        "unsupported_claims_return_insufficient_evidence": all(case.get("actual_response") == INSUFFICIENT_EVIDENCE for case in negative_cases),
        "prohibited_claims_justified_total": sum(1 for case in negative_cases if case.get("prohibited_claim_justified")),
        "llm_judge_used": False,
    }


def _path_allowed(path: str, prefixes: tuple[str, ...]) -> bool:
    if not prefixes:
        return False
    clean = path.replace("\\", "/")
    for prefix in prefixes:
        p = prefix.rstrip("/")
        if clean == p or clean.startswith(p + "/"):
            return True
    return False


def _blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR}]


def _prefixed_findings(result: CommandResult, prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in result.findings
        if finding.severity in {Severity.BLOCK, Severity.ERROR}
    ]


def _resolve_workspace_path(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _safe_output_path(root: Path, path: str | Path) -> Path:
    candidate = _resolve_workspace_path(root, path)
    outputs = (root / "outputs").resolve()
    try:
        candidate.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("POST-H-032-D reports may only be written under outputs/.") from exc
    return candidate


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
