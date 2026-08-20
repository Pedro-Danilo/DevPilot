---
doc_id: "DEVPL-GSDLC-04-A-CLOSURE-REPORT"
title: "DEVPL-GSDLC-04-A — Artifact lifecycle, source and provenance contracts"
status: "pass-candidate/pre-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "pending_windows_validation_and_owner_adjudication"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-04"
micro_sprint: "DEVPL-GSDLC-04-A"
---

# 1. Estado

`PASS-CANDIDATE / PRE-WINDOWS`.

No es `CLOSED/PASS`. Requiere evidencia Windows y adjudicación explícita del owner.

# 2. Implementación

04-A incorpora el cierre owner-adjudicated de GSDLC-03 y define ArtifactState, ArtifactProvenance, ArtifactLifecycleRecord, policy por profile y ArtifactLifecycleService server-authoritative.

No persiste drafts, no escribe documentos, no agrega API/UI routes y no crea un segundo writer. UOC-004/UOC-005 permanecen predecessors.

# 3. Capacidades

- 9 estados lifecycle;
- 6 source types;
- raw + normalized SHA-256;
- artifact version + exact Git base commit;
- actor/session/reviewer;
- lineage;
- role transition matrix;
- FROZEN drift → REVALIDATION_REQUIRED;
- path/type/size/SecretGuard policy;
- ArtifactProfileRegistry binding.

# 4. Pruebas

La evidencia machine-readable de validación local/Windows debe confirmar schemas, lifecycle matrix, negative suite, UOC-004/UOC-005 preservation, Project State, Source Registry, Docs Governance, TCR y Test Impact.

Full regression = 0. Browser acceptance = 0.

# 5. Riesgos y limitaciones

- editor/draft persistence: 04-B;
- paste/upload/import runtime: 04-C;
- approval/apply/freeze E2E: 04-D;
- external reconciliation/browser: 04-E;
- AGENT_ASSISTED es provenance-only.

# 6. PASS/BLOCK

PASS-CANDIDATE si la validación focal/acumulativa queda verde, S0/S1=0 y no existen paths inesperados.

BLOCK si se detectan writes, UI/browser authority, un segundo writer, source type desconocido aceptado, drift histórico/documental o full regression.

# 7. Verificación

Los comandos Windows únicos se entregan exclusivamente en `GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_A_v1_0_0.md`.
