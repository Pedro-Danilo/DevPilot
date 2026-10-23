---
doc_id: MP132-R02-07-PROMPT
version: "0.2.0-APPROVED-187"
status: "OWNER_APPROVED"
execution_authority: true
linked_sprint: "R02_07_FROZEN_PRECODE_DOCUMENTS_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
individual_execution_approval: "2026-10-17"
execution_branch: "evolution/multiprovider-v2"
---
# Prompt de implementación — R02_07_FROZEN_PRECODE_DOCUMENTS

**AUTORIZACIÓN OWNER INDIVIDUAL OTORGADA (2026-10-17), SOLO PARA R02-07.** No habilita API externa, cambio de scope, autoaprobación ni R02-08.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Publicación humana Markdown FROZEN de Vision/Scope/Requirements** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_07_FROZEN_PRECODE_DOCUMENTS_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: docs_governance/markdown_publication.py, lifecycle y frozen_successor R01, coverage gate y Document Authority; leer contratos actuales en Git.
3. Diseña delta específico: Conectar UI Owner review→Markdown publication sin caminos de escritura paralelos; atomicidad, preimages, aprobación real y confirmación archivo/registro. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, L local real elegible como primera ruta de autoría semántica, sin generar automáticamente D; nunca E sin autorización externa específica. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Tres documentos reales con contenido Pilot B, integrity SHA, CSS UI/browser, reload/session, negativos Git lock/denied/stale; no operator write de business docs. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Sin Owner, schema/grounding defectuoso, cambio tardío o conflicto de hash: ninguna publicación; original FROZEN inmutable; reintento no duplica.

## Límites
No autoaprobar contenido L ni escribir documentación desde operador. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.

---

## Enmienda programática post-R02-06 · 187

**Esta enmienda sustituye las instrucciones heredadas incompatibles con L-first/Markdown para ejecución futura; se activa solo por instrucción Owner individual (`OWNER_APPROVED`).** La lectura literal de repo y garantías de audit-first, dry-run, approval de cambios, Git 3-state y evidencia Windows siguen siendo obligatorias. Baseline de referencia: `b666c5641c1b8231c5b609216f64490a72ff1763`, rebindeo de HEAD real obligatorio.

1. Leer HEAD vigente y sus servicios de Pre-code, R01 Candidate Envelope, ModelAdapter/route, Artifact Profiles, Coverage, Publication, Approval/Source Registry y tests. Construir Reuse/Delta exacto. No inventar otra autoridad o regenerar documentos históricos R02-06.
2. Ajustar Guided para **generar un único candidato L real inicial por etapa** en español con prompt/schema específicos, contexto upstream FROZEN y límites/timeout; no generar D como candidato semántico ni competir en un laboratorio. Mantener Manual/Import gobernados si L no está listo; prohibir E sin contrato de R8.
3. Persistir **archivo candidato `.md` real, versionado e inmutable**, provenance separado, revisión/edición Owner en Markdown por UI, diff y aprobación existente. No publicar JSON como si fuera el documento humano ni permitir edición FROZEN.
4. Validar stage-specific before freeze: Vision valor/objetivos/beneficiarios; Scope IN/OUT/DEFERRED/prioridades; RF con ID/reglas/excepciones/AC; trazabilidad y grounding; fallos recuperables. No usar longitud/encabezados como prueba profesional suficiente.
5. Probar L real con modelo identificado, tests negativos y browser desde UI, evidencia correcta. Solo si calidad y approvals reales PASS habilitar freeze. Mantener source allowlist exacta, dry-run seguro, Git no LF/CRLF false positives, stop point final y un solo operador/guía. No iniciar R02-08.
