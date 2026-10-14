---
doc_id: DEVPL-MP-SUCCESSOR-132-CHANGE_IMPACT_AND_SUCCESSOR_CONTRACT_132
title: "Cambios de Pre-code/Planning en desarrollo y vida operativa"
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

# Cambios de Pre-code/Planning en desarrollo y vida operativa

## Lifecycle de modificación

`ChangeRequest` identifica `change_id`, actor, motivo, necesidad, artefactos origen/targets, baseline_refs, risk, desired release, compatibility/migration constraints. `ImpactAnalysis` recorre grafo aprobado de requisitos → design/ADR/API/data/security → roadmap/backlog/stories → source/tests → release/operations y produce `KNOWN_IMPACT`, `POSSIBLE_IMPACT`, `NOT_EVALUATED`, `NO_IMPACT_WITH_REASON`.

`FROZEN` inmutable. Crear `successor_revision` con diff narrativo y estructurado, validador, dependencias `STALE_REVALIDATION_REQUIRED`, Owner approval. Reconciliar sólo el alcance afectado. Nuevo requisito después de release inicia evolución gobernada: change request → impact → backlog/release successor → sprint futuro aprobado → tests → release versionado, sin editar retrospectivamente la decisión vieja.

## Semántica de aprobación

Owner aprueba cambio de alcance, no un cheque en blanco para Git, red o datos. Cada apply por SourceChangePlan mantiene preimage, allowlist, approval, idempotencia, tests y receipt. Un LLM puede sugerir impactos, pero no certifica exhaustividad; combinar dependency graph determinístico, análisis estático y pruebas.

## Negativos

Intentar editar FROZEN, invalidación cruzada, cambio después de commit, migración irreversible sin rollback, concurrency/sessions y sesión revocada → BLOCK. Una corrección de redacción no debe invalidar historias no relacionadas sin causal verificable.
