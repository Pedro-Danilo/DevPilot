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
