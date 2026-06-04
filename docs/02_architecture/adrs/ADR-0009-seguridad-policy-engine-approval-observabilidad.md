---
title: "ADR-0009 — Seguridad por Policy Engine, approvals y observabilidad"
doc_id: "DEVPL-ADR-0009"
status: "proposed"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-02"
approval: "pending_owner_decision"
---
# ADR-0009 — Seguridad por Policy Engine, approvals y observabilidad

## Estado

Proposed.

## Contexto

DevPilot trabajará con repositorios, filesystem, posibles patches, modelos, herramientas, secretos y eventualmente interfaces desktop/web. La seguridad debe ser un componente arquitectónico central, no una tarea posterior.

## Decisión

Adoptar Policy Engine como punto de control transversal para filesystem, Git, patches, agentes, proveedores LLM, secretos, costos y aprobaciones. Toda acción sensible debe ejecutarse en dry-run, producir evidencia y requerir aprobación humana cuando tenga side effects.

## Consecuencias positivas

- Reduce riesgo de acciones destructivas.
- Hace auditable cada decisión.
- Permite extender controles a desktop/web y agentes.
- Centraliza reglas de seguridad.

## Consecuencias negativas / riesgos

- Requiere diseño cuidadoso de policies.
- Puede ralentizar flujos si las aprobaciones son excesivas.
- Requiere UX clara para explicar bloqueos.

## Controles obligatorios

- Deny by default.
- Path sandbox.
- Secret redaction.
- Cost budget.
- Approval queue.
- Logs/traces por acción.
- Tests de seguridad.

## Criterios de aceptación

- Una acción de escritura sin aprobación falla.
- Rutas fuera del workspace fallan.
- Secretos se redactan en reportes.
- Todo bloqueo explica causa y corrección.
