---
doc_id: "POST-H-023-SECURE-TRANSPORT-DESIGN"
title: "Secure transport design"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-023-E"
implementation_status: "closed"
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

POST-H-023-B registra esta decisión en `ADR-POSTH-005` y en `.devpilot/remote/secure_transport_protocol_decision_matrix.json`.

POST-H-023-C agrega `SecureTransportKeyLifecycle` y `docs/03_security/secure_transport_key_lifecycle.md` para lifecycle futuro de llaves/certificados sin generar material criptográfico ni almacenar secretos.


POST-H-023-D agrega `SecureTransportDesignValidator`, `SecureTransportValidationReport` y el subgate `secure-transport-design-only` para convertir el diseño en invariant executable read-only. El validador no abre sockets, no importa clientes HTTP, no genera certificados y no escribe reportes por sí mismo.

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

## 6. Protocol Decision Matrix

| Protocolo | Decisión actual | Razón |
|---|---|---|
| `local-only-no-transport` | Seleccionado | Mantiene local-first sin red, sockets, certificados, secretos ni remote execution. |
| `mTLS-over-HTTP2` | Candidato futuro solamente | Requiere lifecycle de certificados, trust root, pinning, revocación, rotación y quality gate. |
| `HTTPS-token-bound` | Candidato futuro solamente | Requiere token lifecycle, binding anti-robo, replay protection y modelo de secretos. |
| `SSH-restricted` | Rechazado ahora | Riesgo de shell/remote execution, key sprawl y bypass de PolicyEngine. |

Regla de interpretación:

```text
protocol decision matrix != protocol implementation
ADR-POSTH-005 != network allowed
future candidate != selected for execution
```

## 7. Límites del Micro-Sprint B

POST-H-023-B no implementa transporte activo, no crea certificados, no requiere secretos y no habilita red. La decisión aprobada mantiene `selected_for_now=local-only-no-transport`; el lifecycle de claves/certificados queda para POST-H-023-C.


## 8. Validator design-only y no-network invariant — POST-H-023-D

`SecureTransportDesignValidator` valida de forma local y read-only:

```text
.devpilot/remote/secure_transport_requirements.json
docs/schemas/secure_transport_requirements.schema.json
.devpilot/remote/secure_transport_protocol_decision_matrix.json
docs/schemas/secure_transport_design.schema.json
.devpilot/remote/secure_transport_key_lifecycle.json
docs/schemas/secure_transport_key_lifecycle.schema.json
docs/schemas/secure_transport_validation_report.schema.json
```

El validador produce un `CommandResult` con evidencia `SecureTransportValidationReport` en memoria. Esa evidencia confirma `decision_status=design-only`, `selected_for_now=local-only-no-transport`, `lifecycle_status=design-only-no-material`, `report_schema_valid=true`, `no_network_static_scan_passed=true` y `forbidden_network_primitives_total=0`.

El static scan bloquea imports o llamadas de red en `src/devpilot_core/remote`, incluyendo `socket`, `ssl`, `urllib`, `http`, `requests`, `httpx`, `aiohttp`, `grpc`, `websocket`, `websockets`, `socket.socket`, `socket.create_connection`, `ssl.create_default_context`, `http.client.HTTPConnection` y equivalentes definidos por el contrato POST-H-023-D.

El subgate `secure-transport-design-only` integra este validator en perfiles `hardening` e `industrial`. PASS no autoriza implementación de transporte; solo confirma que la línea design-only/no-network sigue íntegra.

## 8. Key/Certificate Lifecycle Design

POST-H-023-C define el lifecycle futuro de generación, almacenamiento, distribución, rotación y revocación. La regla de interpretación es:

```text
key lifecycle design != key generation
certificate lifecycle design != certificate creation
secret handling design != secret storage
transport lifecycle design != network allowed
```

No-go gates añadidos por POST-H-023-C:

```text
certificates_generated=false
certificate_authority_created=false
private_key_material_present=false
raw_secret_storage_allowed=false
secrets_stored=false
secrets_read=false
network_used=false
remote_execution_enabled=false
```

La especificación permite únicamente referencias, fingerprints o hashes en reportes/auditoría. Valores raw de llaves privadas, tokens, CA secrets y cuerpos completos de certificados siguen bloqueados.

## 9. Límites del Micro-Sprint A

POST-H-023-A no crea ADR de protocolo, no selecciona mTLS/SSH/HTTPS token-bound como alternativa aprobada, no diseña lifecycle completo de certificados y no implementa validator ni quality gate. Es una primera versión de requisitos y amenazas para que POST-H-023-B/C/D puedan evolucionar de forma controlada.

## 10. Fuentes Estructuradas

```text
docs/schemas/secure_transport_requirements.schema.json
docs/schemas/secure_transport_design.schema.json
docs/schemas/secure_transport_key_lifecycle.schema.json
.devpilot/remote/secure_transport_requirements.json
.devpilot/remote/secure_transport_protocol_decision_matrix.json
.devpilot/remote/secure_transport_key_lifecycle.json
docs/post_h_023_a_manifest.json
docs/post_h_023_b_manifest.json
docs/post_h_023_c_manifest.json
docs/post_h_023_d_manifest.json
docs/post_h_023_e_manifest.json
```


## 11. Cierre operacional — POST-H-023-E

POST-H-023-E agrega `docs/05_operations/secure_transport_design_runbook.md`, `docs/audits/post_h_023_e_secure_transport_closure_report.md`, `docs/post_h_023_e_manifest.json` y `tests/test_post_h_023_secure_transport_closure.py`.

El hito queda cerrado como `implemented-initial / design-only`. La opción actual sigue siendo `local-only-no-transport`; ningún artefacto de POST-H-023 autoriza TLS/mTLS, SSH, HTTP remoto, sockets, certificados, secretos ni remote execution.

Cualquier implementación futura de transporte requiere una ADR futura de enablement, threat model activo, identity/approval/RBAC endurecidos, lifecycle real de secretos/llaves/certificados, replay protection, revocation/rotation operativas, observabilidad, kill switch, SAST/SCA focal y quality gate de implementación activa.
