---
doc_id: "ADR-GSDLC-004-ARTIFACT-LIFECYCLE-AUTHORITY"
title: "ADR-GSDLC-004 — Server-authoritative artifact lifecycle and provenance"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "approved_for_04_a_candidate"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-A"
---

# Context

GSDLC-04 necesita gobernar autoría e import sin convertir la UI, localStorage o un nuevo writer en una segunda fuente de verdad. DevPilot ya dispone de ArtifactProfileRegistry, planning UOC-004 y apply/rollback UOC-005.

# Decision

1. El lifecycle/provenance es server-authoritative y determinístico.
2. `ArtifactLifecycleService` es metadata-only en 04-A.
3. `ArtifactProfileRegistry` conserva la selección de profile.
4. UOC-004/UOC-005 siguen siendo planning/apply predecessors.
5. FROZEN solo pierde vigencia por drift de hash y entra a REVALIDATION_REQUIRED.
6. Browser storage es UX-only.
7. AGENT_ASSISTED se registra como provenance sin ejecución agentic.
8. No se agregan rutas API/UI ni Sensitive Actions en 04-A.

# Consequences

Positivas:
- no segundo motor de escritura;
- transition matrix testeable;
- provenance auditable;
- compatibilidad con editor/import futuros.

Costos:
- 04-B deberá persistir drafts de forma separada;
- 04-C deberá implementar upload/import respetando esta policy;
- 04-D deberá componer approval/apply sin bypass.

# PASS/BLOCK

PASS si lifecycle/provenance no muta source y todos los gates son determinísticos.

BLOCK si UI adquiere authority, aparece un writer paralelo, se permite FROZEN editable o se aceptan sources desconocidos.

# Riesgos

La política inicial permite authoring/import en perfiles existentes; futuras restricciones por profile deben evolucionar el policy catalog, no ArtifactProfileRegistry.

# Verificación

Validar schemas, policy, tests 04-A, UOC-004/UOC-005 impacted contracts, Docs Governance, TCR, Project State y Test Impact. Full regression está prohibida por rutina en 04-A.
