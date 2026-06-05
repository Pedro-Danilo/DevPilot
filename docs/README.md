---
title: "DevPilot Local — Documentación docs-as-code"
doc_id: "DEVPL-DOCS-README"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
---
 
# DevPilot Local — Documentación docs-as-code

## 1. Propósito

Esta carpeta contiene la documentación viva del proyecto **DevPilot Local / Agent-assisted SDLC personal**. La documentación forma parte del producto, no es un anexo decorativo. Todo artefacto relevante debe poder versionarse, revisarse, auditarse y convertirse progresivamente en validaciones ejecutables.

DevPilot Local aplica dos estándares internos:

- **MIPSoftware — Modelo de Ingeniería Profesional de Software**, estándar general para el ciclo de vida de software.
- **MIASI — Modelo de Ingeniería de Sistemas Agénticos Inteligentes**, extensión obligatoria cuando el sistema usa IA, agentes, LLMs, RAG, memoria, tool calling o automatización inteligente.

## 2. Estructura principal

```text
docs/
  00_product/          # visión, caso de negocio, alcance, roadmap
  01_requirements/     # requerimientos, historias, casos de uso, aceptación, trazabilidad
  02_architecture/     # arquitectura, C4, ADRs
  03_security/         # threat model y privacidad
  04_quality/          # estrategia de pruebas
  05_operations/       # observabilidad y runbook
  06_miasi/            # artefactos MIASI aplicados a DevPilot
  checklists/          # checklists del proyecto
  standards/           # copia versionada actual de MIPSoftware y MIASI
  reference/           # decisiones y procedimientos de adopción
```

## 3. Decisión sobre estándares dentro de `docs/`

Se decidió incluir MIPSoftware y MIASI dentro de `docs/standards/` para que el proyecto tenga una fuente local, versionada y auditable de los estándares que lo gobiernan. Esta decisión es pertinente para un enfoque docs-as-code, siempre que se mantengan reglas claras de sincronización, ownership y referencia.

La decisión formal se documenta en:

```text
docs/reference/standards_inside_docs_decision.md
```

## 4. Estados documentales

| Estado | Significado |
|---|---|
| `draft` | Documento incompleto o en elaboración. |
| `reviewed` | Documento revisado técnicamente, pendiente de aprobación owner o de dependencias. |
| `approved` | Documento aprobado como baseline vigente. |
| `deprecated` | Documento reemplazado o no vigente. |

## 5. Regla de trabajo

Ningún sprint funcional fuerte debe avanzar si sus documentos pre-code obligatorios están incompletos, no trazados o sin revisión.



## 8. Nota sobre la ruta `docs/standards/`

La carpeta física actual de estándares es:

```text
docs/standards/
```

La grafía correcta en inglés sería `docs/standards/`. Se conserva temporalmente la ruta existente para evitar una migración estructural durante la fase pre-code. La decisión queda documentada como brecha menor controlada; si los validadores, scripts o empaquetado lo requieren, se recomienda migrar en una tarea dedicada, con patch explícito, actualización de referencias y verificación de enlaces internos.


## 8. Estado pre-code al cierre de SPRINT-PRECODE-05

| Bloque | Estado |
|---|---|
| `00_product` | approved |
| `01_requirements` | approved |
| `02_architecture` | approved |
| `03_security` | approved |
| `04_quality` | reviewed |
| `05_operations` | reviewed |
| `06_miasi` | draft / pendiente de desarrollo específico |

Siguiente paso recomendado: revisar y aprobar `04_quality` y `05_operations`, y luego avanzar a `SPRINT-PRECODE-06 — MIASI aplicado a DevPilot Local`.
