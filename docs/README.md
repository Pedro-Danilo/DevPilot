---
title: "DevPilot Local — Documentación docs-as-code"
doc_id: "DEVPL-DOCS-README"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
---

# DevPilot Local — Documentación docs-as-code

## 1. Propósito

Esta carpeta contiene la documentación viva del proyecto **DevPilot Local / Agent-assisted SDLC personal**. La documentación forma parte del producto: debe poder versionarse, revisarse, auditarse y convertirse progresivamente en validaciones ejecutables.

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

Se decidió incluir MIPSoftware y MIASI dentro de `docs/standards/` para que el proyecto tenga una fuente local, versionada y auditable de los estándares que lo gobiernan.

La decisión formal se documenta en:

```text
docs/reference/standards_inside_docs_decision.md
```

## 4. Estados documentales

| Estado | Significado |
|---|---|
| `draft` | Documento incompleto o en elaboración. |
| `reviewed` | Documento revisado técnicamente, pendiente de aprobación owner o dependencias. |
| `approved` | Documento aprobado como baseline vigente. |
| `deprecated` | Documento reemplazado o no vigente. |

## 5. Estado pre-code final

| Bloque | Estado |
|---|---|
| `00_product` | approved |
| `01_requirements` | approved |
| `02_architecture` | approved |
| `03_security` | approved |
| `04_quality` | approved |
| `05_operations` | approved |
| `06_miasi` | approved |
| `checklists/checklist_pre_code.md` | approved |
| `precode_audit_report.md` | approved |
| `precode_baseline_decision.md` | approved |

## 6. Decisión de baseline

La fase pre-code queda cerrada y DevPilot Local queda habilitado para iniciar el primer sprint funcional fuerte con alcance controlado:

```text
FUNC-SPRINT-01 — Core CLI de validación MIPSoftware/MIASI
```

## 7. Regla de trabajo

Ningún sprint funcional debe habilitar acciones destructivas, agentes ejecutores, APIs externas con costo o escritura sobre repos reales sin pasar por Policy Engine, SecretGuard, CostGuard, trazas y aprobación humana cuando aplique.
