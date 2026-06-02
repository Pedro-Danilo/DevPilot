---
title: "Product Vision — DevPilot Local"
doc_id: "DEVPL-PROD-001"
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
# Product Vision — DevPilot Local

## 1. Resumen ejecutivo

**DevPilot Local** será una plataforma **agent-assisted SDLC personal**, **local-first**, progresivamente multi-modelo y orientada a producción real. Su propósito es ayudar a gestionar el ciclo de vida completo de creación de software profesional: idea, producto, negocio, stakeholders, requerimientos, arquitectura, diseño, entorno de desarrollo, codificación, revisión de código, validación de patches, refactor seguro, pruebas, seguridad, integración con Git, CI/CD, despliegue, operación, mantenimiento y evolución.

El producto nace para aplicar, validar y operacionalizar dos estándares creados en el proyecto AI_agents:

- **MIPSoftware — Modelo de Ingeniería Profesional de Software**, como estándar general para el ciclo de vida de cualquier aplicación profesional.
- **MIASI — Modelo de Ingeniería de Sistemas Agénticos Inteligentes**, como extensión obligatoria para proyectos que incorporen IA, agentes, LLMs, RAG, memoria, tool calling, evaluación agentic, trazas o automatización asistida por modelos.

La visión de largo plazo no es opcional: **DevPilot Local evolucionará desde un núcleo CLI local hacia una aplicación de escritorio y posteriormente hacia una interfaz web**, manteniendo el CLI y el core como base operativa, automatizable, testeable y reutilizable.

## 2. Problema

El desarrollo de software personal, freelance o de emprendimiento suele degradarse cuando depende de improvisación, intuición aislada, acumulación accidental de código o conversaciones dispersas. Los síntomas recurrentes son:

- proyectos que se empiezan a codificar sin propósito, alcance ni criterio de éxito;
- requerimientos ambiguos, incompletos o no verificables;
- decisiones arquitectónicas sin ADR ni trazabilidad;
- entornos de desarrollo creados manualmente sin evidencia reproducible;
- repositorios sin política clara de ramas, commits, revisión, tags o releases;
- parches aplicados sin validación previa;
- refactors que introducen regresiones o deuda técnica adicional;
- pruebas desconectadas de requerimientos y criterios de aceptación;
- seguridad, privacidad y gestión de secretos tratadas tarde;
- despliegues y releases sin evidencia de calidad ni rollback;
- uso de IA o agentes sin controles formales de permisos, costos, evaluación, trazabilidad y aprobación humana.

DevPilot Local busca convertir el desarrollo de software en un proceso guiado, verificable, trazable y semiautomatizado, empezando por gates locales y evolucionando hacia agentes especializados.

## 3. Oportunidad

Existe una oportunidad estratégica: construir una herramienta propia que actúe como **sistema operativo de ingeniería personal** y como primer producto aplicado del emprendimiento. DevPilot Local permitirá convertir MIPSoftware y MIASI en procesos ejecutables, validadores, reportes, trazas, checklists, políticas y agentes.

La oportunidad se justifica porque:

- MIPSoftware ya define el estándar general de trabajo.
- MIASI ya define los controles específicos para sistemas inteligentes y agénticos.
- El owner necesita una herramienta real para profesionalizar su proceso de desarrollo.
- Git puede actuar como fuente de verdad técnica para historial, ramas, diffs, commits, tags y trazabilidad.
- La plataforma puede iniciar sin nube obligatoria ni API keys.
- La herramienta puede madurar desde CLI hacia escritorio/web sin desechar el core.
- La semiautomatización con agentes puede introducirse de forma controlada y auditable.

## 4. Visión del producto

> **DevPilot Local será una plataforma local-first y agent-assisted para planear, validar, construir, revisar, refactorizar, versionar, evaluar, asegurar, desplegar y operar proyectos de software siguiendo estándares profesionales de ingeniería, con MIPSoftware como marco rector y MIASI como extensión inteligente obligatoria cuando aplique.**

## 5. Usuario primario

| Usuario | Descripción |
|---|---|
| Ingeniero de sistemas / desarrollador independiente | Profesional que desarrolla software propio o para clientes y necesita una forma rigurosa de gestionar todo el ciclo de vida de sus productos. |

