---
doc_id: MP132-R01-09-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "OWNER_APPROVED"
linked_sprint: "R01_09_EVAL_HARNESS_SPRINT.md"
execution_authority: true
planning_baseline: "70b5eddce83708c01cfdd6557e82e8369990e878"
---

# Prompt R01-09 — Harness de evaluación de candidatos

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_09_EVAL_HARNESS_SPRINT.md` y los ítems MP131-R1-06, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Dataset versionado, schema/semantic gates, groundedness, negativos y reporte reproducible por provider/versión; inicialmente mock/D.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Reporte determinista y lineage/costos medidos o NOT_AVAILABLE; input adversarial bloqueado.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
No reclamar modelo local evaluado sin ejecutar modelo real (R2). Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-10 (si aplica).

**Este prompt se encuentra OWNER_APPROVED para R01-09 exclusivamente, por orden explícita del Owner en este turno.**

## Rebind operativo COR-162 (15-10-2026)

- Predecesor R01-08/COR-161: CLOSED/WINDOWS_PASS; commit `70b5eddce83708c01cfdd6557e82e8369990e878`.
- Única autorización de ejecución: MP131-R1-06 / R01-09. R01-10 y MP-1B NO AUTORIZADOS.
- Alcance: evaluación reproducible mock/determinística, datasets versionados, schema/semantic/grounding por reglas, negativos, provenance y cost/latency NOT_AVAILABLE. No evaluar modelos reales ni usar LLM-as-judge.
- Baseline canónico: `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`.
- Cambios Git limitados a 5 rutas según `05_inputs/manifest.json`, con reconciliación de punteros activos y sin modificar snapshot histórico.
- Pruebas focales acumulativas (no full regression), operador reanudable, push no forzado solo tras autorización material.
