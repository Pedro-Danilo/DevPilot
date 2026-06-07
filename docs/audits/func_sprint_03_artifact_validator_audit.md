---
title: "FUNC-SPRINT-03 — Artifact Validator Audit"
doc_id: "DEVPL-AUDIT-FUNC-03"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-07"
approval: "approved_by_execution_evidence"
---

# FUNC-SPRINT-03 — Artifact Validator Audit

## 1. Propósito

Este informe registra la implementación y validación de `FUNC-SPRINT-03 — Validador de artefactos MIPSoftware/MIASI`.

El sprint convierte el contrato documental aprobado en una validación ejecutable adicional: no basta con que un documento tenga frontmatter; ahora DevPilot puede verificar que un artefacto tenga una estructura mínima compatible con su perfil documental.

## 2. Fuente de verdad

- `docs/functional_backlog_after_precode.md`
- `docs/standards/mipsoftware/`
- `docs/standards/miasi/`
- `src/devpilot_core/cli_models.py`
- `src/devpilot_core/validators/frontmatter.py`

## 3. Componentes creados

| Componente | Rol |
|---|---|
| `src/devpilot_core/validators/artifact_profiles.py` | Catálogo determinístico de perfiles de artefactos. |
| `src/devpilot_core/validators/artifact.py` | Validador estructural de documentos Markdown. |
| `tests/test_artifact_validator.py` | Pruebas del validador y del comando CLI. |
| `tests/fixtures/docs/valid_requirements_artifact.md` | Fixture válido. |
| `tests/fixtures/docs/invalid_requirements_missing_sections.md` | Fixture incompleto. |
| `tests/fixtures/docs/approved_missing_sections.md` | Fixture aprobado con estructura inválida para probar `BLOCK`. |

## 4. Componentes modificados

| Componente | Ajuste |
|---|---|
| `src/devpilot_core/cli.py` | Se agregó el comando `validate-artifact`. |
| `README.md` | Se documentó el nuevo comando funcional. |
| `docs/05_operations/runbook.md` | Se agregó la operación del validador de artefactos. |
| `docs/functional_backlog_after_precode.md` | Se marcó FUNC-SPRINT-03 como implementado. |

## 5. Funcionamiento

El comando:

```powershell
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md
```

ejecuta los siguientes pasos:

1. Resuelve la ruta del artefacto.
2. Verifica que exista y sea un archivo Markdown.
3. Parsea el frontmatter con el validador de FUNC-SPRINT-02.
4. Selecciona un perfil documental según ruta y nombre de archivo.
5. Extrae headings Markdown.
6. Verifica H1 único.
7. Verifica secciones requeridas.
8. Emite `Finding` con severidad `warning`, `fail`, `block` o `error`.
9. Devuelve `CommandResult`.

## 6. Regla BLOCK

Si un documento tiene `status: approved` y no cumple estructura mínima, el validador debe emitir `BLOCK`.

Esta regla evita que un artefacto formalmente aprobado pueda permanecer inconsistente sin bloquear el avance.

## 7. Validación ejecutada

Comandos ejecutados en ambiente de desarrollo:

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --json
PYTHONPATH=src python -m devpilot_core validate-artifact docs/06_miasi/agent_card.md --json
PYTHONPATH=src python -m devpilot_core readiness-check --json
PYTHONPATH=src python -m devpilot_core miasi-required --json
```

Resultado:

```text
pytest: 20 passed
validate-artifact requirements_specification.md: PASS
validate-artifact agent_card.md: PASS con warning recomendado no bloqueante
readiness-check: PASS
miasi-required: PASS
```

## 8. Criterios PASS

- Existe `validate-artifact`.
- Usa `CommandResult`.
- Usa perfiles determinísticos.
- Detecta secciones mínimas faltantes.
- Emite `BLOCK` para documentos aprobados con estructura mínima fallida.
- No usa APIs externas.
- No agrega dependencias nuevas.
- Mantiene compatibilidad con comandos anteriores.
- `pytest -q` pasa.

## 9. Criterios BLOCK

El sprint habría quedado bloqueado si:

- `validate-artifact` modificaba archivos.
- Un documento `approved` con estructura mínima fallida no emitía `BLOCK`.
- El comando no soportaba salida `--json`.
- Se rompían `readiness-check`, `miasi-required` o `validate-frontmatter`.
- Se agregaban dependencias externas sin ADR.

## 10. Riesgos residuales

| Riesgo | Tratamiento |
|---|---|
| Los perfiles son mínimos y escritos en código. | Se refinarán en FUNC-SPRINT-04 con Standards Registry. |
| La validación estructural no reemplaza revisión humana. | Correcto; DevPilot combina gates automáticos y revisión owner. |
| El parser Markdown solo detecta headings ATX. | Aceptado para los documentos actuales. |
| Las reglas aún no derivan automáticamente de templates/schemas. | Pendiente para Standards Registry y validadores posteriores. |

## 11. Veredicto

```text
FUNC-SPRINT-03: PASS
Estado: implemented
Siguiente sprint: FUNC-SPRINT-04 — Standards Registry y carga local de reglas
```
