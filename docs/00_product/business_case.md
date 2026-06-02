---
title: "Business Case — DevPilot Local"
doc_id: "DEVPL-PROD-002"
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
# Business Case — DevPilot Local

## 1. Propósito

Este documento justifica la inversión de tiempo y esfuerzo en DevPilot Local como plataforma agent-assisted SDLC personal. Su objetivo es demostrar por qué conviene construir primero un MVP acotado de CLI + validadores documentales y cómo ese MVP evolucionará hacia MVP+ y una plataforma más completa con Git, análisis de repos, validación de patches, refactor seguro, agentes, escritorio y web.

## 2. Problema de negocio

El owner desarrolla proyectos de software propios y potencialmente para clientes. Sin una herramienta de gobierno del ciclo de vida, cada proyecto corre el riesgo de depender de disciplina manual, memoria contextual y conversaciones dispersas. Esto produce:

- arranque de proyectos sin visión ni alcance;
- requerimientos débiles;
- arquitectura tardía o implícita;
- falta de trazabilidad entre decisiones, código, pruebas y releases;
- baja evidencia para clientes o auditorías internas;
- riesgo de usar IA/agentes sin controles suficientes;
- dificultad para repetir procesos profesionales de forma consistente.

## 3. Oportunidad estratégica

DevPilot Local puede convertirse en un activo interno del emprendimiento. Su valor no es solo automatizar tareas, sino **hacer ejecutable el estándar de ingeniería**.

| Activo | Valor |
|---|---|
| MIPSoftware | Estándar general para desarrollo profesional de software. |
| MIASI | Estándar especializado para IA/agentes. |
| DevPilot Local | Plataforma que aplica ambos estándares sobre proyectos reales. |
| Git | Registro técnico de evolución, cambios, ramas y releases. |
| Workspaces | Unidad operativa para gestionar proyectos gobernados. |

## 4. Justificación del MVP acotado

El MVP se acota deliberadamente a CLI local y validadores documentales porque esta es la forma de menor riesgo para validar la base del producto.

### 4.1 Por qué no empezar por agentes complejos

Empezar por agentes capaces de modificar repos, escribir código o aplicar patches sería prematuro porque aún no existirían gates maduros de:

- documentos mínimos;
- criterios de aceptación;
- políticas de permisos;
- validación de patches;
- trazabilidad;
- seguridad de filesystem;
- human approval;
- evaluación de agentes.

### 4.2 Por qué empezar por CLI

El CLI es adecuado porque:

- es rápido de construir;
- es testeable con `pytest`;
- puede ejecutarse localmente;
- produce salidas JSON/Markdown;
- puede integrarse después con CI;
- puede ser consumido por una app desktop/web;
- permite validar reglas antes de crear una interfaz visual.

### 4.3 Por qué empezar por validadores documentales

Los validadores convierten MIPSoftware/MIASI en evidencia verificable. Antes de que un agente sugiera código, el sistema debe poder responder:

```text
¿Existe visión de producto?
¿Hay requerimientos verificables?
¿Hay arquitectura mínima?
¿Hay threat model?
¿Hay estrategia de pruebas?
¿MIASI se activó si corresponde?
¿El proyecto está listo para codificar?
```

## 5. Momento de transición hacia MVP+

El MVP debe evolucionar hacia MVP+ cuando se cumplan estas condiciones:

| Condición | Evidencia |
|---|---|
| Baseline pre-code aprobada | Documentos `docs/` en `reviewed/approved`. |
| Validadores core implementados | `validate-artifact`, `readiness-check --strict`. |
| Reportes reproducibles | JSON/Markdown generados en `outputs/reports`. |
| Pruebas herméticas | `pytest -q` PASS. |
| Política local-first definida | Sin acciones destructivas por defecto. |
| Activación MIASI implementada | Artefactos MIASI obligatorios detectados. |
| Git integration diseñada | ADR + requerimientos para Git Adapter. |

MVP+ debe incluir:

- integración Git local;
- análisis de repos;
- detección de cambios;
- validación de patches;
- code review asistido en dry-run;
- refactor seguro propuesto;
- validación de entornos virtuales;
- primeros agentes documentales y de revisión;
- policy gates;
- human approval;
- trazas JSONL.

