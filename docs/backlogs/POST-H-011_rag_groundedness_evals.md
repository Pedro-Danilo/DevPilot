---
doc_id: "POST-H-011-BACKLOG"
id: "POST-H-011"
title: "POST-H-011 — RAG groundedness evals"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used_by_default: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-011 — RAG groundedness evals

## 1. Objetivo

Diseñar e implementar un sistema local de **evaluación de groundedness para RAG** que permita verificar si las respuestas, resúmenes o recomendaciones generadas a partir de documentación DevPilot están soportadas por fuentes locales citables, vigentes y trazables.

El objetivo no es implementar RAG vectorial avanzado ni conectarse a servicios externos. El objetivo es elevar la confiabilidad del RAG lexical/local actual mediante fixtures, métricas, evidencia, validadores y gates determinísticos.

## 2. Contexto y justificación

DevPilot ya tiene una capa RAG local inicial:

```text
src/devpilot_core/rag/index.py
src/devpilot_core/rag/query.py
src/devpilot_core/rag/models.py
.devpilot/rag/docs_index.json
```

También existen agentes documentales, reverse engineering, onboarding y guías de operador que pueden apoyarse en documentación interna. El riesgo principal es que un agente o consulta RAG produzca una respuesta razonable pero no respaldada por fuentes concretas, o que use documentos obsoletos como si fueran fuente vigente.

Problemas a resolver:

```text
- No hay métrica formal de groundedness.
- No hay fixtures de preguntas con fuentes esperadas.
- No hay detección de respuestas sin evidencia local suficiente.
- No hay evaluación de citas, cobertura y freshness documental.
- No hay gate para impedir que RAG sea tratado como fuente de verdad sin soporte.
```

## 3. Alcance

Incluye:

```text
- Schema para fixtures de groundedness.
- Dataset local de casos RAG post-H.
- Evaluador determinístico de groundedness.
- Métricas de source coverage, citation precision y unsupported claims.
- Reporte local JSON/Markdown.
- Integración opcional con quality-gate.
- Documentación de límites del RAG local.
```

No incluye:

```text
- Vector DB obligatoria.
- Embeddings externos.
- APIs externas.
- LLM judge obligatorio.
- Web search.
- Conectores remotos.
- Reemplazo del sistema RAG actual.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/rag/index.py
src/devpilot_core/rag/query.py
src/devpilot_core/rag/models.py
src/devpilot_core/evals/runner.py
src/devpilot_core/evals/models.py
evals/fixtures/*.json
.devpilot/rag/docs_index.json
docs/backlogs/post_h_prioritized_roadmap.md
docs/audits/post_h_eval_001_baseline_assessment.md
docs/audits/post_h_eval_001_closure_report.md
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/05_operations/runbook.md
```

## 5. Entregables

```text
docs/schemas/rag_groundedness_eval.schema.json
docs/schemas/rag_groundedness_report.schema.json
evals/fixtures/rag_groundedness_post_h_cases.json
src/devpilot_core/rag/groundedness.py
src/devpilot_core/rag/evals.py
src/devpilot_core/rag/citations.py
tests/test_post_h_011_rag_groundedness.py
tests/test_rag_groundedness_schema.py
docs/04_quality/rag_groundedness_eval_strategy.md
outputs/evals/rag_groundedness_report.json       # generado, no versionable
outputs/evals/rag_groundedness_report.md         # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
docs/05_operations/runbook.md
```

## 6. Modelo de datos mínimo

### 6.1 Fixture de groundedness

```json
{
  "schema_version": "1.0",
  "suite_id": "rag-groundedness-post-h",
  "cases": [
    {
      "case_id": "rag-posth-roadmap-next-hitos",
      "question": "¿Cuáles son los próximos hitos P0 del roadmap post-H?",
      "expected_sources": [
        "docs/backlogs/post_h_prioritized_roadmap.md",
        ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json"
      ],
      "required_claims": [
        "POST-H-002",
        "POST-H-003",
        "POST-H-004",
        "POST-H-005"
      ],
      "forbidden_claims": [
        "remote execution enabled",
        "connector write enabled",
        "plugin execution enabled"
      ],
      "minimum_source_coverage": 0.8,
      "minimum_claim_support": 0.8,
      "risk_level": "high"
    }
  ]
}
```

