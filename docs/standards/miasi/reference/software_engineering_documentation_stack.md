---
title: "Stack documental para ingeniería profesional de software"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "software-engineering/documentation-stack"
created: "2026-05-31"
updated: "2026-05-31"
doc_type: "reference"
audience:
  - "arquitectos de software"
  - "ingenieros de sistemas"
  - "responsables de DevPilot Local"
  - "responsables de calidad, seguridad y operación"
related_documents:
  - "../10_auditoria_final_promocion_miasi_v1.md"
  - "../01_modelo_ingenieria_sistemas_agenticos.md"
  - "../03_agentic_sdlc.md"
---

# Stack documental para ingeniería profesional de software

## 1. Propósito

Este documento aclara que MIASI es un estándar especializado en **ingeniería de sistemas agénticos inteligentes**, no un reemplazo completo de una disciplina general de ingeniería de software.

Para construir aplicaciones de software profesionales, reales, industriales y orientadas a producción, se recomienda crear un modelo documental superior que cubra todo el ciclo de vida del software. MIASI debe vivir como una **extensión especializada** dentro de ese modelo.

## 2. Relación jerárquica recomendada

```text
Modelo profesional de ingeniería de software
  ├─ Gobierno del producto y estrategia
  ├─ Ingeniería de requerimientos
  ├─ Arquitectura de software y sistemas
  ├─ Diseño UX/API/Data
  ├─ Desarrollo y construcción
  ├─ Calidad y testing
  ├─ Seguridad y privacidad
  ├─ DevOps, CI/CD y release
  ├─ Operación, SRE y soporte
  ├─ Mantenimiento y evolución
  └─ MIASI — Ingeniería de sistemas agénticos inteligentes
```

## 3. Documentación mínima antes de programar una aplicación profesional

| Dominio | Documento recomendado | Propósito | Referencias base |
|---|---|---|---|
| Gobierno del producto | `00_product_vision.md` | Visión, problema, usuarios, objetivos, métricas de éxito. | Product management, Lean, OKR |
| Caso de negocio | `01_business_case.md` | Justificación, alcance, costos, riesgos, beneficios. | ISO 15288, gestión de producto |
| Stakeholders | `02_stakeholders_context.md` | Interesados, necesidades, restricciones, dependencias. | ISO 15288 |
| Requerimientos | `03_requirements_specification.md` | Requerimientos funcionales, no funcionales, restricciones y trazabilidad. | ISO/IEC/IEEE 29148 |
| Arquitectura | `04_software_architecture.md` | C4, decisiones arquitectónicas, vistas, trade-offs, atributos de calidad. | arc42, C4, ISO 25010 |
| ADRs | `adrs/` | Decisiones técnicas y racionales. | Architecture Decision Records |
| UX/UI | `05_ux_ui_model.md` | Personas, journeys, wireframes, flujos y criterios de usabilidad. | HCI, ISO 25010 |
| API | `06_api_contracts.md` | OpenAPI, errores, versionado, seguridad, compatibilidad. | REST/OpenAPI |
| Datos | `07_data_model_governance.md` | Modelo conceptual/lógico/físico, migraciones, privacidad y retención. | Data governance, privacy by design |
| Seguridad | `08_security_privacy_model.md` | Threat model, authn/authz, controles, secretos, privacidad. | NIST SSDF, OWASP SAMM, ASVS |
| Testing | `09_test_strategy.md` | Estrategia de pruebas, niveles, criterios, datos, automatización. | ISO/IEC/IEEE 29119 |
| DevOps | `10_ci_cd_release_model.md` | Pipelines, quality gates, versionado, artefactos, rollback. | NIST SSDF, SLSA |
| Operación | `11_operations_sre_runbook.md` | Monitoreo, alertas, incidentes, SLO/SLA, soporte. | SRE, OpenTelemetry |
| Mantenimiento | `12_maintenance_evolution.md` | Gestión de deuda técnica, refactor, roadmap y retiro. | ISO 12207 |
| Inteligencia/agentes | `13_miasi_extension.md` | Agentes, LLMs, RAG, memoria, tool calling, evaluación, AgentOps. | MIASI |

## 4. Qué cubre MIASI y qué no

| Área | MIASI la cubre | Observación |
|---|---:|---|
| Agentes IA | Sí | Núcleo del modelo. |
| RAG, memoria, tool calling | Sí | Cobertura profunda. |
| Evaluación de agentes | Sí | Cobertura profunda. |
| Seguridad de agentes | Sí | Secret management, policy-as-code, human approval, OWASP LLM. |
| Ingeniería de requerimientos general | Parcial | Requiere documento superior basado en ISO/IEC/IEEE 29148. |
| Arquitectura general de software | Parcial | MIASI aporta arquitectura agentic; falta arquitectura general del producto. |
| UX/UI | No | Debe documentarse fuera de MIASI. |
| Dominio de negocio | No | Debe documentarse por producto. |
| Datos transaccionales generales | Parcial | MIASI cubre memoria/RAG; no reemplaza gobierno de datos completo. |
| Seguridad web/app general | Parcial | Debe complementarse con OWASP ASVS/SAMM. |
| Testing general | Parcial | Debe complementarse con estrategia de testing general. |
| Operación/SRE general | Parcial | MIASI cubre AgentOps; no reemplaza SRE completo. |

## 5. Modelo documental recomendado para DevPilot Local

Antes de escribir código de DevPilot Local, crear:

```text
docs/devpilot/
  00_product_vision.md
  01_business_case.md
  02_stakeholders_context.md
  03_requirements_specification.md
  04_software_architecture.md
  05_domain_model.md
  06_data_model.md
  07_api_contracts.md
  08_security_privacy_model.md
  09_test_strategy.md
  10_ci_cd_release_model.md
  11_observability_operations_model.md
  12_agentic_extension_miasi.md
  13_mvp_backlog.md
  14_risk_register.md
  adrs/
  runbooks/
```

## 6. Criterio profesional

Un proyecto de software real no debería pasar a implementación si no tiene al menos:

1. visión del producto;
2. alcance del MVP;
3. stakeholders y usuarios;
4. requerimientos y criterios de aceptación;
5. arquitectura base;
6. modelo de datos;
7. modelo de seguridad y privacidad;
8. estrategia de pruebas;
9. CI/CD y release plan;
10. operación y soporte;
11. risk register;
12. ADRs iniciales;
13. extensión MIASI si usa agentes, LLMs, RAG o automatización inteligente.

## 7. Decisión

Para proyectos futuros, MIASI debe tratarse como **módulo especializado obligatorio** cuando una aplicación incorpore agentes de IA, LLMs, RAG, memoria o herramientas inteligentes. Para aplicaciones de software generales, debe crearse un estándar documental superior que gobierne el ciclo de vida completo del software.
