---
doc_id: MP132-R01-14-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "OWNER_APPROVED"
linked_sprint: "R01_14_PROJECT_LAYOUT_SPRINT.md"
execution_authority: true
execution_baseline_commit: "818f2b6358e48ff9097cbf3297d7ac956bd6c605"
planning_baseline: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
---

# Prompt R01-14 — Project Layout vs TechnologyProfile

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_14_PROJECT_LAYOUT_SPRINT.md` y los ítems MP132-R1-15, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Habilitar layout lógico neutral al stack y decisiones tecnológicas posteriores, con documentos lazy/scaffold bajo aprobación.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Crear proyecto sin elegir stack; rutas portables y denegación path traversal; scaffold no se ejecuta sin Owner.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
No migrar repositorios históricos ni scaffolds generales innecesarios. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-15 (si aplica).

**Este prompt es planificación propuesta; no confiere aprobación Owner de ejecución.**

## Rebind autorizado — 2026-10-15
Autorización individual del Owner R01-14 sobre `818f2b6358e48ff9097cbf3297d7ac956bd6c605`, sin ampliar ola ni permitir ejecución retrospectiva.
