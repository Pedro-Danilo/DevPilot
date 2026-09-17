---
doc_id: "DEVPL-UX-P0-E-BROWSER-USABILITY-PLAN"
title: "DEVPL-UX-P0-E — Browser and no-tech usability plan"
status: "ready"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "execution-required-on-windows"
---

# Browser matrix

La sesión debe usar la UI real en 127.0.0.1:5173 y API 127.0.0.1:8787, sin DevTools para navegar ni terminal para completar el journey normal.

Capturas mínimas: login/home; create/open/import; project status; pre-code/documents/planning; story/code+diff; approvals; jobs/quality; release; recovery/reconciliation; AI/provenance; Expert parity; negative authorization guard; tablet 768x1024; mobile 390x844.

# Siete preguntas UX-P0

1. ¿En qué proyecto estoy?
2. ¿En qué etapa del SDLC estoy?
3. ¿Qué está listo y qué está bloqueado?
4. ¿Cuál es la siguiente acción válida?
5. ¿Por qué está bloqueada una acción cuando aplica?
6. ¿Dónde reviso evidencia/diagnóstico sin que domine Guided?
7. ¿Cómo recupero/revalido el flujo sin salir a una terminal externa?

# Usability metrics

Registrar `time_to_next_valid_action_seconds`, `confused_moments`, `block_moments`, `first_attempt_success` y `confidence_1_to_5`. PASS requiere first-attempt success, terminal escapes=0, siete respuestas correctas, no UX-S0/S1 y confidence >=3. Los tiempos son observacionales, no una promesa SLA.

# A11y/responsive

Keyboard-only, Tab/Shift+Tab, focus-visible, skip/main navigation cuando aplique, sin keyboard trap, blocker/error focus legible, desktop/tablet/mobile sin overflow crítico que oculte la acción esencial.
