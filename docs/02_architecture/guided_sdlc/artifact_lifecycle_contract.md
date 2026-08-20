---
doc_id: "DEVPL-GSDLC-04-A-ARTIFACT-LIFECYCLE-CONTRACT"
title: "DEVPL-GSDLC-04-A — Artifact lifecycle, source and provenance contract"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "approved_for_04_a_candidate"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-A"
---

# 1. Objetivo

Establecer una autoridad server-side determinística para estado, source type, hash, version, Git base, actor/session, reviewer y lineage de artefactos Markdown/JSON gobernados.

# 2. Modelo de lifecycle

`MISSING → DRAFT → VALIDATING → FINDINGS/READY_FOR_REVIEW → APPROVAL_REQUIRED → APPROVED → FROZEN`.

Remediación: `FINDINGS → DRAFT`.

Drift externo: `APPROVED|FROZEN → REVALIDATION_REQUIRED → DRAFT`.

`FROZEN` no tiene transición actor-driven de edición. El único successor directo es `REVALIDATION_REQUIRED`, disparado exclusivamente por drift de hash.

# 3. Provenance

Todo draft exige actor autenticado, rol canónico, session principal, reviewer asignado, base commit exacto, source hash, normalized hash, artifact version, timestamps y lineage.

Source types: `MANUAL`, `PASTE`, `UPLOAD`, `IMPORT`, `AGENT_ASSISTED`, `EXTERNAL_EDITOR`.

`AGENT_ASSISTED` es solo una clasificación de provenance en 04-A. No habilita ejecución agentic.

# 4. Profile binding

`ArtifactProfileRegistry` sigue siendo la autoridad para seleccionar perfiles Markdown. `.devpilot/artifacts/artifact_lifecycle_policy.json` referencia IDs de perfil y agrega exclusivamente permisos de authoring/import, validators y necesidad de approval. JSON usa el perfil reservado `structured-json`.

# 5. Escritura

04-A no persiste drafts ni modifica documentos. `WorkspaceEditPlanApplicationService` (UOC-004) y `WorkspaceEditExecutionApplicationService` (UOC-005) permanecen los predecessors de planning/apply. No se introduce un segundo motor de escritura.

# 6. Seguridad

- path repo-relative, canonical y sin traversal;
- `.md/.json` allowlist contractual;
- máximo 1 MiB por source;
- symlink target denegado;
- SecretGuard bloquea auto-version de contenido secret-bearing;
- auth/RBAC/approval no se delegan a browser storage;
- network/API externas deshabilitadas;
- runtime DBs no son source state.

# 7. PASS/BLOCK

PASS:
- schemas y policy válidos;
- matrix de transiciones legal;
- transiciones ilegales/roles incorrectos bloqueados;
- provenance/hash determinísticos;
- drift de APPROVED/FROZEN produce REVALIDATION_REQUIRED;
- `source_mutations_performed=false`.

BLOCK:
- source type desconocido;
- actor/session/reviewer faltante;
- role no canónico;
- path escape, extensión o filename inválido;
- secret-bearing source;
- transición no declarada;
- intento actor-driven de mutar FROZEN.

# 8. Riesgos y limitaciones

Esta es una primera versión contractual. Persistencia de drafts/editor corresponde a 04-B; paste/upload/import runtime a 04-C; approval/apply/freeze end-to-end a 04-D; reconciliación UI y browser closure a 04-E.

# 9. Verificación

La guía operativa de 04-A define los comandos Windows autoritativos. Este documento no habilita full regression ni browser acceptance en 04-A.
