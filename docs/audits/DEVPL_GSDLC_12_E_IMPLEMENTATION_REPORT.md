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
