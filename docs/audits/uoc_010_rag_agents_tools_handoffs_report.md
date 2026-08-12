---
doc_id: DEVPL-UOC-010-AUDIT
title: "UOC-010 — RAG, agents, tools and handoffs implementation report"
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-08-11
approval: sprint-implementation-candidate
---

# UOC-010 — implementation report

## Resultado candidato

Se implementa una primera versión de `/ai` con cuatro adapters tipados (`rag-index`, `rag-query`, `agent-run`, `handoff-run`) sobre el framework UOC-007/UOC-008. No se habilita ejecución genérica del CLI ni de tools.

## Guardrails

- mock mandatory y costo USD 0;
- local provider opt-in/localhost-only;
- external APIs deshabilitadas;
- RAG con citas/freshness y estado insufficient-evidence;
- agent-run approval-bound, un turno y target/task allowlisted;
- memoria opt-in local redactada, 14 días, no evidencia formal;
- handoff `repo-review` dry-run con supervisor y máximo tres pasos;
- connector write, plugin execution, remote execution y arbitrary shell deshabilitados.

## Madurez y riesgos residuales

`implemented-initial`. Los adapters locales reales dependen de configuración explícita del operador y no se exigen para aceptación. Tool execution continúa contract-only. Memory usa JSON local determinista. UOC-011 deberá completar hardening de accesibilidad, rendimiento, límites, caos, instalación/upgrade y release.

## B1 Windows recovery reconciliation v1.0.1

La primera verificación Windows detectó dos clases de defectos previos al cierre: (1) el launcher npm del operador no preservaba correctamente una ruta `npm.cmd` bajo `C:\Program Files`; (2) cinco artefactos globales UOC-010 quedaron parcialmente desincronizados (puntero `last_registered_sprint`, `schemas_total`, mapping `ui.ai`, metadata top-level no permitida en operational flags y `currentSprint`). La recuperación v1.0.1 corrige esas inconsistencias sin ampliar el alcance funcional del sprint y sin repetir `pytest -q`; los tests históricos afectados se vuelven a ejecutar de forma focal.

## Authoritative closure
Windows/browser/canonical closure: **PASS**. UOC-011 authorized; S0=0/S1=0.
