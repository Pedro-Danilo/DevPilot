---
doc_id: "DEVPL-UX-P0-D-BROWSER-ACCEPTANCE-PLAN"
title: "DEVPL-UX-P0-D — Targeted browser acceptance plan"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "windows_validation_pending"
---

# Objetivo
Validar únicamente las superficies impactadas por UX-P0-D. No ejecuta Full Regression.

# Capturas requeridas
1. Story/Code Guided: OperationState, acción principal y diff/evidence progresiva.
2. Approvals Guided: approval summary y acción gobernada.
3. Jobs Guided: running/long-running feedback y estado terminal.
4. Quality Guided: GateSummary y blocker visible.
5. Release Readiness Guided: gate/approval/evidence coherentes.
6. Recovery/Reconciliation Guided: recovery/stale/revalidation con acción segura.
7. AI Guided: provider/policy/provenance visibles con evidencia progresiva.
8. Vista móvil 390x844 de una superficie operacional representativa.

# Observaciones manuales PASS/BLOCK
PASS requiere semántica visual consistente; blocker crítico visible; acciones destructivas/blocked no aparecen como primary; evidence accesible pero no dominante; foco teclado visible; sin overflow horizontal crítico; provider/policy/provenance AI visibles. BLOCK ante hidden blocker, autoridad desplazada al navegador, evidencia perdida, S0/S1 o ejecución de Full Regression.

# Seguridad
Solo navegación y lectura salvo flujos de prueba explícitamente seguros. No publish/deploy, force Git, `reset --hard`, `git clean` ni mutación destructiva.
