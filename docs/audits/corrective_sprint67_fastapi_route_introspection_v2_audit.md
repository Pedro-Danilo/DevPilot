---
title: "Auditoría correctiva — Sprint 67 route introspection v2 compatible con FastAPI/Starlette"
doc_id: "DEVPL-AUDIT-CORR-SPRINT-67-API-ROUTE-INTROSPECTION-V2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-67"
updated: "2026-06-16"
source_repo: "repo_DevPilot_Local_83.zip"
verdict: "PASS"
approval: "approved-for-corrective-patch"
---


# Correctivo Sprint 67 — Introspección robusta de rutas FastAPI v2

## 0. Estado

Veredicto: PASS correctivo.

Este artefacto registra el segundo ajuste correctivo aplicado sobre la API local MVP de FUNC-SPRINT-67. El patch no cambia el contrato funcional de la API ni habilita nuevas rutas; solo endurece la introspección de rutas frente a diferencias internas entre versiones de FastAPI/Starlette.

## 1. Propósito

Corregir el fallo de pytest donde `api_route_paths(app)` devolvía únicamente rutas utilitarias (`/api/v1/docs`, `/api/v1/openapi.json`, `/api/v1/health`) y omitía endpoints incluidos mediante routers como `/api/v1/workspace/status`.

## 2. Causa raíz

El primer correctivo evitó el uso directo de `route.path` sobre objetos sin atributo `path`, pero el helper seguía dependiendo principalmente de `app.routes` plano. En el entorno local con FastAPI/Starlette más reciente, los routers incluidos pueden quedar representados por wrappers internos o contenedores no homogéneos. Por ello, la introspección debe combinar:

1. `app.openapi()["paths"]`, que representa el contrato HTTP semántico de FastAPI.
2. Un recorrido defensivo y recursivo de estructuras `routes`, `router.routes` y `app.routes` para conservar rutas utilitarias y compatibilidad con versiones donde sí se aplanan rutas.

## 3. Alcance implementado

- Se actualizó `api_route_paths(app)` para leer primero el mapa OpenAPI.
- Se agregó un helper interno recursivo `_collect_route_paths_from_route_tree`.
- Se mantuvo el filtrado por prefijo `/api/v1/`.
- Se agregaron pruebas de regresión para rutas OpenAPI y wrappers router-like.

## 4. Archivos modificados

- `src/devpilot_core/interfaces/api/app.py`: introspección robusta de rutas.
- `tests/test_api_local.py`: pruebas de regresión adicionales.
- `docs/audits/corrective_sprint67_fastapi_route_introspection_v2_audit.md`: auditoría correctiva.

## 5. Criterios PASS

- `api_route_paths(create_app(ROOT))` incluye `/api/v1/workspace/status`.
- `api_route_paths(create_app(ROOT))` incluye todos los paths semánticos de `app.openapi()["paths"]`.
- El helper ignora objetos sin `path`.
- El helper recorre objetos router-like con atributo `routes`.
- `api serve --dry-run` reporta rutas reales y `dangerous_routes_total=0`.
- `0.0.0.0` permanece bloqueado.

## 6. Criterios BLOCK

- Si el helper vuelve a depender exclusivamente de `route.path` plano.
- Si se omiten endpoints declarados por OpenAPI.
- Si se agrega una ruta destructiva.
- Si se habilita servidor remoto, CORS o token fuera del alcance de Sprint 67.

## 7. Comandos de verificación

```powershell
python -m pytest tests/test_api_local.py tests/test_api_contract.py -q
python -m pytest tests/test_api_local.py tests/test_api_contract.py tests/test_sprint_67_documentation.py tests/test_application_services.py tests/test_application_services_v2.py -q
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
python -m devpilot_core api serve --host 0.0.0.0 --port 8787 --dry-run --json
python -m devpilot_core validate all --json
```

## 8. Riesgos y limitaciones

- El helper invoca `app.openapi()`; en DevPilot esto es aceptable porque la API es local y el contrato OpenAPI ya forma parte del Sprint 66/67.
- FastAPI puede seguir cambiando internals; por eso el código evita depender de clases internas concretas.
- Token, CORS y policy binding siguen diferidos explícitamente a FUNC-SPRINT-68.

## 9. Conclusión

El fallo de pytest queda corregido mediante una introspección de rutas más estable, basada en el contrato OpenAPI y un recorrido defensivo de estructuras route-like. No se modifica el alcance funcional de la API local MVP.
