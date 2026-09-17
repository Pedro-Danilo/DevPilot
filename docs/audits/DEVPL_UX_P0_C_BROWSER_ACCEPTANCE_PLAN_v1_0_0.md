---
doc_id: "DEVPL-UX-P0-C-BROWSER-ACCEPTANCE-PLAN"
title: "DEVPL-UX-P0-C — Targeted real-browser acceptance plan"
status: "ready"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
source_repo: "repo_DevPilot_Local_433_DEVPL_UX_P0_B_PROJECT_CONTEXT_AUTH_SCOPE_CORRECTIVE_WINDOWS_VALIDATED_CANDIDATE.zip"
full_regression: "PROHIBITED"
---

# Browser acceptance UX-P0-C

## Objetivo

Validar visualmente el critical path productizado sin ejecutar mutaciones de proyecto ni sustituir los contratos automáticos de RBAC/API.

## Capturas obligatorias

1. `01_home_guided_desktop.png` — Home Guided: Create primary, Open/Import secondary y `Retomar proyecto activo` visible.
2. `02_entry_create_guided_desktop.png` — Create Entry: secuencia parámetros/dry-run/revalidation/approval/execute/verify y efecto de aprobación comprensible.
3. `03_project_status_guided_desktop.png` — contexto real, etapa/progreso/blocker/next action/recovery identificables.
4. `04_pre_code_guided_desktop.png` — siete etapas visibles/coherentes, etapa actual y next action clara.
5. `05_documents_guided_desktop.png` — orientación Buscar/Revisar/Draft/Validar/Aplicar sin exigir JSON para entender la siguiente acción.
6. `06_planning_guided_desktop.png` — Roadmap→Backlog→Sprint, acción primaria clara y JSON técnico colapsado por defecto.
7. `07_critical_path_mobile_390x844.png` — una superficie crítica Guided en 390×844 sin overflow horizontal crítico.
8. `08_role_negative_login_guard.png` — acceso project-scoped sin sesión redirige al login; no se habilita ruta protegida.

## Observaciones manuales

Registrar PASS/BLOCK para: siete preguntas del pre-pilot gate; efecto de aprobación; recovery; Guided simple-first; keyboard/focus; responsive; role-negative; no secretos; terminal escapes=0.

## No-go

No ejecutar Create/Open/Import, approvals, apply/freeze ni mutaciones de workspace solo para obtener capturas. El browser gate es de presentación/route authority. API y UI deben ejecutarse foreground y local-only.
