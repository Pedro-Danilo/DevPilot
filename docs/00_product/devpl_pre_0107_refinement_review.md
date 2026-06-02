---
title: "DEVPL-PRE-0107 — Refinamiento MVP+, local-first, Git y workspaces"
doc_id: "DEVPL-PRE-0107"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-01"
updated: "2026-06-02"
approval: "approved_by_owner"
refinement: "DEVPL-PRE-0107 — MVP+ y visión completa de plataforma"
approved_by: "Ordóñez"
approved_at: "2026-06-02"
approval_scope: "SPRINT-PRECODE-01 product baseline"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---
# DEVPL-PRE-0107 — Refinamiento MVP+, local-first, Git y workspaces

## 1. Propósito

Registrar los ajustes aplicados a la baseline de producto de DevPilot Local después de revisar el alcance real esperado para la plataforma agent-assisted SDLC.

## 2. Decisión

Se decide que DevPilot Local no será solo un validador documental. El MVP seguirá siendo CLI + validadores por razones de seguridad y madurez, pero la visión oficial incluye:

- construcción y validación de entornos virtuales;
- gestión de repos reales;
- integración con Git;
- análisis de código;
- validación de patches;
- revisión de código;
- refactor seguro;
- despliegue asistido;
- operación y trazabilidad;
- semiautomatización con agentes IA;
- evolución obligatoria hacia desktop y web.

## 3. Justificación

El MVP acotado reduce riesgos y permite convertir MIPSoftware/MIASI en gates verificables antes de entregar a los agentes acceso a código, repositorios o filesystem. El MVP+ será la fase donde se conecten Git, repo analysis, patch review y primeros agentes controlados.

## 4. Impacto documental

| Documento | Impacto |
|---|---|
| `product_vision.md` | Ampliación de visión y objetivos. |
| `business_case.md` | Justificación MVP/MVP+. |
| `stakeholder_map.md` | Nuevos stakeholders técnicos y roles futuros. |
| `mvp_scope.md` | Separación MVP, MVP+ y post-MVP. |
| `product_roadmap.md` | Roadmap obligatorio CLI → Git/repo → agents → desktop → web. |

## 5. Estado

Todos los ajustes fueron aplicados y quedan listos para revisión del owner.
