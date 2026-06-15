---
title: "Auditoría FUNC-SPRINT-67 — API local MVP read-only/dry-run"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-67-API-LOCAL-MVP"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-67"
updated: "2026-06-15"
source_repo: "repo_DevPilot_Local_81.zip"
verdict: "PASS"
---

# Auditoría FUNC-SPRINT-67 — API local MVP read-only/dry-run

## 0. Estado

Veredicto: `PASS`.

Estado de implementación: `implemented-initial`.

## 1. Propósito

Implementar la primera API HTTP local de DevPilot como adapter de interfaz para Web UI futura, manteniendo arquitectura web-first, local-first, dry-run-first y gobernada por `ApplicationService v2`.

## 2. Alcance implementado

Incluido:

- paquete `src/devpilot_core/interfaces/api`;
- app factory FastAPI;
- routers locales `/api/v1`;
- endpoints read-only/dry-run/plan-only;
- comando CLI `api serve` en modo dry-run por defecto;
- tests HTTP con `TestClient`;
- actualización de contrato API/OpenAPI/mapping;
- declaración de dependencias `api` y `dev` en `pyproject.toml`.

No incluido:

- Web UI;
- token local;
- CORS restringido;
- auth/RBAC;
- exposición pública;
- endpoints críticos `apply`/`execute`;
- Desktop shell.

## 3. Funcionamiento técnico

La API se crea mediante `create_app(root)` y almacena una instancia de `ApplicationService` en `app.state.application_service`. Los routers usan una dependencia `get_application_service()` y despachan operaciones con `ApplicationRequest` hacia `ApplicationService.handle()`.

Flujo:

```text
HTTP /api/v1/*
  → FastAPI router
    → ApiApplicationRequest/query params
      → ApplicationService.handle()
        → DomainService
          → CommandResult
            → ApplicationResponse
```

## 4. Archivos creados

- `src/devpilot_core/interfaces/__init__.py`: declara el paquete de adapters de interfaz.
- `src/devpilot_core/interfaces/api/__init__.py`: exporta `create_app`, host y puerto default.
- `src/devpilot_core/interfaces/api/app.py`: app factory FastAPI, configuración local y rutas.
- `src/devpilot_core/interfaces/api/dependencies.py`: dependencia de `ApplicationService` para routers.
- `src/devpilot_core/interfaces/api/models.py`: request HTTP y helper de dispatch/respuesta.
- `src/devpilot_core/interfaces/api/routers/status.py`: endpoints GET read-only.
- `src/devpilot_core/interfaces/api/routers/validation.py`: endpoints POST de validación/readiness.
- `src/devpilot_core/interfaces/api/routers/actions.py`: endpoints dry-run/plan-only.
- `tests/test_api_local.py`: pruebas HTTP locales.
- `tests/test_sprint_67_documentation.py`: pruebas documentales del sprint.
- `docs/functional_sprint_67_manifest.json`: manifiesto funcional.

## 5. Archivos modificados

- `pyproject.toml`: agrega extras `api` y dependencias `dev` para FastAPI/uvicorn/httpx.
- `src/devpilot_core/cli.py`: agrega `api serve` con dry-run por defecto y bloqueo de host no local.
- `src/devpilot_core/application/services.py`: declara API local MVP implementada y agrega operaciones `app.contract`/`standards.status` al dispatcher.
- `docs/07_interfaces/api_contract_v1.md`: pasa de contrato estático a contrato sincronizado con API MVP.
- `docs/07_interfaces/openapi_v1.json`: actualiza estado `implemented-initial` y agrega `/api/v1/standards/status`.
- `docs/07_interfaces/api_service_mapping.md`: sincroniza mapping con servidor MVP.
- `README.md`, `docs/05_operations/runbook.md`, `docs/devpilot_backlog_fase_F_producto_visual.md`, `docs/functional_backlog_after_precode.md`, `docs/02_architecture/c4_container.md`, `docs/07_interfaces/internal_application_contract.md`: sincronizan estado Fase F.

## 6. Criterios PASS

- API local responde endpoints MVP.
- Host default es `127.0.0.1`.
- `api serve --dry-run --json` no arranca servidor y reporta configuración válida.
- Routers delegan en `ApplicationService`.
- Respuestas funcionales usan `ApplicationResponse`.
- No existen rutas críticas de ejecución.
- `validate all` no reporta bloqueantes.

## 7. Criterios BLOCK

- Host default distinto a `127.0.0.1`.
- Endpoint crítico `apply`/`execute` expuesto.
- Router importando motores internos del core directamente.
- Respuesta funcional fuera de `ApplicationResponse`.
- CORS wildcard o token incompleto implementado antes de Sprint 68.
- Web UI o Desktop implementados en este sprint.

## 8. Riesgos y limitaciones

| Riesgo | Estado | Mitigación |
|---|---|---|
| API sin token/CORS | Aceptado por alcance | Sprint 68 obligatorio. |
| Exposición accidental | Controlado | Host localhost por defecto y bloqueo de host no local en CLI. |
| Divergencia API/OpenAPI | Controlado | Tests contractuales + mapping. |
| Dependencias nuevas | Controlado | Extras `api` y `dev` documentados. |
| Respuestas grandes de reportes/trazas | Pendiente | Límites por query y hardening posterior. |

## 9. Comandos de verificación

```powershell
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
python -m pytest tests/test_api_local.py -q
python -m pytest tests/test_api_contract.py -q
python -m pytest tests/test_sprint_67_documentation.py -q
python -m devpilot_core validate all --json
```

## 10. Conclusión

`FUNC-SPRINT-67` queda implementado como primera API local real de DevPilot. La solución es deliberadamente mínima, local, read-only/dry-run y no expuesta públicamente. La siguiente evolución obligatoria es `FUNC-SPRINT-68`, que debe agregar token local, CORS restringido y policy binding HTTP antes de que la Web UI dependa de esta API para flujos más amplios.
