---
title: "DevPilot Local — Decisión de baseline pre-code"
doc_id: "DEVPL-PRECODE-BASELINE-DECISION"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-07"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
---

# DevPilot Local — Decisión de baseline pre-code

## 1. Decisión

Se aprueba la baseline documental pre-code de **DevPilot Local / Agent-assisted SDLC personal**.

```text
Estado: APPROVED
Fase pre-code: CLOSED
Siguiente fase: Functional MVP — Sprint 01
Uso autorizado: iniciar implementación funcional fuerte con alcance controlado
```

## 2. Alcance de la aprobación

Esta decisión aprueba la documentación de ingeniería necesaria para iniciar desarrollo funcional:

- producto y negocio;
- requerimientos;
- arquitectura;
- seguridad y privacidad;
- calidad y pruebas;
- observabilidad y operación;
- activación MIASI;
- checklist pre-code.

## 3. Límites de la aprobación

Esta aprobación **no** significa que DevPilot Local ya sea production-ready. La aprobación cubre planeación, diseño y readiness pre-code. La implementación debe demostrar mediante pruebas, trazas y quality gates que el sistema cumple lo documentado.

## 4. Condiciones para el primer sprint funcional

El primer sprint funcional debe respetar estas condiciones:

| Condición | Regla |
|---|---|
| Alcance | CLI local + validadores + reportes + checklist. |
| Seguridad | Sin acciones destructivas. |
| Agentes | No habilitar agentes ejecutores todavía; máximo generación/auditoría en dry-run. |
| APIs externas | No obligatorias; si se usan más adelante, deben pasar por CostGuard/SecretGuard. |
| Persistencia | Reportes JSON/Markdown; JSONL opcional inicial; SQLite se diseña antes de implementar estado operativo. |
| Git | Solo lectura al inicio funcional. |
| Aprobación humana | Obligatoria para escritura, patches, costos externos o cambios de policies. |
| Trazabilidad | Todo comando funcional debe producir evidencia. |

## 5. Declaración de readiness

```text
DevPilot Local queda listo para iniciar el primer sprint funcional fuerte.
El primer objetivo será convertir la baseline documental en validadores ejecutables.
```

## 6. Próximo hito

```text
FUNC-SPRINT-01 — Core CLI de validación MIPSoftware/MIASI
```
