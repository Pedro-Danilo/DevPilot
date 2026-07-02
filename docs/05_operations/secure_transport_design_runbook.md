---
doc_id: "POST-H-023-SECURE-TRANSPORT-DESIGN-RUNBOOK"
title: "Secure transport design runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-023-E"
implementation_status: "implemented-initial"
decision_status: "design-only"
transport_implemented: false
secure_transport_implemented: false
network_allowed: false
remote_execution_enabled: false
secrets_required: false
---

# Secure Transport Design Runbook

## 1. Propósito operativo

Este runbook cierra operativamente `POST-H-023 — Secure transport design sin implementación activa` y define cómo interpretar, verificar y preservar el diseño de transporte seguro futuro de DevPilot.

Regla principal:

```text
secure transport design != secure transport implemented
validator PASS != autorización de red
protocol candidate != protocolo habilitado
key lifecycle design != generación de llaves/certificados
remote readiness != remote execution enabled
```

POST-H-023 queda como capacidad **implemented-initial / design-only**. El hito entrega requisitos, amenazas, protocol decision matrix, ADR design-only, lifecycle futuro de llaves/certificados, validator read-only, no-network invariant, quality subgate y este runbook. No habilita transporte activo.

## 2. Alcance cerrado

```text
POST-H-023-A — SecureTransportRequirements y threat baseline.
POST-H-023-B — SecureTransportDesign protocol decision matrix y ADR-POSTH-005.
POST-H-023-C — SecureTransportKeyLifecycle design-only-no-material.
POST-H-023-D — SecureTransportDesignValidator y no-network invariant.
POST-H-023-E — Runbook, cierre documental, TCR y pruebas de cierre.
```

## 3. Estado permitido actual

El único estado permitido después del cierre es:

```text
decision_status=design-only
selected_for_now=local-only-no-transport
lifecycle_status=design-only-no-material
validator_status=design-only-validator
quality_gate_subgate=secure-transport-design-only
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

## 4. Comandos de operación y verificación

Desde la raíz del repo:

```powershell
$env:PYTHONPATH="src"
```

Verificación focal del hito:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_023_secure_transport_closure.py `
  tests/test_post_h_023_secure_transport_validator.py `
  tests/test_post_h_023_no_network_invariant.py `
  tests/test_post_h_023_secure_transport_key_lifecycle.py `
  tests/test_post_h_023_secure_transport_protocol_decision.py `
  tests/test_post_h_023_secure_transport_design.py `
  tests/test_project_global_state.py `
  tests/test_schema_registry.py `
  -q
```

Validaciones contractuales:

```powershell
python -m devpilot_core schema list --json
python -m devpilot_core schema validate --schema-id PostHManifest --instance docs/post_h_023_e_manifest.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core project-state validate --json
```

Smoke directo del validator:

```powershell
python -c "import json; from pathlib import Path; from devpilot_core.remote import SecureTransportDesignValidator; r=SecureTransportDesignValidator(Path('.')).validate(); print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2)); raise SystemExit(int(r.exit_code))"
```

Quality gate acumulativo recomendado:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

## 5. Criterios PASS

PASS cuando se cumpla todo lo siguiente:

```text
Backlog POST-H-023 marcado implementation_status=closed.
Implementation doc POST-H-023 marcado implementation_status=closed.
Manifest docs/post_h_023_e_manifest.json válido contra PostHManifest.
Runbook dedicado presente y aprobado.
Closure report presente y aprobado.
TCR v1/v2 registra post-h-023-secure-transport-runbook-closure.
Docs governance registra runbook, closure report, manifest y test de cierre.
SecureTransportDesignValidator retorna ok=true.
No-network invariant retorna forbidden_network_primitives_total=0.
No-go gates de red, certificados, secretos, remote execution, connector write y plugin execution permanecen false.
```

## 6. Criterios BLOCK

BLOCK si aparece cualquiera de estas señales:

```text
transport_implemented=true
secure_transport_implemented=true
network_allowed=true
network_used=true
sockets_opened=true
certificates_generated=true
certificate_authority_created=true
private_key_material_present=true
raw_secret_storage_allowed=true
secrets_required=true
secrets_stored=true
secrets_read=true
remote_execution_enabled=true
connector_write_enabled=true
plugin_execution_enabled=true
```

También bloquea el avance cualquier import/call de red en `src/devpilot_core/remote`, incluyendo `socket`, `ssl`, `urllib`, `http`, `requests`, `httpx`, `aiohttp`, `grpc`, `websocket` o `websockets`.

## 7. Condiciones futuras para implementar transporte real

Cualquier implementación futura debe tratarse como un hito nuevo, no como continuación automática de POST-H-023. Como mínimo requiere:

```text
ADR futura explícita de enablement.
Threat model actualizado de transporte activo.
Identity lifecycle endurecido.
Approval/RBAC productivo para acciones remotas.
Secret lifecycle real con no raw secret storage.
Key/certificate lifecycle real con generación fuera del repo y redacción obligatoria.
Replay protection.
Revocation/rotation operativas.
Pinning/trust anchor governance.
Observability retention y audit trail.
Kill switch y rollback.
Quality gate de implementación activa.
SAST/SCA focal sobre transporte.
Go/no-go firmado por owner.
```

## 8. Riesgos y mitigaciones

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Confundir diseño con autorización de red | Crítico | Texto explícito en README, backlog, implementation doc, runbook y closure report. |
| Introducir primitives de red accidentalmente | Crítico | Static scan AST en `SecureTransportDesignValidator` y tests no-network. |
| Generar certificados o secretos reales en repo | Crítico | Lifecycle permanece design-only-no-material; no-go gates bloquean material. |
| Habilitar remote execution por implicación de transporte | Crítico | Transport design no concede permisos de ejecución; PolicyEngine/Approval/RBAC siguen obligatorios. |
| Sobredeclarar madurez production/enterprise | Alto | El cierre declara implemented-initial/design-only; no production-ready claim. |

## 9. Relación con próximos hitos

POST-H-024 puede iniciar onboarding operacional sobre una base donde el diseño de transporte seguro está documentado y gobernado, pero no implementado. POST-H-025 podrá evaluar declaraciones de producción solo si todos los no-go gates y disclaimers siguen alineados.
