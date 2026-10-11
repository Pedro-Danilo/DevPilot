---
doc_id: "DEVPL-REB-117-BACKLOG"
title: "Backlog ejecutable de transición P0–P3"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Backlog ejecutable de transición P0–P3

## Reglas de priorización
Todos los items respetan `operator_project_writes=0` para Pilot A, preservación de FROZEN/commits, límites de permisos, no operaciones destructivas, audit-first y minimal change. El backlog mide **seguridad, utilidad de los sucesores y cierre verificable**, no cantidad de archivos.

| ID | Prioridad | Micro-sprint | Resultado requerido | Evidencia / criterio de aceptación |
|---|---|---|---|---|
| RB-000 | P0 | P0 | Decisión G0 y expediente de fuentes | Documento approved, hashes, baseline y fuente original preservados |
| RB-001 | P0 | P0 | Contrato puente Greenfield D05/D06/13-E | Successor publicado; MVP y release NO acreditados |
| RB-002 | P0 | P0 | Contrato puente MP STOP/SYNC, ADR y fuente | STOP=ACTIVE; sin habilitar MP-1B; Source Registry íntegro |
| RB-003 | P0 | P0 | Rebind de índices, protocolos, roadmap, backlog, ejecución | Trazabilidad canónica y no referencias vigentes contradictorias; PASS tests docs |
| RB-010 | P0 | P1 | Inventario RF001/002/003 | SHAs, quality, jobs, commit, evidencia, UX y riesgos reconciliados |
| RB-011 | P0 | P1 | Residual RF004..008 | `DEFERRED_BY_PROGRAM_DECISION / NOT_IMPLEMENTED`, sin alterar estado FROZEN |
| RB-012 | P0 | P1 | D05 stop controlado | Sin StoryExecution mutativa abierta, baseline preservado y adjudicación parcial |
| RB-020 | P0 | P2-A | Recovery sesión/restart | No doble operación; autoridad recuperada |
| RB-021 | P0 | P2-A | Interrupción controlada | Reanudación segura; sin doble apply/approval |
| RB-022 | P0 | P2-A | Drift por edición externa | Preimage invalida el plan; bloqueo explicable; restaura fixture |
| RB-023 | P0 | P2-B | Dirty worktree gobernado | Distingue runtime/`outputs/` y source ajeno; no stage indebido |
| RB-024 | P0 | P2-B | Branch/divergence/conflict | Detecta y resuelve/bloquea sin destructive Git |
| RB-025 | P0 | P2-B | Stale lock | Recuperación segura y auditable; sin bypass de exclusión |
| RB-026 | P0 | P2-C | Adjudicación D06 | 6/6 escenarios respaldados; sin pérdida de evidencias ni SourceWrite externo |
| RB-030 | P0 | P3-A | **Auditoría exhaustiva de estado determinístico final** | Mapa de subsistemas, historias, contratos, calidad, autoridad Git, cambios desde fork y riesgos |
| RB-031 | P0 | P3-A | **Auditoría exhaustiva de capacidades MP instaladas** | Extraer y contrastar código, servicios, adapters, policies, tests, schemas, ADR y plan MP |
| RB-032 | P0 | P3-A | Delta y reuse map | Matriz KEEP/ADAPT/DEPRECATE/NOT-IMPORT; dueño único; equivalencia y gaps |
| RB-033 | P0 | P3-B | Evaluación de alternativas de sincronización | Riesgos, costo, compatibilidad, recuperación, precedencia, rollback |
| RB-034 | P0 | P3-B | Estrategia SYNC-1 exacta con aprobación Owner | Branches, commits, conflictos previstos, paths, plan, autorización distinta |
| RB-035 | P0 | P3-C | Sincronización unidireccional gobernada | Merge det→MP o BLOCK autorizado por auditoría; sin rebase/cherry-pick masivo |
| RB-036 | P0 | P3-C | Validación/rebind/convergencia | Tests paridad, docs, smoke, security, Source Registry, PROMOTION y ZIP completo SHA |
| RB-037 | P0 | P3-C | Adjudicación de STOP y handoff | Solo SYNC1/PASS permite considerar lifting; successor MP roadmap posterior requerido |

## Fuera de alcance deliberado
Implementar RF004–008 en Pilot A; equiparar D05 partial con MVP; limpiar `outputs/`; D07/D08 Pilot A bajo old charter; MP-1B/MP-4; migración masiva de runtime; inventar reglas MIASI/MIPSoftware; LLM real en Pilot A; alterar Source Registry retroactivamente; forzar Git. El programa MP será replanificado después de P3 con estado real.

## Política de deuda y discrepancia
Diferenciar `BLOCK_FUNCIONAL`, `DOCUMENTAL_DRIFT`, `UX_OBSERVE_ONLY`, `ARCHITECTURE_GAP`, `DEFERRED_SCOPE`. S0/S1 críticos y fallos de autoridad bloquean. Cada correctivo genera ZIP limpio y hash desde commit promovido. No repetir un run terminal PASS ni Full Regression por fallos cosméticos o EOL CRLF/LF.
