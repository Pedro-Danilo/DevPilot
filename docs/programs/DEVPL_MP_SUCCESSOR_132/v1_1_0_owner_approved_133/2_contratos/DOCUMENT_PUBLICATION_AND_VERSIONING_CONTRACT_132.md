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
