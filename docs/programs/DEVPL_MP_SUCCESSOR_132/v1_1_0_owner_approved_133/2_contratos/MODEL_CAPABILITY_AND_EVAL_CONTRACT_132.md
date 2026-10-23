---
doc_id: DEVPL-MP-SUCCESSOR-132-MODEL_CAPABILITY_AND_EVAL_CONTRACT_132
title: "Capacidades de modelos, datasets y aceptación real"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Capacidades de modelos, datasets y aceptación real

## Registro de capacidad con evidencia

`provider_id`, `adapter_version`, `model_id`, `model_version`, `runtime_version`, `quantization`, `hardware_environment`, `health_at`, `capabilities_claimed`, `capabilities_tested`, `task_types_evaluated`, `dataset_revision`, `metric_results`, `threshold_policy_ref`, `cost/resource_observations`, `last_eval`, `expiry`, `eligibility_status`.

Se distingue `SUPPORTED` (existe contrato), `CONFIGURED`, `HEALTHY`, `EVALUATED` y `ELIGIBLE_FOR_TASK`. Un health-check no garantiza generación de código. Ollama/LM Studio local son opciones sin key paga por defecto, con evaluación real en R2. Mock sigue disponible para probar el motor; no cuenta como ejecución de modelo real.

## Dimensiones de evaluación

Schema/structured-output validity, groundedness, RF coverage, ADR/security consistency, compilación/tests de código, reversibilidad, alucinaciones/citas no respaldadas, latencia, RAM/VRAM y throughput, cancelación, fallos/timeout, bounded retry, leakage/egress y UX de explicación. D/L/E se comparan en una misma tarea cuando sea semánticamente adecuado, no por número bruto de tokens o aparente fluidez. Fijar umbrales sólo tras medir hardware/dataset autorizados; no inventarlos.

## Controles

Un provider E requiere additionally privacy/egress/cost gate y Pilot C. Prompts, tool/structured output no son semánticamente iguales entre OpenAI Responses API, modelos locales o terceros: adapters versionados y contract tests específicos. Cualquier FAIL crítico de permiso o datos descarta candidato independientemente del score lingüístico.

## Evidence

Dataset y prompts versionados, input/output/context hashes, model, seed si aplica, error/retry/fallback, test/coverage y Owner decision; sin copiar secretos a logs. Pilot B eval L real y 2do dominio contra overfitting RF001–003.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- Para R02 las clases `SUPPORTED`, `CONFIGURED`, `HEALTHY`, `EVALUATED`, `ELIGIBLE_FOR_TASK` **no son intercambiables**. La aceptación de modelo local requiere llamada real, salida estructurada, dataset controlado, fuente/contexto, trazas, negativa de capability/timeout y prueba de que D sigue disponible sin L. El evaluador determinista de R01-09 se reutiliza, pero sus reglas no acreditan una evaluación semántica profunda.

---

## Enmienda programática post-R02-06 · 187

Agregar evaluación **por etapa** y por tarea, no ranking genérico de modelos: `vision_quality`, `scope_boundary_quality`, `requirements_testability`, `architecture_drivers`, `planning_feasibility`, `code_change_quality`; registrar `model_id`, versión, hardware, contexto/hash, prompt/schema version, latencia, formato, idioma, cobertura de hechos, afirmaciones no soportadas y costo real o `NOT_AVAILABLE`. Un provider con JSON válido pero que parafrasea B0 es `CANDIDATE_INSUFFICIENT`, no `ELIGIBLE_FOR_PROFESSIONAL_AUTHORING`. Métricas automáticas complementan revisión Owner, nunca sustituyen pruebas verificables ni inventan benchmarks. Comparación de dos modelos optativa y asociada al mismo contexto/perfil; evitar juez LLM autoaprobador.


---
## Enmienda 188 aprobada — calidad de redacción por tipo (ADOPTADA — autoridad programática)

El dataset de capacidad de autoría necesita `artifact_type/profile_version`, dos dominios representativos, evidencias de referencia, negativos de falsos PASS, falsos BLOCK, tasa de edición técnica del Owner, decisiones de negocio no resueltas, corrección entre artefactos y pruebas del artefacto (e.g. RF→test). `task_eligible` se decide por resultados medidos del modelo y límites de riesgo, no por HEALTHY/JSON PASS. Medir beneficio marginal de agente/E frente a salida L revisada, junto con costo, latencia y privacidad. No inventar umbrales de industrialidad.

**Autoridad:** `MP132-A188`, aprobada por Owner el 2026-10-22; aplicación según `ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. No constituye ejecución R02-08 ni habilitación de E.
