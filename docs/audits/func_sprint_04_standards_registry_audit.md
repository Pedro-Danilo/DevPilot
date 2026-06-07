---
title: "FUNC-SPRINT-04 — Standards Registry y carga local de reglas — Auditoría técnica"
doc_id: "DEVPL-AUDIT-FUNC-004"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-04"
updated: "2026-06-07"
approval: "approved_by_implementation_validation"
---

# FUNC-SPRINT-04 — Standards Registry y carga local de reglas — Auditoría técnica

## 1. Propósito

Registrar la implementación de un registro local de estándares para DevPilot Local. El objetivo del sprint fue permitir que el CLI detecte MIPSoftware y MIASI dentro de `docs/standards`, liste artefactos obligatorios del proyecto y exponga los perfiles de validación disponibles.

## 2. Fuente de verdad

- `docs/functional_backlog_after_precode.md`
- `docs/standards/mipsoftware`
- `docs/standards/miasi`
- `Log_consola_sprint_03.txt`
- `repo_DevPilot_Local_06.zip`

## 3. Componentes creados

### `src/devpilot_core/standards/catalog.py`

Define el catálogo mínimo de estándares requeridos y artefactos obligatorios del proyecto.

### `src/devpilot_core/standards/registry.py`

Implementa `StandardsRegistry` y `build_standards_status_result()`. Descubre estándares locales, verifica archivos requeridos, cuenta plantillas/checklists/schemas/ADRs y expone los perfiles de validación.

### `tests/test_standards_registry.py`

Prueba descubrimiento de MIPSoftware/MIASI, salida JSON del CLI y condición de bloqueo cuando falta un estándar crítico.

### `tests/conftest.py`

Agrega un hook de pytest para imprimir explícitamente el número de pruebas en PASS al ejecutar `pytest -q`.

## 4. Componentes modificados

- `src/devpilot_core/cli.py`: agrega `standards status`.
- `README.md`: sincroniza el estado del proyecto y documenta nuevos comandos.
- `docs/05_operations/runbook.md`: documenta operación del Standards Registry.
- `docs/functional_backlog_after_precode.md`: marca el sprint como implementado.

## 5. Funcionamiento

El comando:

```powershell
python -m devpilot_core standards status --json
```

produce un `CommandResult` con:

- estándares detectados;
- archivos requeridos por estándar;
- conteos de Markdown, JSON, templates, checklists, schemas y ADRs;
- artefactos obligatorios del proyecto;
- perfiles de validación ejecutables.

## 6. Criterios PASS

- Detecta `docs/standards/mipsoftware`.
- Detecta `docs/standards/miasi`.
- Verifica archivos mínimos de cada estándar.
- Lista artefactos obligatorios del proyecto.
- Expone perfiles de validación.
- Usa `CommandResult`.
- No requiere API keys, red ni dependencias externas.
- `pytest -q` pasa e imprime resumen explícito de pruebas.

## 7. Criterios BLOCK

- Falta el directorio de MIPSoftware.
- Falta el directorio de MIASI.
- Se rompe `readiness-check`, `miasi-required`, `validate-frontmatter` o `validate-artifact`.
- El comando modifica archivos sin autorización.
- Se introduce dependencia externa sin ADR.

## 8. Riesgos residuales

- Las reglas de perfil siguen en código Python.
- El registry aún no carga reglas desde schemas o JSON declarativos.
- La alineación completa entre estándares y validadores ejecutables será fortalecida en sprints posteriores.

## 9. Veredicto

`FUNC-SPRINT-04` queda en PASS técnico. DevPilot puede continuar con `FUNC-SPRINT-05 — Checklist pre-code y readiness estricto`.
