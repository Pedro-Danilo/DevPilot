---
doc_id: SPRINT-MP132-R00-05-134
version: 1.0.0
status: DRAFT_EXECUTION_GATED
approval_scope: PROPOSED_INCREMENT_ONLY
program_authority: DEVPL-MP-SUCCESSOR-132/OWNER-133
requires_owner_sprint_approval: true
execution_authority: false
source_mutation_authorized: false
---
# R00-05 — Gate M0, cierre de autoridad y handoff a R1

## A. Objetivo

Determinar mediante revisión independiente si R0 completó la regularización de autoridad, topología Git y bases de medición. **No** iniciar R1, crear sprints R1, activar modelos ni construir nuevas features. Cerrar el conjunto R0 sin false PASS por una decisión owner global previa: el programa aprobado y el STOP global levantado **no sustituyen** la evidencia Windows de los incrementos.

## B. Precondiciones

Receipts y hashes íntegros de R00-01/02/03/04; HEAD resultante de R00-03 y upstream/branch/worktree live; programa v132 57 MD; mapa de 9 ítems; ledger v1.32; 11 ADRs aceptados y su alcance; estados/riesgos. Si alguno está BLOCK o sin adjudicación, `M0_BLOCK/HOLD`, no reconstruir evidencia de memoria.

## C. Acciones

1. Leer literalmente receipts, ZIP y hashes de cuatro sprints, verificar identidad y consistencia temporal, no solo el número de PASS.
2. Confirmar programa 132 como autoridad; `131=HISTORICAL_ONLY`, ratificación G5/COR130 y STOP global levantado reflejados correctamente en Source Registry/Project State/Overlay y registros que correspondan. Confirmar que no hay `131` vigente ni `MP-1B` automáticamente autorizado.
3. Revisar HEAD del primer baseline (`R00-03`) y paridad Git normal: si R00-02 eligió A, probar que no se falsificó una migración B. Verificar protección de histórico Git/63 worktrees/Pilot A y de los ZIP históricos.
4. Completar **matriz de cobertura de los nueve ítems R0** con evidencia por ID, estado `DONE_ACCEPTED`, `NO_OP_ACCEPTED`, `DEFERRED_WITH_REASON` o `BLOCK`. No cerrar todo R0 si falta un P0 sin decisión Owner explícita.
5. Conciliar el audit-first de Settings y hardware con riesgos R1: no permitir que una auditoría desplace sin rastro entregables de R1 ni trate ModelAdapter configurado como modelo probado.
6. Producción de `R00_M0_GATE_RECOMMENDATION` (`PASS`, `PASS_WITH_FINDINGS`, `HOLD` o `BLOCK`), matriz de deuda con owner/prioridad, política de rebind para R1 y decisión Owner explícita. No realizar cambios de código ni Source Registry para fabricar cierre.

## D. Entregables

`R00_05_M0_ACCEPTANCE_MATRIX.md`, `R00_05_GATE_RECEIPT.json`, `R00_05_R1_READINESS_AND_DEPENDENCIES.md`, `R00_05_OWNER_DECISION_TEMPLATE.md` (PENDING hasta respuesta), `R00_05_EVIDENCE_INDEX.md`, evidencia ZIP+SHA, checkpoint. Si se requiere publicar el acta final en Git, debe plantearse **incremento documental adicional con auditoría focal propia**, no mutación silenciosa dentro del gate de solo lectura.

## E. Criterio de cierre

`M0 CLOSED/PASS` cuando autoridad publicada, ubicación A/B segura, primer baseline limpio, Settings/metrics auditados, los nueve ítems adjudicados y Owner aprueba cierre específico. `PASS_WITH_FINDINGS` permitido solo con riesgos no bloqueantes y seguimiento. `M0 HOLD/BLOCK` si G5/COR/STOP no reflejados, otro HEAD no aprobado, permisos abiertos, fuentes ausentes o cualquiera de los P0 de R0 incompletos sin waiver permitido. R1 se mantiene `NOT_AUTHORIZED` hasta decisión específica distinta.

## F. Continuidad

Checkpoint final lista `last_safe_phase`, `current_head`, `next_r1_audit_required`, `approved_program_sha`, `m0_owner_ref`, hallazgos y links hashes. La UI y el runtime no deben presentar cierre de R0 antes de acta Owner; una interrupción de herramientas no cambia estado `PENDING` a PASS.
