---
doc_id: "DEVPL-GSDLC-12-C-USABILITY-SESSION-REPORT"
title: "DEVPL-GSDLC-12-C — Guided/Expert usability session report"
status: "closed-pass-windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-13"
approval: "windows-real-browser-pass/owner-adjudicated"
---

# Objetivo

Demostrar que un usuario no experto puede completar un journey Guided mediante siguiente acción y ayuda contextual, y que Expert añade diagnóstico sin ampliar autoridad.

# Estado

`PENDING-WINDOWS` para la aceptación real-browser. La implementación local y los contratos automatizados están listos; este documento no adjudica comportamiento manual que todavía no se ejecutó en Windows.

# Script Guided obligatorio

1. Entrar con el mismo actor/proyecto que se utilizará en Expert.
2. Seleccionar Guided únicamente con teclado.
3. Usar skip link y navegación principal sin mouse.
4. Abrir Help y localizar explicación de Recovery/Conflict Resolution.
5. Abrir Recovery o Conflict Resolution y confirmar que blocker/next action permanece visible.
6. Provocar el error seguro definido por la guía Windows y comprobar que el foco llega al heading del error y que la explicación incluye causa/impacto/next action/evidence ref sin secretos.

# Script Expert obligatorio

1. Sobre la misma sesión/proyecto, cambiar a Expert.
2. Confirmar que aparecen diagnostics/IDs/hashes/authority traces.
3. Confirmar que no aparece ninguna acción adicional capaz de saltar RBAC, approval, tool/model policy o mutability.
4. Repetir el mismo recovery/conflict y comprobar idéntico resultado de autoridad.

# Checklist manual

- navegación keyboard-only sin trap;
- foco visible y orden lógico;
- skip link funcional;
- mode selector con estado accesible;
- error/recovery con foco correcto;
- Guided no oculta blockers críticos;
- Expert no habilita acciones extra;
- responsive desktop+narrow viewport legible;
- ayuda no muestra tokens, secretos ni rutas locales sensibles.

# PASS / BLOCK

**PASS:** todas las tareas anteriores se completan en una única sesión real-browser y el verifier Windows queda PASS con S0/S1=0.

**BLOCK:** keyboard trap, foco perdido, blocker oculto, Expert bypass, secreto expuesto, error no explicable o tarea crítica que exige operador externo/conocimiento interno.

# Riesgo residual

Primera versión WCAG-oriented. Una auditoría formal multi-screen-reader/dispositivo/contraste queda como hardening industrial posterior; no se declara conformidad WCAG completa en 12-C.

# Resultado Windows

`PASS/REAL-BROWSER`: Guided, Expert, keyboard-only, error/recovery focus y responsive manual checklist completados con el mismo actor/proyecto. S0/S1=0.
