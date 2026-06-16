---
title: "Correctivo Sprint 69 — Smoke test Web UI con npm opt-in y resolución robusta"
doc_id: "DEVPL-AUDIT-CORR-SPRINT69-WEB-UI-NPM-INVOCATION-V2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "CORR-SPRINT-69"
updated: "2026-06-15"
approval: "approved_by_corrective_validation"
---

# Correctivo Sprint 69 — Smoke test Web UI con npm opt-in y resolución robusta

## 0. Estado

Veredicto: `PASS`.

Estado: `corrective-implemented`.

## 1. Propósito

Corregir el fallo de `pytest -q` producido por la ejecución obligatoria de `npm test` desde `tests/test_web_ui_mvp.py` en entornos Windows donde `shutil.which("npm")` detecta un wrapper, pero `subprocess.run(["npm", "test"])` no puede ejecutarlo con `shell=False`.

## 2. Causa raíz

El correctivo anterior hizo opcional la ejecución cuando `npm` no existía, pero mantuvo una ruta frágil: si `shutil.which("npm")` devolvía un resultado, el test intentaba ejecutar literalmente `npm`. En Windows, `npm` suele resolverse como `npm.cmd`; `subprocess` puede fallar si se invoca el nombre sin resolver o si el wrapper no es ejecutable desde el contexto del proceso.

## 3. Corrección aplicada

- El smoke contract Python sigue siendo obligatorio y no requiere Node/npm.
- La ejecución de `npm test` desde pytest pasa a ser explícita mediante `DEVPILOT_RUN_WEB_UI_NPM_TEST=1`.
- Cuando se activa, el test resuelve `npm.cmd`, `npm.exe` o `npm` antes de ejecutar.
- Si el entorno opt-in no puede ejecutar npm, el error explica la causa y las acciones correctivas.

## 4. Archivos modificados

- `tests/test_web_ui_mvp.py`
- `README.md`
- `docs/05_operations/runbook.md`
- `docs/audits/func_sprint_69_web_ui_dashboard_audit.md`
- `ui/web/README.md`

## 5. Criterios PASS

- `pytest -q` no depende obligatoriamente de Node/npm.
- `tests/test_web_ui_mvp.py` valida siempre el contrato API-only/read-only desde Python.
- `npm test` puede ejecutarse bajo opt-in con `DEVPILOT_RUN_WEB_UI_NPM_TEST=1`.
- La UI sigue sin importar `devpilot_core`, sin leer filesystem y sin invocar rutas destructivas.

## 6. Criterios BLOCK

- `pytest -q` vuelve a fallar por ausencia o mala resolución de `npm`.
- El smoke contract Python se elimina o se relaja hasta dejar de validar el contrato UI/API.
- La ejecución opt-in de `npm test` oculta errores reales del frontend cuando sí se solicita explícitamente.

## 7. Comandos de verificación

```powershell
python -m pytest tests/test_web_ui_mvp.py -q
python -m pytest tests/test_web_ui_mvp.py tests/test_sprint_69_documentation.py -q
python -m devpilot_core validate all --json

# Verificación opcional con Node/npm
$env:DEVPILOT_RUN_WEB_UI_NPM_TEST = "1"
python -m pytest tests/test_web_ui_mvp.py -q
Remove-Item Env:DEVPILOT_RUN_WEB_UI_NPM_TEST
```

## 8. Conclusión

El correctivo mantiene reproducible el quality gate Python/core y conserva la verificación Node/npm como prueba explícita de frontend. No cambia el alcance funcional de Sprint 69.
