---
doc_id: "PROMPT-DEVPL-GSDLC-12-C"
title: "DEVPL-GSDLC-12-C — Guided vs Expert modes, accessibility and help"
status: "approved-rebound"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "approved_by_owner/rebound_repo427_after_GSDLC-12-B_windows_closure"
precondition: "GSDLC-12-B CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_repo: "repo_DevPilot_Local_427_DEVPL_GSDLC_12_B_BRANCH_EXTERNAL_EDIT_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
execution_source_commit: "d65db36f3f430f2e96357a931a7da14a8ee8a9e5"
execution_source_sha256: "764fbf23439091a869519c1ccd3963c5e733499ee91523b8b60f47862671d370"
execution_source_policy: "immediate Windows-validated successor of GSDLC-12-B; never regress to repo426/repo425"
full_regression_budget: "0 in 12-C by routine; GSDLC-12 remains 0/1 reserved for 12-E"
browser_policy: "mandatory real-browser Guided/Expert/a11y usability acceptance"
---

# Objetivo

Hacer DevPilot usable por personal no experto mediante Guided mode y progressive disclosure, sin reducir controles, y ofrecer Expert mode con diagnóstico avanzado bajo exactamente la misma autoridad server-side.

# Rebind de ejecución

GSDLC-12-B está `CLOSED/PASS/WINDOWS-VALIDATED`. La única fuente efectiva para 12-C es `repo_DevPilot_Local_427_DEVPL_GSDLC_12_B_BRANCH_EXTERNAL_EDIT_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `d65db36f3f430f2e96357a931a7da14a8ee8a9e5`, SHA-256 `764fbf23439091a869519c1ccd3963c5e733499ee91523b8b60f47862671d370`. El origen histórico de diseño permanece inmutable y no puede usarse para simplificar implementación.

# Implementación requerida

1. Guided/Expert es preferencia UX; no modifica RBAC, policy, approvals, tool/model permissions ni mutability.
2. Guided prioriza next action, progressive disclosure y copy clara sin ocultar blockers.
3. Expert añade hashes, IDs, authority traces y diagnostics sin conceder acciones nuevas.
4. HelpSystem/contextual help/glossary ofrece lenguaje simple + detalle técnico expandible + safe next action + evidence ref.
5. Accesibilidad: keyboard-only, foco visible, skip link, ARIA/landmarks/live regions/labels, asociación de errores, responsive y focus restoration.
6. No exponer secretos/tokens/rutas sensibles en help, aria, logs o screenshots.
7. Mantener parity server-side en Guided/Expert, incluido AI Control Center, Recovery y Conflict Resolution.
8. Automated a11y checks + checklist manual; declarar límites WCAG-oriented de esta primera versión.
9. HCA + Contract Reconciliation + registries current-active deben reconocer ambos modos sin duplicar autoridad.
10. FRX v2.4: Test Impact + focal/acumulativa; `Full Regression = 0` en 12-C.

# Browser acceptance obligatorio

Una sesión Guided y una Expert sobre el mismo actor/proyecto debe demostrar presentación distinta con autoridad idéntica; incluir journey keyboard-only y un error/recovery con foco correcto. Evidencia mínima: `a11y_report.json`, `mode_policy_parity.json`, `usability_session_report.md`, screenshots/verifier/checklist, source delta/Test Impact/HCA/Contract Reconciliation y S0/S1.

# PASS / BLOCK

**PASS:** journey no-tech completo, keyboard path funcional, errores explicables, policy parity, S0/S1=0 y Full=0.

**BLOCK:** Expert bypass, blocker crítico oculto por Guided, keyboard trap, acción sin accessible name, secreto expuesto o tarea crítica imposible sin conocimiento interno/operador externo.

# Salida

12-D solo se autoriza después de PASS Windows de 12-C.
