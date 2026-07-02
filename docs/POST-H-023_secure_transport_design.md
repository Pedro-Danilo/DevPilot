---
doc_id: "POST-H-023-IMPLEMENTATION-DOC"
title: "POST-H-023 — Secure transport design sin implementación activa"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
implementation_status: "active"
current_micro_sprint: "POST-H-023-B"
next_micro_sprint: "POST-H-023-C"
local_first: true
dry_run: true
transport_implemented: false
network_allowed: false
remote_execution_enabled: false
secrets_required: false
---

# POST-H-023 — Secure Transport Design

## Estado

POST-H-023 queda aprobado y activo. El micro-sprint actual es **POST-H-023-B — Protocol decision matrix y ADR**.

Alcance global del hito:

```text
secure transport design != secure transport implemented
transport requirements != network allowed
remote readiness != remote execution enabled
```

## POST-H-023-B — Protocol decision matrix y ADR

POST-H-023-B entrega `SecureTransportDesign` y `ADR-POSTH-005` como decisión design-only. La opción seleccionada para el estado actual es `local-only-no-transport`.

Artefactos principales:

```text
docs/schemas/secure_transport_design.schema.json
.devpilot/remote/secure_transport_protocol_decision_matrix.json
docs/adr/ADR-POSTH-005-secure-transport-design-only.md
docs/audits/post_h_023_b_protocol_decision_matrix_report.md
docs/post_h_023_b_manifest.json
tests/test_post_h_023_secure_transport_protocol_decision.py
```

Decisión:

```text
selected_for_now=local-only-no-transport
decision_status=design-only
requires_future_enablement_adr=true
transport_implemented=false
network_allowed=false
remote_execution_enabled=false
```

Alternativas evaluadas:

```text
mTLS-over-HTTP2: future_candidate_only, no implementación actual.
HTTPS-token-bound: future_candidate_only, no implementación actual.
SSH-restricted: rejected_now.
local-only-no-transport: selected_current.
```

PASS si:

```text
ADR-POSTH-005 mantiene design-only.
La matriz conserva implementation_allowed_now=false para todas las alternativas.
No se habilita red, sockets, certificados, secretos ni remote execution.
Futuro transporte queda condicionado a controles previos y future_enablement_adr.
```

BLOCK si:

```text
Se selecciona mTLS, SSH, HTTPS, gRPC o WebSocket para implementación inmediata.
Se permite network_allowed=true o sockets_opened=true.
Se generan certificados reales.
Se requieren/guardan secretos.
Se habilita remote_execution_enabled=true.
```

## POST-H-023-A — Requisitos y amenazas de transporte

POST-H-023-A entrega una primera versión del contrato `SecureTransportRequirements` y una instancia local design-only con amenazas y controles mínimos antes de cualquier transporte futuro.

Artefactos principales:

```text
docs/schemas/secure_transport_requirements.schema.json
.devpilot/remote/secure_transport_requirements.json
docs/03_security/secure_transport_design.md
docs/post_h_023_a_manifest.json
tests/test_post_h_023_secure_transport_design.py
```

PASS si:

```text
transport_implemented=false
network_allowed=false
sockets_opened=false
certificates_generated=false
secrets_required=false
remote_execution_enabled=false
al menos 6 amenazas críticas/altas documentadas
controles previos obligatorios definidos
selected_for_now=local-only-no-transport
```

BLOCK si:

```text
transport_implemented=true
network_allowed=true
network_used=true
sockets_opened=true
certificates_generated=true
secrets_required=true
remote_execution_enabled=true
```

## Micro-Sprints Pendientes

```text
POST-H-023-C — Key/certificate lifecycle design
POST-H-023-D — Validator de diseño y no-network invariant
POST-H-023-E — Runbook y cierre
```

## Límites

POST-H-023-B es `implemented-initial / design-only`. No implementa transporte activo, no crea secretos/certificados y no habilita red. El lifecycle de claves/certificados queda para POST-H-023-C.
