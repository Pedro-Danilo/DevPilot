---
doc_id: "DEVPL-REB-117-SPRINT-P0"
title: "P0 — Formalización contractual y publicación de successors"
version: "1.0.0"
status: "APPROVED / EXECUTION-GATED"
date: "2026-10-11"
owner_decision: "OWNER-APPROVAL-2026-10-11-REBASELINE-116"
implementation_authority: false
multiprovider_stop_lifted: false
---

# P0 — Formalización contractual y publicación de successors

## Propósito y estado
**Entrada:** G0 PASS; documentación fuente y baseline íntegros; STOP MP activo. **Salida:** `G1 DOCUMENTARY_AUTHORITY_PASS`.

## Scope y tareas

**Trabajo:** identificar autoridad canónica del paquete y registros, reconciliar Greenfield Charter/Brief/roadmap/backlog y 13-D sprint/protocol/runbook/prompt/evidence con `BRIDGE_GREENFIELD_117`; reconciliar MP STOP, synchronization protocol, ADR-008, piloto, dependencia e índices con `BRIDGE_MP_STOP_SYNC_117`. **No** reprogramar todavía olas MP-1B..MP-8. Implementar P0 como sucesores documentales mínimos, con publicación en el índice puente para ambos programas y rebind únicamente del Source Registry determinístico; el MP Source Registry permanece congelado hasta P3-C.

**Validación:** antes/después lista de paths, doc_id/version/lifecycle/supersedes, tests de gobernanza documental, lint de links/indices, coherencia de `STOP ACTIVE`, upstream parity de worktree modificado, 0 mutaciones Pilot A y 0 MP source mutation. Si los archivos MP congelados deben incorporar nuevas cláusulas, solo preparar paquete sucesor documental fuera del MP worktree: **no levantar STOP ni escribir en él hasta gate SYNC-1**. El contrato puente aprobado se publicará en authority neutral/track determinístico con receipt que MP pueda importar cuando sea autorizado; no hacer push de documentación MP en MP congelada.

**Estado de programa:** G0 queda registrado como PASS. G1 exige publicación coherente y accesible de los successors en índice documental puente externo versionado con SHA, más rebind determinístico; `MP Source Registry=PENDING_MP_IMPORT` constituye un estado explícito controlado hasta P3-C. Si no se logra un soporte canónico seguro y accesible para el índice puente, G1 sigue BLOCK. Nunca declarar ficticiamente que MP fue modificado.

**Evidencia:** manifest del successor pack, pruebas focales docs, logs TXT, Git commits (solo track permitido), ZIP limpio+SHA por modificación de plataforma, tabla de reglas sustituidas, decision receipt G1. No dejar un README histórico como autoridad activa.


## Criterios de cierre (PASS)
- Evidencia literal suficiente, checks de seguridad/autoridad, logs y Run Packet persistentes, ausencia de S0/S1 pendientes relacionados con el gate.
- No afirmar un PASS distinto del gate de este sprint; registrar `PASS`, `PASS+FINDING` o `BLOCK` sustentados en autoridad Git/receipts.
- No mutaciones del proyecto Pilot A por consola; todo estado crítico se preserva, validaciones focales, sin Full intermedia.
- Parches de plataforma (solo si necesarios y autorizados): pruebas focales, commit gobernado, promoción Git, **ZIP limpio obligatorio + SHA256** antes de cierre.

## Detener (BLOCK)
Si los contratos puente no pueden ser materializados y auditados sin violar STOP, detener el sprint y solicitar una decisión de publicación neutral; nunca editar MP congelada.

## Paquete de retorno al Owner
Un paquete pequeño con adjudicación, logs TXT, receipts machine-readable, hashes/Git, matriz de impacto, hallazgos y solo capturas decisivas de UI; sin screenshots duplicados de consola ni instrucciones de volver a pasos anteriores.