### 6.2 Reporte de groundedness

Debe contener:

```text
suite_id
cases_total
cases_passed
cases_blocked
source_coverage_avg
claim_support_avg
unsupported_claims_total
missing_sources_total
stale_sources_total
network_used=false
external_api_used=false
findings
```

## 7. Principios de diseño

```text
1. Groundedness before fluency: importa más soporte documental que redacción convincente.
2. Local-only: solo docs locales versionados o indexados.
3. Deterministic baseline: sin LLM judge obligatorio.
4. Evidence-first: cada claim importante debe mapear a fuente.
5. No silent pass: si no hay fuente suficiente, debe haber warning o block.
6. RAG is not source of truth: la fuente es el documento canónico, no la respuesta.
```

## 8. Micro-sprints propuestos

### POST-H-011-A — Schema y fixtures de groundedness

Objetivo: definir el contrato de casos de evaluación RAG y crear primer dataset post-H.

Tareas:

```text
1. Crear rag_groundedness_eval.schema.json.
2. Crear rag_groundedness_report.schema.json.
3. Registrar schemas en schema_catalog.json.
4. Crear evals/fixtures/rag_groundedness_post_h_cases.json.
5. Incluir casos sobre roadmap, seguridad, testing, arquitectura, onboarding y restricciones no-go.
6. Crear tests de validación de fixtures.
```

Criterios PASS:

```text
PASS si fixture valida contra schema.
PASS si incluye al menos 10 casos iniciales.
PASS si hay casos negativos con forbidden_claims.
PASS si incluye fuentes post-H vigentes.
```

Criterios BLOCK:

```text
BLOCK si el fixture requiere web o API externa.
BLOCK si las fuentes esperadas no existen.
BLOCK si se evalúa solo keyword matching trivial sin fuentes.
```

Validación:

```powershell
python -m pytest tests/test_rag_groundedness_schema.py -q
python -m devpilot_core schema validate --schema-id RagGroundednessEval --instance evals/fixtures/rag_groundedness_post_h_cases.json --json
```

### POST-H-011-B — Citation extractor y source coverage

Objetivo: implementar utilidades para mapear respuestas o fragmentos a fuentes locales recuperadas.

Tareas:

```text
1. Implementar src/devpilot_core/rag/citations.py.
2. Normalizar paths, doc_id, headings y snippets.
3. Calcular source_coverage por caso.
4. Detectar fuentes ausentes y fuentes obsoletas si metadata lo permite.
5. Generar findings con source_missing, low_coverage, stale_source.
```

Criterios PASS:

```text
PASS si calcula cobertura por fuente esperada.
PASS si detecta fuentes inexistentes.
PASS si no requiere contenido remoto.
PASS si funciona con docs_index actual y con lectura directa de docs.
```

Criterios BLOCK:

```text
BLOCK si inventa fuentes.
BLOCK si considera outputs generados como fuente canónica sin declarar.
BLOCK si ignora docs con frontmatter deprecated.
```

Validación:

```powershell
python -m pytest tests/test_post_h_011_rag_groundedness.py -q
```

### POST-H-011-C — Evaluador determinístico de claims

Objetivo: validar required_claims y forbidden_claims sin depender de LLM judge.

Tareas:

```text
1. Implementar src/devpilot_core/rag/groundedness.py.
2. Detectar claims requeridos en respuesta o retrieved context.
3. Detectar forbidden_claims.
4. Calcular claim_support y unsupported_claims.
5. Clasificar casos como PASS/WARNING/BLOCK.
6. Permitir modo strict.
```

Criterios PASS:

```text
PASS si required_claims se evalúan con umbral configurable.
PASS si forbidden_claims generan BLOCK.
PASS si unsupported_claims aparecen en reporte.
PASS si no se usa LLM judge por defecto.
```

Criterios BLOCK:

```text
BLOCK si una respuesta puede pasar sin fuentes.
BLOCK si remote/connector/plugin claims pasan como verdaderos sin soporte.
BLOCK si forbidden_claims solo generan info.
```

Validación:

