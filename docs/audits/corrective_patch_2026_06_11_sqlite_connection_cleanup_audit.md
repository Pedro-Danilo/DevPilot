---
title: "Auditoría correctiva — cierre explícito de conexiones SQLite para cleanup Windows"
doc_id: "DEVPL-AUDIT-CORRECTIVE-SQLITE-CLEANUP-20260611"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
approval: "approved_by_owner_direction"
---

# Auditoría correctiva — cierre explícito de conexiones SQLite para cleanup Windows

## 1. Propósito

Documentar el patch correctivo aplicado después de detectar fallos de `pytest` en Windows durante `FUNC-SPRINT-34`. El problema se manifestaba al eliminar workspaces temporales usados por `PolicySimulationSuite` y `SecurityReadiness`, porque `.devpilot/devpilot.db` quedaba bloqueado por una conexión SQLite no cerrada explícitamente.

## 2. Estado

Patch correctivo implementado y validado. No introduce dependencias externas, red, APIs, proveedores, UI, acciones destructivas ni cambios de arquitectura.

## 3. Funcionamiento técnico

Se ajustó `LocalStore._connect()` para usar un context manager propio basado en `contextlib.contextmanager`. A diferencia del context manager nativo de `sqlite3.Connection`, este wrapper hace commit/rollback y además ejecuta `conn.close()` en `finally`. Esto evita que Windows mantenga bloqueado el archivo `.devpilot/devpilot.db` durante la limpieza de `TemporaryDirectory`.

## 4. Integración con DevPilot

El ajuste impacta positivamente toda la persistencia local que pasa por `LocalStore`: estado, historial, eventos, approvals, costos y readiness. No cambia esquemas, contratos JSON, tablas ni contenido funcional de la base de datos.

## 5. Comandos de uso

```powershell
python -m pytest tests/test_local_store.py tests/test_security_readiness.py tests/test_safe_subprocess_runner.py -q
python -m devpilot_core policy simulate --matrix standard --json
python -m devpilot_core security readiness --json
```

## 6. Criterios PASS

- `TemporaryDirectory` puede limpiar workspaces con `.devpilot/devpilot.db` en Windows.
- `tests/test_security_readiness.py` pasa sin `WinError 32`.
- `policy simulate --matrix standard` pasa.
- `security readiness` pasa.
- No se alteran contratos ni comportamiento funcional de Fase B.

## 7. Criterios BLOCK

- Cualquier conexión SQLite queda viva después de operaciones `LocalStore`.
- Vuelve a aparecer `PermissionError: [WinError 32]` sobre `.devpilot/devpilot.db`.
- `security readiness` o `policy simulate --matrix standard` retornan exit code distinto de cero por cleanup de temporales.

## 8. Riesgos

El cambio es bajo riesgo porque conserva el API interno de `LocalStore` y únicamente refuerza el ciclo de vida de conexiones. Debe observarse en Windows real con `pytest -q`, porque Linux permite borrar archivos abiertos y no reproduce exactamente el bloqueo.

## 9. Veredicto

El patch es procedente y necesario. Corrige una incompatibilidad operacional Windows sin relajar controles de seguridad ni introducir dependencias.
