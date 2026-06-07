---
title: "FUNC-SPRINT-05 — Checklist pre-code y readiness estricto — Auditoría técnica"
doc_id: "DEVPL-AUDIT-FUNC-005"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-05"
updated: "2026-06-07"
approval: "approved_by_implementation_validation"
---

# FUNC-SPRINT-05 — Checklist pre-code y readiness estricto — Auditoría técnica

## 1. Propósito

Registrar la implementación de un gate ejecutable para validar la baseline documental pre-code de DevPilot Local. El sprint convierte `docs/checklists/checklist_pre_code.md` en una fuente verificable por CLI y endurece `readiness-check` mediante el modo `--strict`.

## 2. Fuente de verdad

- `docs/functional_backlog_after_precode.md`
- `docs/checklists/checklist_pre_code.md`
- `docs/standards/mipsoftware`
- `docs/standards/miasi`
- `Log_consola_sprint_04.txt`
- `repo_DevPilot_Local_07.zip`

## 3. Componentes creados

### `src/devpilot_core/validators/checklist.py`

Implementa un parser determinístico de tablas Markdown y el gate `validate_precode_checklist()`. Evalúa filas obligatorias, estado `PASS`, existencia de artefactos, directorios de evidencia y `status: approved` en artefactos Markdown.

### `src/devpilot_core/validators/readiness.py`

Centraliza la lógica de readiness. Mantiene compatibilidad con el readiness histórico no estricto y agrega `build_strict_readiness_result()`, que compone validación de frontmatter, artefactos, checklist, Standards Registry y activación MIASI.

### `tests/test_precode_readiness.py`

Agrega pruebas de parser, comando CLI, escenario PASS y escenario BLOCK cuando faltan artefactos obligatorios.

### `docs/functional_sprint_05_manifest.json`

Registra archivos creados, archivos modificados, comandos validados, resultados esperados y ausencia de dependencias externas.

## 4. Componentes modificados

- `src/devpilot_core/cli.py`: agrega `checklist-pre-code` y `readiness-check --strict`.
- `src/devpilot_core/validators/artifact.py`: el extractor de headings ignora fenced code blocks para evitar falsos positivos en ejemplos de consola.
- `src/devpilot_core/validators/artifact_profiles.py`: alinea perfiles determinísticos con los encabezados reales de la baseline aprobada.
- `README.md`: sincroniza estado operativo y comandos del Sprint 05.
- `docs/05_operations/runbook.md`: documenta procedimientos, criterios PASS/BLOCK y evidencia generada.
- `docs/functional_backlog_after_precode.md`: marca Sprint 05 como implementado y promueve Sprint 06 como siguiente hito.

## 5. Funcionamiento

El comando:

```powershell
python -m devpilot_core checklist-pre-code --json
```

produce un `CommandResult` con filas del checklist, estado de obligatoriedad, artefacto asociado, existencia física, estado de frontmatter y hallazgos.

El comando:

```powershell
python -m devpilot_core readiness-check --strict --json
```

produce un `CommandResult` con:

- artefactos obligatorios;
- estado de existencia y tamaño;
- resultado de frontmatter;
- resultado de validación estructural;
- estado del checklist;
- estado del Standards Registry;
- activación MIASI;
- reportes generados.

## 6. Criterios PASS

- `checklist-pre-code --json` devuelve `ok=true`.
- Todas las filas obligatorias del checklist están en `PASS`.
- Los artefactos obligatorios referenciados existen.
- Los artefactos Markdown obligatorios tienen `status: approved`.
- `readiness-check --strict --json` devuelve `ok=true`.
- Se generan `outputs/reports/readiness_check.json` y `outputs/reports/readiness_check.md`.
- `pytest -q` pasa con 30 pruebas.

## 7. Criterios BLOCK

- Falta el checklist pre-code.
- Una fila obligatoria no está en PASS.
- Falta un artefacto obligatorio.
- Falta una pieza MIASI obligatoria.
- Un artefacto obligatorio no está aprobado.
- El Standards Registry no detecta MIPSoftware o MIASI.
- Un documento aprobado incumple estructura mínima.

## 8. Ajustes correctivos sobre sprints previos

Durante la implementación se detectó que `validate-artifact` podía interpretar comentarios dentro de bloques de código como encabezados Markdown. Esto no era un fallo del Sprint 05, sino una limitación del validador del Sprint 03. Se corrigió ignorando fenced code blocks en `extract_headings()`.

También se ajustaron perfiles de artefactos para reflejar los encabezados reales de la baseline aprobada. El ajuste es compatible con MIPSoftware/MIASI, no introduce dependencias y no altera alcance de producto, arquitectura, seguridad, agentes, costos ni APIs. Por tanto, no requiere una nueva ADR.

## 9. Riesgos residuales

- El parser de checklist es una primera versión enfocada en las tablas actuales.
- Los perfiles de validación siguen en Python; deben migrar hacia reglas declarativas versionadas.
- Los warnings recomendados no bloquean todavía.
- La evidencia JSON/Markdown generada por readiness es básica y debe formalizarse en el Sprint 06.

## 10. Veredicto

`FUNC-SPRINT-05` queda en PASS técnico. DevPilot puede continuar con `FUNC-SPRINT-06 — Reportes Markdown/JSON formales y evidencia de gates`.
