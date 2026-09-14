---
doc_id: "DEVPL-GSDLC-12-E-IMPLEMENTATION-REPORT"
title: "GSDLC-12-E — Full browser matrix, exactly-one Full regression and local RC"
status: "implemented-local/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "pending_windows_validation"
---

# Objetivo
Cerrar DEVPL-GSDLC-12 sin introducir una segunda autoridad de producto: browser matrix real, clean-install preliminar, gates current-active, una única logical Full y RC exact-commit.

# Fuente de ejecución
- Repo: `repo_DevPilot_Local_429_DEVPL_GSDLC_12_D_PERFORMANCE_SECURITY_RESOURCE_HARDENING_WINDOWS_VALIDATED_CANDIDATE.zip`
- Commit: `b0fa8fe1c0a31ccd902c4b47368c15d83f5dc19a`
- SHA-256: `b2758b64d6156c0e8f3c1f821dadf5d26571c9e34134992eba63b7bfb7079dd8`

# Invariantes
- PASS: browser matrix + clean-install + HCA/Contract Reconciliation + FRX preflight + Full/composite 100% accounted + S0/S1=0 + RC limpio.
- BLOCK: segunda Full, normal journey dependiente de operador externo, evidence/hash mismatch, auth/RBAC bypass, RC contaminado o Full incompleta.

# Riesgos
La Full puede terminar con FAIL funcional. Ese resultado se preserva; no se relanza la Full. El cierre requiere recovery selectivo exacto y accounting 100%.

# Verificación
La guía Windows única y el operador state-aware materializan el orden irreversible y la recuperación de interrupciones infra dentro de la misma sesión.

# Corrective v1.0.2 — current-active release freshness reconciliation
El focal Windows v1.0.1 detectó correctamente un drift heredado: `.devpilot/release/local_release_candidate_criteria.json` seguía esperando GSDLC-11-E/repo424 mientras Project State ya estaba en GSDLC-12-E. Se clasifica como `current-active/derived`, no como hecho histórico. El corrective sincroniza criteria + `current_repo` + aliases GSDLC de Project State/Source Registry con repo429/12-E, mantiene los snapshots históricos intactos y eleva el source delta a `19/170/288/0`. EvidenceFreshnessScanner y LocalReleaseCandidateReporter deben quedar PASS antes de crear fixture o consumir la Full.

# Corrective v1.0.5 — reconciliación Git semántica LF/CRLF
La recuperación Windows v1.0.4 demostró que `AdvancedWorkspaceReconciliationService` podía convertir un `git status --porcelain` worktree-only `MODIFY` en drift aun cuando `git diff --quiet --no-ext-diff` declaraba contenido normalizado idéntico. Ese comportamiento violaba la política FRX-v2.4 de que LF/CRLF físico no es autoridad. El corrective modifica únicamente la evaluación current-active: un ` M` se suprime solo si Git normaliza el path a diff vacío; staged/mixed changes, mode changes y contenido real siguen visibles. Se añaden regresiones que prueban tanto el falso dirty EOL como que un external edit real continúa clasificándose `REVALIDATE`. El source delta queda `21/170/288/0`; Full local sigue 0.

# Corrective v1.0.6 — regression harness portable para Git-semantic EOL

La validación Windows v1.0.5 preservó 20 PASS y un único FAIL en la nueva regresión de EOL. El FAIL no ejercitó el producto: la prueba asumía que escribir CRLF sobre un checkout gobernado por `eol=crlf` produciría siempre una entrada ` M` en `git status`; en Windows ese supuesto es falso porque el checkout ya puede estar físicamente en CRLF y el status queda clean. v1.0.6 no modifica `AdvancedWorkspaceReconciliationService`; sustituye únicamente el estímulo no determinístico por una inyección controlada del contrato exacto observado en la evidencia real (`porcelain = " M tracked.txt"` + `git diff --quiet = 0`). Se preserva el test real que demuestra que un external edit continúa visible como `REVALIDATE`. La evidencia Windows 20 PASS/1 FAIL queda histórica e inmutable; v1.0.6 reejecuta solo el nodeid corregido y el sentinel de edit real antes de retomar la reparación del fixture. Full sigue 0/1.

## Corrective v1.0.7 — pre-Full isolation authority recovery

Windows v1.0.6 reached the irreversible pre-Full gate with the browser matrix already PASS and the Full budget still `0/1`. `DEVPL-GSDLC-12-E-FULL-01` sealed exactly 3196 nodeids (`f619efabc93e69a8b13a36f90f961ae0a07ea31051af55edd35c168161f584df`) and executed zero tests, but FRX-v2.4 blocked the plan because the current-active Test Isolation Registry covered only 3144 of those 3196 nodeids. The two findings were `FRX24B_ISOLATION_COVERAGE_BLOCK` and the derived `FRX24B_CONFLICT_ISOLATION_COVERAGE_BLOCK`.

The corrective appends exactly 52 missing nodeids as `UNCLASSIFIED`, `parallel_safe=false`, `explicit_review_required=true`; it does not modify the 3153 existing entries, does not delete the 9 historical stale entries, and does not grant parallel authority. The resulting registry contains 3205 entries and covers the complete current collection `3196/3196` with `0` missing. Cumulative Test Impact becomes `22/172/289/0`.

`DEVPL-GSDLC-12-E-FULL-01` is immutable evidence with status `PREFLIGHT-ONLY / NO-EXECUTION / NO-BUDGET`. Because the source commit changes after this corrective, it is not reused or rewritten. The only executable Full session is `DEVPL-GSDLC-12-E-FULL-01-R1`. R1 must recollect exactly 3196 nodeids with the same collection SHA before the operator may reserve/consume the single Full budget. Functional FAIL/ERROR remains preserve-and-no-rerun with composite selective recovery.

### v1.0.7 current-status freshness reconciliation

El estado canónico `gsdlc_12_e_status` permanece `IMPLEMENTED/LOCAL-QUALIFIED/WINDOWS-VALIDATION-PENDING` durante la recuperación pre-Full. Los detalles de recovery se registran en campos específicos `gsdlc_12_e_prefull_*`, `gsdlc_12_e_isolation_*` y en los artefactos de qualification; no se reutiliza el campo de status current-active para codificar una subfase transitoria. Esto mantiene coherente `local_release_candidate_criteria.json` y evita un falso BLOCK de evidence freshness antes de la Full.