En la etapa inicial, el usuario primario es el owner/desarrollador. En fases posteriores, el sistema deberá soportar roles conceptuales adicionales: arquitecto, revisor de seguridad, revisor de código, operador, documentador, product owner y agentes especializados.

## 6. Objetivos de producto

| ID | Objetivo | Resultado esperado |
|---|---|---|
| OBJ-01 | Aplicar MIPSoftware como estándar oficial | Todo proyecto nace con propósito, alcance, requerimientos, arquitectura, seguridad, pruebas y operación mínima. |
| OBJ-02 | Activar MIASI cuando aplique | Todo proyecto con IA/agentes usa Agent Cards, Tool Cards, políticas, evaluación, trazas y human approval. |
| OBJ-03 | Construir entorno de desarrollo reproducible | Crear y validar entorno local, dependencias, estructura y comandos base. |
| OBJ-04 | Gestionar repos reales | Analizar Git status, ramas, diffs, commits, tags, cambios pendientes y trazabilidad. |
| OBJ-05 | Asistir producción y análisis de código | Revisar estructura, calidad, riesgos, deuda técnica y consistencia con arquitectura. |
| OBJ-06 | Validar patches | Analizar cambios antes de aplicarlos o promoverlos. |
| OBJ-07 | Habilitar refactor seguro | Proponer refactors reversibles, testeables y trazables. |
| OBJ-08 | Apoyar despliegue y release | Validar readiness, changelog, rollback, pruebas y evidencias. |
| OBJ-09 | Semiautomatizar con agentes | Usar agentes IA en dry-run, con políticas, evaluación y aprobación humana. |
| OBJ-10 | Evolucionar a escritorio y web | Mantener CLI/core como base y agregar UX visual para workspaces, reportes y flujos SDLC. |

## 7. Propuesta de valor

DevPilot Local aporta valor porque:

- convierte estándares documentales en gates verificables;
- reduce improvisación en proyectos reales;
- aumenta trazabilidad desde producto hasta pruebas y release;
- permite trabajar local-first con privacidad y control;
- integra Git como columna vertebral de cambios;
- separa validadores determinísticos de asistencia con IA;
- habilita agentes sin entregarles control destructivo prematuro;
- prepara una futura app de escritorio/web sobre un core sólido.

## 8. Local-first como principio operativo

DevPilot Local será local-first. Esto implica:

| Dimensión | Implicación |
|---|---|
| Ejecución | Debe funcionar en la máquina local sin nube obligatoria. |
| Datos | Documentos, reportes, trazas, configuraciones y estados viven primero en disco local. |
| Privacidad | Código, documentos y decisiones no se envían a servicios externos por defecto. |
| Modelos IA | Puede operar sin LLM, con modelo local o con API externa opcional. |
| Costos | Costo externo cero por defecto. |
| Seguridad | Toda acción sobre archivos/repos se restringe por políticas. |
| Git | El repositorio local es fuente de verdad inicial. |
| Reproducibilidad | Los gates deben poder repetirse localmente. |
| Auditoría | Toda acción relevante deja evidencia local. |

Este enfoque es adecuado porque DevPilot gestionará repos reales, documentos de proyectos, código fuente, trazas, decisiones y posiblemente secretos. La nube y las APIs externas podrán integrarse después, pero no serán requisito base.

## 9. Visión de workspaces

DevPilot Local debe operar por **workspaces de ingeniería**. Cada proyecto gestionado tendrá un workspace con su configuración, estándares, políticas, reportes, trazas y estado de ciclo de vida.

Estructura conceptual:

```text
D:\Projects\
  DevPilot_Local\
    src/
    docs/
    tests/

  Proyecto_X\
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
    docs/
    src/
    tests/
    README.md
```

Tipos de workspace:

| Tipo | Propósito |
|---|---|
| DevPilot workspace | Desarrollo de la propia plataforma. |
| Project workspace | Proyecto nuevo gobernado por MIPSoftware. |
| Repo workspace | Repo existente incorporado a DevPilot. |
| Multi-repo workspace | Conjunto de repos relacionados. |
| Learning workspace | Laboratorio o experimento. |
| Production workspace | Proyecto real con gates estrictos. |

## 10. Componentes tradicionales, agentic e híbridos

DevPilot será una aplicación híbrida.

