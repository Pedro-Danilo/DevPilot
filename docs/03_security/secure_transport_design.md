---
doc_id: "POST-H-023-SECURE-TRANSPORT-DESIGN"
title: "Secure transport design"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-023-A"
implementation_status: "implemented-initial"
decision_status: "design-only"
transport_implemented: false
network_allowed: false
secure_transport_implemented: false
remote_execution_enabled: false
secrets_required: false
---

# Secure Transport Design

## 1. Propósito

POST-H-023-A define los requisitos y amenazas iniciales para un transporte seguro futuro de DevPilot. El alcance es **design-only**: no implementa sockets, TLS, mTLS, SSH, HTTP remoto, gRPC, WebSocket, túneles, certificados reales, secretos ni remote execution.

Regla operativa:

```text
secure transport design != secure transport implemented
transport requirements != network allowed
remote readiness != remote execution enabled
```

## 2. Estado Actual

```text
transport_implemented=false
network_allowed=false
sockets_opened=false
certificates_generated=false
secrets_required=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

La opción seleccionada para el estado actual sigue siendo `local-only-no-transport`.

## 3. Amenazas Críticas

| ID | Amenaza | Severidad | Razón de bloqueo |
|---|---|---:|---|
| ST-001 | Man-in-the-middle | Crítica | Sin autenticación mutua y pinning, el canal puede ser interceptado o alterado. |
| ST-002 | Replay | Crítica | Aprobaciones o comandos futuros podrían reutilizarse fuera de contexto. |
| ST-003 | Spoofing de endpoint | Crítica | Un runner o endpoint falso podría recibir o emitir operaciones. |
| ST-004 | Robo de tokens/llaves | Crítica | Cualquier secreto de transporte robado abre una vía de escalamiento. |
| ST-005 | Downgrade de protocolo | Alta | La negociación podría caer en un modo débil o no autorizado. |
| ST-006 | Impersonation de actor/servicio | Crítica | El transporte no puede reemplazar Approval/RBAC ni PolicyEngine. |
| ST-007 | Certificado mal emitido o trust root obsoleto | Alta | Una raíz de confianza incorrecta puede legitimar endpoints maliciosos. |
| ST-008 | Bypass de PolicyEngine | Crítica | Ningún transporte futuro puede despachar operación sin policy gate. |

## 4. Controles Requeridos Antes de Implementar Transporte

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
```

## 5. No-Go Gates

POST-H-023-A bloquea el avance si cualquiera de estas señales cambia:

```text
transport_implemented=true
network_allowed=true
network_used=true
sockets_opened=true
certificates_generated=true
secrets_required=true
secrets_stored=true
remote_execution_enabled=true
connector_write_enabled=true
plugin_execution_enabled=true
```

## 6. Límites del Micro-Sprint A

POST-H-023-A no crea ADR de protocolo, no selecciona mTLS/SSH/HTTPS token-bound como alternativa aprobada, no diseña lifecycle completo de certificados y no implementa validator ni quality gate. Es una primera versión de requisitos y amenazas para que POST-H-023-B/C/D puedan evolucionar de forma controlada.

## 7. Fuentes Estructuradas

```text
docs/schemas/secure_transport_requirements.schema.json
.devpilot/remote/secure_transport_requirements.json
docs/post_h_023_a_manifest.json
```
