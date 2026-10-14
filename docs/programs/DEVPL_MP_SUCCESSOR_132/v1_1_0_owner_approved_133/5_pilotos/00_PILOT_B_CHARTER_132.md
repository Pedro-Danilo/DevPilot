---
doc_id: DEVPL-MP-SUCCESSOR-132-00_PILOT_B_CHARTER_132
title: "Pilot B — Charter de aplicación continua, profesional y E2E"
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

# Pilot B — Charter de aplicación continua, profesional y E2E

## 1. Propósito

Pilot B es una aplicación real creada desde cero por DevPilot desde una necesidad de una microempresa de productos de bienestar/cuidado personal con catálogo, inventario, ventas, alertas y recomendaciones. **No** se preescriben los requisitos definitivos, el stack ni RF de Pilot A. Las decisiones nacen en las pantallas normales de DevPilot y sus actas Owner. Su resultado comprueba generalidad del SDLC y asistencias D/L/Agent.

## 2. Principios no negociables

- **Un solo proyecto/workspace B0–B7**, con documentación `docs/` portable, release real, operaciones y evolución. No reiniciar workspace entre olas para maquillar resultado.
- `operator_project_writes=0`, `normal_user_terminal_escapes=0`, `journey_actions_via_devpilot_ui=true`. Scripts del operador sólo arrancan/inspeccionan/fijan evidencia/servidores DevPilot, nunca fabrican artefactos de negocio o source del piloto.
- Project Entry registra negocio/constraints y proyecto neutral; stack se decide tras Requirements+Architecture. Modelo local sólo opt-in e instalado, evaluado y visible; external fuera del Pilot B normal.
- MIPSoftware siempre; MIASI sólo cuando B6 incorpore componentes IA dentro de la aplicación; no exigir Tool Card al inventario convencional por usar IA para programarlo.
- Cada transición consulta PESP, Coverage Gate y apropiados quality gates. Owner revisa alternativas, scope, consecuencias y aprobación sensible; LLM no escoge por él.

## 3. Milestones y entregables

| B | Tarea Owner en UI | Artefactos portables y evidencia |
|---|---|---|
| **B0** | Crear proyecto, describir necesidad, restricciones, roots, modelo deseado | `idea_intake`, contexto, PESP provisional, permisos de root y Git inicial |
| **B1** | Vision/Scope/Requirements; comparar propuestas D/L | Markdown FROZEN, lineage, schema, scores semánticos e Owner review |
| **B2** | Arquitectura, ADRs, datos/API/UX según aplicabilidad, Security, Test Strategy, Technology | docs Markdown vigentes, Coverage PASS, scaffold posterior con permisos y manifests |
| **B3** | Roadmap/Backlog/Sprints/Stories y capacidad | Documentos durables bajo docs/08_planning, story READY traceable |
| **B4** | Solicitar historia no trivial → candidate → review/diff/approve/apply/tests/Quality/Git | Código compilable en stack elegido, commits exactos, E2E funcional, negativas de drift/double apply |
| **B5** | Release, instalación/startup/health, upgrade/rollback | Deploy real, manifests separados, SBOM/secret scan, guía de operación y evidencia de restauración |
| **B6** | Activar un advisory agent con tool limits | MIASI Cards, evals, recomendaciones grounded; ningún stock/price/publicación sin permiso específico |
| **B7** | Recorrer viaje completo y cambios de evolución | Auditoría independiente E2E y una change request FROZEN→successor seguida de release nuevo |

## 4. Aceptación profesional real

Un test `pytest PASS` o un build UI no certifica etapa completa. Es obligatorio un browser walkthrough que muestre estados correctos, aprobación, next action, ausencia de terminal Git manual, persistencia entre sesiones y artefactos portables. Release se instala/arranca **fuera de DevPilot** y pasa rollback. Debe incluir al menos una evolución posterior al primer diseño para demostrar mantenibilidad.

## 5. Fallos y controles

Timeout local model, salida mal formada, escenario sin capacidad, reinicio de API/browser, expiración de sesión, drift file, locks multi-proceso, conflictos Git, error de dependencies, fail de release y rollback. Estos fallos no pueden generar source loss ni autoautorizar acciones. R9 culmina resiliencia real, pero las pruebas negativas pertinentes son obligatorias en cada gate anterior.

## 6. Segunda prueba de generalidad

El programa requiere **otro dominio independiente** antes de R10; puede ser biblioteca, reservas no sensibles o documentación, elegido por el Owner tras contexto. No permitir un generador específico de inventario disfrazado de motor general. El mismo kernel `GenerationRequest/Envelope` y governance deben funcionar en ambas aplicaciones.

## 7. Límites

Sin APIs externas pagas por defecto. Pilot C las evalúa aparte; ausencia de E no invalida `LOCAL_FIRST_PROFESSIONAL`, pero impide `EXTERNAL_ENABLED`. Sin certificaciones regulatorias ni SLA enterprise inventados. Findings UX heredados revalidados contextualmente y ninguna reparación sin auditoría focal.
