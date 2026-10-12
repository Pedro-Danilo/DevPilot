---
doc_id: "DEVPL-REB-117-CONTRACT-MAP"
title: "Matriz de contratos y artefactos a reconciliar"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Matriz de contratos y artefactos a reconciliar

## Fuente de verdad consultada
Paquetes originales ZIP `DEVPL_GSDLC_13_GREENFIELD_PACKAGE_vig.zip` y `DEVPL_MULTIPROVIDER_V2_1_APPROVED_PACKAGE_vig.zip`; propuesta 116 adjunta y repo465. Conservar íntegros sus snapshots, no modificar entradas del ZIP.

## Greenfield — P0 crea successors/rebind, P1/P2 ejecutan el contrato nuevo
| Fuente histórica exacta o familia | Acción y cambio requerido | Momento de autoridad |
|---|---|---|
| `03_DEVPL_GREENFIELD_E2E_PRODUCT_ACCEPTANCE_CHARTER_v1_1_0_APPROVED.md` | Addendum: E2E inventario+venta sigue incumplido por Pilot A; objetivo se traslada a Pilot B sin reescribir necesidad | P0 índice puente |
| `04_DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_REBASELINE_v2_1_0_APPROVED.md` | Successor delimita D05 partial, D06 bounded y posterga D07/D08/13-E | P0 |
| `DEVPL_GSDLC_13_GREENFIELD_REAL_PRODUCT_ACCEPTANCE_ROADMAP_v1_1_0_APPROVED.md` | Puente P0–P3 y referencia a E2E futuro | P0 |
| `DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_BACKLOG_v1_1_0_APPROVED.md` | RF004–008 deferred por programa, no DONE; cleanup de items de alcance | P0/P1 evidence |
| `SPRINT_13D_v1_3_APPROVED_REBOUND.md` | D05 freeze / D06 bounded, D07/D08 no ejecución Pilot A | P0 |
| `PROTOCOL_13D_v1_2_APPROVED_REBOUND.md` | PASS/BLOCK distingue partial y MVP; D06 escenarios y no Full | P0 |
| `RUNBOOK_13D_v1_2_APPROVED_REBOUND.md` | Dejar de repetir story 4+; secuencia G2→G3→P3 audit | P0 |
| `PROMPT_13D_v1_3_APPROVED_REBOUND.md` | Sustituir comando ejecutar next story por P1 freeze | P0 |
| `DEVPL_GSDLC_13_GREENFIELD_PILOT_PROJECT_BRIEF_v1_1_0_APPROVED.md` | Estado de cumplimiento, business need histórico intacto | P0 |
| `DEVPL_GSDLC_13_ACCEPTANCE_EVIDENCE_PLAN_v1_1_0_APPROVED.md` | Evidencias D05 partial, D06 seis escenarios y P3; no capturas consola duplicadas | P0 |
| `SPRINT_DEVPL_GSDLC_13_E...` y `05_PROMPT_DEVPL_GSDLC_13_E...` | E2E antiguo no evaluable; reasignación futura sin falsa adjudicación | P0 indicador; successor profundo pos-P3 |
| índices/manifest/ledger/catalog/source registry Greenfield | lineage y active-authority sin sobrescribir histórico | P0 + P1 evidencia |

## Multiprovider — solo bridge ahora, replan global *después* de P3
| Fuente exacta | Acciones | Timing |
|---|---|---|
| `STOP_MULTIPROVIDER_AFTER_MP_1A_v1_0_0_APPROVED.md` | Registrar successor de condición de reanudación G2/G3/G4/G5, STOP sigue activo | Puente externo P0; bind interno tras SYNC1 |
| `MP_V2_SYNCHRONIZATION_GATE_PROTOCOL_v1_0_0_APPROVED.md` | Auditoría dual obligatoria + aprobación estrategia antes del merge | Puente P0 |
| `ADR-MP-V2-008-branch-worktree-sync-and-final-convergence_v1_0_0_APPROVED.md` | Successor de calendario/condición, misma dirección y prohibición rebase | P0 |
| `MP_V2_GIT_BRANCH_WORKTREE_GOVERNANCE_v1_0_0_APPROVED.md` | Mantener Git 3-estado, clean/remote, worktrees separados | Reafirmar P0; no rewrite |
| `MP_V2_SOURCE_REGISTRY_AND_DOCUMENTATION_REBIND_PLAN_v1_0_0_APPROVED.md` | Registrar documentación puente externamente mientras STOP; source MP real al merge | P0 y P3-C |
| `MP_V2_PILOT_STRATEGY_AND_ACCEPTANCE_CHARTER_v1_0_0_APPROVED.md` | Reconocer Pilot A parcial; Pilot B futuro E2E completo | Addendum P0, detalle pos-P3 |
| `DEVPL_MULTIPROVIDER_IMPLEMENTATION_PROGRAM_v2_1_0_APPROVED.md` | NO reprogramar olas aún: congelar secuencia posterior y ordenar revisión tras G5 | Anotación P0, successor global pos-P3 |
| `MP_V2_MASTER_ROADMAP_v1_0_0_APPROVED.md`, `MP_V2_MASTER_BACKLOG_v1_0_0_APPROVED.md`, `MP_V2_WAVE_DEPENDENCY_MATRIX_v1_0_0_APPROVED.md` | Dejar olas MP-1B..8 sin ejecución y preparar ajuste con baseline fusionado | Pos-P3 |
| `MP_1_PRODUCT_DEFINITION_SPRINT_PLAN_v1_0_0_APPROVED.md` y 1B PROPOSED | NO lanzar MP-1B bajo autoridad MP vieja, rebind tras G5 | Pos-P3 |
| ADR-MP-V2-001..007, especialmente 007 | Mantener invariantes de autoridad del core y política de candidates | Sin cambio salvo incompatibilidad probada |

## Enmienda sin mutar worktree congelado
La decisión Owner aprueba estos successors como **program docs** externos; durante P0 se versiona y publica un *authority overlay* con manifest/hash e identificadores de los históricos superseded. La branch MP conserva exactamente su STOP commit. En P3-C, tras autorización nueva, la autoridad de código y el Source Registry MP se actualizan conjuntamente con la fusión. Si no existe un soporte canónico seguro para ese overlay, P0 debe BLOCK hasta acordarlo con Owner; nunca fingir escritura MP.
