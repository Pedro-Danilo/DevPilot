---
doc_id: DEVPL-MP-SUCCESSOR-132-GENERATION_ROUTE_POLICY_CONTRACT_132
title: "Selección D/L/E, capacidades, fallback y semántica"
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

# Selección D/L/E, capacidades, fallback y semántica

## Resolución por tarea

Input `task_type`, `artifact_profile`, `project_policy`, `context_manifest`, `data_classification`, `complexity`, `requested_capabilities`, `approved_routes`, `model_preferences`, `time_budget`, `cost_budget`, `consent_ref`; output `chosen_route`, `provider/model/version`, `reasons`, `capability_evidence`, `fallback_policy`, `denied_alternatives`, `route_decision_receipt`.

D permanente para scaffolds conocidos, schemas, hashes/diffs, permisos, lifecycle y cambios gobernados. L **preferente cuando disponible, configurado, probado y permitido** para requisitos narrativos, arquitectura, planning semántico y código de historias arbitrarias. External E sólo con habilitación explicita de egreso, secretos, privacidad y presupuesto. No obligar pipeline D→L→E. Agent es flujo, no un provider con aprobación.

## Fallback

- `EQUIVALENT`: segundo método supera el mismo contrato/evals mínimos.
- `REDUCED`: sólo borrador limitado, estado `PARTIAL/NOT_READY`, revisión/consentimiento antes de continuar.
- `MODEL_REQUIRED`: sin ruta competente, STOP o autoría humana; no usar template RF-specific como solución completa.

`SUPPORTED`, `CONFIGURED`, `HEALTHY`, `EVALUATED`, `ELIGIBLE_FOR_TASK` son estados separados. Configuración global no puede debilitar restricciones de proyecto y policy security. El fallback debe registrar pérdida de calidad, razones y costos; nunca gastar API sin consentimiento específico.

## Casos negativos

Model local offline, JSON corrupto, timeout, prompt injection, context overflow, cross-workspace provider, export de PII, insufficient budget y doble candidate deben bloquear o producir estado seguro con provenance. Successful response ≠ Quality PASS.
