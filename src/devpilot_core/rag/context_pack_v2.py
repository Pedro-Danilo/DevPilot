from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.agents.role_bindings import AgentRoleBindingCatalog
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.modeling.budget import ContextBudget, estimate_text_tokens
from devpilot_core.policy import SecretGuard, redact_string
from devpilot_core.schemas.validator import SchemaValidator

POLICY_PATH = Path(".devpilot/rag/context_pack_v2_policy.json")
INDEX_PATH = Path(".devpilot/rag/docs_index.json")
SOURCE_REGISTRY_PATH = Path(".devpilot/docs_governance/source_registry.json")
SCHEMA_ID = "SCHEMA-DEVPL-CONTEXT-PACK-V2"
SCHEMA_CONTRACT = "ContextPackV2"
INSUFFICIENT_EVIDENCE = "insufficient evidence"
_TOKEN_RE = re.compile(r"[\wáéíóúüñÁÉÍÓÚÜÑ]{3,}", re.UNICODE)
_UPDATED_RE = re.compile(r"^updated:\s*[\"']?([^\"'\s]+)", re.MULTILINE)

@dataclass(frozen=True)
class ContextPackV2Options:
    step_id: str = "requirements"
    query: str | None = None
    top_k: int | None = None
    changed_paths: tuple[str, ...] = ()
    as_of_date: date | None = None

