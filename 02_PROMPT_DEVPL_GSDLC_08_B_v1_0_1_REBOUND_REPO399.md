---
doc_id: "02_PROMPT_DEVPL_GSDLC_08_B_V1_0_1_REBOUND_REPO399"
title: "DEVPL-GSDLC-08-B — Roadmap authoring generation review — rebound repo399"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner/rebound_repo399"
source_policy: "repo399/windows-validated-successor-of-DEVPL-GSDLC-08-A"
source_repo: "repo_DevPilot_Local_399_DEVPL_GSDLC_08_A_PLANNING_DOMAIN_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "0c2720a019b2e819d7348cc8ecf8a0c0c06dc073"
source_repo_sha256: "e0610950bd471cb48ef00a63cbe227350c2118b4ea0d013ce6244fae922f7309"
full_regression_runs: 0
browser_required: true
---
# DEVPL-GSDLC-08-B — Roadmap authoring/generation/review — Rebound repo399

Este successor conserva íntegramente la misión, capacidades, UX, pruebas, PASS y reglas transversales del prompt `02_PROMPT_DEVPL_GSDLC_08_B_v1_0_0_APPROVED_REBOUND.md`, pero reemplaza su `source_policy` abstracta por la autoridad Windows-validada efectiva de 08-A.

## Autoridad de ejecución

- repo: `repo_DevPilot_Local_399_DEVPL_GSDLC_08_A_PLANNING_DOMAIN_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit: `0c2720a019b2e819d7348cc8ecf8a0c0c06dc073`;
- SHA-256: `e0610950bd471cb48ef00a63cbe227350c2118b4ea0d013ce6244fae922f7309`;
- `GSDLC-08-A = CLOSED/PASS/WINDOWS-VALIDATED`;
- `GSDLC-08-B = AUTHORIZED`.

## Contrato operativo heredado

1. Construir `RoadmapWorkbench` sobre Planning Domain A.
2. MANUAL, IMPORT y AGENT structured proposal convergen al mismo schema y siempre nacen `DRAFT`.
3. Coverage de requirements/risks y findings explícitos.
4. Review/diff previo a aprobación; owner/product-owner server-side es autoridad de approval/freeze.
5. Freeze produce revisión inmutable; una evolución requiere versión sucesora.
6. Agent proposal nunca auto-aprueba, nunca concede tool authority y no requiere red/API externa para aceptación.
7. UI productiva project-scoped, feedback visible, teclado/accesibilidad básica, provenance legible y controles deny-aware.
8. Test Impact + focal + acumulativa A+B + historical-contract-sweep + Project State/Docs/TCR.
9. Browser focal obligatorio con exactamente tres consolas foreground. Evidencia manual mínima, no redundante.
10. `full=0`; la única full de GSDLC-08 permanece reservada para E.

Commit sugerido: `feat(gsdlc-08): add governed roadmap workbench authoring`
