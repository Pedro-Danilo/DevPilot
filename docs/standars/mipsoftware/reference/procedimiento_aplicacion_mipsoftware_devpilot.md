---
title: "Procedimiento de aplicación de MIPSoftware para DevPilot Local"
doc_id: "MIPS-REF-PROCEDIMIENTO-DEVPILOT"
doc_type: "reference"
version: "0.1.0"
status: "reviewed"
owner: "AI_agents / MIPSoftware"
scope: "devpilot-adoption"
created: "2026-06-01"
updated: "2026-06-01"
related_documents:
  - "MIPS-DOC-003"
  - "MIPS-DOC-014"
  - "MIPS-DOC-016"
  - "MIPS-DOC-017"
---

# Procedimiento de aplicación de MIPSoftware para DevPilot Local

## 1. Objetivo

Definir cómo aplicar **MIPSoftware** como estándar oficial de trabajo en la creación de **DevPilot Local / Agent-assisted SDLC personal**, una herramienta propia para gestionar el ciclo de vida completo del software mediante asistencia de agentes.

## 2. Principio operativo

DevPilot Local no debe comenzar como “código primero”. Debe comenzar como un proyecto gobernado por MIPSoftware:

```text
MIPSoftware define el proceso.
MIASI define la extensión inteligente.
DevPilot Local implementa, automatiza y valida ambos modelos.
```

## 3. Fase 0 — Apertura formal del proyecto

### Entradas

- MIPSoftware `reviewed`.
- MIASI `approved`.
- Alcance inicial de DevPilot Local.
- Repositorio base del proyecto AI_agents.

### Artefactos obligatorios

- `product_vision.md`
- `business_case.md`
- `stakeholder_map.md`
- `mvp_scope.md`
- `checklist_pre_code.md`

### Gate

El proyecto no pasa a requerimientos si no existe un problema claro, usuario primario, alcance MVP y criterio de éxito.

## 4. Fase 1 — Producto y alcance MVP

DevPilot Local debe iniciar como MVP local-first, no como plataforma completa.

### Alcance MVP recomendado

- `devpilot init-project`
- `devpilot checklist pre-code`
- `devpilot validate requirement`
- `devpilot validate adr`
- `devpilot validate security`
- `devpilot miasi-required`
- `devpilot readiness-check`

### Fuera de alcance inicial

- SaaS multiusuario.
- Automatización destructiva.
- Despliegue cloud obligatorio.
- Integraciones pagas obligatorias.
- Agentes que modifiquen repositorios sin aprobación.

## 5. Fase 2 — Requerimientos

### Artefactos

- `requirements_specification.md`
- `user_story.md`
- `use_case.md`
- `acceptance_criteria.md`
- `traceability_matrix.md`

### Gate

Todo requerimiento debe ser verificable, priorizado y trazable a un objetivo de producto.

## 6. Fase 3 — Arquitectura

### Artefactos

- `architecture_document.md`
- `c4_context.md`
- `c4_container.md`
- `c4_component.md`
- `adr_template.md`
- `architecture_risk_log.md`

### Arquitectura inicial sugerida

```text
CLI / futura UI
  ↓
DevPilot Core
  ↓
Project Workspace
  ↓
Validators
  ├─ TemplateValidator
  ├─ ChecklistValidator
  ├─ SchemaValidator
  ├─ MIASIActivationDetector
  └─ ReadinessEvaluator
  ↓
Reports / JSON / Markdown / JSONL
```

## 7. Fase 4 — Activación MIASI

MIASI se activa obligatoriamente porque DevPilot Local es una plataforma agent-assisted.

### Artefactos MIASI mínimos

- Agent Card.
- Tool Card.
- Policy Card.
- Eval Card.
- Human Approval Card.
- Observability Card.

### Gate

No se implementan agentes ejecutores sin dry-run, policy gate, trazas y evaluación offline.

## 8. Fase 5 — Seguridad

### Artefactos

- `security_threat_model.md`
- `privacy_assessment.md`
- `security_test_plan.md`
- `vulnerability_register.md`

### Reglas

- Dry-run por defecto.
- No ejecutar comandos destructivos.
- No almacenar secretos reales.
- No exponer tokens en logs.
- Validar rutas antes de leer/escribir archivos.
- Toda acción de escritura debe registrarse.

## 9. Fase 6 — Testing y quality gates

### Pruebas mínimas

- unit tests de validadores;
- integration tests de comandos CLI;
- snapshot tests de reportes;
- security tests sobre rutas y secretos;
- evals MIASI para agentes si se incorpora LLM/local model;
- pruebas herméticas sin API keys reales.

## 10. Fase 7 — CI/CD y release

### Reglas

- Todo PR/MR debe ejecutar tests.
- Todo release debe tener changelog.
- Todo artefacto debe ser trazable.
- Debe existir rollback documentado.
- No se publican builds con quality gates fallidos.

## 11. Fase 8 — Observabilidad y operación

### Señales mínimas

- logs estructurados;
- trazas JSONL;
- reportes Markdown/JSON;
- eventos de validación;
- errores normalizados;
- resumen de readiness.

## 12. Roadmap por sprints

| Sprint | Objetivo | Entregables |
|---|---|---|
| 1 | Inicialización y estructura | `devpilot init-project`, estructura de proyecto, plantillas base. |
| 2 | Validadores documentales | validación de product vision, requirement, ADR y API contract. |
| 3 | Checklists y readiness | `checklist pre-code`, `readiness-check`, reportes JSON/Markdown. |
| 4 | Integración MIASI | detector MIASI, Agent Card, Tool Card, Policy Card, Eval Card. |
| 5 | Seguridad y trazas | threat model, secret scan básico, trazas JSONL, reportes auditables. |
| 6 | CI local | pytest, quality gates, release local, documentación de operación. |

## 13. Criterio mínimo para iniciar código de DevPilot

Antes de programar el MVP deben existir:

- visión del producto;
- business case mínimo;
- stakeholders;
- alcance MVP;
- requerimientos iniciales;
- arquitectura C4 nivel 1 y 2;
- ADRs iniciales;
- threat model mínimo;
- estrategia de pruebas;
- decisión de activación MIASI;
- checklist pre-code en PASS.

## 14. Criterio de éxito del primer MVP

DevPilot Local será exitoso si puede tomar una carpeta de proyecto y producir:

- diagnóstico de artefactos faltantes;
- validación de schemas;
- ejecución de checklists;
- decisión de activación MIASI;
- reporte de readiness;
- trazas de validación;
- recomendaciones de próximos artefactos.
