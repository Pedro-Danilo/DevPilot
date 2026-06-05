---
title: ADR-0002 — Adoptar Markdown como formato fuente base
doc_id: ADR-0002
doc_type: adr
version: 0.1.0
status: accepted
owner: AI_agents / MIPSoftware
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
decision_status: accepted
---

# ADR-0002 — Adoptar Markdown como formato fuente base

## Estado

Aceptado.

## Contexto

MIPSoftware necesita documentos legibles, editables, compatibles con Git, fáciles de revisar y exportables a otros formatos.

## Decisión

Usar Markdown como formato fuente principal para documentos, plantillas, checklists y ADRs. Cuando se requieran validadores, se usarán schemas JSON complementarios.

## Consecuencias positivas

- Markdown es simple, portable y compatible con repositorios.
- Permite diagramas Mermaid, tablas, código y frontmatter YAML.
- Facilita publicación futura en sitios estáticos o PDF.

## Consecuencias negativas o costos

- Markdown no reemplaza diagramación avanzada cuando se requiera material de presentación.
- Requiere convenciones para evitar documentos inconsistentes.

## Criterios de cumplimiento

- Todo archivo Markdown debe tener título claro.
- Documentos normativos deben tener frontmatter YAML.
- Diagramas deben preferir Mermaid cuando sea suficiente.

## Relación con MIASI

MIASI usa Markdown y Mermaid; MIPSoftware mantiene compatibilidad para poder referenciar e integrar sus documentos.

## Referencias

- Diátaxis.
- arc42.
- C4 Model.
- MIASI v1.0.0.

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | ADR inicial. |
