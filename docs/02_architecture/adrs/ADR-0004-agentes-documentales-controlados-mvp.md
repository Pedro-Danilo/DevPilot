---
title: "ADR-0004 — Agentes documentales controlados desde MVP"
doc_id: "DEVPL-ADR-0004"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-03"
updated: "2026-06-04"
accepted_by: "Ordóñez"
accepted_at: "2026-06-04"
acceptance_scope: "SPRINT-PRECODE-03 architecture baseline"
---
# ADR-0004 — Agentes documentales controlados desde MVP

## Contexto

El valor diferencial de DevPilot no debe limitarse a revisar existencia de documentos. La plataforma debe ayudar a construir y auditar documentación pre-code desde una idea inicial, manteniendo seguridad y control.

## Decisión

Incluir desde MVP agentes documentales controlados:

- `PreCodeDocumentationAgent` para proponer borradores.
- `DocumentationAuditAgent` para detectar brechas y contradicciones.

Ambos operan en dry-run, sin API externa obligatoria, sin aprobación automática y con separación entre recomendaciones agentic y gates determinísticos.

## Consecuencias

- El MVP gana valor real para el usuario.
- MIASI se activa desde el inicio.
- Se requiere diseñar cards, policies, evals y trazas para agentes.