class ContextPackV2Builder:
    """Build a bounded, provenance-complete local context pack for one Guided SDLC step.

    GSDLC-07-B does not call a model. It turns the existing lexical index into a
    policy-filtered input contract that later agent workflows may consume.
    """
    def __init__(self, root: Path, options: ContextPackV2Options | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ContextPackV2Options()
        self.secret_guard = SecretGuard()

    def build(self) -> CommandResult:
        findings: list[Finding] = []
        try:
            policy = _load_json(self.root / POLICY_PATH)
            index = _load_json(self.root / INDEX_PATH)
            registry = _load_json(self.root / SOURCE_REGISTRY_PATH)
        except Exception as exc:
            return CommandResult(command="rag context-pack-v2", ok=False, exit_code=ExitCode.BLOCK, message="ContextPack v2 authority could not be loaded.", data={}, findings=[Finding("CONTEXT_PACK_V2_AUTHORITY_LOAD_BLOCK", str(exc), Severity.BLOCK)])

        catalog = AgentRoleBindingCatalog(self.root)
        binding = catalog.binding(self.options.step_id)
        if binding is None:
            return _blocked("CONTEXT_PACK_V2_STEP_UNKNOWN", f"Unknown Guided SDLC step: {self.options.step_id}")
        descriptor = catalog.descriptor_for_step(self.options.step_id)
        role_id = None if descriptor is None else descriptor.get("agent_role_id")
        runtime_agent_id = None if descriptor is None else descriptor.get("runtime_agent_id")
        required_caps = [] if descriptor is None else list(descriptor.get("required_model_capabilities") or [])
        query = self.options.query or _default_query(self.options.step_id, role_id, binding.allowed_artifacts)
        safe_query = str(self.secret_guard.redact(query).value).strip()
        if not safe_query:
            return _blocked("CONTEXT_PACK_V2_QUERY_EMPTY", "ContextPack v2 requires a non-empty query.")

        registry_map = {str(row.get("path") or "").replace("\\", "/"): row for row in registry.get("documents", []) if isinstance(row, dict)}
        selection = dict(policy.get("selection") or {})
        scope = dict(policy.get("source_scope") or {})
        top_k = max(1, min(int(self.options.top_k or selection.get("top_k_default") or 5), int(selection.get("top_k_max") or 8)))
        as_of = self.options.as_of_date or datetime.now(timezone.utc).date()
        changed = {str(p).replace("\\", "/") for p in self.options.changed_paths}
        tokens = _tokens(safe_query)
        ranked: list[dict[str, Any]] = []
        rejected = {"unregistered": 0, "scope": 0, "runtime": 0, "stale": 0, "missing": 0}

        for chunk in index.get("chunks", []):
            if not isinstance(chunk, dict) or not isinstance(chunk.get("source"), dict):
                continue
            src = chunk["source"]
            path = str(src.get("path") or "").replace("\\", "/")
            if not _scope_allowed(path, scope):
                rejected["runtime" if _runtime_path(path, scope) else "scope"] += 1
                continue
            reg = registry_map.get(path)
            if reg is None or str(reg.get("lifecycle") or "active") not in set(selection.get("approved_registry_lifecycle") or ["active"]):
                rejected["unregistered"] += 1
                continue
            file_path = self.root / path
            if not file_path.is_file():
                rejected["missing"] += 1
                continue
            freshness = _freshness(file_path, chunk, as_of, int(selection.get("max_age_days") or 730))
            if freshness["status"] == "stale" and selection.get("stale_source_action") == "exclude":
                rejected["stale"] += 1
                continue
            score, matched = _score(chunk, tokens)
            diff_priority = path in changed
            if diff_priority:
                score += float(selection.get("diff_first_boost") or 3.0)
            if score <= 0:
                continue
            fragment = redact_string(str(chunk.get("fragment") or ""))
            content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            ref = f"{path}#L{int(src.get('line_start') or 1)}-L{int(src.get('line_end') or 1)}"
            ranked.append({
                "source_id": str(chunk.get("chunk_id") or hashlib.sha256(ref.encode()).hexdigest()[:16]),
                "path": path,
                "title": src.get("title"),
                "content_sha256": content_hash,
                "chunk_sha256": str(chunk.get("hash_sha256") or hashlib.sha256(fragment.encode()).hexdigest()),
                "trust_tag": "approved-local",
                "freshness": freshness,
                "selection_reason": ("diff-first; " if diff_priority else "") + "lexical match: " + ", ".join(matched[:8]),
                "score": round(score, 6),
                "citation_ref": ref,
                "estimated_tokens": estimate_text_tokens(fragment),
                "fragment": fragment[:1200],
                "diff_priority": diff_priority,
            })
        ranked.sort(key=lambda x: (-int(x["diff_priority"]), -float(x["score"]), x["path"], x["citation_ref"]))
        candidates = ranked[: max(top_k * 3, top_k)]

        budget_cfg = dict(policy.get("budget") or {})
        budget = ContextBudget(**{k:int(v) for k,v in budget_cfg.items()})
        requested_tokens = sum(int(x["estimated_tokens"]) for x in candidates)
        diff_tokens = sum(int(x["estimated_tokens"]) for x in candidates if x["diff_priority"]) or None
        retrieval_target = min(requested_tokens, budget.retrieval_budget_tokens)
        plan = budget.plan(requested_input_tokens=requested_tokens, invariant_min_tokens=1 if candidates else 0, diff_first_tokens=diff_tokens, retrieval_tokens=retrieval_target)
        selected: list[dict[str, Any]] = []
        used = 0
        for source in candidates:
            if len(selected) >= top_k:
                break
            tokens_here = int(source["estimated_tokens"])
            if used + tokens_here > plan.selected_input_tokens and selected:
                continue
            if tokens_here > plan.selected_input_tokens and not selected:
                trimmed = dict(source)
                max_chars = max(80, plan.selected_input_tokens * 4)
                trimmed["fragment"] = str(source["fragment"])[:max_chars]
                trimmed["estimated_tokens"] = estimate_text_tokens(trimmed["fragment"])
                source = trimmed
                tokens_here = int(source["estimated_tokens"])
            selected.append(source); used += tokens_here

        minimum = int(selection.get("minimum_sources_required") or 1)
        insufficient = len(selected) < minimum or not plan.allowed
        status = "insufficient-evidence" if insufficient else "grounded"
        citations = [{"citation_id": f"C{i+1}", "source_id": s["source_id"], "ref": s["citation_ref"], "content_sha256": s["content_sha256"]} for i,s in enumerate(selected)]
        stages = [
            {"stage":"indexed","chunks_total":len(index.get("chunks", []))},
            {"stage":"policy-filtered","candidates_total":len(ranked),"rejected":rejected},
            {"stage":"budget-ranked","candidate_preview_total":len(candidates),"strategy":plan.strategy},
            {"stage":"sealed","selected_total":len(selected),"selected_tokens":used,"top_k":top_k},
        ]
        pack = {
            "schema_version":"2.0","schema_id":SCHEMA_ID,"pack_id":"pending","created_by":"DEVPL-GSDLC-07-B","status":status,"step_id":self.options.step_id,
            "agent":{"role_id":role_id,"runtime_agent_id":runtime_agent_id,"required_model_capabilities":required_caps},"query":safe_query,
            "selection_policy":{"policy_id":policy.get("policy_id"),"policy_version":policy.get("schema_version"),"mode":selection.get("mode"),"top_k":top_k,"minimum_sources_required":minimum,"diff_first":bool(changed)},
            "budget":{"context_budget":budget.to_dict(),"plan":plan.to_dict(),"requested_tokens":requested_tokens,"selected_tokens":used,"trimmed":used < requested_tokens},
            "candidate_sources":candidates,"sources":selected,"citations":citations,
            "provenance":{"pack_sha256":"0"*64,"source_hash_parity":all((self.root/s["path"]).is_file() and hashlib.sha256((self.root/s["path"]).read_bytes()).hexdigest()==s["content_sha256"] for s in selected),"citation_source_parity":{c["source_id"] for c in citations}=={s["source_id"] for s in selected},"selection_stages":stages,"generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds")},
            "safety":{"local_first":True,"network_used":False,"external_api_used":False,"embeddings_used":False,"llm_used":False,"secret_guard_used":True,"runtime_sources_excluded":rejected["runtime"] >= 0,"unregistered_sources_excluded":True,"raw_secrets_stored":False,"tools_executed":False,"source_mutations_performed":False},
            "limitations":["v2.0 initial uses deterministic lexical retrieval; semantic embeddings remain opt-in future work.","07-B prepares grounded context only; it does not execute an agent or mutate artifacts."]
        }
        canonical = json.loads(json.dumps(pack)); canonical["provenance"]["pack_sha256"] = "0"*64; canonical["provenance"].pop("generated_at_utc",None)
        digest = hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
        pack["pack_id"] = f"ctx2-{self.options.step_id}-{digest[:12]}"; pack["provenance"]["pack_sha256"] = digest
        schema_result = SchemaValidator(self.root).validate_payload(schema=SCHEMA_CONTRACT,payload=pack,instance_label="in-memory-context-pack-v2")
        if not schema_result.ok:
            return CommandResult(command="rag context-pack-v2", ok=False, exit_code=ExitCode.BLOCK, message="ContextPack v2 failed schema validation.", data={"context_pack":pack}, findings=[Finding("CONTEXT_PACK_V2_SCHEMA_BLOCK", "ContextPack v2 schema validation failed.", Severity.BLOCK, metadata={"findings":[f.to_dict() for f in schema_result.findings]})])
        if insufficient:
            findings.append(Finding("CONTEXT_PACK_V2_INSUFFICIENT_EVIDENCE", INSUFFICIENT_EVIDENCE, Severity.WARNING, metadata={"selected_sources":len(selected),"minimum_sources_required":minimum}))
        else:
            findings.append(Finding("CONTEXT_PACK_V2_GROUNDED_PASS", "ContextPack v2 is grounded, cited and within budget.", Severity.INFO, metadata={"selected_sources":len(selected),"selected_tokens":used,"strategy":plan.strategy}))
        return CommandResult(command="rag context-pack-v2", ok=True, exit_code=ExitCode.PASS, message="ContextPack v2 prepared." if not insufficient else "ContextPack v2 returned insufficient evidence without inventing context.", data={"summary":{"status":status,"step_id":self.options.step_id,"sources_total":len(selected),"candidate_sources_total":len(candidates),"citations_total":len(citations),"budget_strategy":plan.strategy,"selected_tokens":used,"top_k":top_k,"insufficient_evidence":insufficient,"source_hash_parity":pack["provenance"]["source_hash_parity"],"citation_source_parity":pack["provenance"]["citation_source_parity"],"network_used":False,"external_api_used":False,"embeddings_used":False,"source_mutations_performed":False},"context_pack":pack}, findings=findings)


