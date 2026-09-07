from __future__ import annotations

from pathlib import Path
from typing import Any

from devpilot_core.policy import PolicyEffect, SecretGuard

from .models import canonical_sha256

_ALLOWED_SUFFIXES = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".toml", ".yaml", ".yml", ".css", ".html"}
_DENIED_PARTS = {".git", ".venv", "outputs", "__pycache__", ".pytest_cache", "node_modules"}
_MAX_FILE_BYTES = 65536
_MAX_FILE_EXCERPT = 2000
_MAX_RELEVANT_FILES = 20


class StoryContextPackError(ValueError):
    pass


class StoryContextPackBuilder:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.secret_guard = SecretGuard(self.workspace_root)

    def build(
        self,
        *,
        workspace_id: str,
        project_id: str,
        story: dict[str, Any],
        source_fragments: dict[str, dict[str, Any]],
        relevant_files: list[str] | tuple[str, ...],
        created_at_utc: str,
    ) -> dict[str, Any]:
        trace_links = [x for x in story.get("trace_links") or [] if isinstance(x, dict)]
        fragments: list[dict[str, Any]] = []
        for link in sorted(trace_links, key=lambda x: (str(x.get("kind") or ""), str(x.get("target_id") or ""))):
            target_id = str(link.get("target_id") or "").strip()
            source = dict(source_fragments.get(target_id) or {})
            if not source:
                raise StoryContextPackError(f"STORY_CONTEXT_SOURCE_MISSING:{target_id}")
            content = str(source.get("content") or "")
            self._require_secret_free(content, subject=target_id)
            fragments.append(
                {
                    "kind": str(link.get("kind") or ""),
                    "target_id": target_id,
                    "source_ref": str(source.get("source_ref") or target_id),
                    "content": content,
                    "content_sha256": canonical_sha256(content),
                    "authority_scope": str(source.get("authority_scope") or "current-active"),
                    "write_authority": False,
                }
            )

        acceptance = [str(x).strip() for x in story.get("acceptance_criteria") or [] if str(x).strip()]
        acceptance_text = "\n".join(acceptance)
        self._require_secret_free(acceptance_text, subject="acceptance-criteria")
        fragments.append(
            {
                "kind": "acceptance",
                "target_id": f"{story.get('id')}:acceptance",
                "source_ref": f"planning-story:{story.get('id')}",
                "content": acceptance_text,
                "content_sha256": canonical_sha256(acceptance_text),
                "authority_scope": "current-active",
                "write_authority": False,
            }
        )

        files = [self._file_fragment(raw) for raw in sorted(set(relevant_files))[:_MAX_RELEVANT_FILES]]
        stable = {
            "policy_version": "DEVPL-GSDLC-09-A-CONTEXT-MINIMIZATION-V1",
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "story": {"id": str(story.get("id") or ""), "version": str(story.get("version") or ""), "title": str(story.get("title") or "")},
            "fragments": fragments,
            "relevant_files": files,
        }
        digest = canonical_sha256(stable)
        return {
            "schema_id": "SCHEMA-DEVPL-STORY-CONTEXT-PACK-V1",
            "schema_version": "1.0.0",
            "context_pack_id": "story-context-" + digest[:24],
            "context_sha256": digest,
            "created_at_utc": str(created_at_utc),
            **stable,
            "safety": {
                "context_minimized": True,
                "secret_scan_passed": True,
                "runtime_stores_excluded": True,
                "candidate_files_write_authority": False,
                "source_mutations_performed": False,
                "network_used": False,
                "external_api_used": False,
            },
        }

    def _file_fragment(self, raw: str) -> dict[str, Any]:
        rel = Path(str(raw).replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            raise StoryContextPackError(f"STORY_CONTEXT_PATH_ESCAPE:{raw}")
        if any(part in _DENIED_PARTS for part in rel.parts) or rel.name.lower().startswith(("auth.db", "devpilot.db")) or rel.name.lower().startswith(".env"):
            raise StoryContextPackError(f"STORY_CONTEXT_RUNTIME_OR_SECRET_PATH_BLOCKED:{raw}")
        candidate = (self.workspace_root / rel).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError as exc:
            raise StoryContextPackError(f"STORY_CONTEXT_PATH_ESCAPE:{raw}") from exc
        if candidate.suffix.lower() not in _ALLOWED_SUFFIXES:
            raise StoryContextPackError(f"STORY_CONTEXT_BINARY_OR_UNSUPPORTED:{raw}")
        if not candidate.is_file():
            raise StoryContextPackError(f"STORY_CONTEXT_FILE_MISSING:{raw}")
        if candidate.stat().st_size > _MAX_FILE_BYTES:
            raise StoryContextPackError(f"STORY_CONTEXT_FILE_OVERSIZE:{raw}")
        text = candidate.read_text(encoding="utf-8")
        self._require_secret_free(text, subject=str(rel).replace("\\", "/"))
        excerpt = text[:_MAX_FILE_EXCERPT]
        return {
            "path": str(rel).replace("\\", "/"),
            "content_sha256": canonical_sha256(text),
            "excerpt": excerpt,
            "excerpt_truncated": len(text) > len(excerpt),
            "authority_scope": "context-candidate-only",
            "write_authority": False,
        }

    def _require_secret_free(self, text: str, *, subject: str) -> None:
        decision = self.secret_guard.scan_text(text, subject=subject)
        if decision.effect is PolicyEffect.BLOCK:
            raise StoryContextPackError(f"STORY_CONTEXT_SECRET_BLOCKED:{subject}")
