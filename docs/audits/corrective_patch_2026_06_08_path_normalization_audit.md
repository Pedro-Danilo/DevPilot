---
title: Corrective Patch — Path normalization for validator evidence
doc_id: DEVPL-AUDIT-PATCH-2026-06-08-PATHS
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-06-08
approval: approved_by_owner_direction
---

# Corrective Patch — Path normalization for validator evidence

## 1. Propósito

Este artefacto documenta una corrección posterior a `FUNC-SPRINT-09` para eliminar una falla de pruebas en Windows causada por diferencias de separador de rutas (`docs\\valid.md` frente a `docs/valid.md`).

## 2. Error observado

El test `test_cli_validate_frontmatter_emits_gate_event` fallaba porque el evento JSONL emitido por `validate-frontmatter` incluía en `summary.path` una ruta generada por `Path` con separador nativo de Windows. El contrato de evidencias de DevPilot usa rutas tipo repositorio con separador POSIX (`/`) para que JSON, Markdown, JSONL y pruebas sean deterministas entre Windows, Linux y CI.

## 3. Corrección aplicada

Se ajustó `src/devpilot_core/validators/frontmatter.py` para que `_display_path()` normalice siempre las rutas con `/`, tanto cuando calcula rutas relativas al `project_root` como cuando devuelve rutas absolutas o externas.

## 4. Funcionamiento

Antes de persistir o devolver la ruta en `CommandResult.data.path`, `_display_path()` aplica:

```python
.replace("\\\\", "/")
```

Con esto, los eventos derivados por `EventLogger`, los reportes producidos por `ReportEngine` y la salida JSON del validador mantienen una representación estable.

## 5. Integración

La corrección afecta directamente a:

- `validate-frontmatter`;
- `EventLogger.emit_result()` cuando resume `CommandResult.data.path`;
- reportes JSON/Markdown generados desde resultados de frontmatter;
- pruebas de observabilidad del Sprint 07;
- evidencia generada por comandos del Sprint 09.

## 6. Criterios PASS

- `pytest -q` debe pasar completo.
- El test reportado debe pasar en Windows.
- `summary.path` en eventos JSONL debe ser `docs/valid.md`, no `docs\\valid.md`.
- La salida JSON del validador debe conservar rutas normalizadas.
- No debe alterarse la validación semántica del frontmatter.

## 7. Criterios BLOCK

- Persistir rutas con separadores dependientes del sistema operativo en evidencias normalizadas.
- Romper `validate-frontmatter` en Linux, Windows o CI.
- Alterar exit codes o estructura de `CommandResult`.

## 8. Riesgos y evolución

Esta es una corrección puntual, no una nueva arquitectura de rutas. En una versión posterior conviene centralizar una utilidad pública de normalización de rutas para evitar duplicación entre validadores, reportes, observabilidad, workspace y policy guards.

## 9. Pruebas aplicadas

Se agregó una prueba regresiva:

```text
test_frontmatter_result_path_uses_posix_separator_for_windows_style_input
```

Pruebas ejecutadas:

```text
PYTHONPATH=src python -m pytest tests/test_event_logger.py::test_cli_validate_frontmatter_emits_gate_event tests/test_event_logger.py::test_frontmatter_result_path_uses_posix_separator_for_windows_style_input -q
PYTHONPATH=src python -m pytest -q
```

Resultado esperado:

```text
64 passed, 0 failed, 0 errors, 0 skipped
```
