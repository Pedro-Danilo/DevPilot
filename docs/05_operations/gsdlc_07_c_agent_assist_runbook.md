---
doc_id: "DEVPL-GSDLC-07-C-AGENT-ASSIST-RUNBOOK"
title: "DEVPL-GSDLC-07-C — Governed Artifact AI Assist runbook"
status: "current"
version: "1.0.0"
owner: "DEVPL-GSDLC-07-C"
updated: "2026-08-29"
approval: "implementation-candidate"
---

# GSDLC-07-C Agent Assist runbook

07-C mantiene el lifecycle existente del Artifact Workbench. La secuencia obligatoria es `PLAN → RUN → REVIEW DIFF → HUMAN ACCEPT/REJECT/MODIFY`. `PLAN` expone agent/runtime/model/provider/access-route, ContextPack v2, tokens/cost y límites antes del run. `RUN` usa únicamente `mock` o `fake-local`, valida structured output y produce una proposal **UNTRUSTED** sin mutar source. `ACCEPT`/`MODIFY` persisten únicamente una revisión runtime `DRAFT` mediante `ArtifactDraftApplicationService`; `REJECT` no crea revisión. Ninguna operación 07-C concede `APPROVED` o `FROZEN`.

Runtime: `outputs/agent_assist/gsdlc_07_c`; se excluye del candidate. API externa, red y tools ejecutables permanecen deshabilitados en este micro-sprint.
