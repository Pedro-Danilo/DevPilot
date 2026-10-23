---
doc_id: DEVPL-MP-SUCCESSOR-132-PROGRAM_AUTHORITY_AND_DECISION_REGISTER_132
title: "Autoridad programática, aprobaciones y supersession"
version: "1.1.1-r00-succ"
status: "SUCCESSOR_DRAFT_FOR_OWNER_REVIEW"
baseline_commit: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
historical_baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
successor_execution_authority: false
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


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Registro autoridad.
- **Actualización concreta:** Registrar HEAD COR-150 y acta COR-151, aprobación Owner R0-09 diferida; R1 y MP-1B aún no autorizados.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

**Decisión Owner posterior `UI_FIRST_PILOT_B_V1` (179):** mismo Pilot B desde B0 a B7, todas las acciones del proyecto originadas por UI; consolas solo operación y auditoría de plataforma. La autoridad de PathGuard para parent ya aprobado permanece independiente de selección de target. ADR-MP-132-012 acepta esta delimitación; no amplía red, herramientas ni permisos. Esta decisión no transforma retrospectivamente recibos históricos ni aprueba incrementos futuros.

---

## Decisión Owner programática A188

`MP132-OWNER-DECISION-188` → `APPROVED` por instrucción explícita del Owner el 2026-10-22; alcance `PROGRAMMATIC_POLICY_ONLY`; referencia Git `3a0a170f3c646e9955966576dd9212d3f87450e6` como baseline actual de planificación. Objetivo: adoptar autoría/calidad por perfil y ADR-MP132-016. `execution_authority=false`: no sirve para aprobar un candidato ni autorizar R02-08, un push, agente o proveedor externo. Registro separado `0_program/13_DECISION_OWNER_188.md`; evitar fingir recibos firmados que no existen.
