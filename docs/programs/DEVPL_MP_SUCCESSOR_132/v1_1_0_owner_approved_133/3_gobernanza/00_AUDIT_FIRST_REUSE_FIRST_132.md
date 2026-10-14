---
doc_id: DEVPL-MP-SUCCESSOR-132-00_AUDIT_FIRST_REUSE_FIRST_132
title: "Política obligatoria Audit-first / Reuse-first y límites de cambio"
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

# Política obligatoria Audit-first / Reuse-first y límites de cambio

## 1. Mandato transversal

Antes de implementar **toda** modificación al baseline —feature, bug, refactor, schema, API, UI, configuración versionada, test, documentación de autoridad, migración o retiro— se audita literalmente el HEAD y fuente viva. Se identifican servicios, rutas, contratos, tests, datos persistentes, políticas, ledger y autoridad humana. *No programar una funcionalidad si ya existe otra con la misma responsabilidad*. Documentar por qué `REUSE-AS-IS`, `EXTEND`, `REFACTOR`, `REPLACE`, `NEW-CAPABILITY`, `RETIRE` o `NO-OP`.

## 2. Recibo Reuse/Delta Map obligatorio

Campos: `head/upstream/worktree`, `inputs`, `responsibility_boundary`, `source_files_exact`, `tests_existing`, `ui_api_service_flow`, `contracts/ADRs/standards`, `finding_evidence`, `classification`, `allowed_delta_paths`, `data_migrations`, `security/cost/egress`, `rollback`, `test_matrix`, `Owner_scope_approval`. El modo `NO-OP` puede cerrar una investigación sin cambiar Git.

La auditoría no se reemplaza con inspección de nombres de clases ni con memoria histórica de un repo anterior; requiere comprobar el código instalado, authority lineage, effects y negativas. Para LLMs verificar salida real desde UI, no sólo `ModelAdapter` instanciable.

## 3. Gates A0–A6

| Gate | PASS | BLOCK |
|---|---|---|
| A0 authority | HEAD upstream/branch, estados 3 Git, recibos y raíz verificados | dirty desconocido, lineage inexacto, autoridad ausente |
| A1 audit | Reuse/Delta Map, evidencia, componente owner único | duplicación o supuesto no comprobado |
| A2 design | ADR/contrato sucesor cuando altera frontera; threat model y Owner scope | nueva autoridad implícita |
| A3 implement | fixture, dry-run/preimages, allowlist, presupuesto y recheck | escritura fuera de scope o egress |
| A4 validate | focal + negativas + UI/integración según contrato, con paridad Source Registry | false PASS, contrato roto |
| A5 promote | Git tres estados, commit/push normal, ZIP limpio + SHA y rollback | force push/reset-hard, overwrite sin consent |
| A6 accept | evaluación humana, receipts, hallazgos y evidencias sólo pertinentes | defecto S0/S1 o evidencia incompleta |

## 4. Política Windows/seguridad

Operador Python modular idempotente; una guía `.md` completa y consecutiva por incremento, PowerShell cada comando en **una** línea física; tres consolas foreground para API/UI/Owner; sin background ni scripts para escribir código del Pilot B. No full regression salvo cierre/gate aprobado. No utilizar comparaciones byte-a-byte de CRLF/LF como criterio funcional general; preservar evidencia original inmutable y snapshots por hash. `dry-run` por defecto; `execute` sólo con autorización humana exacta. Revisar salida tool/model como dato no confiable.

## 5. Hallazgos

S0/S1 funcional reproducible → BLOCK/corrective; S2 en aprobación/seguridad/critical path requiere revisión preferente; S2/S3 sólo visual en `OBSERVE_ONLY` salvo decisión contextual. Un finding histórico corregido permanece como histórico y no se reabre sin reproducción en el HEAD actual.
