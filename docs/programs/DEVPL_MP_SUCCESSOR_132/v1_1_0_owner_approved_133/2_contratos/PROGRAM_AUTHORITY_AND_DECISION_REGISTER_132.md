---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_AUTHORITY_AND_DECISION_REGISTER_132
title: "Autoridad programática, aprobaciones y supersession"
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

# Autoridad programática, aprobaciones y supersession

## Contrato funcional

Registro único para **decisiones**, no para duplicar el contenido de los documentos. Clave `(decision_id,decision_version)`; campos mínimos `kind` (`PROGRAM_APPROVAL`, `G5_RATIFICATION`, `ADR_ACCEPTANCE`, `WORKTREE_MIGRATION`, `SPRINT_SCOPE`, `PROVIDER_EGRESS`, `PROMOTION`, `PRODUCT_ACCEPTANCE`), `baseline_head`, `target_doc_id`, `doc_sha256`, `decision_actor`, `decision_time`, `approval_method`, `scope`, `constraints`, `expires_at`, `supersedes`, `evidence_refs`, `status`.

Estados `PROPOSED→REVIEWED→APPROVED|REJECTED|EXPIRED`; toda revocación o modificación crea nueva revisión, no altera recibos antiguos. Una aprobación de programa **no** satisface una orden de Git ni autoriza MP-1B; G5 administrativa no ratifica automáticamente 132. Decisiones inmutables con hash y Source Registry/authority graph enlazados.

## Reglas y verificaciones

- No permitir `APPROVED` sin Owner identificable y referencia exacta a versión/HEAD/hash. El propio archivo que dice APPROVED no es evidencia suficiente de ratificación humana.
- Decisiones con duración/alcance revocable, políticas `DENY` superiores y conflicto → BLOCK.
- Supersession de los 12 docs v131 es **total documental**, sin editar histórico; al aprobarse 132, actualizar índice de autoridad sucesor, sellar SHA y marcar 131 `HISTORICAL_ONLY`.
- Validar operaciones negativas: cambio de hash, HEAD drift, aprobación reutilizada en otro scope, doble submit, sin firma, expiración, fallo al registrar.

## Explicación no técnica

Una aprobación debe indicar **exactamente qué se aprobó**, por cuánto tiempo y qué cambios permite. Aceptar el plan del proyecto no significa permitir a una máquina modificar archivos libremente.