def _default_query(step_id: str, role_id: str | None, artifacts: Iterable[str]) -> str:
    return " ".join(["DevPilot", step_id, role_id or "none", *[str(x) for x in artifacts], "requirements architecture security quality provenance"])

def _load_json(path: Path) -> dict[str, Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict): raise ValueError(f"expected object: {path}")
    return payload

def _tokens(text: str) -> dict[str,int]:
    result: dict[str,int]={}
    for token in _TOKEN_RE.findall(text.lower()): result[token]=result.get(token,0)+1
    return result

def _score(chunk: dict[str,Any], query_tokens: dict[str,int]) -> tuple[float,list[str]]:
    counts=chunk.get("tokens") if isinstance(chunk.get("tokens"),dict) else {}
    matched=[]; score=0.0
    for token,q in query_tokens.items():
        c=int(counts.get(token,0) or 0)
        if c: matched.append(token); score += (1.0 + min(c,8)/4.0)*q
    return score, sorted(matched)

def _runtime_path(path: str, scope: dict[str,Any]) -> bool:
    parts=set(path.replace("\\","/").split("/")); name=Path(path).name
    return bool(parts & set(scope.get("denied_parts") or [])) or name in set(scope.get("denied_file_names") or [])

def _scope_allowed(path: str, scope: dict[str,Any]) -> bool:
    if _runtime_path(path,scope): return False
    if Path(path).suffix.lower() not in set(scope.get("allowed_suffixes") or []): return False
    return any(path == p or path.startswith(p.rstrip("/")+"/") for p in scope.get("allowed_prefixes") or [])

def _freshness(file_path: Path, chunk: dict[str,Any], as_of: date, max_age_days: int) -> dict[str,Any]:
    fragment=str(chunk.get("fragment") or "")
    m=_UPDATED_RE.search(fragment)
    updated=None
    if m:
        try: updated=date.fromisoformat(m.group(1)[:10])
        except ValueError: updated=None
    if updated is None:
        return {"status":"unknown","updated":None,"age_days":None,"max_age_days":max_age_days}
    age=max(0,(as_of-updated).days)
    return {"status":"fresh" if age<=max_age_days else "stale","updated":updated.isoformat(),"age_days":age,"max_age_days":max_age_days}

def _blocked(fid: str, message: str) -> CommandResult:
    return CommandResult(command="rag context-pack-v2",ok=False,exit_code=ExitCode.BLOCK,message=message,data={"summary":{"status":"blocked"}},findings=[Finding(fid,message,Severity.BLOCK)])
