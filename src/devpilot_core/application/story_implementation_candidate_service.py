from __future__ import annotations

import ast
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.code_workbench.service import CodeWorkbenchApplicationService
from devpilot_core.story_execution import StoryExecutionStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: str, *, fallback: str) -> str:
    text = str(value or "").lower()
    text = (
        text.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or fallback


class StoryImplementationCandidateApplicationService:
    """13-D-02 deterministic implementation proposal for an empty greenfield source tree.

    The proposal is runtime-only and consumes the already-authoritative StoryExecution,
    StoryContextPack and frozen Architecture document.  It deliberately does not call a
    model, execute tools, install dependencies or mutate source.  Human ACCEPT creates
    SourceDraftBuffer records only; 09-C remains the sole source mutation boundary.
    """

    SCHEMA_ID = "DEVPL-GSDLC-13-D-02-IMPLEMENTATION-CANDIDATE-V2"
    GENERATOR_ID = "deterministic-story-implementation-template-v2"

    def __init__(self, root: Path, *, context_resolver, code_workbench: CodeWorkbenchApplicationService) -> None:
        self.root = Path(root).resolve()
        self.context_resolver = context_resolver
        self.code = code_workbench
        self._lock = RLock()

    def propose(self, *, actor: str, actor_role: str) -> CommandResult:
        command = "story implementation candidate propose"
        if actor_role not in {"owner", "developer"} or not str(actor).strip():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ROLE_BLOCK", "Owner/developer human session is required.")
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_BLOCK", "Active server-valid project context is required.")
        workspace = Path(context.effective_workspace_root)
        workspace_id = str(context.active_workspace_id)
        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        state = store.load_state()
        story_context = store.load_context()
        if state is None or not isinstance(story_context, dict) or str(state.status.value) != "IN_PROGRESS":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_STORY_BLOCK", "Implementation proposal requires StoryExecution IN_PROGRESS with StoryContextPack.")

        sources = self.code.list_sources()
        if not sources.ok:
            return self._dependency_block(command, sources, "GSDLC13D02_IMPLEMENTATION_SOURCE_DISCOVERY_BLOCK")
        if int(((sources.data or {}).get("summary") or {}).get("sources_total") or 0) != 0:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_EMPTY_SOURCE_ONLY_BLOCK", "Deterministic bootstrap proposal is only for a source-empty greenfield; use bounded EDIT/agent proposal for existing source.")

        architecture_path = workspace / "docs/02_architecture/architecture_document.md"
        if not architecture_path.is_file():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ARCHITECTURE_MISSING_BLOCK", "Frozen Architecture document is required before source bootstrap.")
        architecture = architecture_path.read_text(encoding="utf-8-sig")
        technology = self._technology(architecture)
        if technology["backend"] != "fastapi-python" or technology["database"] != "sqlite":
            return self._block(
                command,
                "GSDLC13D02_IMPLEMENTATION_PROFILE_BLOCK",
                "Deterministic implementation provider currently supports the approved fastapi-python + sqlite profile only; do not guess another stack.",
                metadata={"technology": technology},
            )

        story = story_context.get("story") if isinstance(story_context.get("story"), dict) else {}
        story_id = str(story.get("id") or state.story_id)
        title = str(story.get("title") or story_id)
        requirement = self._fragment(story_context, "requirement")
        acceptance = self._fragment(story_context, "acceptance")
        test_intent = self._fragment(story_context, "test-intent")
        namespace = _slug(workspace_id, fallback="app")
        files = [
            self._file(
                f"src/{namespace}/domain/product.py",
                self._domain_module(story_id, title, requirement, acceptance),
                rationale="ARC-C03 · reusable Product domain model + persistence port; no story-specific table or business field invention.",
                artifact_role="domain",
            ),
            self._file(
                f"src/{namespace}/application/create_product.py",
                self._application_module(story_id, title, namespace, requirement, acceptance),
                rationale="ARC-C02 · authorization + create-product use-case orchestration over the domain port.",
                artifact_role="application",
            ),
            self._file(
                f"src/{namespace}/infrastructure/sqlite_product_repository.py",
                self._repository_module(story_id, namespace),
                rationale="ARC-C04 · reusable SQLite ProductRepository adapter with a products table and transactional write.",
                artifact_role="infrastructure",
            ),
            self._file(
                "tests/test_create_product.py",
                self._test_module(story_id, namespace, acceptance),
                rationale="TEST-001 · acceptance-focused authorization and durable-observability tests for RF-001.",
                artifact_role="test",
            ),
        ]
        quality = self._quality_report(files)
        if not quality["ready_for_draft_materialization"]:
            return self._block(
                command,
                "GSDLC13D02_IMPLEMENTATION_INTERNAL_QUALITY_BLOCK",
                "Generated implementation proposal failed the internal architecture/reviewability gate; no proposal was persisted.",
                metadata={"quality": quality},
            )
        stable = {
            "workspace_id": workspace_id,
            "story_execution_id": state.execution_id,
            "story_id": story_id,
            "story_context_sha256": story_context.get("context_sha256"),
            "architecture_sha256": _sha_text(architecture),
            "technology": technology,
            "files": [{k: row[k] for k in ("target_path", "content_sha256", "operation")} for row in files],
        }
        proposal_hash = _sha(stable)
        proposal_id = "implementation-proposal-" + proposal_hash[:24]
        existing = self._load(workspace, workspace_id, proposal_id)
        if isinstance(existing, dict) and str(existing.get("proposal_sha256") or "") == proposal_hash:
            return self._pass(
                command,
                "Existing deterministic implementation proposal recovered without reopening its human decision; source/draft mutations=false.",
                {"proposal": existing, "recovered": True},
            )
        proposal = {
            "schema_id": self.SCHEMA_ID,
            "schema_version": "1.0.0",
            "proposal_id": proposal_id,
            "proposal_sha256": proposal_hash,
            "workspace_id": workspace_id,
            "story_execution_id": state.execution_id,
            "story_id": story_id,
            "story_title": title,
            "status": "PROPOSED",
            "provider": {
                "provider_id": "devpilot-local",
                "model_id": self.GENERATOR_ID,
                "preliminary": True,
                "network_used": False,
                "external_api_used": False,
                "cost_usd": 0.0,
            },
            "technology": technology,
            "quality": quality,
            "rationale": [
                "StoryContextPack is IN_PROGRESS and the source tree is empty.",
                "The frozen Architecture selected fastapi-python + sqlite; the first bounded slice therefore uses Python Application/Domain/Persistence boundaries.",
                "The Story is allocated to ARC-C02/ARC-C03/ARC-C04; the proposal now materializes those responsibilities explicitly as reusable product-oriented modules rather than story-specific persistence.",
                "Requirements do not define a complete product-field schema. The proposal therefore preserves product attributes as opaque governed data and does not invent name/price/SKU/stock business rules.",
                "Every generated Python artifact carries a module docstring that states purpose, responsibilities, boundaries and traceability for human review.",
                "D03 quality/remediation may require a successor change if targeted tests expose a missing boundary or insufficient behavior.",
                "Manual authoring remains available; this proposal is a reviewable default, not authority to write source.",
            ],
            "files": files,
            "provenance": {
                "story_context_pack_id": story_context.get("context_pack_id"),
                "story_context_sha256": story_context.get("context_sha256"),
                "architecture_path": "docs/02_architecture/architecture_document.md",
                "architecture_sha256": _sha_text(architecture),
                "requirement_source_ref": requirement.get("source_ref"),
                "test_intent_source_ref": test_intent.get("source_ref"),
            },
            "safety": {
                "proposal_only": True,
                "human_review_required": True,
                "source_mutations_performed": False,
                "draft_mutations_performed": False,
                "apply_authority": False,
                "approval_authority": False,
                "git_authority": False,
                "network_used": False,
                "external_api_used": False,
            },
            "created_at_utc": _now(),
            "human_decision": None,
            "draft_ids": [],
        }
        self._save(workspace, workspace_id, proposal)
        return self._pass(command, "Deterministic implementation proposal created from StoryContextPack + frozen Architecture; source/draft mutations=false.", {"proposal": proposal})

    def decide(self, *, proposal_id: str, proposal_sha256: str, decision: str, actor: str, actor_role: str) -> CommandResult:
        command = "story implementation candidate decision"
        decision = str(decision or "").upper().strip()
        if actor_role not in {"owner", "developer"} or not str(actor).strip():
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_DECISION_ROLE_BLOCK", "Owner/developer human session is required.")
        if decision not in {"ACCEPT", "REJECT"}:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_DECISION_BLOCK", "Decision must be ACCEPT or REJECT.")
        context = self.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_BLOCK", "Active server-valid project context is required.")
        workspace = Path(context.effective_workspace_root)
        workspace_id = str(context.active_workspace_id)
        proposal = self._load(workspace, workspace_id, proposal_id)
        if proposal is None:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_MISSING_BLOCK", "Implementation proposal was not found.")
        if str(proposal.get("proposal_sha256")) != str(proposal_sha256 or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_HASH_BLOCK", "Implementation proposal SHA-256 changed; refresh before decision.")
        if proposal.get("status") != "PROPOSED":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_PROPOSAL_DECIDED_BLOCK", "Implementation proposal already has a terminal human decision.")
        provider = proposal.get("provider") if isinstance(proposal.get("provider"), dict) else {}
        quality = proposal.get("quality") if isinstance(proposal.get("quality"), dict) else {}
        if str(provider.get("model_id") or "") != self.GENERATOR_ID or quality.get("ready_for_draft_materialization") is not True:
            return self._block(
                command,
                "GSDLC13D02_IMPLEMENTATION_OBSOLETE_PROPOSAL_BLOCK",
                "This proposal predates the architecture/reviewability quality corrective or did not pass its quality gate; generate a fresh proposal before ACCEPT.",
                metadata={"model_id": provider.get("model_id"), "quality": quality},
            )
        if decision == "REJECT":
            proposal["status"] = "REJECTED"
            proposal["human_decision"] = {"decision": decision, "actor": actor, "actor_role": actor_role, "decided_at_utc": _now()}
            self._save(workspace, workspace_id, proposal)
            return self._pass(command, "Implementation proposal rejected; source/draft mutations=false.", {"proposal": proposal, "drafts": []})

        store = StoryExecutionStore(workspace, workspace_id=workspace_id)
        state = store.load_state()
        if state is None or str(state.execution_id) != str(proposal.get("story_execution_id")) or str(state.status.value) != "IN_PROGRESS":
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_STALE_STORY_BLOCK", "StoryExecution changed after proposal generation; regenerate proposal.")
        current_context = store.load_context() or {}
        if str(current_context.get("context_sha256") or "") != str((proposal.get("provenance") or {}).get("story_context_sha256") or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_CONTEXT_DRIFT_BLOCK", "StoryContextPack changed after proposal generation; regenerate proposal.")
        architecture_path = workspace / str((proposal.get("provenance") or {}).get("architecture_path") or "docs/02_architecture/architecture_document.md")
        if not architecture_path.is_file() or _sha_text(architecture_path.read_text(encoding="utf-8-sig")) != str((proposal.get("provenance") or {}).get("architecture_sha256") or ""):
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_ARCHITECTURE_DRIFT_BLOCK", "Frozen Architecture changed after proposal generation; regenerate proposal.")
        current_sources = self.code.list_sources()
        if not current_sources.ok or int((((current_sources.data or {}).get("summary") or {}).get("sources_total") or 0)) != 0:
            return self._block(command, "GSDLC13D02_IMPLEMENTATION_SOURCE_DRIFT_BLOCK", "Source tree changed after proposal generation; regenerate proposal before materializing drafts.")

        listed = self.code.list_drafts()
        if not listed.ok:
            return self._dependency_block(command, listed, "GSDLC13D02_IMPLEMENTATION_DRAFT_RECONCILIATION_BLOCK")
        expected_files = {str(row.get("target_path") or ""): row for row in proposal.get("files") or []}
        drafts: list[dict[str, Any]] = []
        for current in (listed.data or {}).get("drafts") or []:
            target_path = str(current.get("target_path") or "")
            expected_row = expected_files.get(target_path)
            if (
                expected_row is None
                or str(current.get("operation") or "") != "CREATE"
                or str(current.get("content_sha256") or "") != str(expected_row.get("content_sha256") or "")
            ):
                return self._block(
                    command,
                    "GSDLC13D02_IMPLEMENTATION_DRAFT_STATE_DRIFT_BLOCK",
                    "Existing runtime drafts do not match the accepted deterministic proposal; inspect/discard explicitly before retry.",
                    metadata={"unexpected_draft_id": current.get("draft_id"), "target_path": target_path},
                )
            drafts.append(deepcopy(current))
        existing_targets = {str(row.get("target_path") or "") for row in drafts}
        created_this_attempt: list[dict[str, Any]] = []
        for row in proposal.get("files") or []:
            if str(row.get("target_path") or "") in existing_targets:
                continue
            result = self.code.save_draft(
                operation="CREATE",
                content=str(row.get("content") or ""),
                target_path=str(row.get("target_path") or ""),
                source_id=None,
                expected_source_sha256=None,
                expected_revision_sha256=None,
                actor=actor,
                actor_role=actor_role,
            )
            if not result.ok:
                rollback_findings: list[dict[str, Any]] = []
                for prior in reversed(created_this_attempt):
                    cleanup = self.code.discard_draft(
                        str(prior.get("draft_id") or ""),
                        expected_revision_sha256=str(prior.get("revision_sha256") or ""),
                        actor_role=actor_role,
                    )
                    if not cleanup.ok:
                        rollback_findings.append(cleanup.to_dict())
                blocked = self._dependency_block(command, result, "GSDLC13D02_IMPLEMENTATION_DRAFT_MATERIALIZATION_BLOCK")
                if rollback_findings:
                    blocked.data["draft_rollback_failures"] = rollback_findings
                return blocked
            created = deepcopy((result.data or {}).get("draft") or {})
            drafts.append(created)
            created_this_attempt.append(created)
        proposal["status"] = "ACCEPTED"
        proposal["draft_ids"] = [str(x.get("draft_id")) for x in drafts]
        proposal["human_decision"] = {
            "decision": "ACCEPT",
            "actor": actor,
            "actor_role": actor_role,
            "decided_at_utc": _now(),
            "effect": "materialize-runtime-source-draft-set-only",
            "source_write_authorized": False,
        }
        proposal["safety"]["draft_mutations_performed"] = True
        self._save(workspace, workspace_id, proposal)
        return self._pass(command, "Human ACCEPT materialized a runtime-only SourceDraftBuffer set; source remains unchanged.", {"proposal": proposal, "drafts": drafts, "source_mutations_performed": False})

    @staticmethod
    def _technology(text: str) -> dict[str, str]:
        def capture(label: str) -> str:
            match = re.search(rf"-\s*{re.escape(label)}:\s*`([^`]+)`", text, re.I)
            return str(match.group(1)).strip().lower() if match else "unknown"
        profile = re.search(r"Perfil propuesto para decisión Owner:\*\*\s*`([^`]+)`", text, re.I)
        return {
            "profile_id": str(profile.group(1)).strip() if profile else "unknown",
            "frontend": capture("Frontend"),
            "backend": capture("Backend"),
            "database": capture("Database"),
        }

    @staticmethod
    def _fragment(context: dict[str, Any], kind: str) -> dict[str, Any]:
        for row in context.get("fragments") or []:
            if isinstance(row, dict) and str(row.get("kind")) == kind:
                return row
        return {}

    @staticmethod
    def _file(target_path: str, content: str, *, rationale: str, artifact_role: str) -> dict[str, Any]:
        module_docstring = ""
        try:
            tree = ast.parse(content)
            module_docstring = ast.get_docstring(tree, clean=False) or ""
        except SyntaxError:
            module_docstring = ""
        return {
            "operation": "CREATE",
            "target_path": target_path,
            "content": content,
            "content_sha256": _sha_text(content),
            "rationale": rationale,
            "artifact_role": artifact_role,
            "docstring_summary": module_docstring.splitlines()[0].strip() if module_docstring else "",
        }

    @staticmethod
    def _quality_report(files: list[dict[str, Any]]) -> dict[str, Any]:
        required_docstring_sections = ("Purpose:", "Responsibilities:", "Boundaries:", "Traceability:")
        docstrings: list[dict[str, Any]] = []
        syntax_pass = True
        for row in files:
            content = str(row.get("content") or "")
            try:
                tree = ast.parse(content)
                doc = ast.get_docstring(tree, clean=False) or ""
                syntax_ok = True
            except SyntaxError:
                doc = ""
                syntax_ok = False
                syntax_pass = False
            missing = [section for section in required_docstring_sections if section not in doc]
            docstrings.append({
                "target_path": row.get("target_path"),
                "syntax_pass": syntax_ok,
                "module_docstring_present": bool(doc.strip()),
                "required_sections_present": not missing,
                "missing_sections": missing,
            })
        paths = {str(row.get("target_path") or "") for row in files}
        architecture_coverage = {
            "ARC-C02": any("/application/" in path for path in paths),
            "ARC-C03": any("/domain/" in path for path in paths),
            "ARC-C04": any("/infrastructure/" in path for path in paths),
        }
        no_story_specific_storage = all("story_rf_001_records" not in str(row.get("content") or "") for row in files)
        reusable_product_storage = any("CREATE TABLE IF NOT EXISTS products" in str(row.get("content") or "") for row in files)
        docstrings_pass = all(x["module_docstring_present"] and x["required_sections_present"] for x in docstrings)
        ready = syntax_pass and all(architecture_coverage.values()) and no_story_specific_storage and reusable_product_storage and docstrings_pass
        return {
            "ready_for_draft_materialization": ready,
            "python_syntax_pass": syntax_pass,
            "docstring_contract_pass": docstrings_pass,
            "docstring_contract": "module Purpose/Responsibilities/Boundaries/Traceability required for every generated Python artifact",
            "docstrings": docstrings,
            "architecture_coverage": architecture_coverage,
            "story_specific_storage": not no_story_specific_storage,
            "reusable_product_storage": reusable_product_storage,
            "business_field_invention": False,
            "product_data_contract_posture": "opaque-attributes-until-governed-requirement-specializes-fields",
            "known_limitations": [
                "RF-001 does not define a complete product-field schema; the slice preserves arbitrary governed attributes without inventing name/SKU/price/stock rules.",
                "ARC-C01 presentation is intentionally absent because RF-001 is allocated only to ARC-C02/ARC-C03/ARC-C04 in the frozen Architecture.",
                "FastAPI/React technical scaffold and dependency manifests remain a separate project-level hardening concern; this Story does not silently create them.",
            ],
        }

    @staticmethod
    def _module_docstring(*, title: str, purpose: str, responsibilities: list[str], boundaries: list[str], traceability: list[str]) -> str:
        def lines(label: str, values: list[str]) -> str:
            return label + "\n" + "\n".join(f"- {value}" for value in values)
        return (
            f'"""{title}\n\n'
            f'Purpose:\n{purpose}\n\n'
            f'{lines("Responsibilities:", responsibilities)}\n\n'
            f'{lines("Boundaries:", boundaries)}\n\n'
            f'{lines("Traceability:", traceability)}\n'
            '"""'
        )

    @classmethod
    def _domain_module(cls, story_id: str, title: str, requirement: dict[str, Any], acceptance: dict[str, Any]) -> str:
        doc = cls._module_docstring(
            title="Product domain model and persistence port for the first governed product-creation slice.",
            purpose="Represent a product independently of UI/database concerns and define the repository contract required by RF-001.",
            responsibilities=[
                "Represent product identity, opaque governed attributes and availability state.",
                "Expose the ProductRepository port used by Application Services.",
                "Remain reusable by RF-002/RF-003/RF-004 instead of encoding story-rf-001 in storage semantics.",
            ],
            boundaries=[
                "Does not choose presentation/API contracts.",
                "Does not invent business fields such as SKU, price or stock because RF-001 does not define them.",
                "Does not depend on SQLite, network, external APIs or DevPilot runtime stores.",
            ],
            traceability=[f"Story: {story_id} — {title}", "Requirement: RF-001", "Architecture: ARC-C03 + ARC-C04 port", "Test intent: TEST-001"],
        )
        return f'''{doc}

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Product:
    """Domain representation of one product known to the local application."""

    product_id: str
    attributes: Mapping[str, Any]
    available: bool = True


class ProductRepository(Protocol):
    """Persistence port used by product application services."""

    def add(self, product: Product) -> None:
        """Persist a product as one atomic repository operation."""
        ...

    def get(self, product_id: str) -> Product | None:
        """Return the persisted product without mutating repository state."""
        ...
'''

    @classmethod
    def _application_module(cls, story_id: str, title: str, namespace: str, requirement: dict[str, Any], acceptance: dict[str, Any]) -> str:
        doc = cls._module_docstring(
            title="Create-product application service for RF-001.",
            purpose="Orchestrate authorization, domain creation and durable observability for the active Story without embedding persistence details.",
            responsibilities=[
                "Reject callers that have not crossed the authorization boundary.",
                "Create an available Product while preserving caller-supplied attributes as opaque governed data.",
                "Persist through ProductRepository and verify the created product is observable afterwards.",
            ],
            boundaries=[
                "Does not define product-field business rules that are absent from frozen Requirements.",
                "Does not open SQLite connections, render UI, perform network access or write outside the repository port.",
                "Does not grant apply/approval/Git authority.",
            ],
            traceability=[f"Story: {story_id} — {title}", "Requirement: RF-001", "Architecture: ARC-C02 + ARC-C03 + ARC-C04", "Security: SEC-001 + SEC-002", "Test intent: TEST-001"],
        )
        return f'''{doc}

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from src.{namespace}.domain.product import Product, ProductRepository


class AuthorizationRequired(PermissionError):
    """Raised when a caller attempts RF-001 without prior authorization."""


class CreateProductService:
    """Application service implementing the RF-001 creation use case."""

    def __init__(self, repository: ProductRepository) -> None:
        """Bind the use case to the approved product persistence port."""
        self.repository = repository

    def execute(self, *, actor_authorized: bool, attributes: Mapping[str, Any]) -> Product:
        """Create, persist and re-read one available product for an authorized actor."""
        if not actor_authorized:
            raise AuthorizationRequired("authorized actor required")
        product = Product(product_id=uuid.uuid4().hex, attributes=dict(attributes), available=True)
        self.repository.add(product)
        observed = self.repository.get(product.product_id)
        if observed != product:
            raise RuntimeError("created product was not observable after persistence")
        return observed
'''

    @classmethod
    def _repository_module(cls, story_id: str, namespace: str) -> str:
        doc = cls._module_docstring(
            title="SQLite adapter for the reusable ProductRepository port.",
            purpose="Persist Product records locally behind ARC-C04 while keeping RF-001 application/domain code independent of SQLite.",
            responsibilities=[
                "Create the bounded products table when the adapter is initialized.",
                "Persist one Product atomically and reconstruct it by product_id.",
                "Preserve product attributes losslessly as JSON without defining undeclared business fields.",
            ],
            boundaries=[
                "Implements ProductRepository only; no authorization or UI logic.",
                "Uses local SQLite only; no network or external API.",
                "Uses a product-oriented table reusable by later CAP-001 stories instead of story-specific storage.",
            ],
            traceability=[f"Story: {story_id}", "Requirement: RF-001", "Architecture: ARC-C04", "ADR-002: persistence behind port/adaptor", "ADR-004: bounded mutable consistency"],
        )
        return f'''{doc}

from __future__ import annotations

import json
import sqlite3

from src.{namespace}.domain.product import Product


class SQLiteProductRepository:
    """Local SQLite implementation of ProductRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Initialize the adapter and ensure the reusable products table exists."""
        self.connection = connection
        with self.connection:
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS products ("
                "product_id TEXT PRIMARY KEY, attributes_json TEXT NOT NULL, "
                "available INTEGER NOT NULL CHECK (available IN (0, 1)))"
            )

    def add(self, product: Product) -> None:
        """Persist one Product using a single SQLite transaction."""
        with self.connection:
            self.connection.execute(
                "INSERT INTO products(product_id, attributes_json, available) VALUES (?, ?, ?)",
                (product.product_id, json.dumps(dict(product.attributes), sort_keys=True, ensure_ascii=False), int(product.available)),
            )

    def get(self, product_id: str) -> Product | None:
        """Read one Product by identity without mutating storage."""
        row = self.connection.execute(
            "SELECT attributes_json, available FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None
        return Product(product_id=product_id, attributes=json.loads(row[0]), available=bool(row[1]))
'''

    @classmethod
    def _test_module(cls, story_id: str, namespace: str, acceptance: dict[str, Any]) -> str:
        ac = " ".join(str(acceptance.get("content") or "").split())[:400]
        doc = cls._module_docstring(
            title="Acceptance-focused tests for RF-001 product creation.",
            purpose="Verify the active Story's authorization boundary and durable observability against the SQLite adapter without introducing external dependencies.",
            responsibilities=[
                "Verify unauthorized creation is rejected before persistence.",
                "Verify an authorized product is persisted, remains available and can be observed afterwards.",
                "Verify caller-supplied opaque attributes survive the persistence round-trip.",
            ],
            boundaries=[
                "Does not assert undeclared product fields such as SKU, price or stock.",
                "Uses SQLite in-memory and no network/external API.",
                "Does not execute Full Regression; D03 remains the governed validation checkpoint.",
            ],
            traceability=[f"Story: {story_id}", f"Acceptance oracle: {ac}", "Requirement: RF-001", "Test intent: TEST-001", "Security: SEC-001 + SEC-002"],
        )
        return f'''{doc}

import sqlite3

import pytest

from src.{namespace}.application.create_product import AuthorizationRequired, CreateProductService
from src.{namespace}.infrastructure.sqlite_product_repository import SQLiteProductRepository


def test_unauthorized_actor_cannot_create_product() -> None:
    """SEC-001: reject unauthorized creation before any product row is stored."""
    connection = sqlite3.connect(":memory:")
    repository = SQLiteProductRepository(connection)
    service = CreateProductService(repository)

    with pytest.raises(AuthorizationRequired):
        service.execute(actor_authorized=False, attributes={{"example": "opaque-value"}})

    assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0


def test_authorized_product_is_recorded_available_and_observable() -> None:
    """TEST-001: an authorized RF-001 create remains observable after persistence."""
    repository = SQLiteProductRepository(sqlite3.connect(":memory:"))
    service = CreateProductService(repository)
    attributes = {{"example": "opaque-value"}}

    created = service.execute(actor_authorized=True, attributes=attributes)

    observed = repository.get(created.product_id)
    assert observed == created
    assert observed is not None
    assert observed.available is True
    assert dict(observed.attributes) == attributes
'''

    def _store_path(self, workspace: Path, workspace_id: str) -> Path:
        safe = _slug(workspace_id, fallback="workspace")
        return workspace / "outputs" / "story_implementation" / "gsdlc_13_d_02" / safe / "proposals.json"

    def _save(self, workspace: Path, workspace_id: str, proposal: dict[str, Any]) -> None:
        path = self._store_path(workspace, workspace_id)
        with self._lock:
            payload = {"schema_version": "1.0.0", "proposals": {}}
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"implementation proposal store is unreadable: {path}") from exc
                if not isinstance(loaded, dict) or not isinstance(loaded.get("proposals", {}), dict):
                    raise RuntimeError(f"implementation proposal store has invalid structure: {path}")
                payload = loaded
            payload.setdefault("proposals", {})[str(proposal["proposal_id"])] = proposal
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            temp.replace(path)

    def _load(self, workspace: Path, workspace_id: str, proposal_id: str) -> dict[str, Any] | None:
        path = self._store_path(workspace, workspace_id)
        with self._lock:
            if not path.is_file():
                return None
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
            row = (payload.get("proposals") or {}).get(str(proposal_id))
            return deepcopy(row) if isinstance(row, dict) else None

    @staticmethod
    def _pass(command: str, message: str, data: dict[str, Any]) -> CommandResult:
        return CommandResult(command, True, ExitCode.PASS, message, data=data, findings=[Finding("GSDLC13D02_IMPLEMENTATION_PASS", message, Severity.INFO)])

    @staticmethod
    def _block(command: str, code: str, message: str, *, metadata: dict[str, Any] | None = None) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, message, data=metadata or {}, findings=[Finding(code, message, Severity.BLOCK, metadata=metadata or {})])

    @staticmethod
    def _dependency_block(command: str, result: CommandResult, code: str) -> CommandResult:
        return CommandResult(command, False, ExitCode.BLOCK, "Dependency blocked deterministic implementation proposal.", data={"dependency": result.to_dict()}, findings=[Finding(code, "Dependency blocked deterministic implementation proposal.", Severity.BLOCK), *result.findings])
