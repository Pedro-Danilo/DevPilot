---
doc_id: DEVPL-UX-P0-B-PROJECT-CONTEXT-AUTH-SCOPE-CORRECTIVE
status: current
version: 1.0.0
updated: 2026-09-15
source_repo: repo_DevPilot_Local_432_DEVPL_UX_P0_B_PRODUCT_APP_SHELL_WINDOWS_VALIDATED_CANDIDATE.zip
source_commit: 0136c3cac5d10ef8c647f96e38423f4940cadb6c
source_sha256: 527fdf14b91af19638c45dc2b578c834cab8a137c686c582bcd5ffdb84330a76
target_repo: repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip
full_regression: prohibited
---

# UX-P0-B corrective — project context and auth scope

## Correctivo

1. La identidad lógica del active workspace se obtiene de `.devpilot/project.yaml` (`project.id`) cuando existe; el nombre de carpeta queda como fallback.
2. La ruta física continúa protegida por `PathGuard`; no se debilita RBAC.
3. Project Status trata Planning y Reconciliation como proyecciones auxiliares. Un fallo auxiliar ya no sustituye la proyección primaria de estado por un falso error global.
4. Se agregan tests focales para la canonicalización y la resiliencia de Project Status.

## Invariantes preservadas

- human-session y scopes siguen siendo autoridad;
- legacy token no se habilita;
- paths/route IDs permanecen iguales;
- no se modifica approval/tool/model authority;
- no hay remote push;
- no hay Full Regression.

## Criterio de cierre

La aceptación browser correctiva debe demostrar explícitamente:

- project/workspace lógico real, no `unknown`;
- ausencia de 401/403 en Project Status;
- Recovery accesible sin auth-scope blocker;
- Reconciliation accesible sin auth-scope blocker;
- Guided/Expert parity;
- mobile responsive;
- cero secretos en capturas.

UX-P0-C solo puede activarse después de este cierre.
