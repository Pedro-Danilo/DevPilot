---
title: "MIPSoftware — Modelo de Ingeniería Profesional de Software"
doc_id: "MIPS-DOC-INDEX"
doc_type: "index"
version: "0.3.1"
status: "reviewed"
owner: "AI_agents / MIPSoftware"
audience:
  - "arquitectos de software"
  - "desarrolladores"
  - "líderes técnicos"
  - "auditores internos"
  - "futuros agentes DevPilot Local"
scope: "software-engineering-model"
created: "2026-05-31"
updated: "2026-06-01"
related_models:
  - "MIASI v1.0.0 — módulo especializado para sistemas inteligentes/agénticos"
---

# MIPSoftware — Modelo de Ingeniería Profesional de Software

## 1. Propósito

**MIPSoftware** es el estándar general de ingeniería profesional de software del emprendimiento. Su objetivo es guiar, controlar y auditar el ciclo de vida completo de cualquier aplicación: desde idea, producto, negocio, requerimientos, arquitectura y diseño, hasta implementación, pruebas, seguridad, CI/CD, operación, mantenimiento, evolución y retiro.

MIPSoftware no reemplaza a **MIASI - Modelo de ingeniería de sistemas agénticos inteligentes**. MIASI queda integrado como extensión especializada obligatoria cuando el sistema incorpora IA, agentes, LLMs, RAG, memoria, tool calling, automatización inteligente, acciones asistidas por modelos o comportamiento adaptativo.

```text
MIPSoftware
  gobierna el ciclo de vida completo de cualquier software profesional.

MIASI
  extiende MIPSoftware cuando el sistema incluye IA, agentes, LLMs,
  RAG, memoria, tool calling o automatización inteligente.
```

## 2. Estado documental

| Campo | Valor |
|---|---|
| Estado operativo | `reviewed` |
| Veredicto | `approved with exceptions` |
| Versión operativa | `0.3.1` |
| Uso permitido | Estándar profesional de trabajo para DevPilot Local y proyectos reales controlados |
| Promoción futura | `approved v1.0.0` después de validación end-to-end en un proyecto real |

## 3. Índice maestro

| Documento | Ubicación | Propósito |
|---|---|---|
| Manifiesto | `00_manifesto.md` | Principios rectores de ingeniería profesional de software. |
| Documento rector | `01_modelo_ingenieria_profesional_software.md` | Modelo general, dominios, madurez y criterios normativos. |
| Ciclo de vida | `02_ciclo_vida_software.md` | Proceso completo desde idea hasta retiro. |
| Producto, negocio y stakeholders | `03_producto_negocio_stakeholders.md` | Visión, problema, negocio, usuarios, MVP y trazabilidad inicial. |
| Ingeniería de requerimientos | `04_ingenieria_requerimientos.md` | Requerimientos verificables, aceptables y trazables. |
| Arquitectura de software | `05_arquitectura_software.md` | Drivers, C4, ADRs, vistas y patrones arquitectónicos. |
| Dominio, datos e integraciones | `06_dominio_datos_integraciones.md` | Dominio, persistencia, APIs, eventos, webhooks e integraciones. |
| UX/UI y accesibilidad | `07_ux_ui_accesibilidad.md` | Flujos, pantallas, formularios, accesibilidad y design system mínimo. |
| Calidad, testing y verificación | `08_calidad_testing_verificacion.md` | Estrategia de pruebas, quality gates y release readiness. |
| Seguridad, privacidad y compliance | `09_seguridad_privacidad_compliance.md` | Security by design, threat model, secretos, privacy y security gates. |
| DevOps, CI/CD y supply chain | `10_devops_ci_cd_supply_chain.md` | CI/CD, release, rollback, SBOM, provenance y artefactos. |
| Observabilidad, operación y SRE | `11_observabilidad_operacion_sre.md` | Logs, métricas, trazas, SLO/SLA, incidentes, backup y restore. |
| Mantenimiento, evolución y retiro | `12_mantenimiento_evolucion_retiro.md` | Deuda técnica, mantenimiento, deprecación, migración y retiro. |
| Extensión MIASI | `13_extension_miasi.md` | Activación formal de MIASI dentro de MIPSoftware. |
| Plantillas, checklists y schemas | `14_plantillas_checklists_schemas_operativos.md` | Activos reutilizables para operación manual y automatización futura. |
| Auditoría final | `15_auditoria_final_mipsoftware.md` | Veredicto inicial de promoción del estándar. |
| Auditoría post-repo 77 | `16_auditoria_post_repo77_mipsoftware.md` | Auditoría de integración sobre el repo actualizado y correcciones menores. |

## 4. Carpetas operativas

| Carpeta | Propósito |
|---|---|
| `templates/` | Plantillas Markdown reutilizables para los artefactos principales del ciclo de vida. |
| `checklists/` | Checklists de readiness y quality gates. |
| `schemas/` | JSON Schemas iniciales para validación futura por DevPilot Local. |
| `adrs/` | Decisiones arquitectónicas y documentales del estándar. |
| `reference/` | Referencias internas: promoción, excepciones, backlog de validación y procedimiento de adopción. |
| `tutorials/` | Tutoriales futuros orientados a aprendizaje paso a paso. |
| `how_to/` | Guías operativas futuras para ejecutar tareas concretas. |
| `explanations/` | Explicaciones conceptuales futuras. |

## 5. Criterios mínimos antes de iniciar código

Un proyecto no trivial no debe iniciar implementación significativa si no existe evidencia mínima de:

1. visión de producto;
2. problema y oportunidad;
3. stakeholders;
4. alcance MVP;
5. requerimientos verificables;
6. arquitectura mínima;
7. modelo de dominio/datos si hay persistencia;
8. estrategia de pruebas;
9. threat model mínimo;
10. decisión formal sobre si MIASI aplica.

## 6. Activación de MIASI

MIASI se activa cuando el sistema incluye:

- LLMs;
- agentes IA;
- RAG;
- memoria;
- tool calling;
- generación automática de contenido;
- decisiones asistidas por IA;
- automatización inteligente;
- acciones con herramientas;
- comportamiento adaptativo.

## 7. Próximo uso previsto

El primer uso formal de MIPSoftware será **DevPilot Local / Agent-assisted SDLC personal**. Ese proyecto debe validar el modelo mediante:

- `devpilot init-project`;
- `devpilot checklist pre-code`;
- `devpilot validate requirement`;
- `devpilot validate architecture`;
- `devpilot validate security`;
- `devpilot readiness-check`;
- `devpilot miasi-required`.

## 8. Referencias internas clave

- `reference/final_promotion_decision.md`
- `reference/mipsoftware_exception_register.md`
- `reference/devpilot_validation_backlog.md`
- `reference/procedimiento_aplicacion_mipsoftware_devpilot.md`

## 9. Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | Estructura documental inicial. |
| 0.2.0 | 2026-05-31 | Integración de documentos MIPS-DOC-001 a MIPS-DOC-016. |
| 0.3.1 | 2026-06-01 | Auditoría repo 77, normalización de frontmatter, README consolidado y procedimiento de adopción DevPilot. |
