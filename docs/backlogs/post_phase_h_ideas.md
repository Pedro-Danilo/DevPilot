---
title: "Backlog post-Fase H — Hardening industrial"
doc_id: "DEVPL-BACKLOG-POST-H-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "POST-FASE-H"
updated: "2026-06-19"
approval: "implemented-initial"
source_closure: "docs/audits/phase_h_advanced_capabilities_closure.md"
---

# Backlog post-Fase H — Hardening industrial

## Estado

Backlog semilla aprobado para iniciar trabajo post-Fase H.

## Propósito

Este backlog semilla prioriza el trabajo posterior a Fase H. Su objetivo no es agregar autonomía sin control, sino endurecer DevPilot hacia una aplicación más industrial, operable y verificable.

## Priorización inicial

| Prioridad | ID | Tema | Resultado esperado | Riesgo mitigado |
|---|---|---|---|---|
| P0 | POST-H-001 | Industrial hardening de tests y contratos | Reducir regresiones y desincronización documental | Fallos recurrentes en suites grandes |
| P0 | POST-H-002 | Maturity dashboard local | Mostrar production-ready vs implemented-initial vs experimental | Sobreclaiming de madurez |
| P0 | POST-H-003 | Policy/MIASI semantic validator ampliado | Validar consistencia tool-policy-agent más allá de schema | Tools/policies decorativos |
| P1 | POST-H-004 | Observability retention local | Retención, rotación y consulta de trazas/reportes | Pérdida o exceso de evidencia |
| P1 | POST-H-005 | RAG groundedness evals | Medir citas, fuentes y respuesta sin evidencia | Respuestas no trazables |
| P1 | POST-H-006 | UI/API industrial shell | Fortalecer Web UI/API local sin cloud | Producto visual incompleto |
| P1 | POST-H-007 | Approval/RBAC hardening | Sesiones locales, actores, permisos y auditoría | Actor spoofing o permisos débiles |
| P2 | POST-H-008 | Audit/compliance packs firmables | Firma/cifrado opcional local | Integridad de evidencia compartida |
| P2 | POST-H-009 | Connector sandbox avanzado | Read-only fuerte, allowlists y replay tests | Conectores inseguros |
| P3 | POST-H-010 | Remote runners ADR-2 | Diseño de ejecución remota segura sin activarla | Apertura prematura de superficie remota |

## Reglas de ejecución post-H

- No habilitar remote execution real sin ADR nueva.
- No habilitar cloud ni APIs externas por defecto.
- No convertir compliance packs en certificaciones externas sin mapping formal.
- Mantener `dry-run` como valor por defecto para acciones sensibles.
- Mantener `pytest -q`, `validate all` y `quality-gate` como cierre mínimo.
- Todo nuevo módulo debe declarar contratos, tests, MIASI, documentación y criterios PASS/BLOCK.

## Veredicto

La prioridad inmediata es hardening y reducción de regresiones, no expansión de autonomía.
