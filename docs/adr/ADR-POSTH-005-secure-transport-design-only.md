---
doc_id: "ADR-POSTH-005"
title: "ADR-POSTH-005 — Secure transport design-only"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
decision_state: "accepted"
decision_status: "design-only"
micro_sprint: "POST-H-023-B"
phase: "POST-FASE-H"
local_first: true
transport_implemented: false
network_allowed: false
remote_execution_enabled: false
secrets_required: false
requires_future_enablement_adr: true
---

# ADR-POSTH-005 — Secure Transport Design-Only

## 1. Contexto

POST-H-023-A estableció los requisitos y amenazas base para un transporte seguro futuro de DevPilot. Ese trabajo no habilitó transporte, red, sockets, certificados, secretos ni ejecución remota.

POST-H-023-B compara alternativas de transporte para evitar que una decisión futura se tome de forma implícita o por conveniencia operativa. La existencia de una matriz de decisión no equivale a autorización de implementación.

Invariantes actuales:

```text
transport_implemented=false
secure_transport_implemented=false
network_allowed=false
network_used=false
sockets_opened=false
certificates_generated=false
secrets_required=false
secrets_stored=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 2. Decisión

DevPilot selecciona **`local-only-no-transport`** como estado actual.

La decisión aprobada es:

```text
secure transport design exists != secure transport implemented
protocol matrix exists != protocol selected for implementation
ADR-POSTH-005 exists != network allowed
transport readiness exists != remote execution enabled
```

Ningún componente de POST-H-023-B puede abrir sockets, requerir secretos, generar certificados, activar TLS/mTLS/SSH/HTTPS/gRPC/WebSocket, usar red o habilitar remote execution.

Cualquier implementación futura requiere una ADR posterior de enablement, además de controles previos verificados.

## 3. Alternativas Evaluadas

| Alternativa | Decisión actual | Motivo |
|---|---|---|
| `local-only-no-transport` | Aceptada como estado actual | Preserva el principio local-first y evita ampliar superficie de ataque. |
| `mTLS-over-HTTP2` | Candidata futura, rechazada para implementación actual | Requiere lifecycle de certificados, trust root, pinning, revocación, rotación y quality gate de transporte. |
| `HTTPS-token-bound` | Candidata futura, rechazada para implementación actual | Introduce tokens/secretos y requiere mitigación fuerte de robo/replay antes de uso. |
| `SSH-restricted` | Rechazada ahora | Riesgo alto de confundir transporte con shell/remote execution; requiere aislamiento más fuerte, forced command y auditoría estricta. |

## 4. Controles Previos Obligatorios

Antes de cualquier implementación futura de transporte deben existir, como mínimo:

```text
identity_hardening
approval_rbac_hardening
remote_runner_adr2
enterprise_threat_model
observability_retention
runtime_state_lifecycle
secret_handling_model
key_certificate_lifecycle
replay_protection
revocation_rotation
kill_switch_and_rollback
transport_quality_gate
policy_engine_binding
audit_correlation
future_enablement_adr
```

## 5. Consecuencias

- DevPilot gana una decisión explícita y auditable para transporte futuro sin habilitar transporte.
- `mTLS-over-HTTP2` queda documentado como alternativa técnicamente fuerte, pero bloqueada hasta lifecycle y quality gate.
- `HTTPS-token-bound` queda documentado como alternativa posible, pero bloqueada por tokens, replay y secreto.
- `SSH-restricted` queda rechazado ahora por riesgo de shell, bypass de PolicyEngine y auditoría incompleta.
- Los próximos micro-sprints deben diseñar lifecycle de claves/certificados, validator read-only y runbook antes de cualquier discusión de enablement.

## 6. Criterios PASS

```text
selected_for_now=local-only-no-transport
decision_status=design-only
transport_implemented=false
network_allowed=false
sockets_opened=false
certificates_generated=false
secrets_required=false
remote_execution_enabled=false
requires_future_enablement_adr=true
```

## 7. Criterios BLOCK

```text
La ADR selecciona mTLS/SSH/HTTPS para implementación inmediata.
Se permite abrir sockets o usar red.
Se crean certificados reales.
Se requieren o guardan secretos.
Se habilita remote execution.
Se omite future_enablement_adr.
Se interpreta transporte seguro como permiso de ejecutar acciones remotas.
```

## 8. Estado

Aceptada en `POST-H-023-B` como decisión **design-only**. La implementación de transporte seguro permanece bloqueada hasta una ADR futura de enablement y controles previos verificables.
