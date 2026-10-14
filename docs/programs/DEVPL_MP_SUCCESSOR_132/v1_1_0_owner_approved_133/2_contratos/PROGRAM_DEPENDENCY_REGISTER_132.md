---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_DEPENDENCY_REGISTER_132
title: "Dependencias, owner de backlog y bloqueos entre olas"
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

# Dependencias, owner de backlog y bloqueos entre olas

## Unidad de dependencia

`dependency_id`, `source_item_id`, `target_item_id_or_gate`, `dependency_kind HARD|SOFT|OPTIONAL`, `required_capability`, `evidence`, `owner`, `current_status`, `decision_ref`, `allowed_parallelism`. Cada item pertenece a un único backlog de ola; el índice maestro deriva links, no crea clones de prioridad/estado.

## Cadena crítica

R0 program/Git/authority → R1 Candidate/Route/PESP/Coverage/Settings mínimo → R2 L real/Product Definition → R3 design/scaffold → R4 planning/evolution → R5 arbitrary Story→Quality/Git → R6 release/rollback → R10 independent E2E. R7 read-only agents puede empezar con fundamentos R1/R3, pero write agents sólo tras guard R5 y autorización específica. R8 provider externo separado, no dependiente para Pilot B local-first, requerido para `EXTERNAL_ENABLED`. R9 acumula hardening desde temprano y gate final tras funcionalidad relevante.

## Dependencias más sensibles

- Git worktree R0-03 decide carpeta antes del **primer source mutation**, no requiere borrar 63 worktrees históricos.
- PESP/Artifact Profiles requiere estándares versionados, no impedir Pilot B por todos los perfiles del mundo.
- Publication/Successor antes de FROZEN Pilot B para evitar artefactos provisionales sin lineage.
- Settings autoridad antes de exponer local model UX; route/eval antes de declarar modelo `ELIGIBLE`.
- ADR external y CostGuard antes de cualquier llamada API remota.
- Config Agent trust/Tools antes de handoffs mutativos.
- D06 process crash/HTTP/Git receipt-loss antes de claim recuperación producción, no confundir con S1–S6 PASS fixture.

## Replanificación

Si auditoría declara `NO-OP`, cerrar item con receipt, sin commit nuevo. Si descubre dependencia contradictoria, bloquear el sprint y publicar successor de dependencias/roadmap con Owner; no reordenar silenciosamente a mitad de ejecución.
