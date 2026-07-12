---
doc_id: "ADR-POSTH-034-C"
title: "ADR-POSTH-034-C — Remote execution ADR-3"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
decision_state: "continue-blocked"
decision_status: "continue-blocked"
micro_sprint: "POST-H-034-C"
phase: "POST-FASE-H"
local_first: true
remote_execution_enabled: false
remote_runner_enabled: false
runtime_execution_enabled: false
remote_transport_enabled: false
shell_allowed: false
arbitrary_command_execution_allowed: false
network_allowed: false
external_api_allowed: false
credentials_required: false
requires_future_enablement_adr: true
requires_future_backlog: true
preliminary: true
---

# ADR-POSTH-034-C — Remote execution ADR-3

## 1. Contexto

POST-H-021 dejó `Remote Runner ADR-2` como diseño controlado y `remote execution` explícitamente deshabilitado. POST-H-023 agregó diseño de transporte seguro, lifecycle futuro de llaves/certificados y validator no-network, pero no implementó transporte activo. POST-H-034-C debe cerrar la ambigüedad industrial: tener remote runner, readiness y secure transport design no equivale a permitir ejecución remota.

El estado base vigente es:

```text
remote_execution_enabled=false
remote_runner_enabled=false
execution_allowed=false
runtime_execution_enabled=false
remote_transport_enabled=false
shell_allowed=false
arbitrary_command_execution_allowed=false
network_allowed=false
external_api_allowed=false
credentials_required=false
secure_transport_implemented=false
transport_implemented=false
```

## 2. Decisión

La decisión aprobada para POST-H-034-C es **`continue-blocked`**.

DevPilot mantiene la ejecución remota bloqueada. La ADR-3 no habilita remote runner, transporte, red, shell remoto, workers remotos, control plane, credenciales remotas ni ejecución de comandos fuera del workspace local.

Reglas de interpretación:

```text
remote runner registry exists != remote execution enabled
remote readiness exists != remote-ready claim
secure transport design exists != secure transport implemented
protocol matrix exists != network allowed
ADR-POSTH-034-C exists != runtime enablement
```

## 3. Alternativas evaluadas

| Alternativa | Resultado | Motivo |
|---|---|---|
| `continue-blocked` | Aceptada | Preserva local-first, no-network y producción local acotada mientras faltan controles críticos. |
| `pilot-gated-future` | Pospuesta | Puede evaluarse en un backlog futuro con fake remote runner, transport sandbox, identity/RBAC endurecido, Approval binding, kill-switch y pruebas de red controlada. |
| `approved-for-future-implementation` | Rechazada para el estado actual | Faltan secure transport implementado, identity fuerte, sandbox remoto, command allowlist, observabilidad end-to-end, rollback y pruebas adversariales. |
| `enable-now` | Prohibida | Habilitaría una superficie crítica: red, credenciales, shell/comandos y ejecución fuera del control local. |

## 4. Prerrequisitos mínimos para cualquier piloto futuro

Un backlog futuro de piloto remoto, no productivo, solo podría evaluarse si existen todos estos controles:

1. ADR de enablement aprobada posterior a esta ADR-3.
2. Secure transport implementado y validado, no solo design-only.
3. Identity/RBAC robusto por actor, role, workspace, command_id, target y risk.
4. Approval binding explícito antes del dispatch remoto.
5. Remote sandbox con aislamiento de filesystem, workspace y proceso.
6. Command allowlist con deny-by-default y bloqueo de shell arbitrario.
7. Secret handling no versionado, con rotación/revocación y redacción.
8. Observability end-to-end con audit trail de request, approval, dispatch y result.
9. Kill-switch local y remoto.
10. Rollback/cleanup para operaciones fallidas.
11. Network security tests y fake remote runner tests.
12. Rate limits, timeouts, idempotency y replay protection.
13. No cloud control plane sin ADR separada.
14. Quality gate `remote-execution-disabled-or-approved` antes de cualquier piloto.

## 5. No-go gates vigentes

Los siguientes estados siguen bloqueados:

```text
remote_execution_enabled=true
remote_runner_enabled=true
runtime_execution_enabled=true
remote_transport_enabled=true
shell_allowed=true
arbitrary_command_execution_allowed=true
network_allowed=true
external_api_allowed=true
credentials_required=true
secure_transport_implemented=true sin ADR posterior
remote-ready claim=true
```

## 6. Consecuencias

- POST-H-034-C agrega trazabilidad formal para una decisión sensible sin ampliar superficie de ataque.
- El quality gate sensible ahora valida connector write, plugin execution y remote execution como subgates separados.
- Cualquier cambio futuro que pretenda activar remote execution debe modificar una matriz, checklist, ADR, project_state, TCR y pruebas negativas. Eso vuelve el cambio auditable y bloqueable.

## 7. Estado de implementación

Esta ADR queda **implemented-initial / approved** como artefacto de gobierno. No es implementación de runtime remoto. La evolución a producción industrial requerirá backlog separado, threat model actualizado, sandbox real, pruebas adversariales y decisión explícita del owner.
