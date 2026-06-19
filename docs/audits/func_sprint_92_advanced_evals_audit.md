---
title: "Auditoría FUNC-SPRINT-92 — Evaluación avanzada, red teaming y safety scoring"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-92"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-92"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-92 — Evaluación avanzada, red teaming y safety scoring

## Estado

`implemented-initial` / PASS focalizado. Sprint 92 amplía el Evaluation Harness con suites determinísticas `advanced-agentic` y `red-team` para evaluar seguridad agentic, RAG, MCP/conectores y workflows multiagente sin llamar LLM judges, red ni APIs externas.

## Propósito

Crear una primera capa reproducible de evaluación adversarial y safety scoring para capacidades avanzadas de Fase H. El objetivo no es sustituir red teaming industrial, SAST/SCA o jueces LLM, sino introducir un contrato local ejecutable que detecte regresiones de seguridad agentic antes de habilitar plugins, multiworkspace o capacidades enterprise.

## Alcance implementado

- Fixtures sintéticos para `advanced-agentic` y `red-team`.
- `SafetyEvalEngine` determinístico en `src/devpilot_core/evals/safety.py`.
- Extensión de `EvalRunner` para suites avanzadas y métricas de seguridad.
- CLI existente `eval run --suite ...` reutilizado para `advanced-agentic` y `red-team`.
- Subgate `advanced-evals-safety` consumido por `quality-gate run --profile ci` y `release`.
- MIASI actualizado con `eval.safety.run`, `EVAL_SAFETY_SCORING_ALLOW` y `RED_TEAM_FIXTURE_SYNTHETIC_ONLY`.
- Manifest funcional, documentación y pruebas focales.

## Funcionamiento

El `EvalRunner` resuelve el fixture según el `suite_id`, carga casos `EvalCase`, ejecuta componentes `safety.*` con `SafetyEvalEngine` y calcula métricas de suite: `safety_score`, `adversarial_detection_rate`, `clean_pass_rate`, `false_negatives`, `false_positives` y `real_secret_fixture_blocks`.

Las suites pasan si no hay falsos negativos, si el safety score supera el umbral y si los fixtures no contienen patrones compatibles con secretos reales. Los hallazgos adversariales se tratan como bloqueos esperados cuando el caso declara `expected.ok=false`.

## Integración

- CLI: `python -m devpilot_core eval run --suite advanced-agentic --json`.
- CLI: `python -m devpilot_core eval run --suite red-team --json`.
- Quality gate: `python -m devpilot_core quality-gate run --profile ci --json` consume ambas suites mediante subgate local.
- ReportEngine: `--write-report` persiste evidencia bajo `outputs/reports`.
- MIASI: registra tool y reglas de policy para safety scoring y fixtures sintéticos.

## Criterios PASS

- Las suites contienen casos adversariales, no solo felices.
- Hay casos para prompt injection, synthetic secret leakage, unsafe tool use, RAG missing sources, connector misuse y multiagent policy bypass.
- `safety_score >= 90`.
- `false_negatives=0`.
- `real_secret_fixture_blocks=0`.
- No hay red, APIs externas ni LLM judge.
- Quality gate CI consume las suites y pasa.

## Criterios BLOCK

- Fixture con secreto real o patrón de clave privada/token real.
- Red-team suite sin casos adversariales.
- Safety score bajo umbral.
- Falso negativo en prompt injection, tool misuse, RAG missing sources, connector misuse o workflow no dry-run.
- Quality gate no consume los resultados de seguridad.

## Riesgos

La implementación es preliminar. Usa patrones determinísticos y fixtures sintéticos; por tanto puede tener falsos positivos o falsos negativos frente a ataques reales no modelados. No reemplaza pruebas adversariales con LLM judge, fuzzing, SAST/SCA, análisis semántico profundo ni revisión humana.

## Comandos de verificación

```powershell
python -m devpilot_core eval run --suite advanced-agentic --json
python -m devpilot_core eval run --suite red-team --json
python -m devpilot_core quality-gate run --profile ci --json
python -m pytest tests\test_advanced_evals.py tests\test_sprint_92_documentation.py -q
```

## Veredicto

Sprint 92 cumple el alcance del backlog Fase H para una primera versión industrialmente gobernada de evaluación avanzada. La capacidad queda `implemented-initial`: apta para control de regresión local y CI dry-run, no para certificación de seguridad final ni autorización automática de cambios.
