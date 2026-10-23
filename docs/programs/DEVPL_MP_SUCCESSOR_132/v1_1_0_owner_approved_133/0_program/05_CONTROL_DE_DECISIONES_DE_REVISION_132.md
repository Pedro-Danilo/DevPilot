---
doc_id: DEVPL-MP-SUCCESSOR-132-05_CONTROL_DE_DECISIONES_DE_REVISION_132
title: "Matriz de incorporación de todas las decisiones recientes"
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

# Matriz de incorporación de todas las decisiones recientes

## 1. Principio de cobertura

Esta matriz responde a las dos revisiones arquitectónicas que precedieron la solicitud de la nueva versión. Cada decisión tiene ubicación, gate y condición de prueba; nada se considera ejecutado por estar escrito.

| ID | Decisión confirmada/recomendada | Autoridad v1.1 | Criterio verificable |
|---|---|---|---|
| DEC-01 | MIPSoftware base obligatorio, MIASI por componente/risgo probado | PESP, ADR-001, R1/R7 | Applicability con rationale y waiver controlado |
| DEC-02 | Artifact Profile mínimo/recomendado/condicional/N-A; no generar plantillas vacías | Catalog/Coverage, R1–R8 | Gates por riesgo, datos, dominio y deploy |
| DEC-03 | Documento Pre-code histórico 7/7 es mínimo, no catálogo total | R2/R3/R4, Catalog | Data/API/UX/Ops condicionales, coverage real |
| DEC-04 | Estructura documental estable, código por Technology Profile | Layout ADR-006, Publication, R1/R3 | Bootstrap neutral; scaffold tras Architecture |
| DEC-05 | Markdown durable pre-code/planning y una autoridad por propiedad | ADR-002, Publication, R1–R4 | Hash/link/approval, consulta sin runtime |
| DEC-06 | FROZEN inmutable con successor e impacto | ADR-003, ChangeImpact, R1–R5 | No edición in-place, revalidation selectiva |
| DEC-07 | Documentación distinta de evidencia; manifest portable | Layout/Publication, R6 | Sin secretos ni runtime privado en deliverable |
| DEC-08 | Artifact Coverage por cada etapa | Catalog Contract, R1–R10 | Required/conditional/recommended/N-A y PASS/WARN/BLOCK |
| DEC-09 | D permanente para gobernanza, L preferente para semántica compleja | Route Policy, ADR-004, R1/R2/R5 | Fallback equivalente/reducido/no disponible explícito |
| DEC-10 | ModelAdapter capability/eval real antes de `ELIGIBLE_FOR_TASK` | Model Capability, R1/R2 | Evaluación hardware/modelo/dataset, no health-only |
| DEC-11 | L real en R2, Story arbitraria sin templates por RF en R5 | R2/R5, Pilot B | Inferencia real tipada, tests y dos dominios |
| DEC-12 | External E opt-in y separado Pilot C; egress/cost/PII/secret | ADR-010, R8, Pilot C | Rechazo default antes de HTTP |
| DEC-13 | Auditoría focal obligatoria antes de toda mutación, `NO-OP` válido | Audit-first, R0–R10 | Reuse/Delta Map, HEAD y allowlist |
| DEC-14 | Gate B migración worktree antes de 1er source change | Git, ADR-008, R0 | Preflight Windows+rollback, sin cambiar identidad Git |
| DEC-15 | 11 backlogs por ola y un índice derivado (no once programas independientes) | Backlogs R0..R10/index | Cada ID un owner, referencias transversales |
| DEC-16 | ADRs sucesores auditados, no uno por item/sprint | ADR-001..011 | Decision refs, alternativas, compatibilidad |
| DEC-17 | 10 contratos transversales especificados y versionables | `2_contratos` | Inputs/outputs/invariantes/gates |
| DEC-18 | Configuración temprana: global/proyecto/policy/runtime/diagnósticos distintos | ADR-007/Config Matrix, R0/R1/R2 | Effective-value/authority y restart/persistence |
| DEC-19 | UI Settings no write-anything; controls runtime separados | Config + ADR-011 | Approval/deny/revoke/feedback, no leaks |
| DEC-20 | Hallazgos MP-0F progressive disclosure corregidos sólo parcialmente | Ledger coverage + R0/R1/R9 | Mantener carry-forward de settings persistentes |
| DEC-21 | UX estado/feedback próximo al botón, sin PENDING vs PASS contradictorio | ADR-011, R1–R5 | Browser state projection sin stale CTAs |
| DEC-22 | UX histórico por S0–S3, no cerrar sin evidencia | Ledger mapping/R2–R9 | Tests + decisión ID y evidencias |
| DEC-23 | Planning no one-shot; evoluciones/release successors | Change Impact, R1–R6 | CR→impact→Owner→backlog→sprint→release |
| DEC-24 | Owner aprueba scope y cambios sensibles; agentes no autopermisos | ADR-005/009, R5/R7 | Sin source mutation agent/provider |
| DEC-25 | Separar G5 admin, programa, sprint, promoción y product acceptance | Authority Register, R0 | Recibos distintos con hashes y actos humanos |
| DEC-26 | Pilot B continuo B0..B7, Pilot C isolated, segundo dominio | Pilot Charters, R2–R10 | E2E UI, no terminal ni prebuilt RFs |
| DEC-27 | R9 deja de ser vertedero de funciones transversales tardías | Roadmap, backlogs | Settings/FROZEN/UX desde R1; R9 consolida |
| DEC-28 | Riesgos/preimage/rollbacks/SBOM/secret/observability/DR | Risks + gates, R5–R10 | Aceptación industrial por evidencia real |
| DEC-29 | Mantener ADR/contratos de MP v2.1 compatibles, SIN reimportar viejos prompts | Supersession/Traceability | KEEP/ADAPT/DEFERRED/NO-IMPORT por documento |
| DEC-30 | Revisión Owner de waiver, clasificación MIASI y estándares | PESP + Authority Register | Audit trail y excepciones válidas |

## 2. Regla antirregresión de decisiones

Si un futuro backlog, ADR o prompt reemplaza una de estas decisiones, debe citar `DEC-XX`, proponer su sucesor y justificar compatibilidad o migración; nunca se introduce una excepción silenciosa. La tabla no sustituye contratos: sirve como checklist programático de cobertura.


---

## Decisión M1 post-Windows — 15-10-2026

- R01-15/COR171 `CLOSED/WINDOWS_PASS_WITH_FINDINGS`, `M1_REPORT_171.json`: `PASS_WITH_FINDINGS`; HEAD `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc`.
- R01 backlog cerrado para alcance de primera vertical determinista, sin afirmar modelos reales ni E2E integral Pilot B.
- R02 desagregado en diez micro-sprints y diez prompts **DRAFT**; Owner no ha dado aprobación de ejecución individual. Esta decisión autoriza preparación documental exclusivamente.
- Primera mutación R02: drift documental ACTIVO a reconciliar por completo (test/estado/registros/diff por impacto), preservando documentos y evidencias históricas.

---

## Registro de incorporación A188

- `MP132-OWNER-DECISION-188`: **APPROVED**, 2026-10-22; objeto enmienda `12_ENMIENDA_188_APROBADA.md`, ADR-016 y nuevo contrato transversal. Se adoptan sin superseder ADR-013/187 ni autorizar sprints.
- Source code R02-07: commit `3a0a170f3c646e9955966576dd9212d3f87450e6`; el cierre ya ocurrió y no se reabre.
- A188 introduce evaluación de generalización por perfil, prueba multi-dominio y ahorro del esfuerzo Owner. Se asigna a olas sucesoras sin nuevo backlog duplicado.
