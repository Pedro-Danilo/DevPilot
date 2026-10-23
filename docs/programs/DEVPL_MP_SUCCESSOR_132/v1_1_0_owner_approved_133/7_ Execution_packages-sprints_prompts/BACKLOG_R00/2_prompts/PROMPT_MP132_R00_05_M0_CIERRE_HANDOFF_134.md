---
doc_id: PROMPT-MP132-R00-05-134
version: 1.0.0
status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL
linked_sprint: SPRINT-MP132-R00-05-134
execution_authority: false
---
# PROMPT R00-05 — Adjudicación M0 y handoff R1

## Tarea precisa

Efectúa únicamente `SPRINT_MP132_R00_05_M0_CIERRE_HANDOFF_134.md` cuando existan evidencias reales de R00-01..04 completas y verificables. No inferir PASS por el paquete de sprints ni por el STOP Owner-133; las pruebas de R00-03 deben demostrar un **nuevo commit promovido** y los 57 documentos. Si falta algún recibo, **BLOCK** y solicitarlo.

## Auditoría de cierre

1. Validar CRC/SHA de los cuatro paquetes previos, `input_head`/`new_head` y continuidad del HEAD, programa owner-133 exacto, actas Owner G5/COR/STOP y ADRs, Git branch/upstream/current worktree, ausencia de writes en Pilot A.
2. Comprobar Source Registry, Project State y overlay **actuales**: 132 vigente y 131 histórico, G5 y COR ratificados, STOP global levantado y MP-1B aún sin ejecución autorizada, ADR010 external no habilita egress. No confundir `mp_1a_stop_status_at_merge` histórico con flag actual ni alterar campos FROZEN.
3. Conciliar 9 ítems del backlog R00 por ID, sus receipts y decisión (`DONE_ACCEPTED`, `NO_OP_ACCEPTED`, `DEFERRED_WITH_REASON`, `BLOCK`). No declarar cierre de un P0 por simple falta de tiempo.
4. Evaluar Settings/UX/risks/hardware con las limitaciones de `NOT_TESTED`, faltantes locales y evidencias existentes; preparar input focal para R1 sin redactar sprint/prompt R1 ni activar proveedores.
5. Emitir **propuesta** `M0_PASS|PASS_WITH_FINDINGS|HOLD|BLOCK`, acta de Owner en blanco hasta que haya confirmación explícita; sellar evidencia y completar un único handoff con riesgos, dependencias y siguiente HEAD. Si la publicación del acta necesita commit Git, dejar nuevo incremento document-only para su propia autorización, no modificar registro como efecto lateral.

## Implementación herramienta y verificaciones

Permitir un validador Python stdlib `mp132_r00_05_close.py` estrictamente read-only, `inspect|crosscheck|report|package`; comparar manifiestos, git HEAD y receipts, errores ante discrepancia (por ejemplo B elegido pero rama MP todavía checkout MP; G5 pendiente en projection; 56/57 docs); si no hay Git live registrar `NOT_VERIFIED` y NO-GO. Verificar idempotencia y hashes sin reempaquetar ZIP sellados de etapas anteriores. Ningún proceso background ni Full Regression por defecto.

## Entregables

`R00_05_M0_ACCEPTANCE_MATRIX.md`, `R00_05_CLOSURE_RECEIPT.json`, `R00_05_R1_READINESS.md`, `R00_05_OWNER_DECISION_PENDING.md`, evidencia ZIP SHA y una guía única Windows si se emplea operador, con pasos consecutivos sin retornos. Gate final exclusivamente el Owner; emisión de acta no autoriza R1 ni MP-1B de oficio.
