---
doc_id: MP132-R01-05-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "OWNER_APPROVED"
linked_sprint: "R01_05_PESP_PROFILES_SPRINT.md"
execution_authority: true
planning_baseline: "42aca99dcf9d4599ef7475b38071762d777027ea"
---

# Prompt R01-05 — PESP y Artifact Profiles v2 primera vertical

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_05_PESP_PROFILES_SPRINT.md` y los ítems MP131-R1-05, MP132-R1-08, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, cierre M0 COR-151).

## Trabajo solicitado

Unificar contrato PESP (MIPSoftware requerido y MIASI condicionado por IA del proyecto) con Artifact Profiles/aplicabilidad justificable; no catálogo universal.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Proyecto web convencional vs proyecto con agente; waiver controlado; FROZEN preservado.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
N/A no automático; waiver jamás rebaja seguridad legal. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-06 (si aplica).

**Nota histórica:** el prompt original era planificación propuesta. Esta versión sucesora tiene `OWNER_APPROVED` exclusivamente para R01-05.


## Rebind y aprobación de ejecución — 157

- Aprobación Owner individual de R01-05: concedida mediante la solicitud explícita del 15-10-2026; NO se extiende a R01-06, MP-1B o egress externo.
- Repositorio canónico: `D:\Projects\DevPilot_Local`; rama `evolution/multiprovider-v2`; HEAD de entrada `42aca99dcf9d4599ef7475b38071762d777027ea`.
- Alcance material exacto: `src/devpilot_core/validation/artifact_profile_registry.py`, `src/devpilot_core/validation/project_profile.py`, `tests/test_mp132_r01_05_pesp_profiles.py`, `.devpilot/docs_governance/source_registry.json`, `.devpilot/project_state.json`.
- Reuse: `ArtifactProfileRegistry` y `docs/validation/artifact_profiles.json` continúan siendo únicos; PESP se integra como evaluación de aplicabilidad por proyecto, sin catálogo duplicado.
- Tests focales, ejecución Git idempotente, evidencias externas y revalidación Windows; sin full regression ni browser por no modificar UI.
- No proclamar `FROZEN` por crear el perfil o un waiver; perfiles/waivers son propuestas sujetas a aprobación/lineage.