```powershell
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --json --write-report
python -m pytest tests/test_post_h_011_rag_groundedness.py -q
```

### POST-H-011-D — Integración con RAG query y eval runner

Objetivo: conectar evaluador con comandos RAG y sistema de evals.

Tareas:

```text
1. Añadir comando rag groundedness-eval.
2. Integrar con src/devpilot_core/evals/runner.py si aplica sin acoplar excesivamente.
3. Permitir ejecución de suite completa y caso individual.
4. Guardar reportes en outputs/evals.
5. Exponer resumen para quality-gate.
```

Criterios PASS:

```text
PASS si la suite corre offline.
PASS si reporta network_used=false y external_api_used=false.
PASS si el comando produce CommandResult estándar.
PASS si puede ejecutarse en CI local.
```

Criterios BLOCK:

```text
BLOCK si el eval requiere provider externo.
BLOCK si outputs/evals se vuelven fuente versionable obligatoria.
BLOCK si falla sin findings accionables.
```

Validación:

```powershell
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --json
python -m devpilot_core eval run --suite rag-groundedness --json
```

### POST-H-011-E — Gate y documentación de límites RAG

Objetivo: integrar groundedness al quality-gate y documentar límites.

Tareas:

```text
1. Agregar subgate rag-groundedness-ready al quality gate hardening o perfil específico.
2. Actualizar test contract registry.
3. Crear docs/04_quality/rag_groundedness_eval_strategy.md.
4. Actualizar runbook con comandos y criterios.
5. Documentar que RAG local no sustituye fuentes canónicas.
```

Criterios PASS:

```text
PASS si quality-gate puede ejecutar o verificar suite groundedness.
PASS si test-contracts validate pasa.
PASS si documentación declara límites y no-go gates.
PASS si casos negativos bloquean correctamente.
```

Criterios BLOCK:

```text
BLOCK si RAG se declara production-grade sin evals.
BLOCK si se recomienda LLM judge externo obligatorio.
BLOCK si se habilita web search o API externa por defecto.
```

Validación:

```powershell
python -m pytest tests/test_post_h_011_rag_groundedness.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 9. Casos mínimos de evaluación

```text
- Próximos hitos P0 del roadmap.
- Restricciones de remote execution.
- Estado de Test Contract Registry.
- Qué capacidades agentic son ejecutables hoy.
- Qué artefactos no deben entrar en ZIP limpio.
- Qué significa production-ready-local.
- Diferencia entre plugin registry y plugin execution.
- Riesgos del RAG sin groundedness.
- Orden de backlogs post-H.
- Fuente canónica de decisiones ADR.
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Respuestas plausibles sin evidencia | Alta | required_sources, required_claims y BLOCK por baja cobertura. |
| Uso de docs obsoletos | Media-alta | frontmatter status/freshness y canonical sources. |
| Acoplar RAG a LLM externo | Alta | evaluador determinístico local por defecto. |
| Falsa precisión de keyword matching | Media | combinar source coverage, claims y forbidden claims. |
| Crecimiento de docs_index | Media | lifecycle policy y no versionar outputs. |

## 11. No-go gates

```text
NO web search por defecto.
NO LLM judge externo obligatorio.
NO respuesta PASS sin fuentes esperadas.
NO remote/API/connector usage.
NO tratar outputs generados como fuente canónica sin registry.
NO declarar RAG industrial sin suite PASS.
```

## 12. Definition of Done del hito

```text
- Schemas RAG groundedness registrados.
- Fixture post-H creado y validado.
- Evaluador local determinístico implementado.
- Métricas de source coverage y claim support disponibles.
- Comando CLI disponible.
- Reporte JSON/Markdown generado.
- Quality gate integrado.
- Documentación y runbook actualizados.
```

## 13. Comandos finales esperados

```powershell
python -m devpilot_core rag index --json --write-report
python -m devpilot_core rag query --query "próximos hitos P0" --json
python -m devpilot_core rag groundedness-eval --suite evals/fixtures/rag_groundedness_post_h_cases.json --json --write-report
python -m pytest tests/test_post_h_011_rag_groundedness.py tests/test_rag_groundedness_schema.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```
