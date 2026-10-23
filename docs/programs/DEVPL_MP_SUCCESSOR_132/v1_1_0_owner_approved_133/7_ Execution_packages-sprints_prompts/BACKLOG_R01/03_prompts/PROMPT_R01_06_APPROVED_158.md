---
doc_id: MP132-R01-06-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "OWNER_APPROVED"
linked_sprint: "R01_06_COVERAGE_GATE_SPRINT.md"
execution_authority: true
planning_baseline: "154e5eb20fffce2e884dd8f2bc3c4ae46e7d73b7"
---

# Prompt R01-06 — Catalog/Coverage ejecutable

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_06_COVERAGE_GATE_SPRINT.md` y los ítems MP132-R1-09, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Registrar requeridos/condicionales/recomendados/N-A y dependencias por etapa, con gate que distingue archivo existente de contenido aceptable.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Required ausente BLOCK; recommended WARN; conditional sin evidencia REVIEW_REQUIRED.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
No templates vacíos; no cobertura global artificial. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-07 (si aplica).

**Este prompt es planificación propuesta; no confiere aprobación Owner de ejecución.**

## Rebind de ejecución R01-06 / 158

- Aprobación Owner individual: sprint y prompt R01-06 únicamente, instrucción expresa de este turno; sin aprobación de R01-07.
- Baseline vivo: `154e5eb20fffce2e884dd8f2bc3c4ae46e7d73b7`, rama `evolution/multiprovider-v2`, worktree `D:\Projects\DevPilot_Local`.
- Estado de R01-05: CLOSED / WINDOWS_PASS; evidencia SHA/CRC, 90 pruebas, cinco rutas y promoción.
- Reuse/Delta: `ArtifactProfileRegistry` fuente única; evaluador independiente `ArtifactCoverageGate`, sin catálogo paralelo.
- Alcance Git exacto: `src/devpilot_core/validation/artifact_coverage_gate.py`, `src/devpilot_core/validation/artifact_profile_registry.py`, `tests/test_mp132_r01_06_coverage_gate.py`.
- Niveles probatorios: código/servicio mock + pruebas focales; sin aceptación semántica por automatismo, browser no exigido, sin modelos.
- Sólo dos aprobaciones materiales: commit local y push normal. Sin full regression ni egress.
