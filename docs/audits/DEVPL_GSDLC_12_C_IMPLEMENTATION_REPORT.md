---
doc_id: "DEVPL-GSDLC-12-C-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-12-C — Guided vs Expert modes, accessibility and help implementation report"
status: "local-functional-qualified/windows-validation-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "local-qualification-pass/windows-browser-pending"
---

# Objetivo

Implementar Guided/Expert, accesibilidad y ayuda sobre el successor Windows-validado repo427, sin ampliar autoridad y sin consumir la Full Regression reservada para 12-E.

# Fuente de ejecución

- Repo: `repo_DevPilot_Local_427_DEVPL_GSDLC_12_B_BRANCH_EXTERNAL_EDIT_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Commit: `d65db36f3f430f2e96357a931a7da14a8ee8a9e5`.
- SHA-256: `764fbf23439091a869519c1ccd3963c5e733499ee91523b8b60f47862671d370`.
- 12-B: `CLOSED/PASS/WINDOWS-VALIDATED`.

# Implementación

`ExperienceMode` es una preferencia UX browser-only. Guided ofrece progressive disclosure, next-action focus y copy simple; Expert hace visibles IDs/hashes/authority traces, pero ambos usan exactamente las mismas rutas, sesión, RBAC, approvals, tool/model permissions y mutability server-side.

Se incorpora `HelpSystemView`, ayuda contextual y glosario, errores plain+technical seguros, foco programático verificable, live regions, accessible names, skip-link/focus-visible preservados y responsive layout. Recovery y Conflict Resolution se endurecen sin cambiar su autoridad ni sus operaciones. AI Control Center declara explícitamente mode-policy parity.

# Pruebas locales

- Focal 12-C: `8/8 PASS`.
- Selección acumulativa current-active: `40/40 PASS`.
- UI static/a11y smoke: `16/16 PASS`.
- UI route/schema/enforcement: PASS dentro de la selección acumulativa.
- Project State: PASS.
- Docs Governance: PASS observado durante la validación local.
- TCR v2: PASS.
- Test Impact v2: se registra en `DEVPL_GSDLC_12_C_TEST_IMPACT.json`, sin paths huérfanos.
- Full Regression: `0`; budget GSDLC-12 permanece `0/1` para 12-E.

# Riesgos y limitaciones

- La aceptación real-browser Guided/Expert/keyboard/error-focus sigue pendiente y es obligatoria para cerrar 12-C.
- Los checks WCAG-oriented son una primera versión industrial: no constituyen certificación formal WCAG ni sustituyen matriz multi-screen-reader/dispositivo/contraste instrumental.
- Expert muestra diagnóstico adicional, no autoridad adicional.
- El selector de modo usa `localStorage` únicamente como preferencia UX; nunca como autoridad.

# PASS / BLOCK

**PASS local:** focal/acumulativa/smoke/gates current-active PASS, Test Impact sin huérfanos, S0/S1=0, Full=0 y 12-D no autorizado.

**PASS Windows:** además, una sesión real demuestra Guided y Expert sobre el mismo actor/proyecto, keyboard-only sin trap, error/recovery con foco correcto, responsive legible y policy parity sin bypass.

**BLOCK:** Expert bypass, Guided oculta blocker crítico, keyboard trap, acción sin accessible name, secreto expuesto, error sin next action/evidence ref o Full Regression ejecutada sin hard trigger owner-approved.

# Evolución posterior

12-C entrega una primera versión WCAG-oriented. Una auditoría formal de conformidad y una matriz ampliada de tecnologías asistivas deben tratarse como hardening industrial posterior, sin reinterpretar este cierre como certificación WCAG completa.
