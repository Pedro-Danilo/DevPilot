---
title: "Policy Matrix — DevPilot Local"
doc_id: "DEVPL-MIASI-POLICY-MATRIX"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
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
| Model | external API | Deny by default | CostGuard+SecretGuard | Sí | cost+model event |
| Agent | suggest | Allow | agent policy | No | agent event |
| Agent | execute critical tool | Deny by default | tool+policy+approval | Sí | full trace |
| Secrets | print/store raw | Deny | SecretGuard | No | redaction event |
| Deployment | deploy | Deny pre-code/MVP | release policy futura | Sí | deployment event |
