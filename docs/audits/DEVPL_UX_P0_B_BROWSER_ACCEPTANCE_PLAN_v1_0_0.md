---
doc_id: "DEVPL-UX-P0-B-BROWSER-ACCEPTANCE-PLAN"
title: "DEVPL-UX-P0-B — Targeted real-browser acceptance plan"
status: "current"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
source_repo: "repo_DevPilot_Local_431_DEVPL_UX_P0_A_AUTHORITY_DESIGN_SYSTEM_FOUNDATION_WINDOWS_VALIDATED_CANDIDATE.zip"
manual_validation_required: true
full_regression: "PROHIBITED"
---

# DEVPL-UX-P0-B — Targeted real-browser acceptance plan

## Objetivo

Validar únicamente el chrome transversal modificado por UX-P0-B. No convertir B en una browser matrix integral ni en la aceptación greenfield de UX-P0-C/E.

## Evidencia mínima

1. `01_guided_project_status_desktop.png`
   - viewport desktop;
   - navegación agrupada visible;
   - breadcrumb/location context;
   - Project Context persistente;
   - proyecto, etapa, estado/blocker y Next Action identificables;
   - diagnósticos raw no dominan Guided.

2. `02_expert_project_status_desktop.png`
   - mismo proyecto/contexto;
   - Expert muestra diagnósticos adicionales;
   - ninguna autoridad o acción adicional por cambiar de modo.

3. `03_guided_project_status_mobile.png`
   - viewport móvil;
   - navegación/contexto utilizables;
   - sin overflow horizontal crítico;
   - targets críticos utilizables.

4. `04_recovery_project_context_desktop.png`
   - ruta `/recovery`;
   - contexto de proyecto sigue visible;
   - recovery indicator/estado no oculta blockers.

## Observaciones manuales obligatorias

Registrar PASS/BLOCK para:

- grouped navigation;
- breadcrumb/location;
- project/stage/state/blocker/next-action;
- Guided vs Expert authority parity;
- keyboard/focus y skip link;
- responsive/no horizontal overflow crítico;
- recovery context;
- no secrets/credenciales visibles.

## Handoff de approvals

La preservación exact-ID de `/approvals?handoff=...` se valida principalmente con contratos automatizados. No se obliga a crear una aprobación artificial solo para una captura si no existe una operación real pendiente.

## Seguridad

Las capturas nunca deben contener contraseñas, tokens, API keys ni secretos. Si una pantalla muestra información sensible accidentalmente, no capturarla: adjudicar BLOCK y corregir.
