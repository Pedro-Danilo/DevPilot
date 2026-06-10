---
title: "C4 Context — DevPilot Local"
doc_id: "DEVPL-ARCH-002"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-20"
updated: "2026-06-10"
approval: "approved_by_owner_direction"
change_reason: "Reconciled by FUNC-SPRINT-20 to distinguish implemented, partial, planned, disabled and future nodes."
approved_by: "Ordóñez"
approved_at: "2026-06-04"
approval_scope: "SPRINT-PRECODE-03 architecture baseline"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---
# C4 Context — DevPilot Local

## 1. Propósito

Este documento representa la vista **C4 Nivel 1 — Contexto** de DevPilot Local. Su objetivo es mostrar el sistema dentro de su entorno operativo: owner/developer, proyectos gestionados, estándares MIPSoftware/MIASI, repositorios, Git, modelos/agentes, persistencia local y futuras interfaces desktop/web.

El C4 Context no describe todos los componentes internos; muestra límites, actores, sistemas externos opcionales y dependencias principales.

## 2. Sistema bajo diseño

| Elemento | Descripción |
|---|---|
| Sistema | DevPilot Local |
| Tipo | Plataforma local-first híbrida agent-assisted SDLC personal |
| Usuario primario | Owner/Developer |
| Estándar general | MIPSoftware |
| Extensión inteligente | MIASI |
| Unidad operativa | Workspace |
| Interfaz inicial | CLI |
| Interfaces comprometidas | Desktop y Web |
| Modelos IA | Mock/local/API externa opcional bajo ModelAdapter y CostGuard |
| Persistencia | Markdown, JSON/YAML, SQLite, JSONL y vector store futuro |

## 3. Diagrama C4 Context

```mermaid
flowchart LR
  Owner[Owner / Developer] --> DevPilot[DevPilot Local]
  Architect[Software Architect] --> DevPilot
  Reviewer[Requirements / Security / QA Reviewer] --> DevPilot
  Supervisor[Agent Supervisor] --> DevPilot

  DevPilot --> ProjectWorkspace[Project Workspace
D:/Projects/*]
  ProjectWorkspace --> Docs[docs/ pre-code]
  ProjectWorkspace --> Repo[Repositorio Git local]
  ProjectWorkspace --> Outputs[outputs/reports + traces]
  ProjectWorkspace --> DevpilotDir[.devpilot/ metadata]

  DevPilot --> Standards[MIPSoftware + MIASI]
  DevPilot --> Templates[Templates / Checklists / Schemas]
  DevPilot --> LocalRuntime[Python + venv local]
  DevPilot --> LocalDB[SQLite local]

  DevPilot -. MVP+ .-> Git[Git CLI / local repository]
  DevPilot -. MVP+ .-> LocalLLM[Modelo local opcional
Ollama / LM Studio]
  DevPilot -. MVP+ opcional .-> ExternalLLM[LLM APIs opcionales
OpenAI / Gemini / Mistral / HF]
  DevPilot -. Post-MVP .-> MCP[MCP/API tools opcionales]
  DevPilot -. Post-MVP .-> Desktop[Desktop UI]
  DevPilot -. Post-MVP .-> Web[Web UI]
```

## 4. Límites del sistema

| Dentro de DevPilot | Fuera de DevPilot |
|---|---|
| Validar documentos, checklists, frontmatter, schemas y trazabilidad. | Reemplazar IDEs o herramientas profesionales completas. |
| Crear y auditar documentación pre-code con agentes controlados. | Aprobar automáticamente decisiones generadas por IA. |
| Generar reportes, hallazgos, recomendaciones y evidencias. | Hacer commits/despliegues automáticos sin aprobación. |
| Consultar Git inicialmente en modo read-only. | Administrar repos remotos como SaaS inicial. |
| Ejecutar modelos mock/local/API opcional bajo ModelAdapter. | Obligar a depender de un proveedor LLM único. |
| Persistir estado local, runs, gates, approvals, traces y costos. | Almacenar secretos en claro. |
| Preparar desktop/web futuros sobre core común. | Iniciar como plataforma cloud obligatoria. |

