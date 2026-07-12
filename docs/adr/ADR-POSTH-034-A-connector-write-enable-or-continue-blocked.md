---
doc_id: "ADR-POSTH-034-A"
title: "ADR-POSTH-034-A — Connector write enablement decision"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
decision_state: "accepted"
decision_status: "continue-blocked"
micro_sprint: "POST-H-034-A"
phase: "POST-FASE-H"
local_first: true
connector_write_enabled: false
runtime_write_enabled: false
network_allowed: false
external_api_allowed: false
credentials_required: false
requires_future_enablement_adr: true
requires_future_backlog: true
---

# ADR-POSTH-034-A — Connector Write Enablement Decision

## 1. Contexto

DevPilot ya tiene conectores con registry, sandbox, replay fixtures, redaction, policy binding, Approval/RBAC checks y el quality gate `connector-sandbox`. Esa base **no autoriza connector write**. POST-H-034-A formaliza la frontera entre evidencia read-only/dry-run/replay y cualquier escritura real futura.

Estado actual obligatorio:

```text
connector_write_enabled=false
runtime_write_enabled=false
network_allowed=false
external_api_allowed=false
credentials_required=false
remote_execution_enabled=false
plugin_execution_enabled=false
```

## 2. Decisión

La decisión aprobada es **`continue-blocked`**.

```text
connector sandbox exists != connector write enabled
replay fixture exists != production write authorization
policy binding exists != approval for side effects
POST-H-034-A ADR exists != runtime enablement
```

POST-H-034-A no habilita escritura, no crea credenciales, no permite APIs externas, no requiere red y no amplía el claim `production-ready-local`.

## 3. Alternativas evaluadas

| Alternativa | Decisión | Motivo |
|---|---|---|
| `continue-blocked` | Aceptada | Es el único estado coherente con la falta de rollback/compensación, fake write tests, data classification, rate limits, idempotency y kill-switch. |
| `pilot-gated-future` | Pospuesta | Puede evaluarse en backlog futuro con fake connector write no productivo y prerrequisitos completos. |
| `approved-for-future-implementation` | Rechazada para el estado actual | Los prerrequisitos mínimos industriales no están completos. |
| Habilitación inmediata | Prohibida | Violaría los no-go gates actuales y el alcance local-first. |

## 4. Prerrequisitos antes de cualquier piloto futuro

```text
ADR aprobada
Threat model por conector write
Rollback/compensación
Fake connector write tests
Replay fixtures negativas
Approval/RBAC por actor, connector_id, operation_id y subject
Secret handling no versionado
Observability y audit trail
Data classification
Rate limits e idempotency
Kill-switch
Quality gate connector-write-disabled-or-approved
```

## 5. Criterios PASS

```text
decision_status=continue-blocked
connector_write_enabled=false
runtime_write_enabled=false
network_allowed=false
external_api_allowed=false
credentials_required=false
requires_future_enablement_adr=true
claims_changed=false
```

## 6. Criterios BLOCK

```text
La ADR habilita escritura inmediata.
Se agregan tokens, credenciales reales o secretos versionados.
Se permite red o API externa real.
Se interpreta sandbox/replay como autorización de write.
Se omite rollback, approval/RBAC, audit trail o kill-switch para pilotos futuros.
Se modifica production-ready-local hacia claims más amplios.
```

## 7. Consecuencias

- DevPilot gana una decisión auditable para una capacidad sensible sin activar side effects.
- El sandbox de conectores conserva su rol de validación local read-only/dry-run.
- Cualquier evolución futura requiere backlog explícito, fake write tests, threat model, approval/RBAC reforzado y quality gate.
- La documentación debe seguir diferenciando `exists as design/readiness` de `enabled as production capability`.

## 8. Estado

Aprobada en `POST-H-034-A` como decisión **continue-blocked**. No autoriza runtime write ni pilotos productivos.
