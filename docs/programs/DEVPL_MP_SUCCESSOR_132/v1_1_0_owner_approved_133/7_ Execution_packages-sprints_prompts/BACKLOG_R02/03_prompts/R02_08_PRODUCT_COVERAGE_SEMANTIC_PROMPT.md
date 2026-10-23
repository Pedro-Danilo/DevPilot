---
doc_id: MP132-R02-08-PROMPT
version: "0.1.0-DRAFT-172"
status: "DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL"
execution_authority: false
linked_sprint: "R02_08_PRODUCT_COVERAGE_SEMANTIC_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REBIND_REQUIRED"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---
# Prompt de implementación — R02_08_PRODUCT_COVERAGE_SEMANTIC

**NO EJECUTAR** hasta orden Owner individual de este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **PESP y Coverage Gate para Product Definition contextual** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_08_PRODUCT_COVERAGE_SEMANTIC_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: artifact_coverage_gate.py, PESP service R01-05, candidate_harness.py, Source Registry, registro de normas.
3. Diseña delta específico: Reglas semánticas de Product Definition con fuentes reales y revisión Owner, sin duplicar evaluador; evidencia de referencias verificadas, missing required y diferencias de juicio del modelo. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Positive/negative cases, 1 waiver razonado, 1 NO_APLICA, 1 grounding negativo; browser Guided/Expert si UI cambia; test impacto. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Plantillas vacías, N/A automático, waiver sin Owner, hallucination source, MIASI obligatorio sin componente IA en app y falsos FAIL históricos deben bloquear o clasificarse bien.

## Límites
No prometer calidad semántica absoluta mediante reglas D. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.

---

## Enmienda programática post-R02-06 · 187

**Esta enmienda sustituye las instrucciones heredadas incompatibles con L-first/Markdown para ejecución futura; no activa el prompt (`DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL`).** La lectura literal de repo y garantías de audit-first, dry-run, approval de cambios, Git 3-state y evidencia Windows siguen siendo obligatorias. Baseline de referencia: `b666c5641c1b8231c5b609216f64490a72ff1763`, rebindeo de HEAD real obligatorio.

Auditar el quality gate mínimo aceptado en R02-07, no volver a construirlo. Implementar Coverage/PESP profesional con reglas por etapa y cross-stage, detectar contradicciones/no-grounding, índices RF→Scope→Vision y requisitos no testeables. Distinguir blocker contractual de refinamiento cosmético; cuando FROZEN requiera corrección, proponer successor, nunca editarlo. Evidencia por UI y pruebas focales, sin imponer nueva aprobación por cómputo. No seleccionar E ni obligar D/L.

---

## Adenda A188 — instrucciones de referencia NO ejecutables

Previamente a activar el prompt de forma individual, consultar literalmente A188, ADR-016, contrato transversal, sprint R02-08 y baseline `3a0a170f3c646e9955966576dd9212d3f87450e6`. **Se preserva `DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL`**. Implementar Coverage/PESP semántico read-only Product Definition, dos dominios, reuse-first del evaluador existente, clasificación material vs editorial, sin añadir approvals inocuas. Este archivo no ordena ejecutar ni modifica permisos de E.
