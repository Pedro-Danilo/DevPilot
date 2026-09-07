from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEffect, SecretGuard
from devpilot_core.story_execution import StoryExecutionStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode("utf-8"))


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


class CodeWorkbenchApplicationService:
    """GSDLC-09-B bounded manual code viewer/editor boundary.

    All authoring operations persist SourceDraftBuffer records under outputs/.
    There is intentionally no source-apply method in this service. 09-C owns
    SourceChangePlan, approval and atomic source mutation.
    """

    def __init__(self, platform_root: Path, *, context_resolver) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.context_resolver = context_resolver
        self.policy = json.loads((self.platform_root / ".devpilot/code_workbench/source_policy.json").read_text(encoding="utf-8"))
        self.allowed_extensions = {str(x).lower() for x in self.policy["allowed_extensions"]}
        self.denied_dirs = {str(x) for x in self.policy["denied_directory_names"]}
        self.denied_prefixes = tuple(str(x).lower() for x in self.policy["denied_file_prefixes"])
        self.max_bytes = int(self.policy["maximum_inline_bytes"])
        self.max_files = int(self.policy["maximum_discovery_files"])
        self.max_depth = int(self.policy["maximum_discovery_depth"])

    def status(self) -> CommandResult:
        context, failure = self._context("story code status")
        if failure: return failure
        assert context is not None
        story = StoryExecutionStore(context.effective_workspace_root, workspace_id=str(context.active_workspace_id)).current_story_projection()
        return self._pass("story code status", "Code Workbench status projected from server-authoritative workspace/story context.", {
            "workspace_id": context.active_workspace_id,
            "story": story,
            "source_policy": self._safe_policy(),
            "authoring": {"operations":["CREATE","EDIT","RENAME"],"apply_enabled":False,"runtime_only":True},
            "ui_workspace_context": context.summary(),
        })

    def list_sources(self) -> CommandResult:
        context, failure = self._context("story code sources list")
        if failure: return failure
        assert context is not None
        root = context.effective_workspace_root
        nodes: list[dict[str, Any]] = []
        discovered = 0
        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            rel_dir = current_path.relative_to(root)
            if len(rel_dir.parts) > self.max_depth:
                dirs[:] = []; continue
            dirs[:] = sorted([d for d in dirs if d not in self.denied_dirs and not d.startswith(".") and not self._reparse(current_path / d)])
            for name in sorted(files):
                if discovered >= self.max_files: break
                candidate = current_path / name
                if self._blocked_name(name) or self._reparse(candidate): continue
                rel = candidate.relative_to(root).as_posix()
                if candidate.suffix.lower() not in self.allowed_extensions: continue
                try: size = candidate.stat().st_size
                except OSError: continue
                discovered += 1
                nodes.append({"source_id": self._source_id(rel), "relative_path": rel, "name": name, "extension": candidate.suffix.lower(), "size_bytes": size, "readable": size <= self.max_bytes, "language_hint": self._language(candidate.suffix.lower())})
        return self._pass("story code sources list", "Bounded source tree indexed without following hidden/reparse/runtime paths.", {
            "workspace_id": context.active_workspace_id, "sources": nodes,
            "summary": {"sources_total":len(nodes),"maximum_inline_bytes":self.max_bytes,"source_mutations_performed":False,"symlink_following":False},
            "source_policy": self._safe_policy(),
        })

    def read_source(self, source_id: str) -> CommandResult:
        context, failure = self._context("story code source read")
        if failure: return failure
        assert context is not None
        resolved = self._resolve_source(context.effective_workspace_root, source_id)
        if isinstance(resolved, CommandResult): return resolved
        path, rel = resolved
        raw, error = self._safe_read(path, rel)
        if error: return error
        assert raw is not None
        try: text = raw.decode("utf-8-sig")
        except UnicodeDecodeError: return self._block("story code source read", "GSDLC09B_ENCODING_BLOCK", "Only UTF-8 source files are supported.", path=rel)
        return self._pass("story code source read", "Source read through opaque bounded identifier.", {
            "source": {"source_id":source_id,"relative_path":rel,"sha256":_sha_bytes(raw),"content":text,"size_bytes":len(raw),"language_hint":self._language(path.suffix.lower()),"read_only_source":True},
            "safety":{"source_mutations_performed":False,"runtime_only":False,"network_used":False,"external_api_used":False},
        })

    def save_draft(self, *, operation: str, content: str, target_path: str, source_id: str | None, expected_source_sha256: str | None, expected_revision_sha256: str | None, actor: str, actor_role: str) -> CommandResult:
        command = "story code draft save"
        context, failure = self._context(command)
        if failure: return failure
        assert context is not None
        op = str(operation).upper().strip()
        if op not in {"CREATE","EDIT","RENAME"}: return self._block(command,"GSDLC09B_OPERATION_BLOCK","Operation must be CREATE, EDIT or RENAME.")
        if actor_role not in {"owner","developer"}: return self._block(command,"GSDLC09B_ROLE_BLOCK","Manual code authoring requires owner or developer role.")
        target = self._target(context.effective_workspace_root, target_path, command=command)
        if isinstance(target, CommandResult): return target
        target_abs, target_rel = target
        source: dict[str, Any] = {"source_id":None,"relative_path":None,"sha256":None}
        source_abs: Path | None = None
        if op in {"EDIT","RENAME"}:
            if not source_id or not expected_source_sha256: return self._block(command,"GSDLC09B_SOURCE_PREIMAGE_REQUIRED_BLOCK","EDIT/RENAME require opaque source_id and expected source SHA-256.")
            resolved = self._resolve_source(context.effective_workspace_root, source_id)
            if isinstance(resolved, CommandResult): return resolved
            source_abs, source_rel = resolved
            raw, error = self._safe_read(source_abs, source_rel)
            if error: return error
            actual = _sha_bytes(raw or b"")
            if actual != expected_source_sha256: return self._conflict(command,"GSDLC09B_SOURCE_PREIMAGE_CONFLICT","Source changed before draft save.", path=source_rel, metadata={"expected":expected_source_sha256,"actual":actual})
            source = {"source_id":source_id,"relative_path":source_rel,"sha256":actual}
            if op == "EDIT" and target_rel != source_rel: return self._block(command,"GSDLC09B_EDIT_TARGET_BLOCK","EDIT target path must equal the selected source path.", path=target_rel)
            if op == "RENAME" and target_rel == source_rel: return self._block(command,"GSDLC09B_RENAME_NOOP_BLOCK","RENAME requires a different allowlisted target path.", path=target_rel)
        else:
            if source_id or expected_source_sha256: return self._block(command,"GSDLC09B_CREATE_SOURCE_BLOCK","CREATE must not supply an existing source preimage.")
        if op in {"CREATE","RENAME"} and target_abs.exists(): return self._conflict(command,"GSDLC09B_TARGET_EXISTS_CONFLICT","Draft target already exists; source remains unchanged.", path=target_rel)
        if op == "RENAME" and source_abs is not None:
            raw = source_abs.read_bytes()
            if not content: content = raw.decode("utf-8-sig")
        secret = SecretGuard(context.effective_workspace_root).scan_text(content, subject=target_rel)
        if secret.effect is PolicyEffect.BLOCK: return self._block(command,"GSDLC09B_SECRET_DRAFT_BLOCK","Secret-like content is not allowed in SourceDraftBuffer.", path=target_rel)
        if len(content.encode("utf-8")) > self.max_bytes: return self._block(command,"GSDLC09B_DRAFT_OVERSIZE_BLOCK","Draft exceeds bounded editor size.", path=target_rel)
        store_dir = self._draft_root(context.effective_workspace_root, str(context.active_workspace_id))
        stable = {"workspace_id":context.active_workspace_id,"operation":op,"source":source,"target_path":target_rel}
        draft_id = "source-draft-" + _canonical_sha(stable)[:24]
        path = store_dir / f"{draft_id}.json"
        existing = self._load_json(path)
        current_revision = str((existing or {}).get("revision_sha256") or "") or None
        expected_revision = str(expected_revision_sha256 or "").strip() or None
        if current_revision != expected_revision: return self._conflict(command,"GSDLC09B_DRAFT_REVISION_CONFLICT","Draft revision is stale; refresh before saving.", metadata={"expected":expected_revision,"current":current_revision})
        now = _now(); content_sha = _sha_text(content)
        base = {
            "schema_id":"SCHEMA-DEVPL-GSDLC-09-B-SOURCE-DRAFT-BUFFER-V1","schema_version":"1.0.0","draft_id":draft_id,
            "workspace_id":str(context.active_workspace_id),"story_execution_id":self._story_execution_id(context.effective_workspace_root,str(context.active_workspace_id)),
            "operation":op,"source":source,"target_path":target_rel,"content":content,"content_sha256":content_sha,"status":"DRAFT",
            "created_at_utc":str((existing or {}).get("created_at_utc") or now),"updated_at_utc":now,"actor":actor,"actor_role":actor_role,
            "safety":{"source_mutations_performed":False,"apply_enabled":False,"shell_enabled":False,"path_guard_passed":True,"secret_scan_passed":True,"runtime_only":True,"network_used":False,"external_api_used":False},
        }
        base["revision_sha256"] = _canonical_sha({k:v for k,v in base.items() if k!="revision_sha256"})
        store_dir.mkdir(parents=True, exist_ok=True); self._atomic_json(path, base)
        return self._pass(command,"SourceDraftBuffer persisted in runtime state; workspace source was not modified.",{"draft":base,"source_mutations_performed":False})

    def get_draft(self, draft_id: str) -> CommandResult:
        context, failure = self._context("story code draft get")
        if failure: return failure
        assert context is not None
        path = self._draft_path(context.effective_workspace_root,str(context.active_workspace_id),draft_id)
        if isinstance(path,CommandResult): return path
        payload=self._load_json(path)
        if payload is None: return self._block("story code draft get","GSDLC09B_DRAFT_MISSING_BLOCK","SourceDraftBuffer does not exist.")
        return self._pass("story code draft get","SourceDraftBuffer loaded from runtime state.",{"draft":payload})

    def recheck_draft(self, draft_id: str) -> CommandResult:
        command="story code draft recheck"
        context, failure=self._context(command)
        if failure:return failure
        assert context is not None
        path=self._draft_path(context.effective_workspace_root,str(context.active_workspace_id),draft_id)
        if isinstance(path,CommandResult):return path
        draft=self._load_json(path)
        if draft is None:return self._block(command,"GSDLC09B_DRAFT_MISSING_BLOCK","SourceDraftBuffer does not exist.")
        op=str(draft.get("operation")); target=self._target(context.effective_workspace_root,str(draft.get("target_path") or ""),command=command)
        if isinstance(target,CommandResult):return target
        target_abs,target_rel=target; reasons=[]
        source=dict(draft.get("source") or {})
        if op in {"EDIT","RENAME"}:
            source_id=str(source.get("source_id") or "")
            resolved=self._resolve_source(context.effective_workspace_root,source_id)
            if isinstance(resolved,CommandResult): reasons.append("source-missing-or-no-longer-allowlisted")
            else:
                source_abs,source_rel=resolved
                try: actual=_sha_bytes(source_abs.read_bytes())
                except OSError: actual=""
                if actual!=str(source.get("sha256") or ""): reasons.append("source-preimage-changed")
        if op in {"CREATE","RENAME"} and target_abs.exists(): reasons.append("target-now-exists")
        status="CONFLICT" if reasons else "DRAFT"
        draft["status"]=status; draft["updated_at_utc"]=_now()
        draft["revision_sha256"]=_canonical_sha({k:v for k,v in draft.items() if k!="revision_sha256"})
        self._atomic_json(path,draft)
        if reasons:return self._conflict(command,"GSDLC09B_EXTERNAL_EDIT_CONFLICT","External source/target change invalidated the draft preimage.",path=target_rel,metadata={"reasons":reasons,"draft":draft})
        return self._pass(command,"Draft preimage remains valid; source is still unchanged.",{"draft":draft,"reasons":[],"source_mutations_performed":False})

    def discard_draft(self, draft_id: str, *, expected_revision_sha256: str, actor_role: str) -> CommandResult:
        command="story code draft discard"
        context,failure=self._context(command)
        if failure:return failure
        assert context is not None
        if actor_role not in {"owner","developer"}:return self._block(command,"GSDLC09B_ROLE_BLOCK","Manual code authoring requires owner or developer role.")
        path=self._draft_path(context.effective_workspace_root,str(context.active_workspace_id),draft_id)
        if isinstance(path,CommandResult):return path
        draft=self._load_json(path)
        if draft is None:return self._pass(command,"Draft already absent; discard is idempotent.",{"discarded":False,"source_mutations_performed":False})
        if str(draft.get("revision_sha256") or "")!=str(expected_revision_sha256):return self._conflict(command,"GSDLC09B_DRAFT_REVISION_CONFLICT","Draft revision is stale; discard rejected.")
        path.unlink()
        return self._pass(command,"Runtime SourceDraftBuffer discarded; source remained unchanged.",{"discarded":True,"source_mutations_performed":False})

    def _context(self, command: str):
        context=self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or not context.active_workspace_root:
            return None,self._block(command,"GSDLC09B_PROJECT_CONTEXT_BLOCK","Code Workbench requires active server-validated project context.")
        return context,None

    def _safe_policy(self)->dict[str,Any]:
        return {k:self.policy[k] for k in ("policy_id","status","allowed_extensions","maximum_inline_bytes","allow_create","allow_edit","allow_rename","apply_enabled","shell_enabled","symlink_following")}

    def _source_id(self, rel:str)->str:return "source-"+hashlib.sha256(rel.encode("utf-8")).hexdigest()[:24]
    def _blocked_name(self,name:str)->bool:
        lower=name.lower(); return name.startswith(".") or any(lower.startswith(p) for p in self.denied_prefixes)
    def _reparse(self,path:Path)->bool:
        try:
            st=path.lstat()
            return stat.S_ISLNK(st.st_mode) or bool(getattr(st,"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0))
        except OSError:return True
    def _language(self,suffix:str)->str:
        return {".py":"Python",".pyi":"Python",".ts":"TypeScript",".tsx":"TSX",".js":"JavaScript",".jsx":"JSX",".css":"CSS",".html":"HTML",".json":"JSON",".toml":"TOML",".yaml":"YAML",".yml":"YAML",".sql":"SQL"}.get(suffix,"Text")

    def _all_sources(self,root:Path):
        result={}
        listed=self.list_sources()
        if not listed.ok:return result
        for item in listed.data["sources"]:result[str(item["source_id"])]=str(item["relative_path"])
        return result
    def _resolve_source(self,root:Path,source_id:str):
        rel=self._all_sources(root).get(str(source_id))
        if not rel:return self._block("story code source resolve","GSDLC09B_SOURCE_ID_BLOCK","Opaque source identifier is unknown or no longer allowlisted.")
        path=(root/Path(rel)).resolve()
        try:path.relative_to(root)
        except ValueError:return self._block("story code source resolve","GSDLC09B_PATH_ESCAPE_BLOCK","Resolved source escaped workspace root.",path=rel)
        if self._reparse(path):return self._block("story code source resolve","GSDLC09B_REPARSE_BLOCK","Symlink/reparse sources are not allowed.",path=rel)
        return path,rel
    def _target(self,root:Path,raw:str,*,command:str):
        normalized=str(raw or "").replace("\\","/").strip().lstrip("./") if str(raw or "").startswith("./") else str(raw or "").replace("\\","/").strip()
        rel=Path(normalized)
        if not normalized or rel.is_absolute() or ".." in rel.parts or any(part.startswith(".") for part in rel.parts) or any(part in self.denied_dirs for part in rel.parts) or self._blocked_name(rel.name):
            return self._block(command,"GSDLC09B_PATH_ESCAPE_BLOCK","Target path is hidden, denied, absolute or traverses outside workspace.",path=normalized)
        if rel.suffix.lower() not in self.allowed_extensions:return self._block(command,"GSDLC09B_EXTENSION_BLOCK","Target extension is not allowlisted by project source policy.",path=normalized)
        target=(root/rel).resolve()
        try:target.relative_to(root)
        except ValueError:return self._block(command,"GSDLC09B_PATH_ESCAPE_BLOCK","Target path escapes workspace root.",path=normalized)
        parent=target.parent
        probe=parent
        while probe!=root and probe.exists():
            if self._reparse(probe):return self._block(command,"GSDLC09B_REPARSE_BLOCK","Target parent traverses symlink/reparse point.",path=normalized)
            probe=probe.parent
        return target,rel.as_posix()
    def _safe_read(self,path:Path,rel:str):
        try:
            if self._reparse(path):return None,self._block("story code source read","GSDLC09B_REPARSE_BLOCK","Symlink/reparse sources are blocked.",path=rel)
            if path.stat().st_size>self.max_bytes:return None,self._block("story code source read","GSDLC09B_OVERSIZE_BLOCK","Source exceeds bounded editor size.",path=rel)
            with path.open("rb") as f:raw=f.read(self.max_bytes+1)
        except OSError:return None,self._block("story code source read","GSDLC09B_SOURCE_READ_BLOCK","Source could not be read safely.",path=rel)
        if len(raw)>self.max_bytes:return None,self._block("story code source read","GSDLC09B_OVERSIZE_BLOCK","Source exceeds bounded editor size.",path=rel)
        if b"\x00" in raw:return None,self._block("story code source read","GSDLC09B_BINARY_BLOCK","Binary-like source is blocked.",path=rel)
        return raw,None
    def _draft_root(self,root:Path,workspace_id:str)->Path:
        safe="".join(c if c.isalnum() or c in "-_" else "-" for c in workspace_id).strip("-") or "workspace"
        return root/"outputs"/"code_workbench"/"gsdlc_09_b"/safe/"drafts"
    def _draft_path(self,root:Path,workspace_id:str,draft_id:str):
        if not str(draft_id).startswith("source-draft-") or len(str(draft_id))!=37:return self._block("story code draft path","GSDLC09B_DRAFT_ID_BLOCK","Invalid SourceDraftBuffer identifier.")
        return self._draft_root(root,workspace_id)/f"{draft_id}.json"
    def _story_execution_id(self,root:Path,workspace_id:str)->str:
        state=StoryExecutionStore(root,workspace_id=workspace_id).load_state()
        return state.execution_id if state else "story-execution-unavailable"
    @staticmethod
    def _load_json(path:Path):
        if not path.is_file():return None
        try:return json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):return None
    @staticmethod
    def _atomic_json(path:Path,payload:dict[str,Any]):
        path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8"); tmp.replace(path)
    def _pass(self,command:str,message:str,data:dict[str,Any]):
        return CommandResult(command,True,ExitCode.PASS,message,data=data,findings=[Finding("GSDLC09B_PASS",message,Severity.INFO)])
    def _block(self,command:str,code:str,message:str,*,path:str|None=None,metadata:dict[str,Any]|None=None):
        return CommandResult(command,False,ExitCode.BLOCK,message,data=metadata or {},findings=[Finding(code,message,Severity.BLOCK,path=path,metadata=metadata or {})])
    def _conflict(self,command:str,code:str,message:str,*,path:str|None=None,metadata:dict[str,Any]|None=None):
        return self._block(command,code,message,path=path,metadata=metadata)
