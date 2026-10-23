---
doc_id: MP132-R01-01-IMPLEMENTATION-PROMPT
version: "1.0.1-OWNER-EXECUTION-APPROVED"
status: "OWNER_APPROVED"
linked_sprint: "R01_01_HIGIENE_Y_STORY_BRIDGE_SPRINT.md"
execution_authority: true
planning_baseline: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
---

# Prompt R01-01 — Higiene documental M0 y primer bridge Story→Envelope

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_01_HIGIENE_Y_STORY_BRIDGE_SPRINT.md` y los ítems MP131-R1-01, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Auditar TODO drift vigente heredado de M0 (campos de autoridad, docs de cierre, referencias presentes/históricas, snapshots y source registry) y ejecutar la reconciliación aprobada junto con un bridge tipado Story→GenerationRequest→ArtifactCandidateEnvelope sin segundo apply authority.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. Para R01-01, incluye en el mismo primer cambio al baseline TODA reconciliación documental M0 real: registro de cierre COR-151, punteros CURRENT aún antiguos y contratos vivos; distingue expresamente snapshots históricos que NO deben reescribirse.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Dos dominios fixture; cierre M0 actual verificable; rechazo de nuevo propietario de apply; ningún drift de contrato global vigente.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
NO_OP donde paridad ya exista; excluir ajustes históricos; no importar código de un Pilot RF específico. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-02 (si aplica).

**Versión ejecutiva sucesora:** `OWNER_APPROVED` individual para R01-01 según orden expresa del Owner. Otros sprints, MP-1B, modelos externos y R1 global permanecen sin autorización.

## Rebind del prompt 153
Ejecutar únicamente seis paths declarados en `05_inputs/manifest.json` contra HEAD `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. El operador exige aprobación para mutación local/commit y otra para push. No confundir `LOCAL_PASS` con aceptación Windows.
