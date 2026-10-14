---
doc_id: DEVPL-MP-SUCCESSOR-132-03_LEDGER_UX_Y_POLITICA_DE_ABSORCION_132
title: "Mapa de hallazgos UX/arquitectura y absorción por olas"
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

# Mapa de hallazgos UX/arquitectura y absorción por olas

## 1. Fuente y limitación

Basado en `ledger_v1_32_MP0F_REB117_INTEGRADO.md` (working ledger, no source authority). Las reproducciones son históricas y pueden no persistir exactamente en HEAD 8db5…; se debe volver a demostrar el hallazgo antes de declarar bug actual o cerrar su acción. No volver a abrir resueltos por simple copia del ledger.

## 2. Settings (prioridad temprana)

| ID | Evidencia | Acción propuesta |
|---|---|---|
| `UX-P1-02-B01-004` | Densidad y falta de jerarquía pre-proyecto | R0 audit → R1 Settings Home/readiness |
| `UX-P1-02-B01-006` | Mezcla plan-only/read-only con disable/revoke mutativo | R1 dividir persistencia/policy/runtime y explicar efectos |
| `CAP-13B01-SETTINGS-001` | Falta experiencia unificada de configuración persistente con authority | R1 typed config/effective values; R2 local model; R8 external |
| `UX-P1-MP0F-001` | Captura llegó al ceiling 16384 y zoom ilegible | MP-0F disclosure aplicado parcialmente; mantener diseño modular y browser evidence |
| `ARCH-13B03-001` / `CAP-13B03-LAUNCH-001` | Binding de workspace/arranque todavía no productizado | R0/R1 setup scope, R9 launcher/upgrade/restore |

**No resolver sólo con CSS/acordeones** ni añadir un editor general de JSON para policy. Primero autoridad efectiva, seguridad y UI plan/execute.

## 3. Hallazgos por superficie a incorporar contextualmente

| Familia/IDs exactos | Propuesta / ola |
|---|---|
| `UX-P1-02-B01-002`, `UX-P1-02-B01-003` | Abrir vs retomar; roles/capabilities resumidos Guided, R2 y R1 respectivamente |
| `UX-P1-02-B01-001`, `UX-P1-02-B01-005` | Login branding e IDs técnicos; diferir S3 si no afecta tarea, R9 |
| `UX-P1-02-B02-001/002`, `ARCH-13B02-001` | Históricamente corregidos por Project Entry neutral; validar no regresión B0 R2 |
| `UX-P1-13D02-021`, `UX-P1-13D03-007`, `UX-P1-13D04-001/002` | Cross-surface status stale, Quality PASS vs PENDING, Pre-code FROZEN CTA: R1 state projection, R2–R5 browser gates |
| `UX-P1-13D03-006/008/009/010` | Job duration/heartbeat, validation history, retry after PASS y queued start: R5 |
| `UX-P1-13D05-002/003/004/005/006/007/008/009` | Post-apply CTA, ID manifiesto, session 401, job overflow, Quality ID, exact pathset, JSON Guided: R5 |
| `UX-P1-13D04-003` | CommitPlan completed styling tras PASS: R5 |
| `REB-TEST-P2A-001`, `REB-TEST-P2B-001` y `D06-P2A-L01..L03`/`D06-P2B-L04..L06` | Límites D06: crash/API/locks/git/revalidation real en R5–R9 |
| `REB-ARCH-P3C-CANDIDATE-001` | Bridge Story/Envelope y L real no completo: R1/R5 |
| `REB-UX-P3C-BUILD-001` | Chunk Vite warning/perf, no build FAIL: R9 |
| `REB-GOV-P3C-REGISTRY-001` | COR-130 resolvió estado actual; no reescribir snapshot sellado: R0 mantener pruebas sucesoras |

## 4. Disposición para nuevo programa

Cada backlog usa `finding_id` como trazabilidad, nunca se cierra un finding por existir un ticket. Calificación S0/S1 funcional reproducible implica correctivo focal; S2 en acciones sensibles revisado antes de gate, demás S2/S3 por contexto/Owner; S3 puramente cosmético diferible. `RESOLVED` históricos permanecen preservados con su evidencia.
