---
doc_id: DEVPL-MP-SUCCESSOR-132-01_MATRIZ_RIESGOS_Y_DECISIONES_132
title: "Matriz de riesgos 132 y decisiones de mitigación"
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

# Matriz de riesgos 132 y decisiones de mitigación

## Registro de riesgo derivado del programa 131 y auditoría v1.32

| Riesgo | Severidad programática | Escenario | Mitigación / owner decision | Gate |
|---|---|---|---|---|
| RSK-01 | P0 | Doble motor de generación o apply entre Story y MP | Adapter único Story→Envelope y SourceChangePlan como authority | R1/R5 |
| RSK-02 | P0 | L adapter existe pero genera código/Requirements sin E2E real | Health ≠ EVAL; dataset L real y Pilot B UI | R2/R5 |
| RSK-03 | P0 | Egress remoto, secretos/PII y costo no gobernado | ADR externa + CostGuard + owner opt-in | R8 |
| RSK-04 | P0 | Agentes obtienen permisos por prompt/handoff | Tool allowlist, scope, approvals, bounded loops | R7 |
| RSK-05 | P0 | Recovery fixture confundido con crash de proceso real | Fault injection browser/API/worker/Git real | R5/R9 |
| RSK-06 | P1 | RAG grounded en fuente técnica obsoleta | Technical Source Profile, citations, freshness, evals negativas | R3 |
| RSK-07 | P0 | Pilot A parcial usado como éxito E2E | Pilot B fresh + segundo dominio independiente | R2–R10 |
| RSK-08 | P0 | Ejecutar prompt MP1B/SYNC2 pre-fusión sobre HEAD actual | Supersession total y G-PROGRAM | R0 |
| RSK-09 | P0 | `.venv` apunta al source de otra rama | Imports/env/procesos verificados post migration | R0 |
| RSK-10 | P0 | Git branch checked-out en dos worktrees; pérdida de untracked | Preflight Gate B + backup/rollback + aprobación | R0 |
| RSK-11 | P1 | Source Registry y overlay proyectan estados históricos actuales | COR-130 ya corrigió; successors y drift tests, no reeditar históricos | R0 |
| RSK-12 | P1 | G5 admin sin acto Owner inequívoco | **RESOLVED_BY_OWNER_133** mediante acta separada con SHA/HEAD y límites; registrar en Source Registry vivo en R0 | R0 |
| RSK-13 | P1 | UX inconsistencias/estado stale comprometen decisión | StateProjection y browser evidence por vertical | R1–R5/R9 |
| RSK-14 | P2 | Bundle Vite > tamaño esperado | Medición perf; warning no es FAIL de build | R9 |
| RSK-15 | P0 | Artifacts FROZEN editados o docs/runtime dual-authority | Contract successor + publish/hash + drift tests | R1–R4 |
| RSK-16 | P0 | PASS por conteo de tests sin vertical real | Evaluation maturity matrix y Pilot B real | R1/R10 |
| RSK-17 | P0 | Credenciales o PII empaquetadas | Deliverable/Evidence manifests separados + secret scan | R6 |
| RSK-18 | P0 | Release sin backup/rollback/startup | Real deploy + restore/smoke | R6/R10 |
| RSK-19 | P0 | PESP/MIASI aplicada a todas las apps de modo indiscriminado | Applicability por componente y risk/waiver explícitos | R1–R7 |
| RSK-20 | P0 | Template genérico presentado como equivalente a creación L semántica | GenerationRoute fallback `MODEL_REQUIRED` sin false pass | R1–R5 |
| RSK-21 | P1 | Markdown publicado pierde paridad o se edita fuera de DevPilot | Publish receipts/lineage y conflict-gate | R1–R6 |
| RSK-22 | P0 | Configuración global/proyecto/runtime sin precedence segura | Settings Authority Matrix y deny-floor policy | R0/R1 |
| RSK-23 | P1 | Backlogs por ola divergen en prioridades o deps | ID dueño único + índice consolidado derivado | R0–R10 |
| RSK-24 | P1 | R1 se infla y demora valor real | `minimum vertical first`, expansión por Pilot B | R1–R4 |
| RSK-25 | P1 | No se puede evolucionar producto tras primer release | ChangeImpact successor/versioned release | R1–R6 |

## Distinción de evidencias

`OPEN` de riesgo no equivale a bug reproducido hoy. El ledger v1.32 contiene estados históricos, algunos ya resueltos; antes de source correction se revisa HEAD vivo y se registra ID. Riesgos programáticos de datos/seguridad se mantienen priorizados aunque no exista todavía exploit demostrado. El Owner decide de manera independiente cualquier aceptación de riesgo residual.
