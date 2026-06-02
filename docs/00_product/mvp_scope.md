---
title: "MVP Scope — DevPilot Local"
doc_id: "DEVPL-PROD-004"
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
# MVP Scope — DevPilot Local

## 1. Propósito

Este documento define el alcance del **MVP**, del **MVP+** y de la visión post-MVP de DevPilot Local. Su función es impedir expansión prematura, pero también evitar que el MVP se interprete como una visión limitada. El MVP es el primer núcleo verificable; el MVP+ es la primera expansión hacia repositorios reales, Git, patches, refactor seguro y agentes controlados.

## 2. Definición del MVP

El MVP de DevPilot Local será una herramienta **CLI local-first** que permita inicializar, revisar y validar artefactos mínimos de ingeniería conforme a MIPSoftware y activar MIASI cuando el proyecto incluya IA, agentes, LLMs, RAG, memoria, tool calling o automatización inteligente.

El MVP demuestra que el estándar puede convertirse en flujo operativo antes de introducir automatización avanzada.

## 3. Definición del MVP+

El MVP+ será la expansión inmediata del MVP hacia capacidades reales de SDLC sobre repos locales:

- integración con Git;
- análisis de repositorios;
- validación de patches;
- revisión de código asistida en dry-run;
- propuestas de refactor seguro;
- validación de entorno virtual;
- trazas JSONL;
- primeros agentes controlados;
- aprobación humana para acciones sensibles.

## 4. Objetivo del MVP

> Validar que DevPilot Local puede guiar un proyecto de software desde la apertura formal hasta un readiness pre-code verificable, sin depender de API keys, servicios pagos ni agentes autónomos.

## 5. Objetivo del MVP+

> Validar que DevPilot Local puede operar sobre repos reales de forma local-first, analizar cambios, revisar patches, asistir código/refactor y preparar decisiones de ingeniería sin ejecutar acciones destructivas por defecto.

## 6. In scope funcional del MVP

| ID | Capacidad | Descripción | Evidencia |
|---|---|---|---|
| MVP-F01 | CLI local | Ejecutar comandos desde terminal. | `python -m devpilot_core ...` |
| MVP-F02 | Readiness pre-code | Validar artefactos mínimos antes de codificar. | `readiness-check` |
| MVP-F03 | Detector MIASI | Determinar si un proyecto requiere extensión inteligente. | `miasi-required` |
| MVP-F04 | Validación de artefactos | Validar existencia, frontmatter, campos obligatorios y estructura. | Reporte PASS/FAIL |
| MVP-F05 | Validación de checklists | Evaluar checklist pre-code. | Checklist PASS/FAIL |
| MVP-F06 | Reportes | Generar reportes JSON y Markdown. | `outputs/reports/` |
| MVP-F07 | Pruebas herméticas | Ejecutar tests offline. | `pytest -q` |
| MVP-F08 | Plantillas base | Crear o validar estructura documental mínima. | `docs/` |
| MVP-F09 | No API keys | Funcionar sin servicios externos. | `.env.example` sin secretos reales |
| MVP-F10 | Dry-run por defecto | Evitar modificaciones destructivas. | Policy documentada |

## 7. In scope funcional del MVP+

| ID | Capacidad | Descripción | Evidencia |
|---|---|---|---|
| MVPPLUS-F01 | Git status | Leer estado del repo local. | Reporte de cambios. |
| MVPPLUS-F02 | Git diff analysis | Analizar diffs sin modificar archivos. | Reporte de impacto. |
| MVPPLUS-F03 | Patch validation | Validar patches antes de aplicar. | PASS/FAIL + recomendaciones. |
| MVPPLUS-F04 | Code review dry-run | Revisar código localmente. | Reporte de review. |
| MVPPLUS-F05 | Safe refactor proposal | Proponer refactor reversible. | Plan de refactor. |
| MVPPLUS-F06 | Env validation | Verificar entorno virtual, dependencias y comandos. | Reporte de entorno. |
| MVPPLUS-F07 | Repo scan | Analizar estructura, tests, docs, riesgos. | Repo report. |
| MVPPLUS-F08 | Agent-assisted review | Agentes en dry-run para documentos/código. | Recomendaciones trazables. |
| MVPPLUS-F09 | Human approval | Solicitudes de aprobación para acciones sensibles. | Approval log. |
| MVPPLUS-F10 | JSONL traces | Registrar eventos de validación/agentes. | `outputs/traces/*.jsonl` |

