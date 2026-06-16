---
title: "Correctivo Sprint 69 — Smoke test Web UI tolerante a ausencia de npm"
doc_id: "DEVPL-AUDIT-CORR-SPRINT-69-WEB-UI-NPM-OPTIONAL"
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

# Correctivo Sprint 69 — Smoke test Web UI tolerante a ausencia de npm

## 0. Estado

Veredicto: `PASS`.

Estado: `corrective-patch`.

## 1. Propósito

Corregir el fallo de `pytest -q` cuando el entorno Python de DevPilot no tiene `npm` disponible en `PATH`, sin debilitar el contrato de Web UI API-only/read-only definido en `FUNC-SPRINT-69`.

## 2. Causa raíz

`tests/test_web_ui_mvp.py` ejecutaba siempre `subprocess.run(["npm", "test"], ...)`. En Windows, si Node.js/npm no están instalados o no están en `PATH`, `subprocess.Popen` lanza `FileNotFoundError` antes de que el test pueda evaluar el contrato de UI.

El test era inconsistente con su intención original de validar el smoke contract sin instalar dependencias frontend. La ausencia de npm no debe bloquear la suite Python del core.

## 3. Corrección aplicada

- Se agregó un smoke contract Python equivalente a las verificaciones críticas de `ui/web/scripts/smoke-test.mjs`.
- El test Python valida siempre el contrato API-only/read-only sin Node/npm.
- `npm test` se ejecuta adicionalmente solo cuando `npm` está disponible.
- Se actualizó documentación para distinguir entre gate Python obligatorio y smoke test npm opcional según toolchain local.

## 4. Archivos modificados

- `tests/test_web_ui_mvp.py`
- `README.md`
- `docs/05_operations/runbook.md`
- `docs/audits/func_sprint_69_web_ui_dashboard_audit.md`
- `ui/web/README.md`

## 5. Archivos creados

- `docs/audits/corrective_sprint69_web_ui_smoke_npm_optional_audit.md`

## 6. Criterios PASS

- `pytest -q` no falla por ausencia de `npm`.
- `tests/test_web_ui_mvp.py` valida que la UI no importe `devpilot_core`.
- El cliente frontend sigue usando `/api/v1` y `X-DevPilot-Token`.
- La UI no invoca rutas destructivas.
- `npm test` sigue pasando cuando Node.js/npm están disponibles.

## 7. Criterios BLOCK

- El test Python omite validar el contrato de UI cuando no hay npm.
- La UI importa Python/core o lee `outputs/`/`.devpilot/`.
- Se elimina `npm test` como verificación opcional de frontend.
- Se introducen dependencias nuevas no justificadas.

## 8. Riesgos y limitaciones

- El smoke contract Python no reemplaza una prueba visual end-to-end con navegador.
- La ejecución real de la Web UI sigue requiriendo Node.js 20+.
- Sprint 70 deberá mantener la misma separación: tests Python obligatorios reproducibles y pruebas frontend explícitas cuando exista toolchain Node.

## 9. Comandos de verificación

```powershell
python -m pytest tests/test_web_ui_mvp.py -q
python -m pytest tests/test_web_ui_mvp.py tests/test_sprint_69_documentation.py -q
python -m devpilot_core validate-artifact docs/audits/corrective_sprint69_web_ui_smoke_npm_optional_audit.md --json
python -m devpilot_core validate all --json

# Opcional si Node.js/npm están instalados
cd ui/web
npm test
cd ../..
```

## 10. Conclusión

El patch mantiene el alcance de Sprint 69 y corrige el único fallo reportado en `pytest` sin agregar dependencias ni cambiar comportamiento runtime de la API o la Web UI.
