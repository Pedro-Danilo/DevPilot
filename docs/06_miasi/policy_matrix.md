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
