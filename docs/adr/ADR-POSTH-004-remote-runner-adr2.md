---
doc_id: "ADR-POSTH-004"
title: "ADR-POSTH-004 — Remote Runner ADR-2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
decision_state: "accepted"
decision_status: "design-only"
micro_sprint: "POST-H-021-B"
phase: "POST-FASE-H"
local_first: true
remote_execution_allowed: false
remote_runner_enabled: false
requires_future_adr: true
---

# ADR-POSTH-004 — Remote Runner ADR-2

## 1. Contexto

DevPilot ya contiene un baseline experimental de remote runner en `src/devpilot_core/remote/` y `.devpilot/remote/runner_registry.json`. Ese baseline es metadata/stub bloqueado: existe para inventario, readiness y diseño, no para ejecutar comandos fuera del workspace local.

POST-H-021-A confirmó los invariantes actuales:

```text
remote_execution_allowed=false
remote_runner_enabled=false
execution_allowed=false
remote_execution_used=false
cloud_control_plane_enabled=false
network_used=false
external_api_used=false
shell_allowed=false
credentials_required=false
secrets_read=false
requires_future_adr=true
```

El riesgo principal es que la existencia de registry, módulo remoto o readiness criteria sea confundida con autorización de ejecución remota. Esta ADR fija la frontera arquitectónica para evitar esa ambigüedad.

## 2. Decisión

DevPilot mantiene **remote execution deshabilitada**. POST-H-021-B aprueba únicamente la decisión arquitectónica de diseño y los prerrequisitos mínimos para una evaluación futura.

La decisión operativa es:

```text
remote registry existe != capacidad remota activa
remote readiness existe != remote execution permitido
remote ADR existe != transport seguro implementado
remote design existe != permiso de ejecución
```

Ningún manifest, registry, readiness report, quality gate o documento de POST-H-021 puede ser interpretado como autorización para ejecutar comandos remotos, abrir transporte remoto, cargar credenciales remotas, activar workers remotos o usar red/API externa.

## 3. Alternativas Evaluadas

| Alternativa | Resultado | Motivo |
|---|---|---|
| Mantener remote runner deshabilitado con ADR-2 y readiness design-only | Aceptada | Preserva trazabilidad y criterios futuros sin ampliar superficie de ataque. |
| `enable-now` | Rechazada | Habilitar ejecución remota ahora sería crítico: faltan threat model enterprise, transporte seguro, RBAC/Approval endurecido, sandbox, observabilidad y kill-switch. |
| `SSH ad hoc` | Rechazada | SSH directo acopla credenciales, red, shell y auditoría incompleta; no provee contrato uniforme de PolicyEngine, Approval ni trazas. |
| `connector-as-runner` | Rechazada | Los conectores de DevPilot siguen sujetos a sandbox/read-only/dry-run; convertirlos en runner mezclaria lectura/integración con ejecución remota. |
| `plugin-as-runner` | Rechazada | El sistema de plugins permanece metadata-only; usar plugins como runner violaría el bloqueo de `plugin.code.execute` y los no-go gates de POST-H-019. |

## 4. Prerrequisitos Mínimos Para Habilitación Futura

Una habilitación futura solo podría evaluarse con una ADR nueva posterior a POST-H-021 y, como mínimo, con estos entregables aprobados:

```text
POST-H-022 — Enterprise deployment threat model.
POST-H-023 — Secure transport design.
RBAC/Approval hardening con actor, role, command_id, tool_call_id y subject binding verificables.
Sandbox remoto con aislamiento de workspace, allowlist de comandos, límites de filesystem y bloqueo de acciones destructivas por defecto.
Observabilidad y auditoría con trazas, retention policy, redaction y evidencia reproducible.
Modelo de secretos y credenciales que no exponga valores ni permita lectura implícita de secretos.
Kill-switch y rollback operativo probado.
Quality gate remote-disabled/remote-readiness que bloquee activación accidental.
Evals adversariales y test contracts de seguridad para transporte, autorización, sandbox y auditoría.
Dry-run obligatorio por defecto, con separación explícita entre plan, approval y execute.
```

Hasta que esos prerrequisitos existan, cualquier intento de activar remote runner debe ser un BLOCK.

## 5. Consecuencias

- DevPilot puede documentar arquitectura remota futura sin habilitar ejecución remota.
- El baseline remoto queda limitado a inventario, status y readiness design-only.
- Los comandos existentes de remote runner deben permanecer status/read-only o block-by-default.
- Los quality gates deben tratar como condiciones bloqueantes cualquier cambio que active remote runner, permita ejecución, requiera red, requiera credenciales o registre uso de ejecución remota.
- POST-H-022 y POST-H-023 quedan como prerrequisitos de diseño para cualquier discusión de ejecución remota real.

## 6. No-Go Gates

```text
remote_execution_allowed=false
remote_runner_enabled=false
execution_allowed=false
remote_execution_used=false
cloud_control_plane_enabled=false
network_required=false
external_api_required=false
secrets_required=false
credentials_required=false
shell_allowed=false
arbitrary_command_execution_allowed=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 7. Criterios PASS

```text
ADR status=approved.
decision_status=design-only.
remote_execution_allowed=false.
remote_runner_enabled=false.
POST-H-022 y POST-H-023 están definidos como prerrequisitos.
RBAC, Approval, sandbox, observabilidad, secretos, kill-switch y quality gate quedan explicitados.
Alternativas rechazadas: enable-now, SSH ad hoc, connector-as-runner y plugin-as-runner.
```

## 8. Criterios BLOCK

```text
La ADR autoriza ejecución remota inmediata.
Se habilita SSH, HTTP remote, gRPC, websockets, túneles o cloud control plane.
Se agregan credenciales remotas o lectura de secretos.
Se permite shell o ejecución arbitraria de comandos.
Se omite RBAC, Approval, sandbox, observabilidad o kill-switch.
Se interpreta plugin, connector, manifest o readiness como runner ejecutable.
```

## 9. Estado

Aceptada en `POST-H-021-B` como decisión **design-only**. No habilita ejecución remota. Debe revisarse únicamente después de POST-H-022, POST-H-023 y una ADR futura específica de enablement.
