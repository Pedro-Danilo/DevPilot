# R02 — índice de 10 sprints/prompts y estados

Basado en `BACKLOG_R02_132.md`, R01 CERRADO M1 `PASS_WITH_FINDINGS`, HEAD `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc`.

- Primero leer `00_PLAN_R02_172.md` y `01_REGLAS_R02_172.md`.
- Después, el Owner aprueba una sola pareja sprint/prompt y se rebindea a su HEAD vivo; **todos los aquí entregados son DRAFT, no ejecutables ahora**.
- Primer R02 repo mutation = R02-01: corregir drift documental activo heredado, no confundir snapshots históricos.
- `R02-04` si LM Studio ausente → diferir con evidencia y seguir por Ollama válido, no falsificar health.
- Milestone B0/B1 Pilot B requiere un workspace continuo y documentos FROZEN de fuente humana, jamás generados por scripts del operador.

| Sprint / Prompt | Resultado |
|---|---|
| [`02_sprints/R02_01_AUDIT_AND_DOC_DRIFT_SPRINT.md`](02_sprints/R02_01_AUDIT_AND_DOC_DRIFT_SPRINT.md) · [`03_prompts/R02_01_AUDIT_AND_DOC_DRIFT_PROMPT.md`](03_prompts/R02_01_AUDIT_AND_DOC_DRIFT_PROMPT.md) | Rebind M1, inventario R2 y reconciliación documental activa |
| [`02_sprints/R02_02_LOCAL_MODEL_READINESS_SPRINT.md`](02_sprints/R02_02_LOCAL_MODEL_READINESS_SPRINT.md) · [`03_prompts/R02_02_LOCAL_MODEL_READINESS_PROMPT.md`](03_prompts/R02_02_LOCAL_MODEL_READINESS_PROMPT.md) | Readiness/Settings y descubrimiento seguro de modelos locales |
| [`02_sprints/R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md`](02_sprints/R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md) · [`03_prompts/R02_03_OLLAMA_REAL_CANDIDATE_PROMPT.md`](03_prompts/R02_03_OLLAMA_REAL_CANDIDATE_PROMPT.md) | Primera generación real Ollama opt-in para Product Definition |
| [`02_sprints/R02_04_LM_STUDIO_PARITY_SPRINT.md`](02_sprints/R02_04_LM_STUDIO_PARITY_SPRINT.md) · [`03_prompts/R02_04_LM_STUDIO_PARITY_PROMPT.md`](03_prompts/R02_04_LM_STUDIO_PARITY_PROMPT.md) | Paridad opcional LM Studio sin degradar la ruta determinista |
| [`02_sprints/R02_05_PILOT_B_ENTRY_RESUME_SPRINT.md`](02_sprints/R02_05_PILOT_B_ENTRY_RESUME_SPRINT.md) · [`03_prompts/R02_05_PILOT_B_ENTRY_RESUME_PROMPT.md`](03_prompts/R02_05_PILOT_B_ENTRY_RESUME_PROMPT.md) | Pilot B B0: Project Home/Entry neutral y reanudación |
| [`02_sprints/R02_06_DL_COMPARISON_AND_REVIEW_SPRINT.md`](02_sprints/R02_06_DL_COMPARISON_AND_REVIEW_SPRINT.md) · [`03_prompts/R02_06_DL_COMPARISON_AND_REVIEW_PROMPT.md`](03_prompts/R02_06_DL_COMPARISON_AND_REVIEW_PROMPT.md) | Comparación D/L semántica con revisión Owner y provenance |
| [`02_sprints/R02_07_FROZEN_PRECODE_DOCUMENTS_SPRINT.md`](02_sprints/R02_07_FROZEN_PRECODE_DOCUMENTS_SPRINT.md) · [`03_prompts/R02_07_FROZEN_PRECODE_DOCUMENTS_PROMPT.md`](03_prompts/R02_07_FROZEN_PRECODE_DOCUMENTS_PROMPT.md) | Publicación humana Markdown FROZEN de Vision/Scope/Requirements |
| [`02_sprints/R02_08_PRODUCT_COVERAGE_SEMANTIC_SPRINT.md`](02_sprints/R02_08_PRODUCT_COVERAGE_SEMANTIC_SPRINT.md) · [`03_prompts/R02_08_PRODUCT_COVERAGE_SEMANTIC_PROMPT.md`](03_prompts/R02_08_PRODUCT_COVERAGE_SEMANTIC_PROMPT.md) | PESP y Coverage Gate para Product Definition contextual |
| [`02_sprints/R02_09_LOCAL_FAILURE_RESILIENCE_SPRINT.md`](02_sprints/R02_09_LOCAL_FAILURE_RESILIENCE_SPRINT.md) · [`03_prompts/R02_09_LOCAL_FAILURE_RESILIENCE_PROMPT.md`](03_prompts/R02_09_LOCAL_FAILURE_RESILIENCE_PROMPT.md) | Negativas de modelo local y reanudación segura Product Definition |
| [`02_sprints/R02_10_M2_PILOT_B_GATE_SPRINT.md`](02_sprints/R02_10_M2_PILOT_B_GATE_SPRINT.md) · [`03_prompts/R02_10_M2_PILOT_B_GATE_PROMPT.md`](03_prompts/R02_10_M2_PILOT_B_GATE_PROMPT.md) | Cierre M2: Pilot B B0–B1 y modelo local real |

---

## Enmienda programática post-R02-06 · 187

El programa posterior al cierre R02-06 está rebindeado a `b666c5641c1b8231c5b609216f64490a72ff1763`. Consultar ADR MP132-013–015, contrato de incrementos y sprints/prompts R02-07..10 actualizados. Los planes de R02-01..06 son **históricos**; no ejecutar instrucciones de generación D/L obligatoria ni reescribir candidatos previos para el nuevo B1. Para ejecutar R02-07 es imprescindible su aprobación Owner individual y auditoría de HEAD actual.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

Cierre sucesor definitivo R02: `R02_CLOSEOUT_189.md`. Los diez archivos sprint/prompt originales son registros de planificación; recibos Windows posteriores acreditan cada ejecución. Baseline `1f15fa5b770db37c684e870a49572dcb569bd3a4`. Ninguna instrucción DRAFT de esta carpeta se debe relanzar.
