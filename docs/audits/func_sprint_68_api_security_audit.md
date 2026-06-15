---
title: "Auditoría FUNC-SPRINT-68 — Seguridad API local"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-68"
status: "approved"
approval: "approved_after_security_implementation_review"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-68"
updated: "2026-06-15"
source_repo: "repo_DevPilot_Local_84.zip"
---

# Auditoría FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding

## 0. Estado

Veredicto: `PASS` / `implemented-initial`.

Sprint 68 endurece la API local MVP antes de que la Web UI local la consuma. El alcance es deliberadamente limitado: token local temporal, CORS restringido, headers mínimos y policy binding. No implementa RBAC enterprise, usuarios, login, sesiones, TLS productivo ni despliegue público.

## 1. Propósito

Reducir la superficie de ataque de la API localhost creada en Sprint 67, manteniendo el principio local-first, dry-run-first, policy-first y ApplicationService-first.

## 2. Alcance implementado

- Token local requerido para endpoints protegidos.
- Endpoints públicos mínimos: `/api/v1/health`, `/api/v1/docs`, `/api/v1/openapi.json`.
- CORS allowlist local sin wildcard.
- Headers mínimos: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control`, `Permissions-Policy`.
- Binding de rutas protegidas con `PolicyEngine` vía `API_ROUTE_POLICIES`.
- CLI `api token` para generar token sin persistirlo.
- CLI `api serve` actualizado para reportar seguridad sin imprimir token crudo.

## 3. Funcionamiento técnico

La API aplica un middleware HTTP central:

```text
request /api/v1/*
  → public path check
  → token validation
  → route policy lookup
  → PolicyEngine.evaluate
  → route handler
  → ApplicationService.handle
  → ApplicationResponse
```

Los routers siguen sin importar validadores o motores internos directamente. La seguridad se ubica en el adapter HTTP y la lógica de negocio permanece detrás de `ApplicationService`.

## 4. Archivos creados

- `src/devpilot_core/interfaces/api/security.py`: configuración de token, CORS, policy binding, redacción y errores de seguridad.
- `tests/test_api_security.py`: pruebas de token ausente/inválido/válido, CORS restringido, policy binding, `api token`, `api serve` y bloqueo de host remoto.
- `docs/audits/func_sprint_68_api_security_audit.md`: auditoría del sprint.
- `docs/functional_sprint_68_manifest.json`: manifiesto funcional.

## 5. Archivos modificados

- `src/devpilot_core/interfaces/api/app.py`: middleware de seguridad, CORS, headers y health actualizado.
- `src/devpilot_core/interfaces/api/__init__.py`: exports de helpers de seguridad.
- `src/devpilot_core/cli.py`: comando `api token` y `api serve` endurecido.
- `src/devpilot_core/application/services.py`: `application_contract()` reporta `api_security_implemented=true`.
- `docs/07_interfaces/api_contract_v1.md`: contrato v1 actualizado a `secured-initial`.
- `docs/07_interfaces/openapi_v1.json`: OpenAPI con `LocalTokenAuth`, status `secured-initial` y `401`.
- `docs/07_interfaces/api_service_mapping.md`: mapping endpoint→policy binding.
- `docs/03_security/ui_api_threat_model.md`: controles Sprint 68 anotados.
- `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_F_producto_visual.md`, `docs/functional_backlog_after_precode.md`, `docs/02_architecture/c4_container.md`, `docs/07_interfaces/internal_application_contract.md`: sincronización de estado.

## 6. Criterios PASS

- Token requerido para endpoints no públicos.
- CORS sin wildcard por defecto.
- Headers de seguridad presentes.
- `API_ROUTE_POLICIES` cubre rutas protegidas.
- `api token --json` genera token sin escribir reportes.
- `api serve --dry-run --json` no imprime token crudo.
- Host remoto sigue bloqueado.
- No se implementa Web UI ni Desktop.

## 7. Criterios BLOCK

- CORS wildcard por defecto.
- Token crudo persistido en logs/reportes.
- Endpoint protegido sin policy binding.
- API aceptando `0.0.0.0`.
- Endpoint write/execute expuesto sin Approval Workflow.
- UI o Desktop implementados por fuera del alcance del sprint.

## 8. Riesgos y limitaciones

| Riesgo | Estado | Mitigación |
|---|---|---|
| Token local no protege contra malware local | Aceptado MVP | No persistir token y documentar límite. |
| No hay RBAC/login | Aceptado | Sprint 68 no implementa multiusuario. |
| Sin TLS | Aceptado localhost | Web real futura requiere ADR/threat model. |
| Policy binding inicial usa acciones read/dry-run | Aceptado | Acciones mutantes futuras deberán usar approval. |

## 9. Comandos de verificación

```powershell
python -m devpilot_core api token --json
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
python -m pytest tests/test_api_security.py -q
python -m pytest tests/test_api_local.py tests/test_api_contract.py -q
python -m devpilot_core validate all --json
```

## 10. Conclusión

Sprint 68 queda implementado como primera capa de seguridad local ejecutable para la API. La API sigue siendo local, preliminar e industrializable; el siguiente paso lógico es `FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI` consumiendo esta API y sin importar código del core.
