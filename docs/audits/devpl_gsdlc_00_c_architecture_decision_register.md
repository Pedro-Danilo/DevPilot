---
doc_id: "DEVPL-GSDLC-00-C-ARCHITECTURE-DECISION-REGISTER"
title: "DEVPL-GSDLC-00-C — Architecture decision register"
status: "implemented-initial"
version: "1.0.0"
owner: "DEVPL-GSDLC-00-C"
updated: "2026-08-14"
---
# DEVPL-GSDLC-00-C — Architecture decision register

| ADR | Decisión | Estado runtime | Owner futuro | Gate |
|---|---|---|---|---|
| ADR-GSDLC-001 | GuidedSDLCService/WorkflowEngine detrás de ApplicationService | planned | GSDLC-01 | state engine acceptance |
| ADR-GSDLC-002 | Platform/WorkspaceEngineering/Runtime state separados | planned | GSDLC-01 | reconciliation/restart acceptance |
| ADR-GSDLC-003 | authenticated local operator successor, no enterprise | planned | GSDLC-02 | auth/RBAC negative tests |
| ADR-GSDLC-004 | UI-complete ProjectShell + StepActionAdvisor | planned | GSDLC-03/GSDLC-05 | zero-PowerShell normal journey |

## Decisiones no reabiertas

- local-first + ModelAdapter/CostGuard;
- ApplicationService boundary;
- no arbitrary shell;
- governed jobs;
- PolicyEngine/approval/evidence;
- POST-H-034-D `multiuser.auth=continue-blocked` histórico.

## Autorización

Los ADRs quedan `reviewed` y con `approval: pending_owner_00_c_adjudication`. La adjudicación owner de 00-C puede aprobarlos como conjunto. No autorizan runtime por sí mismos.
