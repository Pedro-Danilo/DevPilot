---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R07_132
title: "Backlog R7 — Agentes/handoffs delimitados"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Backlog R7 — Agentes/handoffs delimitados

## Resultado y gate de ola

**Ola R7 — Agentes/handoffs delimitados.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R7-01 | P0 | Audit/Threat model de tool calling y handoffs | Inventario de tools/roles, workspace scopes, deny by default y matriz de authority aprobada |
| MP131-R7-02 | P0 | Agent review/enrichment para Requirements/Architecture/Code/Test/Release | Findings tipados+trace, no source write/approval; evidencia de 2+ roles distintos |
| MP131-R7-03 | P0 | Agent orchestrator bounded: memoria, retries, cancelación, costes, human handoff | Loops limitados; sin duplicar tool execution; resume tras restart y revocación de sesión |
| MP131-R7-04 | P1 | Agentes Pilot B: inventario, ventas, borradores comerciales | Recomendaciones con fuentes/datos; no publicación, compra, stock/price changes sin permiso y confirmación |
| MP131-R7-05 | P0 | Evals adversariales de agentes (prompt injection, exfiltration, cross-workspace) | Salidas contaminadas rechazadas; acciones sin autorización bloqueadas; logs redactados |
| MP131-R7-06 | P2 | MCP/conectores como extensión opcional separada | Contract de server trust/tool allowlist/consent, disabled-by-default; no dependencia de Pilot B básico |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R7-07 | P0 | Agent/Tool Contracts MIASI por autonomía y risk | Scopes, costs, cancellation, human handoff y memoria minimizada |
| MP132-R7-08 | P1 | Read-only-first agents con capability eligibility y tests adversariales | No source write/stock change sin approval, traces en Pilot B |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

---

## Enmienda programática post-R02-06 · 187

MIASI debe aplicarse a componentes inteligentes **del producto** (Agent/Tool/Memory/Autonomy), con Agent/Tool/Eval Cards y políticas por riesgo; la presencia de LLM en el flujo de autoría de DevPilot no hace obligatorio MIASI para módulos convencionales. Handoffs y reviews read-only se integran como sugerencias semánticas sin permisos automáticos; el incremento agentic de Pilot B exige pruebas adversariales y aceptación del resultado funcional integrado, sin mutaciones de stock/precio/publicidad sin autorización.

---

## Enmienda 188 — criterios prospectivos R07

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Owner de esta ola:** Agentes aplican crítica/repair y acciones delimitadas, con permisos, dry-run, budget e intervención Owner solo en actos sensibles. No reintroducir agentes como publishers ni autorizar escritura no gobernada.
