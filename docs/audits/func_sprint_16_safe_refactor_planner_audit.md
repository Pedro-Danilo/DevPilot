---
title: "FUNC-SPRINT-16 — Safe Refactor Planner Audit"
doc_id: "DEVPL-AUDIT-FUNC-016"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-16"
updated: "2026-06-08"
---
# FUNC-SPRINT-16 — Safe Refactor Planner Audit

## Propósito

Documentar la implementación inicial de `FUNC-SPRINT-16 — Safe Refactor Planner`, cuyo objetivo es producir planes de refactor seguros, reversibles y testeables sin modificar código automáticamente.

## Alcance implementado

Se implementó un flujo `plan-only`:

- módulo `src/devpilot_core/refactor/planner.py`;
- API pública `src/devpilot_core/refactor/__init__.py`;
- comando CLI `python -m devpilot_core refactor-plan`;
- integración con `PolicyEngine`, `SecretGuard`, `CodeReviewEngine`, `ReportEngine`, `EventLogger` y `LocalStore`;
- actualización de Tool Registry MIASI con `refactor.plan`;
- pruebas automatizadas en `tests/test_refactor_planner.py`.

## Funcionamiento técnico

`RefactorPlanner` valida primero la intención y el target mediante políticas determinísticas. Después analiza archivos Python con `ast` de la biblioteca estándar, identifica candidatos heurísticos y emite un plan serializable con pasos, pruebas requeridas y rollback. La documentación oficial de Python define `ast` como el módulo para trabajar con árboles de sintaxis abstracta de Python, lo cual encaja con este análisis estructural sin ejecutar código.

El planner no emite contenido crudo de archivos, no genera patches, no ejecuta tests, no llama modelos, no usa APIs externas y no modifica archivos.

## Comandos

```powershell
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json
python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared helpers" --json --write-report
```

## Criterios PASS

```text
refactor-plan devuelve CommandResult JSON parseable.
dry_run=true.
plan_only=true.
files_modified=0.
patch_generated=false.
tests_required=true.
approval_required_for_execution=true.
reportes opcionales se escriben solo bajo outputs/reports.
pytest -q pasa completo.
```

## Criterios BLOCK

```text
target fuera del workspace.
ruta bloqueada por PathGuard.
goal con secreto sintético.
target inexistente.
error de sintaxis Python en archivos analizados.
cualquier intento de modificar archivos o generar/aplicar patches.
```

## Pruebas aplicadas

`tests/test_refactor_planner.py` cubre:

- generación de plan sin modificar archivos;
- bloqueo de goal con secreto sintético sin fuga del valor crudo;
- bloqueo de target fuera del workspace;
- plan conservador para archivo pequeño sin candidatos;
- CLI JSON + `--write-report` parseable;
- detección de error de sintaxis Python.

Resultado esperado:

```text
pytest -q -> 108 passed
```

## Riesgos y limitaciones

Esta es una primera versión. No es un refactorizador semántico, no aplica transformaciones AST, no genera patches, no ejecuta tests, no integra linters externos, no valida tipos, no garantiza que una propuesta sea óptima y no reemplaza revisión humana. La ejecución futura de refactors deberá requerir aprobación humana, sandbox, backup/rollback y gates de calidad.

## ADR

No se abrió una ADR nueva. Se actualizó `ADR-0005-git-adapter-read-only-mvp-plus.md`, porque Sprint 16 continúa la misma línea arquitectónica: lectura/análisis/planificación segura antes de cualquier acción modificadora.
