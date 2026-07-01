---
doc_id: "POST-H-021-B-REMOTE-ADR2-REPORT"
title: "POST-H-021-B — Remote Runner ADR-2 report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
---

# POST-H-021-B — Remote Runner ADR-2 Report

## Resultado

POST-H-021-B queda implementado como `implemented-initial`.

Se crea `docs/adr/ADR-POSTH-004-remote-runner-adr2.md` como decisión arquitectónica aprobada y design-only. La decisión mantiene:

```text
remote_execution_allowed=false
remote_runner_enabled=false
execution_allowed=false
remote_execution_used=false
network_required=false
external_api_required=false
credentials_required=false
secrets_required=false
```

## Alcance Implementado

```text
- ADR formal con contexto, opciones evaluadas, decisión y consecuencias.
- Alternativas rechazadas: enable-now, SSH ad hoc, connector-as-runner y plugin-as-runner.
- Prerrequisitos futuros: POST-H-022 y POST-H-023.
- Controles mínimos: RBAC, Approval, sandbox, observabilidad, secretos, kill-switch, quality gate y dry-run.
- Test de regresión documental contra activación remota accidental.
```

## Límites

No se implementa ejecución remota, transporte seguro, SSH, HTTP remote, gRPC, websockets, túneles, cloud control plane, credenciales remotas, workers remotos, connector write ni plugin execution.

## Evolución Pendiente

POST-H-021-C debe crear el readiness report read-only. La habilitación remota real queda fuera de POST-H-021 y requeriría POST-H-022, POST-H-023 y una ADR futura específica de enablement.
