---
title: Plantilla — C4 Nivel 1 Contexto
doc_id: MIPS-TPL-C4-CONTEXT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-architecture
created: '2026-05-31'
updated: '2026-05-31'
---

# C4 Nivel 1 — Contexto: [Nombre del sistema]

## Propósito

Mostrar el sistema como caja negra dentro de su entorno.

## Personas y sistemas externos

| Elemento | Tipo | Relación con el sistema | Datos intercambiados |
|---|---|---|---|
| Usuario final | persona | usa |  |
| Sistema externo | sistema | integra |  |

## Diagrama Mermaid

```mermaid
flowchart LR
  U[Usuario] --> S[Sistema]
  S --> EXT[Sistema externo]
  S --> DB[(Datos propios)]
```

## Límites

- Dentro del sistema:
- Fuera del sistema:

## Riesgos de contexto

| Riesgo | Impacto | Mitigación |
|---|---|---|
|  |  |  |

## Criterios de revisión

- [ ] Personas identificadas.
- [ ] Sistemas externos identificados.
- [ ] Límites explícitos.
- [ ] Datos sensibles identificados.
- [ ] MIASI evaluado si hay IA/agentes.
