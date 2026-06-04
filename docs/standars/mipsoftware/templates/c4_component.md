---
title: Plantilla — C4 Nivel 3 Componentes
doc_id: MIPS-TPL-C4-COMPONENT
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: software-architecture
created: '2026-05-31'
updated: '2026-05-31'
---

# C4 Nivel 3 — Componentes: [Contenedor]

## Propósito

Describir componentes internos relevantes de un contenedor.

## Componentes

| Componente | Responsabilidad | Entrada | Salida | Dependencias | Pruebas |
|---|---|---|---|---|---|
| Controller/API |  |  |  |  |  |
| Application Service |  |  |  |  |  |
| Domain Model |  |  |  |  |  |
| Repository |  |  |  |  |  |

## Diagrama Mermaid

```mermaid
flowchart TB
  C[Controller] --> S[Application Service]
  S --> D[Domain Model]
  S --> R[Repository]
  R --> DB[(Database)]
```

## Riesgos internos

| Riesgo | Componente | Mitigación |
|---|---|---|
|  |  |  |

## Criterios de revisión

- [ ] Responsabilidades claras.
- [ ] Dependencias razonables.
- [ ] Lógica de dominio ubicada correctamente.
- [ ] Pruebas mínimas definidas.
