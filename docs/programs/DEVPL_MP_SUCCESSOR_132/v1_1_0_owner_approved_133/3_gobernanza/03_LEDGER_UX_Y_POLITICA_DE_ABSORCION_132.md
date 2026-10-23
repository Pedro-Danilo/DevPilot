---
doc_id: DEVPL-MP-SUCCESSOR-132-03_LEDGER_UX_Y_POLITICA_DE_ABSORCION_132
title: "Mapa de hallazgos UX/arquitectura y absorción por olas"
version: "1.1.1-r00-succ"
status: "OWNER_APPROVED_PROGRAM"
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
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
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


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** UX.
- **Actualización concreta:** Conservar findings históricos OBSERVE_ONLY, R00-04 UI NOT_TESTED; primera reproducción real R01-11; S0/S1 reproducible bloquea.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- R01-11 validó Settings tras COR-166; R01-13 validó Project Status tras CONT-169. Se mantienen como `OBSERVE_ONLY` la descubribilidad de navegación Project Home→Status y distinción Gate READY vs RECONCILIATION_BLOCK, salvo reproducción de defecto funcional real en R02. Chunk Vite warning no se eleva a BLOCK de producto sin impacto.