## 6. Beneficios esperados

### 6.1 Beneficios técnicos

- Requerimientos más claros y verificables.
- Arquitectura mínima antes de implementación.
- Validación de patches antes de cambios.
- Refactor seguro y reversible.
- Mejor control de repos reales con Git.
- Trazabilidad entre documentos, commits, pruebas y releases.
- Seguridad y privacidad desde el diseño.
- Integración gradual con agentes bajo MIASI.

### 6.2 Beneficios operativos

- Menos dependencia de memoria personal.
- Mayor consistencia entre proyectos.
- Menor fricción para iniciar proyectos profesionales.
- Mejor base para auditorías, handoffs y documentación de clientes.
- Mayor control sobre calidad antes del desarrollo fuerte.

### 6.3 Beneficios estratégicos

- Activo interno reutilizable para el emprendimiento.
- Base para servicios profesionales de desarrollo de software.
- Laboratorio aplicado para IA/agentes en SDLC.
- Posible producto futuro si madura suficientemente.
- Plataforma propia para mejorar productividad sin dependencia inicial de proveedores.

## 7. Viabilidad de desarrollo

La aplicación es viable si se construye incrementalmente:

```text
MVP documental → validadores → Git/repo analysis → patch review
→ agentes controlados → desktop → web → operación avanzada
```

No sería viable si se intentara empezar directamente con una plataforma web multiusuario y agentes que modifican código de forma autónoma. La ruta local-first reduce complejidad, costo, riesgo de seguridad y dependencia externa.

## 8. Naturaleza híbrida de la aplicación

DevPilot combina software tradicional y sistemas agénticos.

| Parte | Naturaleza |
|---|---|
| CLI, core, validators, reports, Git adapter | Software tradicional |
| Workspaces, policies, checklists, schemas | Software tradicional con reglas |
| RequirementsAgent, CodeReviewAgent, SecurityAgent | Agentes IA |
| Patch review, refactor seguro, recomendaciones | Híbrido |
| Human approval, policy gates, trazas | Control y gobernanza |

La utilidad se concentra en la combinación: reglas determinísticas para PASS/FAIL y agentes para análisis contextual y propuestas.

## 9. Costos estimados

| Rubro | MVP | MVP+ | Comentario |
|---|---:|---:|---|
| Python local | 0 | 0 | Base del core. |
| Git local | 0 | 0 | Control de versiones. |
| pytest | 0 | 0 | Pruebas offline. |
| Markdown/JSON | 0 | 0 | Documentación y reportes. |
| LLM/API | 0 | Opcional | No obligatorio. |
| Modelo local | No requerido | Opcional | Ollama/LM Studio futuro. |
| Desktop UI | No | Futuro | Fase posterior. |
| Web UI | No | Futuro | Fase posterior al desktop. |

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Scope creep | Alto | Separar MVP, MVP+ y post-MVP. |
| Automatización prematura | Alto | Dry-run, gates, human approval. |
| Dependencia de LLM | Medio | Ruta sin API y modelos locales opcionales. |
| Complejidad UI temprana | Medio | CLI/core primero. |
| Modificación accidental de repos | Alto | Git adapter read-only inicial, policy gate. |
| Falsos PASS | Alto | Validadores estrictos y pruebas negativas. |

## 11. Criterios para continuar

DevPilot debe continuar si el MVP demuestra:

- capacidad para validar artefactos MIPSoftware;
- activación MIASI correcta;
- reportes reproducibles;
- pruebas en PASS;
- Git hygiene;
- utilidad real en el propio proyecto.

## 12. Criterios de pausa o abandono

El proyecto debe pausarse si:

- se intenta automatizar código sin gates;
- el MVP no aporta valor al proceso real;
- los validadores son demasiado superficiales;
- el alcance se desplaza a UI antes de core;
- la seguridad local-first no queda garantizada.

## 13. Veredicto

El business case justifica continuar. La estrategia correcta es iniciar con un MVP acotado pero mantener como compromiso cierto la evolución hacia MVP+, escritorio y web.
