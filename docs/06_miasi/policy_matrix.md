---
title: "Policy Matrix — DevPilot Local"
doc_id: "DEVPL-MIASI-POLICY-MATRIX"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
baseline_role: "precode_approved_baseline"
---

# Policy Matrix — DevPilot Local

| Dominio | Acción | Default | Gate | Aprobación | Observabilidad |
|---|---|---|---|---:|---|
| Docs | Leer artefacto | Allow | Path policy | No | read event |
| Docs | Validar artefacto | Allow | Schema/checklist | No | validation event |
| Docs | Escribir borrador | Deny unless safe output | Path + backup | Sí | write event |
| Filesystem | Borrar | Deny | N/A | No en MVP | block event |
| Git | status/diff | Allow MVP+ | Git read policy | No | git event |
| Git | commit/tag/push | Deny MVP/MVP+ | release policy futura | Sí | git write event |
| Patch | parse/dry-run | Allow MVP+ | patch policy | No | patch event |
| Patch | apply | Deny MVP | patch+approval | Sí | approval+patch event |
| Model | mock/local | Allow controlled | model policy | No | model event |
| Model | external API | Deny by default | CostGuard+SecretGuard+ApprovalPolicyChecker | Sí | cost+model event |
| Agent | suggest | Allow | agent policy | No | agent event |
| Agent | execute critical tool | Deny by default | tool+policy+approval | Sí | full trace |
| Secrets | print/store raw | Deny | SecretGuard | No | redaction event |
| Deployment | deploy | Deny pre-code/MVP | release policy futura | Sí | deployment event |


## Nota de implementación FUNC-SPRINT-30

`ApprovalPolicyChecker` queda registrado como gate ejecutable inicial para validar `approval_id`, `status`, expiración y scope antes de considerar una acción approval-gated. Esta integración es `implemented-initial`: no ejecuta herramientas, no aplica patches, no corre tests y no sustituye PathGuard, SecretGuard ni CostGuard.


## FUNC-SPRINT-62 — Reglas de telemetría OTel dry-run

| Regla | Efecto | Uso |
|---|---|---|
| `OTEL_EXPORT_DRY_RUN_ALLOW` | allow | Permite generar payload OTel-like local sin red. |
| `OTEL_REMOTE_EXPORT_BLOCK` | block | Bloquea endpoint remoto, collector externo o modo no dry-run. |

Estas reglas mantienen la postura de no exfiltración de Fase E.


## Actualización FUNC-SPRINT-63 — Regla `AGENTOPS_STATUS_ALLOW`

La regla `AGENTOPS_STATUS_ALLOW` autoriza la ejecución local del comando `agentops status` como operación read-only/report.

Condiciones:

- solo lee evidencia local;
- reportes únicamente bajo `outputs/reports`;
- no usa red;
- no requiere UI;
- no habilita telemetría remota;
- debe emitir `CommandResult`;
- debe bloquear si MIASI o documentos de cierre obligatorios están ausentes.

## Actualización FUNC-SPRINT-90 — Reglas MultiAgentCoordinator

| Regla | Efecto | Uso |
|---|---|---|
| `MULTIAGENT_COORDINATOR_DRY_RUN_ALLOW` | allow | Permite `multiagent run` solo como workflow local, secuencial y dry-run. |
| `MULTIAGENT_EXECUTE_DENY` | block | Bloquea ejecución multiagente no dry-run, autonomía abierta o acciones críticas. |
| `MULTIAGENT_HANDOFF_TRACE_REQUIRED` | allow condicionado | Exige `HandoffRecord`, `PolicyEngine` y evento `multiagent.handoff.evaluated` antes del agente destino. |

Estas reglas no autorizan graph planner, agentes `planned/future`, shell, red externa, API externa ni modificación de archivos.

