---

doc_id: "POST-H-023-BACKLOG"
id: "POST-H-023"
title: "POST-H-023 — Secure transport design sin implementación activa"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "pending_owner_review"
phase: "POST-FASE-H"
priority: "P3"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-023 — Secure transport design sin implementación activa

## 1. Objetivo

Diseñar los requisitos, amenazas, controles y decisiones técnicas de un **secure transport futuro** para DevPilot, sin implementar transporte activo, sin sockets, sin llamadas de red, sin certificados reales y sin remote execution.

El hito debe producir un diseño validable que establezca qué tendría que existir antes de cualquier comunicación remota futura.

## 2. Contexto y justificación

Cualquier evolución futura hacia remote runner o enterprise deployment requeriría transporte seguro. Sin embargo, implementar transporte antes de tener threat model, approval/RBAC hardening, observability retention y runtime lifecycle elevaría demasiado el riesgo.

POST-H-023 es por tanto un backlog de diseño controlado: define protocolos aceptables, gestión de claves, autenticación, autorización, auditoría, rotación, revocación, pinning, replay protection y failure modes, pero no implementa comunicación activa.

## 3. Alcance

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

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-004-remote-runner-adr2.md
docs/03_security/enterprise_deployment_threat_model.md
src/devpilot_core/policy/
src/devpilot_core/identity/
src/devpilot_core/approval/
src/devpilot_core/observability/
src/devpilot_core/remote/
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
docs/03_security/secure_transport_design.md
docs/adr/ADR-POSTH-005-secure-transport-design-only.md
docs/schemas/secure_transport_design.schema.json
docs/schemas/secure_transport_requirements.schema.json
.devpilot/remote/secure_transport_requirements.json
src/devpilot_core/remote/transport_design.py
tests/test_post_h_023_secure_transport_design.py
tests/test_post_h_023_no_network_invariant.py
docs/05_operations/secure_transport_design_runbook.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Secure transport requirements

```json
{
  "schema_version": "1.0",
  "status": "design-only",
  "transport_implemented": false,
  "network_allowed": false,
  "protocol_candidates": ["mTLS-over-HTTP2", "SSH-restricted", "local-only-no-transport"],
  "selected_for_now": "local-only-no-transport",
  "required_controls_before_implementation": [
    "identity_hardening",
    "approval_rbac_hardening",
    "remote_runner_adr2",
    "enterprise_threat_model",
    "observability_retention",
    "runtime_state_lifecycle"
  ],
  "no_go_gates": {
    "sockets_opened": false,
    "certificates_generated": false,
    "remote_execution_enabled": false,
    "secrets_required": false
  }
}
```

## 7. Principios de diseño

```text
1. Design-only means no transport implementation.
2. No network calls in POST-H-023.
3. No secrets or certificates are generated.
4. Secure transport requires identity, approval, audit and retention first.
5. Replay protection and revocation are mandatory in any future design.
6. Transport must never bypass PolicyEngine.
7. Transport must never imply remote execution permission.
8. All future transport must be observable and kill-switchable.
9. Failure must be safe-closed.
10. Local-only remains the selected option until future ADR approval.
```

## 8. Micro-sprints propuestos

### POST-H-023-A — Requisitos y amenazas de transporte

Tareas:

```text
1. Crear secure_transport_requirements.schema.json.
2. Crear secure_transport_requirements.json.
3. Identificar amenazas: MITM, replay, spoofing, token theft, downgrade, impersonation.
4. Definir controles requeridos.
```

Criterios PASS:

```text
- transport_implemented=false.
- network_allowed=false.
- Amenazas críticas documentadas.
```

### POST-H-023-B — Protocol decision matrix y ADR

Tareas:

```text
1. Comparar mTLS, SSH restringido, HTTPS token-bound, local-only.
2. Seleccionar local-only-no-transport para el estado actual.
3. Crear ADR-POSTH-005.
4. Documentar alternativas rechazadas.
```

Criterios PASS:

```text
- ADR mantiene diseño sin implementación.
- Futuro transporte queda condicionado a controles previos.
```

### POST-H-023-C — Key/certificate lifecycle design

Tareas:

```text
1. Diseñar lifecycle futuro: generation, storage, rotation, revocation.
2. Diseñar redaction/audit de credenciales.
3. Definir no storage of raw secrets.
4. No implementar generación real.
```

Criterios BLOCK:

```text
- Se crean certificados reales.
- Se guardan secretos reales.
```

### POST-H-023-D — Validator de diseño y no-network invariant

Tareas:

```text
1. Crear src/devpilot_core/remote/transport_design.py.
2. Crear validator read-only del diseño.
3. Crear tests que fallen si se habilitan sockets/red.
4. Integrar con quality gate.
```

Criterios PASS:

```text
- El validator produce design-only PASS.
- Los tests confirman no network.
```

### POST-H-023-E — Runbook y cierre

Tareas:

```text
1. Crear secure_transport_design_runbook.md.
2. Documentar condiciones futuras de implementación.
3. Actualizar test contracts.
4. Ejecutar validaciones.
```

## 9. Comandos de validación esperados

```powershell
python -m pytest tests/test_post_h_023_secure_transport_design.py tests/test_post_h_023_no_network_invariant.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate-artifact docs/03_security/secure_transport_design.md --json
```

## 10. No-go gates

```text
- network_used=true
- sockets opened
- certificates generated
- secrets stored
- remote_execution_enabled=true
- secure_transport_implemented=true
- connector_write_enabled=true
- plugin_execution_enabled=true
```

## 11. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Implementar transporte prematuramente | Crítico | Tests no-network y ADR design-only. |
| Omitir revocación/rotación | Alto | Lifecycle design obligatorio. |
| Confundir transporte con permiso de ejecución | Crítico | Policy gate y texto explícito. |
| Introducir secrets | Alto | No secrets, no cert generation. |

## 12. Definition of Done

```text
[ ] Secure transport design documentado.
[ ] ADR design-only aprobada.
[ ] Requirements JSON validado.
[ ] Validator/read-only implementado.
[ ] Tests no-network pasan.
[ ] No se implementa transporte activo.
```