## 8. In scope documental

| Área | Documentos mínimos |
|---|---|
| Producto | product vision, business case, stakeholder map, MVP scope, roadmap |
| Requerimientos | specification, user stories, use cases, acceptance criteria, traceability |
| Arquitectura | architecture document, C4 context, C4 container, ADRs |
| Seguridad | threat model, privacy assessment |
| Calidad | test strategy |
| Operación | observability plan, runbook |
| MIASI | agent, tool, policy, eval, human approval, observability cards |
| Checklists | checklist pre-code |

## 9. Out of scope del MVP

| Elemento | Motivo |
|---|---|
| UI web completa | Requiere validar primero core y seguridad. |
| Aplicación desktop completa | Comprometida para fase posterior, no MVP. |
| SaaS multiusuario | Fuera del objetivo personal inicial. |
| Integración obligatoria con OpenAI/Gemini/Mistral/etc. | Mantener costo cero y local-first. |
| LLM obligatorio | Validadores offline primero. |
| Agentes autónomos ejecutores | Riesgo alto sin policies/evals maduras. |
| Escritura automática en repositorios externos | Requiere human approval y permisos. |
| CI/CD remoto real | Fase posterior. |
| Base de datos compleja | No necesaria en MVP. |

## 10. Out of scope del MVP+ inicial

| Elemento | Motivo |
|---|---|
| Aplicar patches automáticamente sin revisión | Riesgo alto. |
| Push automático a repos remotos | Requiere seguridad y aprobación. |
| Despliegue cloud automático | Fase posterior. |
| Agentes con autonomía alta | Primero agentes recomendadores/dry-run. |
| Multiusuario | Requiere modelo de identidad, permisos y seguridad web. |

## 11. Restricciones

| Restricción | Decisión |
|---|---|
| Sistema operativo inicial | Windows local. |
| Lenguaje principal | Python. |
| Costos externos | 0 en MVP. |
| API keys | No requeridas. |
| Datos sensibles | No usar secretos reales en pruebas. |
| Acciones críticas | No ejecutar sin aprobación humana. |
| Validadores | Primero determinísticos/offline. |
| Git | Read-only en primeras capacidades MVP+. |

## 12. Local-first en alcance

DevPilot debe conservar:

- ejecución local;
- almacenamiento local;
- reportes reproducibles;
- no envío de código a terceros por defecto;
- API externa opcional, nunca obligatoria;
- modelos locales opcionales;
- Git local como base de trazabilidad;
- configuración por workspace.

## 13. Workspaces en alcance

El MVP debe preparar la noción de workspace, aunque no implemente toda su gestión todavía.

```text
.devpilot/
  project.yaml
  standards.yaml
  miasi_activation.yaml
  workspace_state.json
  policies/
  reports/
  traces/
  gates/
  approvals/
```

## 14. Criterios de éxito del MVP

| Criterio | Meta |
|---|---|
| Tests | `pytest -q` PASS. |
| Readiness | `readiness-check` PASS. |
| MIASI | `miasi-required` true para DevPilot. |
| Documentos | Baseline pre-code aprobada. |
| Reportes | JSON/Markdown generados. |
| Seguridad | Sin acciones destructivas. |

## 15. Criterios de éxito del MVP+

| Criterio | Meta |
|---|---|
| Git status | Leer cambios locales sin modificar repo. |
| Diff analysis | Explicar impacto de cambios. |
| Patch review | Validar patch en dry-run. |
| Repo scan | Detectar estructura, riesgos y deuda inicial. |
| Agent review | Recomendaciones con trazas y políticas. |
| Human approval | Acciones sensibles bloqueadas hasta aprobación. |

## 16. Decisión de alcance

El MVP queda acotado a CLI + validadores, pero la visión aprobada exige MVP+ como siguiente evolución obligatoria antes de desktop/web.
