---
doc_id: DEVPL-MP-SUCCESSOR-132-02_ROADMAP_INDUSTRIAL_132
title: "Roadmap industrial R0–R10 — objetivos, gates y dependencias"
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

# Roadmap industrial R0–R10 — objetivos, gates y dependencias

## 1. Principio de ejecución por valor y no por cantidad de archivos

Cada ola habilita una capacidad que se puede **usar y comprobar** en un flujo real. La aplicación Pilot B es continua; no nace otro workspace por ola. R1 no debe convertir PESP, Settings y documentación en una plataforma teórica sin valor al usuario: se implementan primero **contratos mínimos y una vertical**, y se generalizan según demanden los hitos siguientes.

| Ola | Resultado objetivo verificable | Prioridades arquitectónicas v1.1 | Gate y evidencia |
|---|---|---|---|
| **R0 Autoridad/entorno** | Aprobación programática, G5 administrativo separado, Git worktree seguro, auditoría de Settings y métricas iniciales | Gate de alternativa B antes del primer source change; Source Registry successor sólo autorizado | M0: Owner + HEAD/upstream, tracked/untracked/ignored, backups y rollback, STOP scope |
| **R1 Contratos y primera integración** | Kernel Story→Envelope, eval reusable y primera vertical de Settings/PESP/Artifacts | GenerationRoutePolicy D/L/E por tarea; PESP+Coverage; Markdown/publication; FROZEN successor; roles efectivos/configuración; estado UI confiable | M1: pruebas D/Mock, prueba de profile+gate, deny, reentrada, publicación y reversibilidad |
| **R2 Product Definition / Pilot B B0-B1** | Owner crea proyecto neutral y obtiene Vision/Scope/Requirements contextualizados por L real y D | Modelo local competente, preferido para semántica; artefactos humanos; perfil profesional contextual; setup/readiness | M2: Ollama o LM Studio real, provenance/candidate válido, tres FROZEN, UI sin terminal |
| **R3 Technical Design / B2** | Architecture, ADRs, Security, Test Strategy, Traceability y condicionales datos/API/UX; Technology Profile y scaffold posterior | Standards Coverage; RAG técnico, versionado, rutas docs estables, código según stack | M3: consistencia RF→ADR→tests, elección Owner, scaffold/aprovisionamiento aprobado, pruebas negativas |
| **R4 Planning / B3** | Roadmap, backlogs, sprints y stories READY; MIASI condicional | Markdown durable, dependencies, capacidad, successor y cambios de planificación | M4: decisiones aprobadas, coverage Planning, historias trazables, sin falsas estimaciones |
| **R5 Construction / B4** | Story arbitraria → código real → tests/Quality/Git gobernados | L preferente evaluado, ContextPack, adapter único, SourceChangePlan, UI status y ledger UX | M5: al menos dos dominios/pruebas de independencia; no duplicación ni manual project writes |
| **R6 Release / B5** | Instalación, startup, release, SBOM, rollback, backup/restore y portabilidad | Application Deliverable Manifest separado de Engineering Evidence Manifest; runbooks | M6: release iniciado y revertido en entorno real, secrets scan, smoke/restore |
| **R7 Agents / B6** | Agentes de revisión y asesores Pilot B con permisos limitados y handoffs | MIASI operativo, evals, autonomía acotada, tool allowlist, kill, bounded loops | M7: trazas, humano y pruebas adversariales; ninguna mutación directa |
| **R8 External / Pilot C** | Provider externo opcional con egress autorizado, privacy y CostGuard | ADR trust boundary aprobada antes de HTTP; datasets sintéticos, costos máximos | M8: aceptación real externa o `NOT_ENABLED`, nunca falso PASS |
| **R9 Productización/Resiliencia** | UX consolidada, launcher, fault injection real, rendimiento y operación de DevPilot | Consolidar y medir mejoras iniciadas desde R0–R6, no diferir Settings/FROZEN básicos | M9: restart/recovery/rollback y browser E2E instrumentados |
| **R10 Aceptación independiente** | Pilot B B0–B7, segundo dominio, seguridad, operación y madurez adjudicadas | Evaluación independiente, regresión de cierre aprobada, S0/S1=0 del critical path | M10: Owner aceptación por alcance separado L/Agent/E |

## 2. Dependencias y concurrencia

Camino principal R0→R1→R2→R3→R4→R5→R6→R10. Las foundations de R7 pueden iniciar read-only sin esperar toda R6; ningún tool write por agente precede al guard de R5. R8 se habilita sólo tras security/cost gates propios. R9 se distribuye desde el inicio y cierra al final; no es vertedero de todos los defectos.

**Crosscutting de prioridad temprana:** PESP/Artifact Coverage, documentación durable, successor FROZEN, `GenerationRoutePolicy`, Settings con autoridad, estado/feedback UX y auditoría focal, todos definidos en R1 y ampliados por vertical. Las prácticas de continuidad y cambio afectan todas las olas.

## 3. Cadena de Pilot B

B0 Project Entry neutral → B1 Product Definition → B2 Technical Design → B3 Planning → B4 Construction → B5 Release/Operations → B6 advisory agents → B7 evaluación E2E. Se mantiene el escenario de microempresa de bienestar/cuidado personal, inventario/ventas, catálogo, stock y propuestas comerciales **como problema inicial**, no como requerimientos/código preescritos para facilitar las pruebas. Owner decide alcance y stack durante el workflow real.

## 4. Gates transversales

Cada incremento: A0 authority, A1 audit/Reuse/Delta Map, A2 ADR/contrato/approval, A3 dry-run/preimage, A4 pruebas semánticas/técnicas/seguridad/UI pertinentes, A5 Git 3-estados/snapshot, A6 Owner acceptance. Cada fase revisa Artifact Coverage y ledger por IDs; las violaciones funcionales S0/S1 bloquean, preferencias S2/S3 no fuerzan cambios fuera de scope.

## 5. Programación futura

Roadmap y backlog son **OWNER_APPROVED_PROGRAM para planeación, no órdenes de ejecución**. Al iniciar una ola se consultará el baseline vivo y la auditoría podrá reorganizar dependencias. Se emitirán posteriormente sprints/prompts autorizables uno a uno: **no forman parte de la presente entrega**.
