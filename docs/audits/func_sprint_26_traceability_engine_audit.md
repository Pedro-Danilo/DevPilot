---
title: "FUNC-SPRINT-26 — Traceability Engine: validate, coverage y report"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-26-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-26"
updated: "2026-06-10"
approval: "approved_by_owner"
---

# FUNC-SPRINT-26 — Traceability Engine: validate, coverage y report

## 1. Propósito

Este artefacto audita la implementación de `FUNC-SPRINT-26`. El sprint construye la primera versión ejecutable del `TraceabilityEngine`, responsable de validar gaps, calcular cobertura y generar reportes de trazabilidad SDLC a partir de evidencia explícita en documentos locales.

El resultado es una versión **implemented-initial**: el motor detecta relaciones Req→AC, Req→Test/Eval y Req→Doc cuando están presentes en tablas o referencias controladas, pero no realiza razonamiento semántico ni modifica documentos.

## 2. Alcance implementado

Se implementó:

- `TraceabilityEngine` en `src/devpilot_core/traceability/engine.py`;
- reglas de cobertura en `src/devpilot_core/traceability/rules.py`;
- helper de resumen en `src/devpilot_core/traceability/reports.py`;
- comandos `traceability validate`, `traceability coverage` y `traceability report`;
- soporte `--json`, `--target` y `--write-report`;
- detección de requisitos sin criterios (`TRACEABILITY_REQUIREMENT_WITHOUT_ACCEPTANCE_CRITERIA`);
- detección de criterios sin requisito (`TRACEABILITY_ACCEPTANCE_CRITERION_WITHOUT_REQUIREMENT`);
- detección de requisitos sin test/eval cuando aplica (`TRACEABILITY_REQUIREMENT_WITHOUT_TEST_EVIDENCE`);
- métricas de cobertura y porcentajes;
- fixtures de cobertura completa e incompleta;
- pruebas de CLI, reproducibilidad y smoke sobre docs reales.

No se implementó:

- corrección automática de documentos;
- inferencia semántica con LLM;
- severidades configurables;
- bloqueo por gaps recomendados;
- validación de architecture/code drift;
- dashboards;
- escritura sobre la matriz de trazabilidad.

## 3. Funcionamiento técnico

`TraceabilityEngine` consume el `MarkdownTraceabilityExtractor` de Sprint 25 para obtener fuentes y entidades. Luego `build_coverage()` analiza filas Markdown y líneas controladas para construir enlaces explícitos:

- `requirement_to_acceptance_criterion`;
- `requirement_to_test_or_eval_evidence`;
- evidencia de documento fuente por ocurrencia del requisito.

La cobertura se calcula por requisito y por criterio de aceptación. Los gaps se emiten como `Finding` con severidad `warning`, porque Sprint 26 busca visibilidad y evidencia antes de convertir reglas en gates bloqueantes.

## 4. Integración y rol dentro de DevPilot

Sprint 26 convierte la trazabilidad en una capacidad ejecutable de DevPilot. Se integra con:

| Componente | Relación |
|---|---|
| `cli.py` | Expone `traceability validate/coverage/report`. |
| `MarkdownTraceabilityExtractor` | Reutiliza el scan conservador de Sprint 25. |
| `CommandResult` | Normaliza resultados y findings. |
| `ReportEngine` | Persiste evidencia con `--write-report`. |
| `EventLogger` | Emite eventos locales best-effort desde CLI. |
| `LocalStore` | Persiste historial best-effort desde CLI. |

El rol del sprint es cerrar la brecha de Traceability Engine identificada en el informe de avance y preparar Sprint 27 para architecture/code drift y cierre de Fase A.

## 5. Comandos de uso

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core traceability validate --json
python -m devpilot_core traceability coverage --json
python -m devpilot_core traceability report --json --write-report
python -m devpilot_core traceability validate --target docs/01_requirements --json
python -m pytest tests/test_traceability_engine.py -q
python -m pytest -q
```

## 6. Criterios PASS

- `TraceabilityEngine` es importable.
- `traceability validate` devuelve `CommandResult`.
- `traceability coverage` genera métricas y porcentajes.
- `traceability report` genera payload reproducible.
- `--write-report` persiste JSON/Markdown.
- Se detectan requisitos sin criterios.
- Se detectan criterios sin requisito.
- Se detectan requisitos sin test/eval cuando aplica.
- Los gaps son accionables y no bloqueantes.
- No se modifican documentos.
- No se usa red ni API keys.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- El motor bloquea por gaps recomendados que todavía deben ser warnings.
- El reporte no es reproducible.
- El comando falla si un documento opcional no existe.
- El motor inventa relaciones semánticas no explicitadas.
- Se agregan dependencias externas sin ADR.
- Se modifica la matriz de trazabilidad automáticamente.

## 8. Riesgos

- La cobertura depende de evidencia explícita en documentos; si la evidencia está en lenguaje libre puede no detectarse.
- Algunas evidencias tipo `report`, `schema` o `checklist` se consideran test/eval de forma conservadora.
- Los gaps son warnings, por lo que aún no funcionan como quality gate bloqueante.
- Las reglas de severidad deben ser configurables en fases futuras.

## 9. ADR

No se creó ADR nueva porque Sprint 26 no introduce dependencia externa, proveedor, red, almacenamiento nuevo ni acción destructiva. La implementación usa biblioteca estándar y componentes existentes de DevPilot.

## 10. Pruebas implementadas

- `tests/test_traceability_engine.py`;
- `tests/fixtures/traceability_engine/complete.md`;
- `tests/fixtures/traceability_engine/incomplete.md`;
- `tests/test_sprint_26_documentation.py`.

## 11. Evolución recomendada

El siguiente paso es `FUNC-SPRINT-27 — Architecture/code drift inicial y cierre de Baseline Industrial Mínima`. Debe integrar la trazabilidad con la validación de drift arquitectura/código y producir evidencia de cierre formal de Fase A.
