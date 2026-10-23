---
doc_id: MP132-R01-02-IMPLEMENTATION-PROMPT
version: "1.0.0-PROPOSED"
status: "OWNER_APPROVED"
linked_sprint: "R01_02_CANDIDATE_LIFECYCLE_SPRINT.md"
execution_authority: true
planning_baseline: "caad145436d26404875dbd800559d27a1db590ba"
---

# Prompt R01-02 — Estado de candidatos, idempotencia y provenance

Actúa como ingeniero responsable de DevPilot Local. Implementa **únicamente** el sprint `R01_02_CANDIDATE_LIFECYCLE_SPRINT.md` y los ítems MP131-R1-02, cuando el Owner autorice individualmente este incremento. Antes de cualquier mutación Git, rebindea a `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD vivo, y comprueba que el sprint predecesor está aceptado según evidencia (para R01-01, evidencia Windows COR-153 y HEAD caad145436d26404875dbd800559d27a1db590ba).

## Trabajo solicitado

Reutilizar envelope/candidate store; dar persistencia terminal, lineage y hashes context/input/output/provider/prompt/version, con idempotencia de reintentos.

1. Consulta literalmente el sprint, `BACKLOG_R01_132.md`, los contratos programáticos pertinentes, la fuente viva y las pruebas existentes. No adivines API, paths ni estado de ejecución.
2. Produce un `Reuse/Delta Map` verificable. Evalúa `REUSE_AS_IS`, `NO_OP_ACCEPTED`, delta mínimo y riesgos. No abras cambios ajenos a este sprint.
3. Especifica la allowlist exacta a partir de inspección, endpoints/contratos afectados, pruebas positivas y negativas, idempotencia y rollback; crear ADR únicamente si existe decisión nueva.
4. Implementa un candidato local sobre copia aislada, sin APIs externas ni herramientas de borrado. Diseña operator Python focal, con estado reanudable basado en Git real; no crear dependencia de carpetas hermanas externas al ZIP.
5. Ejecuta pruebas unitarias/servicio y browser cuando lo exija el sprint; registra el nivel real de evidencia. Validación exigida: Reintento terminal no crea duplicado; context/version reproducibles; conflicto concurrente bloqueado.
6. Prepara un solo bundle Windows con `GUIA_UNICA_WINDOWS.md` totalmente consecutiva (ningún volver/saltar paso), comandos PowerShell cada uno en una línea con estados PASS/BLOCK, evidencias exactas y rollback explícito.
7. No aplicar/cerrar automáticamente: informar `LOCAL_PASS/WINDOWS_PENDING` hasta recibir evidencia Windows y adjudicarla según el contrato del sprint. Evitar FULL REGRESSION salvo excepción justificada.

## Prohibiciones y controles
Ningún segundo authority de apply; no side effects por retry. Ninguna API key por defecto, egress DENY, sin proveedor de pago, sin cambio de rama/worktree ni habilitar MP-1B. Comparar **contenido de Git**, no bytes de checkout CRLF/LF, excepto cuando el contrato exige bytes exactos. El operador debe aceptar reejecución idempotente y detenerse ante source drift real.

## Salida requerida
1. Resumen técnico del delta y rationale arquitectónico.
2. Paquete ZIP descargable con guía única y manifest SHA; Python modular + pruebas completas relevantes.
3. Checkpoints `aprendido/implementado/probado/pendiente` y errores reales.
4. Identificación expresa del sprint siguiente R01-03 (si aplica).

**Nota histórica:** este prompt fue planificación propuesta; el addendum COR-154 formaliza la autorización Owner individual y solamente para R01-02.


## Addendum de ejecución y rebind — COR-154 (15-10-2026)

- **Autoridad individual:** `SPRINT_EXECUTION_APPROVED` / `OWNER_APPROVED`, exclusivamente `MP131-R1-02`. No se extiende a R01-03, R1 completo, MP-1B ni APIs externas.
- **Fuente técnica viva:** Git limpio `D:\Projects\DevPilot_Local`, rama `evolution/multiprovider-v2`, HEAD `caad145436d26404875dbd800559d27a1db590ba`, acreditado por COR-153.
- **Reuse/Delta:** contratos `GenerationRequest`, `ArtifactCandidateEnvelope`, `CandidateLineage`, `LEGAL_TRANSITIONS` reutilizados; incorporar adaptador SQLite local transaccional para persistencia, retries y CAS, y pruebas focales.
- **Allowlist Git:** `src/devpilot_core/generation/__init__.py`, `src/devpilot_core/generation/lifecycle_store.py`, `tests/test_mp132_r01_02_candidate_lifecycle.py`. La ADR de diseño se entrega como documento propuesto en el bundle, sin insertar un registro documental incompleto en Git antes de R1-10.
- **Alcance real:** store transaccional mock/servicio, SIN conexión activa al runtime Story o a UI; esa conexión necesitará aceptación de otro incremento. No afirmar capacidad production end-to-end ni equivalencia con modelo real.
- **Evidencia:** pruebas focales kernel/Story/store; Git index exacto; normal push; SHA/CRC de Git archive y paquete de evidencia.
- **Autorizaciones:** únicamente operación material apply+commit y push remoto, con confirmaciones separadas; ninguna validación Owner para lectura.
- **Gate STOP:** diferencia real de HEAD, seguridad o source, colisión de idempotencia no controlada, o pruebas funcionales focales fallidas.