## 5. Actores y expectativas

| Actor | Expectativa |
|---|---|
| Owner/Developer | Gestionar proyectos propios con disciplina profesional, agentes asistidos y control local. |
| Software Architect | Obtener arquitectura, ADRs, riesgos y trazabilidad desde producto/requisitos. |
| Requirements Reviewer | Verificar requisitos, historias, casos de uso y criterios de aceptación. |
| Security Reviewer | Revisar threat model, políticas, secretos, agentes y herramientas. |
| Agent Supervisor | Aprobar o rechazar acciones agentic sensibles. |
| Future Operator | Consultar runbooks, reportes, trazas e incidentes. |

## 6. Sistemas externos opcionales

| Sistema externo | Etapa | Uso | Control obligatorio |
|---|---|---|---|
| Git local | MVP+ | Estado, diff, branch, commit, historial. | Read-only inicial. |
| Modelos locales | MVP+ | Agentes sin costo externo obligatorio. | ModelAdapter + evals. |
| LLM APIs externas | MVP+/Post-MVP | Mejorar calidad cuando se justifique. | API keys opcionales, CostGuard, SecretGuard. |
| MCP/API tools | Post-MVP | Integración con herramientas y fuentes externas. | Tool Registry + policy gate. |
| Desktop UI | Post-MVP | Experiencia visual local. | Core común. |
| Web UI | Post-MVP | Dashboard/control opcional. | Auth, threat model y controles propios. |

## 7. Decisión de contexto

DevPilot Local debe ser diseñado como una plataforma que funciona localmente desde el primer día, pero preparada para operar de forma híbrida cuando el owner configure modelos locales o APIs externas. La arquitectura debe mantener control de costos, seguridad, evaluación y trazabilidad sin convertir la nube o un proveedor LLM en dependencia obligatoria.


---

## 8. Reconciliación post-18 de estados C4

### 8.1 Propósito

Esta sección fue agregada por `FUNC-SPRINT-20` para que la vista Context no mezcle intención histórica con disponibilidad operativa. La vista conserva la dirección de producto, pero debe leerse con la siguiente leyenda.

### 8.2 Estado de nodos externos y periféricos

| Nodo C4 Context | Estado reconciliado | Explicación operativa |
|---|---|---|
| Owner/Developer | `implemented` | Usuario primario vigente del CLI local. |
| Project Workspace | `implemented-initial` | `.devpilot/project.yaml`, docs, reports y traces existen; faltan perfiles/migraciones. |
| Git local | `implemented-initial` | Lectura segura con `git-status`; ramas/tags/log quedan pendientes. |
| MIPSoftware + MIASI | `implemented` | Estándares locales y registries validados. |
| SQLite local | `implemented-initial` | LocalStore v0; approval/cost workflow aún no operativo. |
| Modelo mock | `implemented` | MockModelAdapter funcional, sin costo externo. |
| Modelos locales Ollama/LM Studio | `planned` | Declarados como dirección futura; sin cliente real. |
| APIs externas OpenAI/Gemini/Mistral/HF | `disabled` | Bloqueadas por CostGuard/SecretGuard hasta ADR, presupuesto y approval. |
| MCP/API tools | `future` | No hay módulo MCP. |
| Desktop UI | `future` | Solo existe `app contract`; no hay shell visual. |
| Web UI/API | `future` | Solo existen rutas contract-only; no hay servidor. |

### 8.3 Funcionamiento e integración

La sección opera como control documental de drift. Se integra con `docs/audits/capability_status_matrix_after_sprint_18.md` y con `docs/audits/roadmap_reconciliation_after_sprint_18.md`.

### 8.4 Criterios PASS/BLOCK

PASS: todos los nodos aspiracionales tienen estado `planned`, `disabled` o `future` cuando no hay implementación real. BLOCK: documentar UI, MCP o APIs externas como implementadas.

### 8.5 Riesgos

Esta reconciliación es manual. Debe evolucionar hacia validación por schemas y trazabilidad en Fase A.
