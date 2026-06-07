---
title: "FUNC-SPRINT-01 — Auditoría de arquitectura interna del CLI"
doc_id: "DEVPL-AUDIT-FUNC-01-CLI-CORE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-01"
updated: "2026-06-06"
approval: "approved_by_implementation_evidence"
---

# FUNC-SPRINT-01 — Auditoría de arquitectura interna del CLI

## Propósito

Registrar la implementación del contrato común de resultados del CLI de DevPilot Local.

## Componentes creados

- `src/devpilot_core/cli_models.py`: define `CommandResult`, `Finding`, `Severity` y `ExitCode`.
- `src/devpilot_core/errors.py`: define `DevPilotError` para fallos controlados.
- `tests/test_cli_core.py`: valida contrato común, salida JSON y compatibilidad de comandos bootstrap.

## Componentes ajustados

- `src/devpilot_core/cli.py`: refactorizado para construir resultados normalizados y soportar `--json` en `readiness-check` y `miasi-required`.
- `README.md`: documenta comandos y códigos de salida.
- `docs/05_operations/runbook.md`: agrega operación del CLI core.

## Criterios PASS

- Los comandos existentes siguen funcionando.
- `--json` produce JSON parseable.
- `pytest -q` pasa.
- No se agregan dependencias externas.

## Riesgos

- Cambiar el contrato CLI sin mantener compatibilidad rompería sprints futuros.
- Salidas JSON inestables dificultarían reportes y validadores automatizados.

## Resultado

`FUNC-SPRINT-01` queda implementado y listo para servir de base a `FUNC-SPRINT-02 — Validador de frontmatter y metadatos documentales`.
