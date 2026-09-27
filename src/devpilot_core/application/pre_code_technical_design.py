from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from devpilot_core.rag.context_pack_v2 import ContextPackV2Builder, ContextPackV2Options

C02_STAGES = ("architecture", "security", "test-strategy", "traceability")
C02_SCHEMA = "devpilot.gsdlc13c02.technical_design_derivation.v1"
C02_MODEL = "deterministic-technical-design-template-v1"
_SHA = re.compile(r"^[0-9a-f]{64}$")
_RF_HEADING = re.compile(r"^###\s+((?:RF|RNF)-\d+)\s*$", re.I | re.M)
_FIELD = re.compile(r"^-\s+\*\*([^*]+):\*\*\s*(.+?)\.?\s*$", re.M)


class TechnicalDesignCandidateProvider(Protocol):
    provider_id: str
    model_id: str

    def derive(
        self,
        *,
        root: Path,
        stage_id: str,
        workspace_id: str,
        project_name: str,
        document_date: str,
        project_metadata: dict[str, Any],
        upstream: dict[str, str],
        semantic_model: dict[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        ...


@dataclass(frozen=True)
class RequirementRecord:
    requirement_id: str
    requirement_type: str
    statement: str
    sources: tuple[str, ...]
    priority: str
    acceptance: str
    verification: str
    owner_decision: str | None = None

    @property
    def is_mutation(self) -> bool:
        text = self.statement.lower()
        return any(token in text for token in (
            "crear ", "registrar ", "modificar ", "actualizar ", "retirar ", "eliminar ",
            "ajustar ", "cambiar ", "guardar ", "persistir ", "asignar ", "aprobar ", "rechazar ",
        ))

    @property
    def is_query(self) -> bool:
        text = self.statement.lower()
        return any(token in text for token in ("consultar ", "visualizar ", "listar ", "buscar ", "identificar ", "mostrar ", "obtener "))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(value).upper()).strip("_") or "PROJECT"


def _frontmatter(*, workspace_id: str, stage_id: str, title: str, updated: str) -> list[str]:
    return [
        "---",
        f'doc_id: "{_slug(workspace_id)}_{_slug(stage_id)}"',
        f'title: "{title}"',
        'status: "draft"',
        'version: "0.1.0"',
        'owner: "Owner / DevPilot"',
        f'updated: "{updated}"',
        'lifecycle_authority: "DevPilot runtime state"',
        'derivation: "DEVPL deterministic technical design + local ContextPack v2"',
        "---",
        "",
    ]


def parse_requirements(markdown: str) -> list[RequirementRecord]:
    text = str(markdown or "")
    matches = list(_RF_HEADING.finditer(text))
    rows: list[RequirementRecord] = []
    for index, match in enumerate(matches):
        rid = match.group(1).upper()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        fields: dict[str, str] = {}
        for key, value in _FIELD.findall(block):
            normalized = re.sub(r"\s+", " ", key.strip().lower())
            fields[normalized] = " ".join(value.strip().split())
        statement = fields.get("statement", "")
        source = fields.get("fuente", fields.get("source", ""))
        sources = tuple(x.strip() for x in re.split(r"[,;]", source) if x.strip())
        if not statement:
            continue
        rows.append(RequirementRecord(
            requirement_id=rid,
            requirement_type=fields.get("tipo", "FR"),
            statement=statement,
            sources=sources,
            priority=fields.get("prioridad", "UNSPECIFIED"),
            acceptance=fields.get("criterio de aceptación", fields.get("criterio de aceptacion", "")),
            verification=fields.get("método de verificación", fields.get("metodo de verificacion", "")),
            owner_decision=fields.get("decisión owner vinculada", fields.get("decision owner vinculada")),
        ))
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _technology_decision(root: Path) -> dict[str, Any]:
    current = _load_json(root / ".devpilot/workspaces/technology_catalog_gsdlc13_v2.json")
    legacy = _load_json(root / ".devpilot/workspaces/technology_catalog.json")
    current_profiles = [x for x in current.get("profiles", []) if isinstance(x, dict)]
    baseline = current_profiles[0] if len(current_profiles) == 1 else {}
    candidates = [x for x in legacy.get("profiles", []) if isinstance(x, dict)]
    selected = candidates[0] if len(candidates) == 1 else None
    return {
        "current_catalog_id": current.get("catalog_id"),
        "current_profile": baseline,
        "candidate_profiles": candidates,
        "selected_profile": selected,
        "selection_basis": "single-compatible-versioned-profile" if selected else "owner-decision-required",
    }


def _rag_grounding(root: Path, stage_id: str, requirements_text: str) -> dict[str, Any]:
    step = {"architecture": "architecture", "security": "security-plan", "test-strategy": "test-plan", "traceability": "test-plan"}[stage_id]
    technical_terms = {
        "architecture": "architecture application service boundary c4 component container ADR guided sdlc artifact lifecycle persistence consistency local-first",
        "security": "security threat model authentication authorization trust boundary asset threat control local-first guided sdlc",
        "test-strategy": "test strategy quality gate test intent integration unit security regression guided sdlc",
        "traceability": "traceability requirement architecture ADR security control test intent coverage guided sdlc",
    }[stage_id]
    query = " ".join([
        technical_terms,
        "requirements",
        " ".join(r.requirement_id for r in parse_requirements(requirements_text)[:16]),
    ]).strip()
    result = ContextPackV2Builder(root, ContextPackV2Options(step_id=step, query=query, top_k=8)).build()
    if not result.ok:
        return {
            "status": "unavailable",
            "pack_id": None,
            "pack_sha256": None,
            "citations": [],
            "source_refs": [],
            "findings": [f.to_dict() for f in result.findings],
        }
    pack = (result.data or {}).get("context_pack") or {}
    return {
        "status": str(pack.get("status") or "unknown"),
        "pack_id": pack.get("pack_id"),
        "pack_sha256": ((pack.get("provenance") or {}).get("pack_sha256")),
        "citations": list(pack.get("citations") or []),
        "source_refs": [
            {"path": s.get("path"), "citation_ref": s.get("citation_ref"), "sha256": s.get("content_sha256"), "kind": "context-pack-v2"}
            for s in (pack.get("sources") or []) if isinstance(s, dict)
        ],
        "findings": [f.to_dict() for f in result.findings],
    }


def _component_for(req: RequirementRecord) -> str:
    if req.is_query:
        return "ARC-C02 / ARC-C03 / ARC-C04"
    if req.is_mutation:
        return "ARC-C02 / ARC-C03 / ARC-C04"
    return "ARC-C02 / ARC-C03"


def _adr_for(req: RequirementRecord) -> str:
    if req.is_mutation:
        return "ADR-001, ADR-002, ADR-004"
    return "ADR-001, ADR-002"


def _security_for(req: RequirementRecord) -> str:
    if req.is_mutation:
        return "SEC-001, SEC-002 / CTRL-001, CTRL-002, CTRL-003"
    return "SEC-001, SEC-003 / CTRL-001, CTRL-003"


def _test_for(req: RequirementRecord, index: int) -> str:
    return f"TEST-{index:03d}"


def _capability_ids(requirements: list[RequirementRecord], semantic_model: dict[str, Any] | None) -> list[str]:
    ids = sorted({src for r in requirements for src in r.sources if re.fullmatch(r"CAP-\d+", src, re.I)})
    if ids:
        return [x.upper() for x in ids]
    model = semantic_model or {}
    return [str(x.get("id")) for x in model.get("capabilities", []) if isinstance(x, dict) and str(x.get("id") or "").startswith("CAP-")]


def _technology_lines(tech: dict[str, Any]) -> tuple[list[str], list[str]]:
    selected = tech.get("selected_profile") if isinstance(tech.get("selected_profile"), dict) else None
    candidates = tech.get("candidate_profiles") or []
    if selected:
        profile_id = str(selected.get("profile_id") or "unknown")
        chosen = [
            f"- **Perfil propuesto para decisión Owner:** `{profile_id}`.",
            f"- Frontend: `{selected.get('frontend')}`.",
            f"- Backend: `{selected.get('backend')}`.",
            f"- Database: `{selected.get('database')}`.",
            "- La selección se propone porque es el único perfil materializable versionado disponible en la authority local; el Owner puede editar/rechazar antes del approval.",
        ]
    else:
        chosen = [
            "- **Decisión bloqueante:** no existe un único perfil tecnológico local compatible que pueda proponerse determinísticamente.",
            "- El Owner debe resolver la selección dentro de Architecture antes de review/approval; DevPilot no inventará el stack.",
        ]
    alternatives = [f"- `{row.get('profile_id')}`: frontend `{row.get('frontend')}`, backend `{row.get('backend')}`, database `{row.get('database')}`." for row in candidates]
    if not alternatives:
        alternatives = ["- No hay perfiles materiales alternativos versionados en la authority local."]
    return chosen, alternatives


def _architecture(*, workspace_id: str, project_name: str, updated: str, metadata: dict[str, Any], requirements: list[RequirementRecord], semantic_model: dict[str, Any] | None, upstream: dict[str, str], tech: dict[str, Any], rag: dict[str, Any]) -> str:
    caps = _capability_ids(requirements, semantic_model)
    constraints = metadata.get("project_constraints") if isinstance(metadata.get("project_constraints"), dict) else {}
    chosen, alternatives = _technology_lines(tech)
    req_rows = [f"- {r.requirement_id} → {_component_for(r)}." for r in requirements]
    mutation_ids = [r.requirement_id for r in requirements if r.is_mutation]
    lines = _frontmatter(workspace_id=workspace_id, stage_id="architecture", title=f"Architecture Document — {project_name}", updated=updated)
    lines += [
        "# Architecture Document", "", "## Propósito", "",
        "Definir un baseline técnico local-first que convierta Requirements FROZEN en responsabilidades, boundaries y decisiones explícitas, manteniendo al Owner como autoridad de aprobación.", "",
        "## Alcance", "",
        f"- Requirements cubiertos: {len(requirements)} ({', '.join(r.requirement_id for r in requirements)}).",
        f"- Capabilities cubiertas: {', '.join(caps) if caps else 'derivadas de Requirements'}.",
        "- El baseline no introduce cloud ni API externa como dependencia obligatoria.",
        "- La implementación concreta permanece posterior a este documento; aquí se fijan decisiones y contratos técnicos.", "",
        "## Drivers", "",
        "- DRV-001 — Cumplir todos los Requirements FROZEN con trazabilidad verificable.",
        f"- DRV-002 — Local-first: {'sí' if bool(constraints.get('local_first', True)) else 'no'}; cloud obligatorio: {'sí' if bool(constraints.get('cloud_required', False)) else 'no'}.",
        "- DRV-003 — Mantener mutaciones gobernadas y consistentes, evitando estados parciales ante fallos.",
        "- DRV-004 — Mantener componentes suficientemente simples para un MVP y evolucionables sin introducir distribución prematura.",
        "- DRV-005 — Hacer Security y Test Strategy derivables desde los mismos IDs de Requirements y Architecture.", "",
        "## Componentes", "",
        "- **ARC-C01 — Presentation / Interaction Adapter.** Recibe interacción del usuario y presenta resultados; no contiene reglas de negocio ni persistencia directa.",
        "- **ARC-C02 — Application Services.** Orquesta casos de uso, autorización, validación y límites transaccionales; depende de puertos de dominio/persistencia.",
        "- **ARC-C03 — Domain Core.** Contiene comportamiento y políticas propias de las capabilities/requisitos aprobados, sin acoplarse a UI, red o proveedor LLM.",
        "- **ARC-C04 — Persistence Port + Local Adapter.** Provee almacenamiento local, consultas y transacciones mediante una interfaz sustituible.",
        "- **ARC-C05 — Governance / Observability Boundary.** Registra errores y eventos técnicos necesarios para pruebas/operación sin convertir observabilidad en lógica de dominio.", "",
        "### Requirement allocation", "", *req_rows, "",
        "## Persistencia y consistencia", "",
        "- La persistencia base es local y accedida exclusivamente a través de ARC-C04.",
        "- Application Services define una unidad de trabajo por caso de uso mutable; cambios relacionados se confirman o revierten como una sola unidad cuando el Requirement los acople.",
        f"- Requirements con mutación detectada: {', '.join(mutation_ids) if mutation_ids else 'ninguno'}.",
        "- Las reglas no especificadas en Requirements permanecen abiertas; Architecture no debe inventarlas silenciosamente.", "",
        "## Tecnología", "", *chosen, "", "### Alternativas disponibles", "", *alternatives, "",
        "## ADRs", "",
        "### ADR-001 — Estilo arquitectónico local-first modular", "",
        "- **Contexto:** MVP local-first, alcance acotado y sin requisito de despliegue distribuido.",
        "- **Decisión:** usar un monolito modular con separación Presentation → Application → Domain → Persistence.",
        "- **Alternativas:** servicios distribuidos/microservicios; monolito sin boundaries explícitos.",
        "- **Consecuencias:** menor complejidad operativa; los límites internos deben respetarse para conservar evolucionabilidad.", "",
        "### ADR-002 — Persistencia local gobernada por port/adaptor", "",
        "- **Contexto:** el producto debe operar localmente y mantener estado durable.",
        "- **Decisión:** usar persistencia local detrás de un puerto estable; el motor concreto se vincula al perfil tecnológico aprobado.",
        "- **Alternativas:** archivos ad-hoc; base remota obligatoria.",
        "- **Consecuencias:** testabilidad y sustitución del motor; requiere migraciones/backup explícitos antes de producción.", "",
        "### ADR-003 — Perfil tecnológico", "", *chosen, "", "- **Alternativas consideradas:**", *alternatives, "- **Consecuencias:** el perfil queda aprobado solo cuando el Owner aprueba este DRAFT; cambios posteriores requieren otra decisión gobernada.", "",
        "### ADR-004 — Consistencia de operaciones mutables", "",
        "- **Contexto:** varios Requirements modifican estado y algunos casos de uso pueden relacionar más de un registro/agregado.",
        "- **Decisión:** Application Services delimita transacciones/unidades de trabajo y Persistence Adapter implementa commit/rollback atómico cuando el caso de uso lo requiera.",
        "- **Alternativas:** escrituras independientes best-effort; compensación asíncrona.",
        "- **Consecuencias:** reduce estados parciales; la especialización de reglas ocurre en Stories/Test Strategy sin inventar comportamiento de negocio.", "",
        "## Seguridad", "",
        "- La UI no escribe almacenamiento directamente; toda mutación pasa por ARC-C02/ARC-C03/ARC-C04.",
        "- No se habilita red/API externa por defecto para el producto baseline.",
        "- Security Threat Model profundizará activos, trust boundaries, amenazas y controles después de Architecture FROZEN.", "",
        "## RAG grounding", "",
        f"- ContextPack v2 status: `{rag.get('status')}`.",
        f"- Pack ID: `{rag.get('pack_id') or 'none'}`.",
        "- RAG es grounding suplementario de normas/arquitectura DevPilot; Requirements/Project Context FROZEN son la authority primaria del producto.",
        *[f"- {row.get('citation_ref') or row.get('path')}" for row in rag.get("source_refs", [])[:6]], "",
        "## Riesgos", "",
        "- RISK-001 — El perfil tecnológico disponible puede ser único; el Owner debe revisar que la decisión sea apropiada y no confundir disponibilidad de catálogo con verdad universal.",
        "- RISK-002 — Requirements no definidos no pueden completarse mediante suposiciones arquitectónicas; deben volver como decisión/Story cuando sean materialmente necesarios.",
        "- RISK-003 — El baseline local no elimina obligaciones de backup, migración y recuperación antes de operación productiva.",
        "- RISK-004 — Un provider local/externo futuro puede enriquecer alternativas, pero no sustituye hashes, diff, approval ni quality gates.", "",
        "## Upstream trace", "",
        f"- Product Vision FROZEN SHA-256: {_sha(upstream.get('product-vision', ''))}.",
        f"- MVP Scope FROZEN SHA-256: {_sha(upstream.get('scope', ''))}.",
        f"- Requirements FROZEN SHA-256: {_sha(upstream.get('requirements', ''))}.", "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _security(*, workspace_id: str, project_name: str, updated: str, requirements: list[RequirementRecord], upstream: dict[str, str], rag: dict[str, Any]) -> str:
    assets = sorted({src for r in requirements for src in r.sources}) or [r.requirement_id for r in requirements]
    trace = [f"- {r.requirement_id} → {_security_for(r)}." for r in requirements]
    lines = _frontmatter(workspace_id=workspace_id, stage_id="security", title=f"Security Threat Model — {project_name}", updated=updated)
    lines += [
        "# Security Threat Model", "", "## Propósito", "",
        "Derivar un baseline de amenazas y controles desde Requirements y Architecture FROZEN, sin convertir riesgos genéricos en requisitos de negocio inventados.", "",
        "## Alcance", "",
        "- Presentation, Application, Domain y Persistence del baseline Architecture.",
        "- Datos y operaciones cubiertos por Requirements FROZEN.",
        "- Baseline local-first; red/API externa no es una dependencia obligatoria.", "",
        "## Activos", "",
        *[f"- ASSET-{i:03d} — Información/estado asociado a `{asset}`." for i, asset in enumerate(assets, 1)], "",
        "## Límites de confianza", "",
        "- TB-001 — Usuario/UI → Application Services.",
        "- TB-002 — Application/Domain → Persistence Adapter / local data store.",
        "- TB-003 — DevPilot/model providers permanecen fuera del runtime funcional del producto salvo decisión futura explícita.", "",
        "## Amenazas", "",
        "- **SEC-001 — Acceso/acción local no autorizada.** Un actor no autorizado ejecuta una operación o consulta protegida.",
        "- **SEC-002 — Mutación inválida o inconsistente.** Input manipulado, validación incompleta o fallo intermedio deja estado incorrecto/parcial.",
        "- **SEC-003 — Pérdida/corrupción de datos locales.** Fallo de almacenamiento, migración o recuperación afecta información durable.",
        "- **SEC-004 — Drift de boundary local-first.** Se introduce red/API externa como dependencia silenciosa.", "",
        "## Controles", "",
        "- **CTRL-001 — Authorization/validation boundary.** Todas las operaciones pasan por Application Services antes del Domain/Persistence.",
        "- **CTRL-002 — Atomic mutation boundary.** Operaciones relacionadas usan unidad de trabajo/transaction cuando el caso de uso requiere consistencia conjunta.",
        "- **CTRL-003 — Persistence integrity.** Constraints, relaciones y errores de persistencia se validan; fallos no se reportan como éxito.",
        "- **CTRL-004 — Local-first network policy.** Red/API externa permanece disabled-by-default y requiere decisión/provenance si se habilita.",
        "- **CTRL-005 — Backup/recovery readiness.** Antes de go-live debe existir procedimiento probado de backup/restauración del store local.", "",
        "## Trazabilidad", "", *trace, "",
        "## RAG grounding", "",
        f"- ContextPack v2: `{rag.get('pack_id') or 'none'}` / `{rag.get('status')}`.",
        "- RAG no autoriza controles ni mutaciones; aporta contexto local citado.", "",
        "## Criterios de bloqueo", "",
        "- BLOCK si una mutación puede omitir autorización/validación definida por la Architecture.",
        "- BLOCK si operaciones relacionadas pueden dejar estado parcial sin estrategia explícita de consistencia.",
        "- BLOCK si red/API externa se vuelve obligatoria sin decisión gobernada.",
        "- BLOCK para readiness productivo si no existe estrategia de backup/recovery del almacenamiento local.", "",
        "## Upstream trace", "",
        f"- Requirements FROZEN SHA-256: {_sha(upstream.get('requirements', ''))}.",
        f"- Architecture FROZEN SHA-256: {_sha(upstream.get('architecture', ''))}.", "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _test_strategy(*, workspace_id: str, project_name: str, updated: str, requirements: list[RequirementRecord], upstream: dict[str, str], rag: dict[str, Any]) -> str:
    intents: list[str] = []
    for i, r in enumerate(requirements, 1):
        kind = "integration + unit" if r.is_mutation else "unit/integration"
        if r.verification.upper() == "DEMONSTRATION":
            kind += " + controlled demonstration"
        intents += [
            f"### {_test_for(r, i)} — {r.requirement_id}", "",
            f"- **Requirement:** {r.statement}",
            f"- **Base verification:** {r.verification or 'UNSPECIFIED'}.",
            f"- **Test level:** {kind}.",
            f"- **Acceptance oracle:** {r.acceptance or 'Debe especializarse antes de ejecución; no inventar un oracle.'}",
            f"- **Architecture responsibility:** {_component_for(r)}.",
            f"- **Security:** {_security_for(r)}.", "",
        ]
    lines = _frontmatter(workspace_id=workspace_id, stage_id="test-strategy", title=f"Test Strategy — {project_name}", updated=updated)
    lines += [
        "# Test Strategy", "", "## Propósito", "",
        "Definir una estrategia de pruebas trazable a Requirements, Architecture y Security FROZEN, sin inventar métricas cuantitativas no aprobadas.", "",
        "## Alcance", "",
        f"- Requirements: {', '.join(r.requirement_id for r in requirements)}.",
        "- Responsabilidades técnicas y boundaries aprobados en Architecture.",
        "- Controles/riesgos del Security Threat Model.", "",
        "## Tipos de pruebas", "",
        "- Unitarias para reglas de dominio y validadores puros.",
        "- Integración para Persistence Adapter, transacciones y Application Services.",
        "- End-to-end para los principales casos de uso visibles al Owner.",
        "- Seguridad negativa para autorización, validación, tampering y boundaries local-first.",
        "- Recuperación para backup/restauración antes de go-live.", "",
        "## Quality gates", "",
        "- GATE-001 — todo RF/RNF FROZEN tiene al menos un Test Intent trazado.",
        "- GATE-002 — toda mutación material prueba éxito y rollback/error-path cuando corresponda.",
        "- GATE-003 — controles de Security con comportamiento verificable tienen prueba negativa/positiva asociada.",
        "- GATE-004 — el baseline puede ejecutarse y probarse sin API externa obligatoria.",
        "- GATE-005 — un FAIL funcional reproducible se clasifica; no se rerunea solo para ocultarlo.", "",
        "## Criterios", "",
        "- PASS requiere observar el criterio de aceptación; 'no lanzó excepción' no es suficiente por sí solo.",
        "- Los edge cases no definidos por Requirements se registran como decisiones/Stories, no se inventan silenciosamente en el test.",
        "- Métricas de performance/latencia no se fijan hasta que exista un NFR cuantitativo gobernado.", "",
        "## Test intents", "", *intents,
        "## Trazabilidad", "",
        *[f"- {r.requirement_id} → {_component_for(r)} → {_adr_for(r)} → {_security_for(r)} → {_test_for(r, i)}." for i, r in enumerate(requirements, 1)], "",
        "## RAG grounding", "",
        f"- ContextPack v2: `{rag.get('pack_id') or 'none'}` / `{rag.get('status')}`.", "",
        "## Upstream trace", "",
        f"- Requirements FROZEN SHA-256: {_sha(upstream.get('requirements', ''))}.",
        f"- Architecture FROZEN SHA-256: {_sha(upstream.get('architecture', ''))}.",
        f"- Security FROZEN SHA-256: {_sha(upstream.get('security', ''))}.", "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _traceability(*, workspace_id: str, project_name: str, updated: str, requirements: list[RequirementRecord], upstream: dict[str, str], rag: dict[str, Any]) -> str:
    rows = ["| Requirement | Capability/source | Architecture | ADR | Security/control | Test intent |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(requirements, 1):
        rows.append(f"| {r.requirement_id} | {', '.join(r.sources) or '-'} | {_component_for(r)} | {_adr_for(r)} | {_security_for(r)} | {_test_for(r, i)} |")
    lines = _frontmatter(workspace_id=workspace_id, stage_id="traceability", title=f"Traceability Matrix — {project_name}", updated=updated)
    lines += [
        "# Traceability Matrix", "", "## Propósito", "",
        "Conectar semánticamente Requirements FROZEN con Architecture, ADRs, Security y Test Strategy; los hashes complementan, pero no sustituyen, esa relación.", "",
        "## Matriz", "", *rows, "",
        "## Decisiones upstream", "",
        "- Las decisiones de negocio resueltas downstream se consumen a través del Requirements FROZEN; los artefactos upstream no se reescriben después de su approval.",
        "- ADR-001..ADR-004 nacen como decisiones gobernadas dentro del Architecture Document de C-02; tras el companion gate se materializan como ADRs standalone bajo docs/02_architecture/adrs y quedan referenciados por ID.", "",
        "## Provenance", "",
        f"- Product Vision SHA-256: {_sha(upstream.get('product-vision', ''))}.",
        f"- Scope SHA-256: {_sha(upstream.get('scope', ''))}.",
        f"- Requirements SHA-256: {_sha(upstream.get('requirements', ''))}.",
        f"- Architecture SHA-256: {_sha(upstream.get('architecture', ''))}.",
        f"- Security SHA-256: {_sha(upstream.get('security', ''))}.",
        f"- Test Strategy SHA-256: {_sha(upstream.get('test-strategy', ''))}.",
        f"- ContextPack v2: `{rag.get('pack_id') or 'none'}` / `{rag.get('status')}`.", "",
    ]
    return "\n".join(lines).rstrip() + "\n"


class DeterministicTechnicalDesignProvider:
    provider_id = "devpilot-local"
    model_id = C02_MODEL

    def derive(
        self,
        *,
        root: Path,
        stage_id: str,
        workspace_id: str,
        project_name: str,
        document_date: str,
        project_metadata: dict[str, Any],
        upstream: dict[str, str],
        semantic_model: dict[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        if stage_id not in C02_STAGES:
            raise ValueError(f"unsupported C-02 stage: {stage_id}")
        requirements = parse_requirements(upstream.get("requirements", ""))
        if not requirements:
            raise ValueError("C-02 derivation requires observable Requirements records from the FROZEN Requirements artifact")
        rag = _rag_grounding(root, stage_id, upstream.get("requirements", ""))
        tech = _technology_decision(root)
        if stage_id == "architecture":
            content = _architecture(workspace_id=workspace_id, project_name=project_name, updated=document_date, metadata=project_metadata, requirements=requirements, semantic_model=semantic_model, upstream=upstream, tech=tech, rag=rag)
        elif stage_id == "security":
            content = _security(workspace_id=workspace_id, project_name=project_name, updated=document_date, requirements=requirements, upstream=upstream, rag=rag)
        elif stage_id == "test-strategy":
            content = _test_strategy(workspace_id=workspace_id, project_name=project_name, updated=document_date, requirements=requirements, upstream=upstream, rag=rag)
        else:
            content = _traceability(workspace_id=workspace_id, project_name=project_name, updated=document_date, requirements=requirements, upstream=upstream, rag=rag)
        canonical = {
            "schema_id": C02_SCHEMA,
            "provider": self.provider_id,
            "model": self.model_id,
            "stage_id": stage_id,
            "workspace_id": workspace_id,
            "requirements": [r.__dict__ for r in requirements],
            "project_constraints": project_metadata.get("project_constraints") or {},
            "model_policy": project_metadata.get("model_policy") or {},
            "technology": tech,
            "upstream_sha256": {k: _sha(v) for k, v in upstream.items()},
            "semantic_model_sha256": (semantic_model or {}).get("semantic_model_sha256"),
            "rag_context_pack_id": rag.get("pack_id"),
            "rag_context_pack_sha256": rag.get("pack_sha256"),
        }
        derivation = {
            "schema_id": C02_SCHEMA,
            "mode": "DEVPL_MOCK",
            "provider": self.provider_id,
            "model": self.model_id,
            "network_used": False,
            "external_api_used": False,
            "cost_usd": 0.0,
            "model_execution_used": False,
            "agent_execution_used": False,
            "rag_execution_used": True,
            "rag_grounding_status": rag.get("status"),
            "rag_context_pack_id": rag.get("pack_id"),
            "rag_context_pack_sha256": rag.get("pack_sha256"),
            "rag_citations": rag.get("citations") or [],
            "rag_source_refs": rag.get("source_refs") or [],
            "technical_design_provider_contract": "TechnicalDesignCandidateProvider",
            "technology_selection_basis": tech.get("selection_basis"),
            "decision_summary": ([
                {"adr_id":"ADR-001","title":"Arquitectura local-first y modular","decision":"Arquitectura por capas/servicios de aplicación con boundaries explícitos.","status":"INCLUDED_IN_DRAFT"},
                {"adr_id":"ADR-002","title":"Persistencia detrás de port/adapter","decision":"Persistencia aislada detrás de contratos/ports para preservar testabilidad y sustitución.","status":"INCLUDED_IN_DRAFT"},
                {"adr_id":"ADR-003","title":"Perfil tecnológico","decision":f"Perfil propuesto: {(tech.get('selected_profile') or {}).get('profile_id') or 'DECISION_REQUIRED'}","status":"OWNER_APPROVAL_REQUIRED" if tech.get('selected_profile') else "OWNER_INPUT_REQUIRED","selection_basis":tech.get('selection_basis')},
                {"adr_id":"ADR-004","title":"Consistencia transaccional","decision":"Consistencia delimitada por operation/application-service boundary.","status":"INCLUDED_IN_DRAFT"},
            ] if stage_id == "architecture" else []),
            "canonical_input_sha256": _sha(json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)),
            "generated_content_sha256": _sha(content),
            "semantic_model_sha256": (semantic_model or {}).get("semantic_model_sha256"),
            "semantic_model_schema_id": (semantic_model or {}).get("schema_id"),
            "owner_review_required": True,
            "approval_required_before_source_write": True,
        }
        return content, derivation


def derive_technical_stage(**kwargs: Any) -> tuple[str, dict[str, Any]]:
    return DeterministicTechnicalDesignProvider().derive(**kwargs)


def _headings(markdown: str) -> set[str]:
    return {re.sub(r"\s+", " ", m.group(1).strip().lower()) for m in re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M)}


def validate_technical_artifact(stage_id: str, content: str, requirements_text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expected = {
        "architecture": {"propósito", "alcance", "drivers", "componentes", "adrs", "persistencia y consistencia", "tecnología", "riesgos", "upstream trace"},
        "security": {"propósito", "alcance", "activos", "límites de confianza", "amenazas", "controles", "criterios de bloqueo", "upstream trace"},
        "test-strategy": {"propósito", "alcance", "tipos de pruebas", "quality gates", "criterios", "test intents", "trazabilidad", "upstream trace"},
        "traceability": {"propósito", "matriz", "decisiones upstream", "provenance"},
    }.get(stage_id, set())
    missing = sorted(expected - _headings(content))
    if missing:
        findings.append({"id": "GSDLC13C02_REQUIRED_SECTION_BLOCK", "message": "Faltan secciones técnicas obligatorias.", "missing": missing})
    if re.search(r"\b(?:TODO|TBD|FIXME)\b", content):
        findings.append({"id": "GSDLC13C02_PLACEHOLDER_BLOCK", "message": "El DRAFT contiene placeholders no resueltos."})
    reqs = parse_requirements(requirements_text)
    req_ids = [r.requirement_id for r in reqs]
    if not req_ids:
        findings.append({"id": "GSDLC13C02_REQUIREMENTS_SOURCE_BLOCK", "message": "No se pudieron leer Requirements FROZEN para validar cobertura."})
        return findings
    if stage_id == "architecture":
        for token in ("ARC-C01", "ADR-001", "ADR-002", "ADR-003"):
            if token not in content:
                findings.append({"id": "GSDLC13C02_ARCH_STRUCTURE_BLOCK", "message": f"Architecture no materializa {token}."})
        if "Decisión bloqueante" in content:
            findings.append({"id": "GSDLC13C02_TECHNOLOGY_DECISION_BLOCK", "message": "Technology profile requiere decisión Owner antes de approval-ready."})
    elif stage_id == "security":
        for token in ("SEC-001", "CTRL-001"):
            if token not in content:
                findings.append({"id": "GSDLC13C02_SECURITY_STRUCTURE_BLOCK", "message": f"Security no materializa {token}."})
    elif stage_id == "test-strategy":
        for index, rid in enumerate(req_ids, 1):
            if rid not in content or f"TEST-{index:03d}" not in content:
                findings.append({"id": "GSDLC13C02_TEST_COVERAGE_BLOCK", "message": f"Falta Test Intent trazable para {rid}.", "requirement_id": rid})
    elif stage_id == "traceability":
        for rid in req_ids:
            if rid not in content:
                findings.append({"id": "GSDLC13C02_TRACE_COVERAGE_BLOCK", "message": f"Traceability no cubre {rid}.", "requirement_id": rid})
        for token in ("Architecture", "ADR", "Security", "Test intent"):
            if token.lower() not in content.lower():
                findings.append({"id": "GSDLC13C02_TRACE_AXIS_BLOCK", "message": f"Traceability omite eje {token}."})
    return findings
