---
title: "Registro de decisión de promoción MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
related_docs:
  - "../09_auditoria_final_miasi.md"
---
# Registro de decisión de promoción MIASI

## 1. Decisión

MIASI queda promovido a:

```text
Estado: reviewed
Baseline: MIASI v1.0.0
Uso permitido: estándar profesional de trabajo para iniciar DevPilot Local
```

Queda promovido a `approved` v1.0.0 dentro de su alcance específico: ingeniería de sistemas agénticos inteligentes. Esta promoción no equivale a certificación industrial externa ni sustituye un estándar general de ingeniería de software.

## 2. Justificación

La documentación cumple los requisitos mínimos para guiar proyectos agénticos profesionales:

- modelo rector;
- arquitectura de referencia;
- Agentic SDLC;
- estándares técnicos;
- plantillas;
- checklists;
- controles;
- política de datos;
- política de referencias;
- incidentes/SLO/SLA;
- schemas iniciales;
- contrato CLI DevPilot;
- modelo lógico DevPilot;
- auditoría final.

## 3. Condiciones para v1.0

MIASI podrá promoverse a `approved` cuando:

1. DevPilot Local implemente al menos `init-project`, `new-agent` y `readiness-check`.
2. Las plantillas `Agent Card`, `Tool Card`, `Eval Card` y `Policy Card` sean validadas por CLI.
3. El pipeline documental valide links, frontmatter, schemas y Mermaid.
4. Al menos un proyecto aplicado use MIASI de extremo a extremo.
5. Se registre una retrospectiva técnica con ajustes incorporados.

## 4. Riesgo aceptado

Se acepta iniciar DevPilot Local con brechas no bloqueantes:

- tutoriales/how-to/explanations aún mínimos;
- schemas sin validador ejecutable;
- trazabilidad LAB por bloques;
- supply chain avanzado como roadmap.

Estas brechas no afectan la capacidad de MIASI para operar como estándar inicial de ingeniería.


## 5. Alcance frente a ingeniería de software general

MIASI no reemplaza un marco completo de ingeniería profesional de software. Debe integrarse como extensión especializada dentro de un stack documental más amplio que cubra producto, negocio, requerimientos, arquitectura general, UX, datos, seguridad, testing, DevOps, operación y mantenimiento.

Referencia complementaria: `software_engineering_documentation_stack.md`.
