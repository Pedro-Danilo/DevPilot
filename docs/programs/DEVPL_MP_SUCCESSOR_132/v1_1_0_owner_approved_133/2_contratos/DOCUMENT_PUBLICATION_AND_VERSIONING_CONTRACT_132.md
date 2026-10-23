---
doc_id: DEVPL-MP-SUCCESSOR-132-DOCUMENT_PUBLICATION_AND_VERSIONING_CONTRACT_132
title: "Markdown durable, autoridad y portabilidad"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Markdown durable, autoridad y portabilidad

## Identidad y fuente canónica

Campos de publicación: `doc_id`, `artifact_type`, `revision`, `content_authority_kind`, `canonical_ref`, `canonical_hash`, `markdown_path`, `markdown_hash`, `renderer_version`, `approval_ref`, `frozen_at`, `superseded_by`, `publication_receipt`. Artefactos narrativos pueden tener Markdown aprobado como contenido canónico; Planning/Jobs con stores estructurados publican Markdown proyectado y hash-linked. **Una sola autoridad por propiedad.**

## Directorios lógicos estables

`docs/00_product`, `01_requirements`, `02_architecture`, `03_security`, `04_quality`, `05_operations`, `06_miasi`, `07_standards`, `08_planning`, `09_evolution`, `10_release`; materialización lazy según PESP. El `TechnologyProfile` aprobado decide estructura fuente propia de stack; no imponer `src/` a todo lenguaje.

`outputs/` son borradores, logs y evidencia temporal. Markdown aprobado Pre-code/Planning en `docs/` versionado Git, consultable sin instalar DevPilot. Edición externa → DRIFT y reconciliación, nunca sync silencioso. Hash de bytes para ZIP; equivalencia de documentos controlada semánticamente ante LF/CRLF si política lo permite.

## Dos manifiestos de entrega

`ApplicationDeliverableManifest`: source, approved docs, lockfiles, release build, infra necesaria, runbook sin secretos. `EngineeringEvidenceManifest`: referencias a receipts, traces, QA, approvals y hashes en evidence store. Evitar .venv/cache/runtime DB/PII/API keys, rutas absolutas Windows y secretos en ZIP.

## Quality gates

Atomic publish, failure injection, hash provenance y lectura offline; sin doble autoridad, sin overwrites FROZEN, sin logs privados; restauración desde ZIP debe poder compilar/arrancar bajo Technology Profile documentado.

---

## Enmienda programática post-R02-06 · 187

**Revisión humana obligatoriamente Markdown:** cada propuesta narrativa seleccionable tiene archivo real `.md`, `candidate_id`, `revision`, `content_sha256`, `source_context_sha256`, `provider/model/prompt`, estado `DRAFT/REVIEWED/SELECTED/SUPERSEDED`, y lineage; copia de preview puede ser read-only, pero la edición Owner en UI produce revisión nueva con su propio hash. Prohibido editar un candidato histórico in-place o autoaprobar por el proveedor. Comparación de dos Markdown es optativa.

**Planning con autoridad estructurada:** el Owner revisa/edita una representación Markdown proyectada; DevPilot valida que los cambios se traduzcan explícita, reversiblemente y sin pérdida al JSON canónico mediante un workflow; el `.md` de Planning no puede convertirse por accidente en otra autoridad editable. Si un campo no puede round-trip, bloquear con explicación y ofrecer editor semántico de ese campo, no fingir persistencia. FROZEN publica una proyección humana hash-bound; stores estructurados siguen siendo única autoridad de estado.

Una publicación requiere quality gate específico, dependencias fresh, diff/preimage, approval Owner aplicable, apply atómico y `freeze_receipt`; controles de LF/CRLF comparan correctamente blobs Git y conversiones de archive sin false drift. Un archivo `.md` no se considera FROZEN por existir físicamente.

---

## Frontera de publicación conforme A188

Separar respuesta L/E/agent (`GENERATED` no confiable), candidato inmutable (`ADMITTED_FOR_OWNER_REVIEW`), calidad (`QUALITY_ACCEPTABLE`) y decisión aprobada (`APPROVED/FROZEN`) mediante el publisher/lifecycle existentes. Guardar perfil, fuentes upstream, hashes de revisión y pruebas; no publicar source desde el texto del modelo ni permitir reescrituras de FROZEN. Cambios editoriales inocuos no crean gates o approvals adicionales.
