---
title: "Auditoría correctiva — Sprint 67 route introspection compatible con FastAPI/Starlette"
doc_id: "DEVPL-AUDIT-CORR-SPRINT-67-API-ROUTE-INTROSPECTION"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-67"
updated: "2026-06-15"
source_repo: "repo_DevPilot_Local_82.zip"
verdict: "PASS"
approval: "approved-for-corrective-patch"
---

# Auditoría correctiva — Sprint 67 route introspection compatible con FastAPI/Starlette

## 0. Estado

Veredicto: `PASS`.

Tipo: patch correctivo mínimo post-implementación de `FUNC-SPRINT-67`.

## 1. Propósito

Corregir un fallo de compatibilidad observado al ejecutar `pytest -q` con versiones recientes de FastAPI/Starlette, donde `app.routes` puede contener objetos internos sin atributo `path`.

El problema afectaba la prueba `test_api_local_routes_are_limited_to_read_or_dry_run_mvp` y podía afectar también el resumen dry-run del comando `python -m devpilot_core api serve --dry-run`.

## 2. Causa raíz

La implementación inicial del Sprint 67 asumía que todos los elementos de `FastAPI.app.routes` exponían un atributo string `path`.

Esa suposición es frágil porque `app.routes` pertenece a la implementación interna de FastAPI/Starlette y puede incluir objetos auxiliares route-like que no representan rutas HTTP concretas.

## 3. Alcance corregido

Incluido:

- helper `api_route_paths(app, prefix="/api/v1/")`;
- uso del helper en CLI `api serve`;
- uso del helper en tests Sprint 67;
- test explícito que simula un objeto sin `path` dentro de `app.routes`.

No incluido:

- cambios en endpoints;
- cambios en OpenAPI;
- cambios en seguridad token/CORS;
- cambios en Web UI;
- cambios en Desktop;
- nuevas dependencias.

## 4. Funcionamiento técnico

El helper `api_route_paths()` itera defensivamente sobre `app.routes`, obtiene `path` mediante `getattr`, verifica que sea string y filtra únicamente rutas con prefijo `/api/v1/`.

Esto mantiene estable el contrato operativo de DevPilot aunque cambien detalles internos de FastAPI/Starlette.

## 5. Archivos modificados

- `src/devpilot_core/interfaces/api/app.py`: agrega `api_route_paths()`.
- `src/devpilot_core/interfaces/api/__init__.py`: exporta `api_route_paths`.
- `src/devpilot_core/cli.py`: reemplaza introspección directa de `app.routes` por `api_route_paths(app)`.
- `tests/test_api_local.py`: reemplaza introspección directa por helper y agrega prueba de compatibilidad.

## 6. Criterios PASS

- `tests/test_api_local.py` pasa.
- `tests/test_api_contract.py` pasa.
- `api serve --dry-run` reporta rutas sin fallar.
- Host no local sigue bloqueado.
- No aparecen rutas críticas `patch/apply`, `rollback/execute`, `refactor/execute`.
- `validate all` no tiene findings bloqueantes.

## 7. Criterios BLOCK

Debe bloquearse si:

- el CLI `api serve --dry-run` vuelve a iterar `app.routes` directamente usando `route.path` sin guardas;
- una prueba depende de detalles internos no estables de FastAPI/Starlette;
- la corrección introduce rutas nuevas no declaradas;
- la corrección habilita red externa, token/CORS parcial o endpoints destructivos.

## 8. Riesgos y limitaciones

- El patch no resuelve la advertencia de deprecación `StarletteDeprecationWarning` sobre `TestClient`; no es un fallo funcional y deberá evaluarse en un sprint o patch posterior si se vuelve bloqueante.
- La API sigue siendo MVP `implemented-initial`; token y CORS siguen diferidos a `FUNC-SPRINT-68`.

## 9. Comandos de verificación

```powershell
python -m pytest tests/test_api_local.py tests/test_api_contract.py -q
python -m pytest tests/test_api_local.py tests/test_api_contract.py tests/test_sprint_67_documentation.py tests/test_application_services.py tests/test_application_services_v2.py -q
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
python -m devpilot_core api serve --host 0.0.0.0 --port 8787 --dry-run --json
python -m devpilot_core validate-artifact docs/audits/corrective_sprint67_fastapi_route_introspection_audit.md --json
python -m devpilot_core validate all --json
```

## 10. Conclusión

El fallo fue causado por introspección frágil de rutas, no por un defecto funcional de los endpoints API. El patch centraliza la introspección de rutas en un helper estable y mantiene intacto el alcance de `FUNC-SPRINT-67`.
