---
doc_id: "DEVPL-GSDLC-00-C-C4-DELTA"
title: "DEVPL-GSDLC-00-C — C4 target delta"
status: "implemented-initial"
version: "1.0.0"
owner: "DEVPL-GSDLC-00-C"
updated: "2026-08-14"
---
# DEVPL-GSDLC-00-C — C4 target delta

## Propósito

Registrar únicamente la diferencia entre el baseline arquitectónico vigente y el target GSDLC, sin reescribir estados históricos.

## Implemented-current preservado

- Web UI local y API local.
- ApplicationService/boundary policy.
- nueve rutas UI UOC como baseline actual.
- typed approvals/Git/jobs/Quality/RAG-agent surfaces según sus contratos cerrados.
- PolicyEngine, evidence/traces, ModelAdapter/CostGuard parcial.
- identity/RBAC inicial local, **sin login/sesiones reales**.

## Planned-GSDLC

- `GuidedSDLCService`;
- `WorkflowEngine`;
- `WorkspaceEngineeringStateRepository`;
- `ProjectShell`;
- `Project Status`;
- `StepActionAdvisor`;
- local authenticated sessions/RBAC successor;
- executable MIPSoftware/MIASI;
- planning/story/release workflows.

## Blocked-by-policy

- arbitrary shell;
- public/non-local API;
- remote execution;
- agent self-approval;
- external API por defecto;
- generic connector/plugin execution;
- force push y reset-hard/rebase automáticos.

## Future-out-of-scope

- enterprise IAM;
- tenancy;
- OIDC/SSO;
- cloud/SaaS control plane;
- remote runner operativo.

## Consistencia

Ningún elemento `planned-GSDLC` se representa como clase, endpoint o ruta ya existente. Los diagramas target usan una leyenda explícita y coexisten con secciones históricas anteriores.
