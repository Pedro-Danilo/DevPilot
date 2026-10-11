---
doc_id: "DEVPL-REB-117-ROADMAP"
title: "Roadmap de transición P0–P3"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Roadmap de transición P0–P3

## Norte estratégico
Construir una plataforma general de ingeniería de software asistida por IA conforme a los estándares de proyecto MIPSoftware y MIASI, con generación contextual posterior y núcleo de autoridad determinístico estable. **No crear un generador por story.** Mantener separación control plane/generation plane; cualquier propuesta de LLM sigue sin autoridad de apply/Git.

## Secuencia de decisión
| Fase | Estado al emitir este paquete | Actividades | Salida verificable | Gate que habilita siguiente |
|---|---|---|---|---|
| G0 | PASS (decisión Owner) | Aprobar rebaseline | Decisión 116 elevada y archivada | P0 autorizado documentalmente |
| P0 — contrato puente | NOT STARTED | Alinear dos programas, charter/stop, autoridad, registry, evidencia y entrega aprobada | `G1 DOCUMENTARY_AUTHORITY_PASS` | P1 |
| P1 — freeze D05 | NOT STARTED | Auditar RF001–003, cinco pendientes, UX, estado técnico, ausencia de operaciones en curso | `D05 PARTIAL_ACCEPTANCE / REBASELINED_STOP` | P2 |
| P2 — D06 revisado | NOT STARTED | Seis escenarios controlados de recovery, 2 lotes + cierre | `D06 REBASELINED/PASS` | P3-A |
| P3-A — auditoría pre-SYNC | NOT STARTED | **Auditoría integral obligatoria de las dos ramas**, inventario de capacidades/contratos y matriz de reutilización | `PRE_SYNC_AUDIT_PASS` y opciones de integración | P3-B |
| P3-B — decisión de estrategia | NOT STARTED | Diseñar merge más seguro según auditoría; resolver KEEP/ADAPT/DEPRECATE, migraciones y compatibilidad | `SYNC_STRATEGY_OWNER_APPROVED`, plan exacto | P3-C |
| P3-C — SYNC-1 controlado | NOT STARTED | Implementar sólo plan aprobado, verificar y promover determinístico→MP | `SYNC1/PASS`, nuevo baseline MP con ZIP | Revisión **posterior** del programa MP |

## Dependencias y restricciones
`G0 → P0/G1 → P1/G2 → P2/G3 → P3-A/G4a → P3-B/G4b → P3-C/G5`. Los gates no son intercambiables. Una auditoría de P3-A NO autoriza automáticamente realizar el merge. Si se descubre incompatibilidad crítica, STOP permanece y se emite correctivo/alternativa aprobable.

## Después de P3 (NO planificado en detalle ahora)
Auditar resultado de SYNC-1 y **solo entonces** actualizar programa Multiprovider v2.1 (roadmap, backlog, dependencias, olas, DoD, release/Pilot B, MP-1B). Dejar `MP-1B` bloqueado hasta ese rebaseline posterior aprobado, aunque SYNC1 sea PASS, si aún no hay plan de sucesión. Pilot B será quien pruebe una app real E2E generalizable; no trasladar automáticamente sus historias ni declarar MVP Pilot A realizado.

## Full Regression y costo
Se define **un backlog transversal P0–P3**. P0–P2 y P3-A/B usan pruebas focales/acumulativas y análisis de impacto, `full_regression=0`. Solo P3-C, como micro-sprint de cierre del backlog de transición, podrá ejecutar **una** Full Regression de cierre si su política aprobada y el alcance del merge así lo establecen, con presupuesto y receipt; una excepción intermedia exige riesgo documentado y aprobación Owner, no ejecución espontánea. No duplicar una corrida válida por interrupciones.
