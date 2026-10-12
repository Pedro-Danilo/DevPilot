---
doc_id: "DEVPL-REB-117-GF-BRIDGE"
title: "Successor puente de Greenfield: D05, D06 y alcance de salida"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# Successor puente de Greenfield: D05, D06 y alcance de salida

## Ámbito del successor
Complementa y, **una vez registrado como activo en P0**, sustituye para la ejecución futura las cláusulas incompatibles de:
`SPRINT_13D_v1_3_APPROVED_REBOUND`, `PROTOCOL_13D_v1_2_APPROVED_REBOUND`, `RUNBOOK_13D_v1_2_APPROVED_REBOUND`, `PROMPT_13D_v1_3_APPROVED_REBOUND`, charter/brief/roadmap/backlog/evidence originales **solo en las disposiciones indicadas**. La matriz `AUTORIDAD_Y_SUPERSESSION_117` es obligatoria. No altera su ejecución histórica ni el business need original.

## Reglas nuevas
1. Cerrar D05 bajo código nuevo `REBASELINED_STOP/PARTIAL_ACCEPTANCE`, con RF001–003 DONE y RF004–008 `DEFERRED_BY_PROGRAM_DECISION / NOT_IMPLEMENTED`. El estado `READY` dentro del backlog congelado no se altera para hacer cuadrar el documento.
2. Prohibir nuevos incrementos específicos Pilot A, reinicio de RF003 y RUN_03/RF004 sin decisión nueva de programa. El proyecto permanece snapshot/fixture para recuperación; no fabricar MVP.
3. Calificar D06 contra el estado real de construcción a través de seis escenarios gobernados, en fixtures copiadas aisladas para escenarios disruptivos; recovery no depende de un MVP de 8 stories.
4. Tras D06/PASS, **auditoría P3-A previa a cualquier integración**, no sync automática. D07/D08/13-E del charter original quedan `DEFERRED / NOT-EVALUABLE-UNDER-OLD-MVP`, no PASS.
5. Pilot B absorberá en futuro programa MP revisado la demostración E2E real de inventario+venta, release/install/rollback y generalización. Esta reasignación es un compromiso de programa, no prueba de que Pilot B ya cumpla.
6. D01–D04, aprobaciones, artifacts FROZEN, commits y evidencias permanecen inmutables; 13-D full regression sigue en 0.

## Exit conditions
Contrato puente publicado + Source Registry y links de navegación/Run Cards actualizados en P0, prohibiciones verificadas; sólo adjudicación P1 puede declarar D05 partial y habilitar D06. Si source vigente obliga a operar contrary, activar documental/focal corrective; nunca parchear los estados de proyecto para forzar el gate.
