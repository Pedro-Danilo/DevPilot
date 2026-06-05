---
title: ADR-0001 — Adoptar docs-as-code para MIPSoftware
doc_id: ADR-0001
doc_type: adr
version: 0.1.0
status: accepted
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
decision_status: accepted
---

# ADR-0001 — Adoptar docs-as-code para MIPSoftware

## Estado

Aceptado.

## Contexto

MIPSoftware debe convertirse en un estándar vivo, versionable y revisable. Los documentos aislados en formatos cerrados tienden a desactualizarse y no se integran naturalmente con revisión técnica, pull requests ni automatización futura.

## Decisión

Adoptar un enfoque docs-as-code: toda la documentación fuente vive en el repositorio, se escribe en Markdown, se versiona con Git, se revisa por pull request y puede validarse con herramientas automatizadas.

## Consecuencias positivas

- La documentación queda cerca del código y de los artefactos de ingeniería.
- Se habilitan diffs, revisión, trazabilidad y auditoría.
- Se facilita publicar en HTML/PDF/DOCX desde una fuente única.
- Se prepara la automatización futura con DevPilot Local.

## Consecuencias negativas o costos

- Requiere disciplina de mantenimiento.
- Exige convenciones de nombres, frontmatter y revisión.
- Puede requerir tooling futuro para validar enlaces, frontmatter y diagramas.

## Criterios de cumplimiento

- Todo documento debe tener frontmatter.
- Todo cambio importante debe pasar por revisión.
- Los documentos normativos deben incluir criterios PASS/FAIL.
- Los ADRs deben registrar decisiones relevantes.

## Relación con MIASI

MIASI ya adoptó un enfoque equivalente. MIPSoftware hereda esta práctica para el estándar general y MIASI queda como módulo especializado.

## Referencias

- ISO/IEC/IEEE 12207.
- arc42.
- Diátaxis.
- MIASI v1.0.0.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | ADR inicial. |
