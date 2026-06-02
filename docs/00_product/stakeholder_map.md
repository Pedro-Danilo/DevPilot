---
title: "Stakeholder Map — DevPilot Local"
doc_id: "DEVPL-PROD-003"
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
# Stakeholder Map — DevPilot Local

## 1. Propósito

Este documento identifica los stakeholders de DevPilot Local, sus intereses, necesidades, riesgos, influencia y relación con el producto. La intención es evitar que la plataforma se diseñe únicamente desde la perspectiva técnica y asegurar que el MVP, MVP+ y las fases desktop/web respondan a necesidades reales de ingeniería, operación, seguridad, calidad y evolución.

## 2. Mapa general de stakeholders

| Stakeholder | Tipo | Rol | Interés principal | Influencia | Riesgo asociado |
|---|---|---|---|---:|---|
| Ordóñez | Interno | Owner, usuario primario, desarrollador principal | Profesionalizar su proceso completo de desarrollo de software | Alta | Alcance excesivo o cambio frecuente de prioridades |
| Futuro cliente freelance | Externo indirecto | Beneficiario de mejores procesos | Recibir software con más calidad, evidencia y trazabilidad | Media futura | Sobreprometer madurez industrial prematura |
| MIPSoftware | Normativo | Estándar general | Gobernar el SDLC completo | Alta | Aplicación parcial o superficial |
| MIASI | Normativo especializado | Extensión inteligente | Gobernar IA, agentes, herramientas, evaluación y AgentOps | Alta cuando aplica | Activación incompleta o tardía |
| DevPilot CLI | Sistema | Interfaz inicial | Ejecutar validaciones, gates y reportes | Alta en MVP | Comandos insuficientes o ambiguos |
| DevPilot Core | Sistema | Núcleo operativo | Orquestar validadores, políticas, workspaces y reportes | Alta | Acoplamiento excesivo |
| DevPilot Desktop | Sistema futuro | Interfaz visual local | Gestionar workspaces, gates, documentos y aprobaciones | Alta futura | UI sin core sólido |
| DevPilot Web | Sistema futuro | Interfaz web futura | Visualización, colaboración y dashboards | Media futura | Mayor superficie de seguridad |
| Git Adapter | Sistema | Integración con repos | Leer estado, diffs, ramas, commits y tags | Alta en MVP+ | Escritura accidental o mala interpretación de diffs |
| Validadores | Sistema | Quality gates | Detectar brechas documentales y técnicas | Alta | Falsos PASS |
| Agentes futuros | Sistema inteligente | Asistentes especializados | Apoyar requerimientos, arquitectura, código, pruebas y seguridad | Alta futura | Acciones inseguras o no evaluadas |
| Repositorios reales | Activo local | Fuente de código y evidencia | Ser analizados y asistidos por DevPilot | Alta en MVP+ | Exposición de secretos, pérdida de cambios |
| Herramientas externas futuras | Integración | Git remoto, CI/CD, modelos, APIs | Ampliar capacidades | Baja en MVP | Dependencia, costo o exposición |

## 3. Usuario primario

| Campo | Descripción |
|---|---|
| Nombre operativo | Owner/desarrollador independiente |
| Perfil | Ingeniero de sistemas que desarrolla software propio y para posibles clientes. |
| Necesidad | Gestionar el ciclo de vida de software con rigor, trazabilidad y apoyo progresivo de agentes. |
| Dolor actual | La calidad depende demasiado de memoria, disciplina manual y conversaciones dispersas. |
| Resultado deseado | Una plataforma que guíe, valide y documente el proceso de desarrollo. |
| Criterio de éxito | Poder iniciar, construir, revisar, versionar y operar proyectos con baseline de ingeniería. |

## 4. Roles de uso futuro

| Rol | Necesidad | Funcionalidad relacionada |
|---|---|---|
| Developer | Pasar de requerimientos a tareas implementables y código revisado | Backlog, Git Adapter, CodeReviewAgent |
| Architect | Validar diseño, C4, ADRs, módulos y riesgos | ArchitectureAgent, architecture gates |
| Security reviewer | Revisar threat model, secretos, dependencias y permisos | SecurityAgent, SAST/SBOM, policy gates |
| Product owner | Revisar valor, alcance, roadmap y releases | Product docs, roadmap, readiness dashboard |
| Operator/SRE | Operar, monitorear y resolver incidentes | Observability, runbooks, incident reports |
| Documentation reviewer | Mantener documentación viva | DocumentationAgent, docs-as-code validators |
| Release manager | Preparar release, rollback, tags y changelog | ReleaseAgent, Git Adapter, release gates |

## 5. Stakeholders por fase del producto

| Fase | Stakeholders dominantes | Necesidad central |
|---|---|---|
| MVP | Owner, CLI, Core, Validadores, MIPSoftware, MIASI | Validar estándar como gates ejecutables. |
| MVP+ | Owner, Git Adapter, Repos, Agentes en dry-run, Security reviewer | Analizar repos reales y patches sin acciones destructivas. |
| Desktop | Owner, Developer, Architect, Operator | Navegar workspaces, gates, documentos y aprobaciones. |
| Web | Owner, posibles colaboradores, clientes futuros | Visualización, colaboración y reportes remotos controlados. |

## 6. Necesidades por stakeholder

| Stakeholder | Necesidad | Evidencia esperada |
|---|---|---|
| Owner | Controlar el ciclo de vida completo | Dashboard/gates, reportes, Git status, trazabilidad |
| Developer | Saber qué implementar y si el cambio es seguro | Backlog, aceptación, tests, patch review |
| Architect | Ver arquitectura y decisiones | C4, ADRs, architecture report |
| Security reviewer | Evaluar amenazas y secretos | Threat model, security report |
| Operator | Ejecutar y recuperar el sistema | Runbook, observability, incidents |
| Agent runtime futuro | Operar bajo límites | Policy Card, Eval Card, Human Approval Card |

## 7. Implicaciones para diseño

1. El CLI debe existir como interfaz estable y automatizable.
2. La app desktop debe ser compromiso de producto, no posibilidad.
3. La app web debe llegar después de estabilizar core, seguridad y workspace model.
4. Git debe aparecer como actor técnico central del MVP+.
5. Los agentes no deben reemplazar gates determinísticos.
6. Toda acción que modifique archivos o repos debe tener dry-run y policy gate.
7. Los workspaces deben ser unidad operativa del sistema.

## 8. Riesgos de stakeholder

| Riesgo | Afecta a | Mitigación |
|---|---|---|
| El owner espera plataforma completa demasiado pronto | Owner | Roadmap MVP/MVP+/post-MVP. |
| Los agentes se usan antes de políticas | Owner, repos, clientes futuros | MIASI obligatorio. |
| El Git Adapter modifica repos prematuramente | Repos | Read-only inicial + dry-run. |
| La UI desktop/web se construye antes del core | Producto | Core-first. |
| Clientes futuros interpretan DevPilot como producto comercial maduro | Clientes | Mantener alcance personal hasta validación. |

## 9. Veredicto

El mapa de stakeholders confirma que DevPilot Local debe empezar como herramienta personal local-first, pero con compromiso explícito hacia una plataforma CLI + escritorio + web que gestione workspaces de ingeniería completos.