### 10.1 Componentes de software tradicional

| Componente | Función |
|---|---|
| CLI | Interfaz inicial, automatizable y testeable. |
| Core | Motor de reglas, validación y orquestación. |
| Workspace Manager | Gestión de proyectos y `.devpilot/`. |
| Git Adapter | Lectura de status, diff, ramas, commits y tags. |
| Report Engine | Reportes JSON, Markdown y JSONL. |
| Validator Engine | Validación de documentos, schemas y checklists. |
| Policy Engine | Reglas de permisos, rutas, dry-run y acciones. |
| Desktop/Web UI | Interfaces visuales futuras sobre el mismo core. |

### 10.2 Componentes agénticos

| Agente futuro | Función |
|---|---|
| RequirementsAgent | Analizar y mejorar requerimientos. |
| ArchitectureAgent | Revisar arquitectura, C4 y ADRs. |
| CodeReviewAgent | Revisar código y detectar riesgos. |
| PatchReviewAgent | Evaluar patches antes de aplicar. |
| RefactorAgent | Proponer refactor seguro. |
| TestPlannerAgent | Proponer pruebas y matriz de cobertura. |
| SecurityAgent | Analizar amenazas, secretos, dependencias y permisos. |
| ReleaseAgent | Revisar readiness, changelog y rollback. |
| DocumentationAgent | Mantener documentación viva. |
| RepoAnalysisAgent | Analizar estructura y evolución de repos. |

### 10.3 Componentes híbridos

El patrón central será:

```text
Validador determinístico → evidencia PASS/FAIL
Agente IA → recomendación contextual
Policy gate → autorización o bloqueo
Humano → aprobación de acciones sensibles
Git → trazabilidad de cambios
```

## 11. MVP, MVP+ y visión post-MVP

### MVP

El MVP inicial se concentra en:

- CLI local.
- Validadores documentales.
- Readiness pre-code.
- Detección MIASI.
- Reportes JSON/Markdown.
- Checklists.
- Tests offline.

### MVP+

El MVP+ expande el núcleo hacia capacidades reales de SDLC:

- integración Git local;
- análisis de repos;
- validación de patches;
- code review asistido en dry-run;
- propuestas de refactor seguro;
- generación de backlog técnico;
- validación de entornos virtuales;
- primeros agentes controlados;
- policy gates;
- trazas JSONL;
- human approval.

### Post-MVP

El post-MVP consolida:

- aplicación de escritorio;
- aplicación web;
- workspaces visuales;
- dashboard de gates;
- integración con modelos locales/API externa opcional;
- operación sobre múltiples proyectos;
- colaboración futura;
- despliegue asistido.

## 12. Compromiso de evolución de interfaz

La evolución de interfaz es un compromiso de producto:

```text
CLI local → CLI + desktop → CLI + desktop + web
```

El CLI seguirá siendo el core operativo. La app desktop será la primera interfaz visual fuerte para trabajo personal con repos locales. La web llegará después, cuando el core, los gates y la seguridad estén suficientemente maduros.

## 13. Indicadores de éxito

| Métrica | Criterio inicial |
|---|---|
| Readiness documental | `readiness-check` PASS. |
| Activación MIASI | `miasi-required` detecta correctamente DevPilot. |
| Pre-code gate | Checklist pre-code en PASS. |
| Pruebas | `pytest -q` PASS. |
| Git hygiene | Working tree limpio antes de cerrar sprint. |
| MVP+ readiness | Git integration y patch review diseñados antes de implementación. |
| Seguridad | No hay acciones destructivas sin dry-run/aprobación. |
| Trazabilidad | Producto → requerimiento → prueba → release. |

## 14. Criterios de bloqueo

El producto no debe avanzar a desarrollo funcional fuerte si:

- la visión no reconoce el alcance SDLC completo;
- el MVP no diferencia MVP y MVP+;
- Git no aparece como componente central;
- local-first no está definido operativamente;
- MIASI no está activado;
- no existe estrategia de workspaces;
- no se diferencian componentes tradicionales y agénticos;
- la evolución desktop/web queda como posibilidad vaga y no como compromiso.

## 15. Veredicto

Con los refinamientos de DEVPL-PRE-0107, `product_vision.md` queda en estado **reviewed** y listo para aprobación del owner.
