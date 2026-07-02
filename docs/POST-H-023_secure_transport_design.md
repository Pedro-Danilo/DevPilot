---
doc_id: "POST-H-023-IMPLEMENTATION-DOC"
title: "POST-H-023 — Secure transport design sin implementación activa"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
implementation_status: "active"
current_micro_sprint: "POST-H-023-A"
next_micro_sprint: "POST-H-023-B"
local_first: true
dry_run: true
transport_implemented: false
network_allowed: false
remote_execution_enabled: false
secrets_required: false
---

# POST-H-023 — Secure Transport Design

## Estado

POST-H-023 queda aprobado y activo. El micro-sprint actual es **POST-H-023-A — Requisitos y amenazas de transporte**.

Alcance global del hito:

```text
secure transport design != secure transport implemented
transport requirements != network allowed
remote readiness != remote execution enabled
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
POST-H-023-B — Protocol decision matrix y ADR
POST-H-023-C — Key/certificate lifecycle design
POST-H-023-D — Validator de diseño y no-network invariant
POST-H-023-E — Runbook y cierre
```

## Límites

POST-H-023-A es `implemented-initial / design-only`. No implementa transporte activo ni crea secretos/certificados. La decisión de protocolo y ADR quedan explícitamente diferidas a POST-H-023-B.
