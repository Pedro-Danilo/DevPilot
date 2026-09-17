---
doc_id: "DEVPL-UX-P0-B-FINAL-CLOSURE-ADJUDICATION"
title: "DEVPL-UX-P0-B — Final closure adjudication after project-context/auth-scope corrective"
status: "CLOSED/PASS/WINDOWS-VALIDATED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
baseline_repo: "repo_DevPilot_Local_432_DEVPL_UX_P0_B_PRODUCT_APP_SHELL_WINDOWS_VALIDATED_CANDIDATE.zip"
corrective_successor_repo: "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
corrective_successor_commit: "dc63672f2d617968998f3c68374a03581b348578"
corrective_successor_sha256: "f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246"
evidence_sha256: "ec8428ca89a80fcb20087926d1f9a26862ab0904bd90041c9ff0b53f439b3a71"
full_regression_runs: 0
---

# DEVPL-UX-P0-B — Final closure adjudication

## Veredicto

`DEVPL-UX-P0-B = CLOSED/PASS/WINDOWS-VALIDATED`.

## Evidencia decisiva

- corrective focal validation PASS;
- browser validation PASS con cinco capturas reales;
- canonical project/workspace `devpilot-local`;
- Project Status sin 401/403;
- Recovery sin auth-scope 401/403;
- Reconciliation sin auth-scope 401/403;
- Guided/Expert parity PASS;
- responsive 390×844 PASS;
- package exact-commit tracked-only PASS;
- promotion fast-forward-only PASS;
- Full Regression ejecutada en B: `0`.

## Correctivo incorporado

La identidad lógica del active workspace se deriva de `.devpilot/project.yaml` (`project.id`) y no del nombre físico de la carpeta. Project Status conserva su proyección primaria aunque una proyección auxiliar falle.

## Findings para evolución natural

- UX-S2: Project Home debe exponer un camino explícito para retomar un proyecto server-active después de login.
- UX-S2: Project Status sigue siendo denso en Guided y puede expresar un gate `UNKNOWN` con wording técnico; UX-P0-C debe productizarlo sin alterar autoridad.

## Siguiente authority

UX-P0-C queda autorizado únicamente sobre `repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip` / `dc63672f2d617968998f3c68374a03581b348578` / `f4415775bd3bf5a01b6368197d0754374de93b659fa5f6bbff8b7a2b8ead4246`.
