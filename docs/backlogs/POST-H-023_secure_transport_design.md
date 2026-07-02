---
doc_id: "POST-H-023-BACKLOG"
id: "POST-H-023"
title: "POST-H-023 — Secure transport design sin implementación activa"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
implementation_status: "closed"
current_micro_sprint: "POST-H-023-E"
next_micro_sprint: "POST-H-024"
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
transport_implemented: false
secure_transport_implemented: false
network_allowed: false
secrets_required: false
---

# POST-H-023 — Secure transport design sin implementación activa

## Estado de Implementación

POST-H-023 queda **approved / closed** como `implemented-initial / design-only`.

El hito produjo requisitos, amenazas, matriz de decisión, ADR, lifecycle de llaves/certificados, validator read-only, no-network invariant, quality subgate, runbook dedicado y cierre documental. No habilita transporte activo, red, sockets, certificados, llaves privadas, secretos ni remote execution.

## 1. Objetivo

Diseñar los requisitos, amenazas, controles y decisiones técnicas de un **secure transport futuro** para DevPilot, sin implementar transporte activo, sin sockets, sin llamadas de red, sin certificados reales y sin remote execution.

## 2. Contexto y justificación

Cualquier evolución futura hacia remote runner o enterprise deployment requeriría transporte seguro. Sin embargo, implementar transporte antes de tener threat model activo, approval/RBAC hardening, observability retention, runtime lifecycle, secret lifecycle, revocation/rotation y go/no-go formal elevaría demasiado el riesgo.

POST-H-023 fue por tanto un backlog de diseño controlado: define protocolos aceptables, gestión de claves, autenticación, autorización, auditoría, rotación, revocación, pinning, replay protection y failure modes, pero no implementa comunicación activa.

## 3. Alcance cerrado

Incluye:

```text
- Secure transport requirements.
- Threat model específico de transporte.
- Protocol decision matrix.
- Key/certificate lifecycle design.
- Handshake design abstracto.
- Replay protection design.
- Audit and observability requirements.
- Validator de diseño y no-network invariant.
- Runbook operacional y cierre.
```

No incluye:

```text
- TLS/mTLS real.
- Certificados reales.
- Sockets.
- HTTP/gRPC/WebSocket productivo.
- SSH.
- Túneles.
- Remote runner activo.
- Network calls.
- Secrets reales.
```

## 4. Micro-sprints cerrados

### POST-H-023-A — Requisitos y amenazas de transporte

Estado: `implemented-initial`.

Entregó `SecureTransportRequirements`, amenazas críticas y controles previos. PASS: `transport_implemented=false`, `network_allowed=false` y amenazas críticas documentadas.

### POST-H-023-B — Protocol decision matrix y ADR

Estado: `implemented-initial / design-only`.

Entregó `SecureTransportDesign`, protocol decision matrix y `ADR-POSTH-005`, seleccionando `local-only-no-transport` para el estado actual.

### POST-H-023-C — Key/certificate lifecycle design

Estado: `implemented-initial / design-only-no-material`.

Entregó lifecycle futuro de generation, storage, distribution, rotation y revocation sin generar certificados, CA, llaves privadas ni secretos.

### POST-H-023-D — Validator de diseño y no-network invariant

Estado: `implemented-initial / design-only-validator`.

Entregó `SecureTransportDesignValidator`, `SecureTransportValidationReport`, static scan no-network y subgate `secure-transport-design-only` en hardening/industrial.

### POST-H-023-E — Runbook y cierre

Estado: `closed / implemented-initial / design-only`.

Entregó:

```text
docs/05_operations/secure_transport_design_runbook.md
docs/audits/post_h_023_e_secure_transport_closure_report.md
docs/post_h_023_e_manifest.json
tests/test_post_h_023_secure_transport_closure.py
```

## 5. No-go gates vigentes

```text
transport_implemented=false
secure_transport_implemented=false
network_allowed=false
network_used=false
sockets_opened=false
certificates_generated=false
certificate_authority_created=false
private_key_material_present=false
raw_secret_storage_allowed=false
secrets_required=false
secrets_stored=false
secrets_read=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 6. Comandos de validación esperados

```powershell
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_023_secure_transport_closure.py tests/test_post_h_023_secure_transport_validator.py tests/test_post_h_023_no_network_invariant.py tests/test_post_h_023_secure_transport_key_lifecycle.py tests/test_post_h_023_secure_transport_protocol_decision.py tests/test_post_h_023_secure_transport_design.py tests/test_project_global_state.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id PostHManifest --instance docs/post_h_023_e_manifest.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 7. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Implementar transporte prematuramente | Crítico | Tests no-network, ADR design-only, runbook y closure report. |
| Omitir revocación/rotación | Alto | Lifecycle design obligatorio y condición futura de enablement. |
| Confundir transporte con permiso de ejecución | Crítico | Policy gate y texto explícito: transport design no concede remote execution. |
| Introducir secrets | Alto | No secrets, no cert generation, no raw secret storage. |
| Sobredeclarar production/enterprise readiness | Alto | POST-H-023 se declara implemented-initial/design-only. |

## 8. Definition of Done

```text
[x] Secure transport design documentado.
[x] ADR design-only aprobada.
[x] Requirements JSON validado.
[x] Key/certificate lifecycle design documentado sin material real.
[x] Validator/read-only implementado.
[x] Tests no-network pasan.
[x] Runbook dedicado creado.
[x] Test contracts actualizados.
[x] No se implementa transporte activo.
[x] Cierre documental y manifest generados.
```

## 9. Próximo hito

`POST-H-024 — Operator onboarding bootstrap`.
