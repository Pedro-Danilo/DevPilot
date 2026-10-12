---
doc_id: DEVPL-REB-118-P0-PUBLICATION
title: "P0 — autoridad puente publicada y alcance de supersession"
version: "1.0.0"
status: "APPROVED / PUBLICATION-GATED"
date: "2026-10-11"
owner_decision: OWNER-APPROVAL-2026-10-11-REBASELINE-116
supersedes_scope: "prospective D05/D06/SYNC-1 gating only"
implementation_authority: false
multiprovider_stop_lifted: false
---

# P0 — publicación limitada de successors Greenfield y Multiprovider

## Naturaleza y autoridad
La autoridad de esta publicación depende de **commit Git validado, promoción origin y ZIP limpio de HEAD**, junto al receipt G1 emitido por el operador. La mera presencia de este archivo no es G1 PASS. G0 fue aprobado por el Owner; los gates G2–G5 siguen PENDING.

La fuente autoritativa de este overlay documental es la rama determinística `official/devpilot-local`, en `docs/program_rebaseline_117/` y `.devpilot/docs_governance/rebaseline_p0_overlay.json`; el índice de autoridad de MP permanece físicamente intacto en STOP. El `mp_registry_state` es **PENDING_MP_IMPORT**, que solo puede cambiar durante P3-C luego de auditoría P3-A, estrategia P3-B y merge autorizado.

## Reglas activas SOLO para ejecuciones posteriores a G1
1. **Greenfield D05**: sustituir exclusivamente `repeat until MVP` como condición de autorización de D06 por `REBASELINED_STOP/PARTIAL_ACCEPTANCE` adjudicado en P1. RF-001..003 DONE; RF-004..008 diferidas por programa, no ejecutadas, sin editar stories FROZEN ni mentir sobre el MVP.
2. **Greenfield D06**: permite seis escenarios reproducibles de recuperación con evidencia, no exige MVP completo; un bloqueo de recuperación mantiene G3 BLOCK. No se autoriza Full Regression intermedia.
3. **Greenfield D07/D08 y 13-E**: no emitir PASS del release/E2E Pilot A; quedan DEFERRED/NOT-EVALUABLE-UNDER-OLD-MVP hasta sucesores aprobados. La aceptación integral debe demostrarse de manera real en Pilot B, sin heredar PASS ficticio.
4. **Multiprovider**: MP STOP sigue activo en P0, P1, P2, P3-A y P3-B; MP Source Registry, working tree y HEAD no se modifican. P3-C sigue prohibido sin auditoría detallada de ambas ramas, diagnóstico del código real instalado, matriz KEEP/ADAPT/DEPRECATE/NO_IMPORT y aprobación Owner posterior y específica del plan de sincronización. Se conserva la dirección determinístico→MP, merge sin rebase/force.
5. **MP-1B**: incluso luego de SYNC-1 PASS, requiere autorización de reprogramación del programa MP; G0/G1 no la concede.
6. **GENERAL-113**: el ModelAdapter local de Pilot A no habilita inferencia real ni licencia copiar un router paralelo a MP. Componentes se adjudican solo después de auditar el source MP.

## Precedencia sin pérdida histórica
- Las cláusulas **no afectadas** de Greenfield Charter/Brief/Sprint/Protocol/Runbook/Prompt/Backlog/Roadmap/Evidence conservan su fuerza; se guardan sus versiones históricas y su valor de trazabilidad.
- Las cláusulas incompatibles sobre la condición de finalización D05, elegibilidad D06, STOP/SYNC y Pilot A release quedan prospectivamente reemplazadas por `BRIDGE_GF_117.md`, `BRIDGE_MP_117.md`, `AUTHORITY_117.md`, `DECISION_116.md` y este índice. No se editan documentos FROZEN.
- Los documentos programáticos MP-1B..MP-8 quedan congelados en su estado; se reprogramarán **solo tras** SYNC-1 reforzado PASS. Ninguna edición en MP durante P0.
- P0 no ejecuta P1 ni adjudica RF-004; `STOP ACTIVE` se comprueba en cada fase.

## Matriz de sucesión de las fuentes históricas
| Fuente histórica exacta (paquete externo aprobado) | Cláusula sustituida para futuro | Fuente sucesora |
|---|---|---|
| Greenfield `SPRINT_13D_v1_3_APPROVED_REBOUND.md` | D05 repeat until MVP; D06 eligibility; D07/D08 release | `BRIDGE_GF_117.md` y `GATES_117.md` |
| Greenfield `PROTOCOL_13D_v1_2_APPROVED_REBOUND.md` | D05/D06 PASS/BLOCK, gate de D06 | `BRIDGE_GF_117.md` |
| Greenfield `RUNBOOK_13D_v1_2_APPROVED_REBOUND.md` | repetición de historias, secuencia tras D06 | `BRIDGE_GF_117.md` |
| Greenfield `PROMPT_13D_v1_3_APPROVED_REBOUND.md` | emisión de RUN_03 RF-004 por defecto | `SPRINT_P0_117.md` → sprint P1 con G1 |
| Greenfield Charter/Brief, roadmap/backlog/evidence | E2E Pilot A/8 historias como único cierre | `BRIDGE_GF_117.md` y `CONTRACT_MAP_117.md` |
| Greenfield `SPRINT_DEVPL_GSDLC_13_E_v1_1_0_APPROVED.md` | cierre E2E sobre Pilot A incompleto | `BRIDGE_GF_117.md` |
| MP `STOP_MULTIPROVIDER_AFTER_MP_1A_v1_0_0_APPROVED.md` | requisito D05 MVP PASS antes de sync | `BRIDGE_MP_117.md` |
| MP `MP_V2_SYNCHRONIZATION_GATE_PROTOCOL_v1_0_0_APPROVED.md` | elegibilidad sync y auditoría previa | `BRIDGE_MP_117.md`, `AUDIT_SYNC1_117.md` |
| MP `ADR-MP-V2-008-branch-worktree-sync-and-final-convergence_v1_0_0_APPROVED.md` | calendario; no dirección de merge ni integridad | `ADR-DEVPL-REB-117.md` |
| MP Pilot Strategy/Program/Master Roadmap | hito Pilot A E2E como prerequisite | `BRIDGE_MP_117.md`; replan global pos-P3 |

## Gate de salida P0
**G1 PASS** solo con: comprobación del baseline de plataforma `e5ed2592...`, Pilot A `0f5f1518...`, STOP MP `54085701...`; Source Registry rebind válido; SHA del overlay y docs registrado; 0 cambios Pilot A y MP; pytest focal/documental PASS; Git upstream/remoto sincronizados; repo limpio completo `repo_466` y SHA-256; receipt persistido G1. G1 nunca declara G2 ni G3.

Si falta un prerequisito o se altera alguna fuente fuera de los paths declarados: `BLOCK`, sin rebase, limpieza destructiva, parche de UI o Full Regression.
