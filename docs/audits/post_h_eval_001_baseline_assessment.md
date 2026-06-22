# POST-H-EVAL-001 — Baseline assessment DevPilot post-Fase H

## Estado ejecutivo

`POST-H-EVAL-001-A` establece la línea base objetiva para iniciar la evaluación integral post-Fase H de DevPilot. El micro-sprint se implementa como trabajo de documentación y metadata: aprueba el backlog ejecutable, crea el assessment inicial, crea el manifiesto de evaluación y refuerza la higiene de `.gitignore` para evitar que artefactos generados vuelvan a entrar al repositorio.

La fuente ZIP analizada confirma que DevPilot ya posee un baseline industrial local-first significativo: project state centralizado, test contracts, quality gates, MIASI, schema catalog, industrial readiness y validaciones reproducibles. Sin embargo, también confirma una deuda de distribución: `repo_DevPilot_Local_131.zip` todavía contiene runtime artifacts heredados (`outputs/`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/`). Esa deuda no bloquea la evaluación, pero debe quedar registrada como riesgo de higiene y ser corregida en fuentes ZIP posteriores.

**Conclusión del micro-sprint A:** procede continuar con `POST-H-EVAL-001-B — Assessment integral de capacidades y madurez`, siempre que el siguiente repo entregable se mantenga limpio de runtime artifacts.

## Fuente de verdad analizada

| Elemento | Valor |
|---|---|
| Repo base | `repo_DevPilot_Local_131.zip` |
| SHA-256 repo base | `2e6a2e18ce6066068f0bdf54fa82fe3978bb2c607d4eb99c652087d3426048f6` |
| Backlog ejecutable adjunto | `POST-H-EVAL-001_backlog_ejecutable.md` |
| SHA-256 backlog adjunto | `abab0381d9b21c66dae9e6092b459b6d39ba22b2cbb26edb9c2da3658c1429ba` |
| Backlog incorporado en repo | `docs/POST-H-EVAL-001_backlog_ejecutable.md` |
| Status aplicado al backlog | `approved` |
| Rama esperada para ejecución real | `post-h-eval-001-baseline-assessment` |
| Rama observada en sandbox | No disponible: el ZIP no incluye metadatos `.git`. |
| Fecha UTC de generación | `2026-06-22T19:53:44Z` |

## Comandos ejecutados

Los siguientes comandos de validación baseline fueron ejecutados en modo local, con `PYTHONPATH=src`, sin red y sin APIs externas:

```powershell
PYTHONPATH=src python -m devpilot_core project-state validate --json
PYTHONPATH=src python -m devpilot_core test-contracts validate --json
PYTHONPATH=src python -m devpilot_core quality-gate run --profile hardening --json
PYTHONPATH=src python -m devpilot_core industrial-readiness check --json
PYTHONPATH=src python -m devpilot_core rag index --target docs --index-path .devpilot/rag/docs_index.json --json
PYTHONPATH=src python -m pytest tests/test_project_global_state.py tests/test_test_contract_registry.py tests/test_test_impact.py -q
PYTHONPATH=src python -m pytest tests/test_sprint_*_documentation.py -q
```

### Resultado consolidado

| Validación | Resultado | Evidencia principal |
|---|---:|---|
| `project-state validate` | PASS | 6/6 checks; `last_completed_sprint=POST-H-001`; `next_sprint=POST-H-002`. |
| `test-contracts validate` | PASS | 84 contratos; 78 históricos; 1 global-state; 2 quality-gate. |
| `quality-gate run --profile hardening` | PASS | 12/12 subgates; 0 blockers; 24 warnings no bloqueantes. |
| `industrial-readiness check` | PASS | Score 84.18 >= 80; maturity `industrial-baseline-ready`; remote disabled. |
| `rag index` | PASS | 604 docs indexed; 2850 chunks; lexical local; embeddings disabled; redactions applied. |
| Pytest focal POST-H-001 | PASS | 8 passed; 0 failed/errors/skipped. |
| Pytest histórico documental | PASS | 303 passed; 0 failed/errors/skipped. |

## Snapshot cuantitativo

| Métrica | Valor |
|---|---:|
| Archivos Python en `src/devpilot_core` | 199 |
| Líneas Python aproximadas en `src/devpilot_core` | 47085 |
| Archivos `test_*.py` | 184 |
| Líneas aproximadas de tests | 17398 |
| Archivos en `docs` después de A | 604 |
| Líneas documentales aproximadas después de A | 92573 |
| Manifiestos funcionales `functional_sprint_*_manifest.json` | 100 |
| Documentos markdown en `docs/audits` después de A | 124 |
| Schemas registrados en `schema_catalog.json` | 27 |
| Agentes MIASI | 14 |
| Tools MIASI | 97 |
| Reglas de policy MIASI | 97 |
| Test contracts | 84 |

### Distribución de test contracts

| Scope | Cantidad |
|---|---:|
| `feature` | 1 |
| `global-state` | 1 |
| `historical-sprint` | 78 |
| `integration` | 1 |
| `quality-gate` | 2 |
| `ui-smoke` | 1 |


## Estado de `.devpilot/project_state.json`

| Campo | Valor |
|---|---|
| `current_phase` | `POST-FASE-H` |
| `phase_h_status` | `closed_implemented_initial` |
| `industrial_baseline_ready` | `True` |
| `maturity_level` | `industrial-baseline-ready` |
| `last_completed_sprint` | `POST-H-001` |
| `last_functional_sprint` | `FUNC-SPRINT-99` |
| `next_sprint` | `POST-H-002` |
| `source_repo` | `repo_DevPilot_Local_130.zip` |
| `current_repo` | `repo_DevPilot_Local_131_POST_H_001.zip` |

## Estado de `.gitignore`

Se reforzó `.gitignore` como metadata de higiene para cubrir explícitamente runtime artifacts locales y artefactos de frontend. Esta acción no modifica semántica runtime.

| Patrón requerido | Presente |
|---|---:|
| `outputs/` | sí |
| `.devpilot/*.db` | sí |
| `.devpilot/*.db-*` | sí |
| `.devpilot/agent_sessions/` | sí |
| `Log_consola_*.txt` | sí |
| `.pytest_cache/` | sí |
| `.venv/` | sí |
| `node_modules/` | sí |
| `ui/web/node_modules/` | sí |
| `ui/web/dist/` | sí |
| `__pycache__/` | sí |


## Presencia de runtime artifacts en fuente ZIP analizada

La extracción de `repo_DevPilot_Local_131.zip` evidencia artefactos generados que no deben propagarse en próximas fuentes de verdad.

| Ruta | Presente | Entradas | Bytes aproximados |
|---|---:|---:|---:|
| `outputs` | sí | 21 | 67176 |
| `.devpilot/devpilot.db` | sí | 1 | 883335168 |
| `.devpilot/agent_sessions` | sí | 546 | 1370703 |
| `.pytest_cache` | no | 0 | 0 |
| `.venv` | no | 0 | 0 |
| `node_modules` | no | 0 | 0 |
| `ui/web/node_modules` | no | 0 | 0 |
| `ui/web/dist` | no | 0 | 0 |
| `__pycache__` | no | 0 | 0 |


## Hallazgos iniciales

### HALL-A-001 — Baseline industrial local-first validado

El baseline pasa `project-state validate`, `test-contracts validate`, `quality-gate hardening` e `industrial-readiness check`. Esto confirma que DevPilot tiene una base industrial local-first verificable para iniciar evaluación post-H.

### HALL-A-002 — POST-H-001 quedó centralizado como último hito cerrado

`.devpilot/project_state.json` mantiene `last_completed_sprint=POST-H-001` y `next_sprint=POST-H-002`. Para `POST-H-EVAL-001`, se recomienda no mutar aún el estado global hasta cerrar el hito completo o hasta que se defina formalmente su inserción antes de `POST-H-002`.

### HALL-A-003 — El backlog POST-H-EVAL-001 queda aprobado

El backlog ejecutable se incorporó como `docs/POST-H-EVAL-001_backlog_ejecutable.md` y su frontmatter fue elevado a `status: "approved"` con alcance de aprobación explícito.

### HALL-A-004 — La fuente ZIP 131 contiene runtime artifacts heredados

El ZIP base contiene `outputs/`, `.devpilot/devpilot.db` y `.devpilot/agent_sessions/`. Esto no bloquea el diagnóstico, pero sí exige que los próximos zips de fuente de verdad excluyan estos artefactos.

### HALL-A-005 — El proyecto tiene escala suficiente para requerir gobierno arquitectónico

El tamaño de `src`, `tests`, `docs`, MIASI, schemas y contratos confirma que DevPilot ya no debe crecer por simple acumulación de features. A partir de este hito se requiere priorización industrial por madurez, riesgo y costo de cambio.

## Riesgos preliminares

| ID | Riesgo | Severidad | Estado | Acción recomendada |
|---|---|---:|---|---|
| RISK-A-001 | Fuente ZIP con runtime artifacts | Alta | Detectado | Excluir en repo entregable y formalizar export policy. |
| RISK-A-002 | POST-H-002 definido antes de assessment | Media-alta | Detectado | Refinar POST-H-002 con la evaluación B-F. |
| RISK-A-003 | Quality gate con warnings no bloqueantes | Media | Detectado | Analizar en POST-H-EVAL-001-E y F. |
| RISK-A-004 | Test contracts dominados por históricos | Media-alta | Detectado | Evolucionar a Test Contract Registry 2.0. |
| RISK-A-005 | Sin metadatos git en ZIP | Baja | Normal en sandbox | Validar rama en entorno local real. |

## Alcance implementado en micro-sprint A

| Entregable | Estado | Observación |
|---|---|---|
| `docs/POST-H-EVAL-001_backlog_ejecutable.md` | Approved | Incorporado desde adjunto y actualizado a `status: approved`. |
| `docs/audits/post_h_eval_001_baseline_assessment.md` | Created | Documento actual. |
| `docs/post_h_eval_001_manifest.json` | Created | Manifest machine-readable del hito y micro-sprint A. |
| `.gitignore` | Hardened | Se agregan patrones faltantes para logs, outputs generales y frontend artifacts. |
| `.devpilot/rag/docs_index.json` | Updated | Índice lexical local regenerado para incluir backlog y assessment POST-H-EVAL-001-A. |

## Criterios PASS de POST-H-EVAL-001-A

| Criterio | Resultado |
|---|---:|
| Existe baseline assessment inicial | PASS |
| Existe manifest inicial | PASS |
| Las validaciones baseline pasan o quedan registradas | PASS |
| Se documenta fuente de verdad exacta | PASS |
| Se identifica si el ZIP contiene runtime artifacts | PASS |
| No se modifica código core/runtime | PASS |
| No se habilita remote execution | PASS |
| No se usan APIs externas | PASS |

## Criterios BLOCK revisados

| Criterio BLOCK | Estado |
|---|---:|
| Modificación de código core sin justificación | No activado |
| Validaciones fallidas ocultas | No activado |
| Fuente de verdad omitida | No activado |
| Runtime artifacts ignorados | No activado |

## Próximo paso

Continuar con:

```text
POST-H-EVAL-001-B — Assessment integral de capacidades y madurez
```

Este siguiente micro-sprint debe construir la matriz por dominio, evidencia, madurez, riesgo, acción recomendada y prioridad. La evaluación B debe usar como insumo este snapshot y no debe habilitar nuevas capacidades runtime.
