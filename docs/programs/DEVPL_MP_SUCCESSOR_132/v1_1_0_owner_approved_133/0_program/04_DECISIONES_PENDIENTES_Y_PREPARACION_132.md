---
doc_id: DEVPL-MP-SUCCESSOR-132-04_DECISIONES_PENDIENTES_Y_PREPARACION_132
title: "Matriz de preparación: qué falta antes de autorizar implementaciones"
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
---

# Matriz de preparación: qué falta antes de autorizar implementaciones

## 1. Estado verificable por documento de este paquete

| Grupo | Estado que puede aprobarse ahora | Completar/actualizar antes de implementar |
|---|---|---|
| Programa maestro y roadmap | `OWNER_APPROVED_PROGRAM` por decisión 133 | **Pendiente:** publicación gobernada en Source Registry vivo, verificando SHA y HEAD |
| 11 backlogs por ola | `OWNER_APPROVED_PROGRAM` para prioridades y AC iniciales; ítems individuales no iniciados | **Cada ítem**: audit-first live, Reuse/Delta Map, scope de sprint, tests, límites de costo y aprobación |
| ADR-001..008 | `OWNER_ACCEPTED` tras auditoría 133 de código y ADRs históricos | Antes del primer cambio: Reuse/Delta Map del HEAD vivo, schemas y pruebas; ADR-008 requiere gate Windows B |
| ADR-009 Agent/Tool Boundary | `OWNER_ACCEPTED` arquitectura de seguridad, activación de tools condicionada | Threat model, matriz exacta de tools y workspace permissions antes de R7 writes |
| ADR-010 External Trust | `OWNER_ACCEPTED_ARCHITECTURE / EXTERNAL_ACTIVATION_DEFERRED` | Egress/PII/legal/costo, secret refs, provider exacto, decisión Owner antes de cualquier llamada |
| ADR-011 UI State | `OWNER_ACCEPTED` decisión UI transversal | Mapa de superficies, source audit, pruebas browser/state y contratos UI antes de cambiar source |
| PESP/Catalog/Coverage | Especificación conceptual versionable | Extraer estándares vigentes de `.md`, profiles actuales, schemas reales y mínima vertical R1; confirmar aplicabilidad por proyecto |
| Publicación/FROZEN/Impact | Semántica de autoridad y estados | Resolver interacción real stores/Markdown/Source Registry/Git; compatibilidad con documentos FROZEN; migrations y tests |
| GenerationRoute/ModelCapability | Reglas D/L/E/fallback y capacidades | Auditar interfaces existentes, hardware real y dataset de evaluación; API external continúa denegada |
| Configuration Matrix | Dominios/scope/precedencia propuestos | Auditoría SettingsView, settings_service, endpoint RBAC/policy, storage; plan de migración; negatives |
| Project Layout | Contrato logical-path e implementación tardía | Resolver TechnologyCatalog, root policy, portabilidad por stack; no elegir stack durante Intake |
| Pilot B Charter | Negocio y gates verificables | Intake humano dentro de UI, dataset sintético, entorno aceptado, Owner aprueba límites y éxito |
| Matriz riesgos/deuda | Registro revisado por fuente | Refresh sobre HEAD que se modifique; ledger UX v1.32 es histórico y necesitará nueva adjudicación por reproducción |
| Git estrategia B | `OWNER_ACCEPTED_CONDITIONAL_PREFLIGHT` | Tracked/untracked/ignored, procesos, upstream, backups, rollback y pruebas Windows; sin traslado actual |

## 2. Orden mínimo de autorización futuro

`Aprobación 132 y G5 ratificado (actas Owner-133)` → `publicación gobernada de supersession/Source Registry sobre HEAD vivo` → `auditar y decidir worktree R0` → `ratificar compatibilidad focal de ADRs ya OWNER_ACCEPTED y completar contratos aplicables al primer delta` → `audit-first real/Reuse-Delta` → `proyectar y aprobar sprint + prompt (futuro, no aquí)` → `dry-run` → `execute/canary` → `evidencia Windows` → `Owner adjudication`.

Ningún componente que trate datos personales, coste o acciones mutativas se activa mediante cambio de UI/config sin threat model y policy aprobados. Si el audit-first revela `NO-OP` no crear bundle de implementación.

## 3. Criterios de GO / NO-GO programáticos

- **GO para aprobación conceptual:** fuentes verificadas, 66 ítems preservados, supersession explícita, contratos coherentes, pendientes y riesgos transparentes.
- **NO-GO para mutaciones automáticas hoy:** faltan orden/alcance de incremento, auditoría focal sobre HEAD vivo, preflight/migración Git si se elige B, pruebas y aprobación de promoción. **ADRs ya OWNER_ACCEPTED**; STOP global levantado. Costo/tool/egress sigue requiriendo decisión separada.
- **NO-GO para declarar industrialidad:** no existen aún Pilot B E2E, L real aceptado transversalmente, release probado ni aceptación independiente.
