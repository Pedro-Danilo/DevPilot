---
title: Plantilla — C4 Nivel 2 Contenedores
doc_id: MIPS-TPL-C4-CONTAINER
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-architecture
created: '2026-05-31'
updated: '2026-05-31'
---

# C4 Nivel 2 — Contenedores: [Nombre del sistema]

## Propósito

Describir las aplicaciones, servicios, bases de datos, workers y otros contenedores ejecutables/persistentes.

## Contenedores

| Contenedor | Responsabilidad | Tecnología | Datos | Riesgos | Observabilidad |
|---|---|---|---|---|---|
| Frontend |  |  |  |  |  |
| Backend API |  |  |  |  |  |
| Database |  |  |  |  |  |
| Worker |  |  |  |  |  |

## Diagrama Mermaid

```mermaid
flowchart TB
  FE[Frontend] --> API[Backend API]
  API --> DB[(Database)]
  API --> W[Worker]
```

## Contratos entre contenedores

| Origen | Destino | Protocolo | Contrato | Error handling |
|---|---|---|---|---|
|  |  | REST/Event/SQL |  |  |

## Criterios de revisión

- [ ] Cada contenedor tiene responsabilidad clara.
- [ ] No hay contenedor sin razón de existir.
- [ ] Contratos principales definidos.
- [ ] Datos y seguridad considerados.
