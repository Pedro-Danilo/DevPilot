---
title: "ADR-0003 — Workspaces como unidad operativa"
doc_id: "DEVPL-ADR-0003"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-04"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0003 — Workspaces como unidad operativa

## Contexto

DevPilot debe gestionar proyectos reales, no solo archivos aislados. Cada proyecto necesita documentos, reportes, gates, policies, trazas, estado Git y activación MIASI.

## Decisión

Adoptar el concepto de **workspace** como unidad operativa. En MVP se detecta una estructura mínima; en MVP+ se persistirá `.devpilot/project.yaml`.

## Consecuencias

- Facilita separar proyectos.
- Permite estado y trazabilidad por repo.
- Prepara dashboards desktop/web.
- Exige controlar rutas, outputs y metadatos.
