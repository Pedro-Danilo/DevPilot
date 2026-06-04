---
title: "Procedimiento de adopción de MIPSoftware en DevPilot Local"
doc_id: "DEVPL-REF-001"
status: "reviewed"
version: "0.2.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "PRECODE"
updated: "2026-06-04"
approval: "ready_for_owner_approval"
---

# Procedimiento de adopción de MIPSoftware en DevPilot Local

## 1. Propósito

Este documento define cómo DevPilot Local aplica MIPSoftware y MIASI como estándares oficiales de trabajo durante la fase pre-code y durante los sprints funcionales posteriores.

## 2. Regla principal

DevPilot Local no debe avanzar a implementación funcional fuerte si no existe evidencia documental mínima aprobada para producto, requerimientos, arquitectura, seguridad, calidad, operación y activación MIASI.

## 3. Baseline pre-code

| Bloque | Estado actual esperado | Comentario |
|---|---|---|
| `00_product` | `approved` | Baseline de producto vigente. |
| `01_requirements` | `approved` | Baseline de requerimientos vigente, con cambios controlados. |
| `02_architecture` | `reviewed` | Pendiente de aprobación owner de ADR-0002..ADR-0009. |
| `03_security` | `draft` | Siguiente sprint. |
| `04_quality` | `draft` | Pendiente. |
| `05_operations` | `draft` | Pendiente. |
| `06_miasi` | `draft` | Pendiente de desarrollo aplicado. |

## 4. Estándares dentro de `docs/`

La copia local de MIPSoftware y MIASI se conserva en:

```text
docs/estándares/mipsoftware/
docs/estándares/miasi/
```

La decisión formal está documentada en:

```text
docs/reference/standards_inside_docs_decision.md
```

## 5. Procedimiento operacional

1. Abrir proyecto formal en `D:\Projects\DevPilot_Local`.
2. Mantener estándares locales versionados dentro de `docs/estándares/`.
3. Crear artefactos pre-code por sprints.
4. Auditar cada bloque contra MIPSoftware y MIASI.
5. Registrar decisiones arquitectónicas mediante ADR.
6. Mantener trazabilidad producto → requerimiento → arquitectura → prueba → gate.
7. Ejecutar validaciones locales (`pytest`, `readiness-check`, `miasi-required`).
8. Promover documentos a `approved` solo cuando no existan brechas críticas.
9. Mantener cambios controlados hasta cerrar toda la baseline pre-code.
10. Iniciar implementación funcional fuerte solo después del gate pre-code.

## 6. Próximo gate

El próximo gate es aprobar `02_architecture` o registrar sus pendientes antes de avanzar a `03_security`.

