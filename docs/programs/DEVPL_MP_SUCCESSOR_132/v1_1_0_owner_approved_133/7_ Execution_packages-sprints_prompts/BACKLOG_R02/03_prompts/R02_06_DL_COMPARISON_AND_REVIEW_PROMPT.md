---
doc_id: MP132-R02-06-PROMPT
version: "0.1.1-APPROVED-179-REBIND-0386c29"
status: "OWNER_APPROVED"
execution_authority: true
linked_sprint: "R02_06_DL_COMPARISON_AND_REVIEW_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "0386c29b7e07d89b732ac1d3eb80451688026283"
---
# Prompt de implementación — R02_06_DL_COMPARISON_AND_REVIEW

**AUTORIZACIÓN INDIVIDUAL:** La solicitud Owner del 16-10-2026 autoriza únicamente R02-06, tras el cierre verificado R02-05. Esta aprobación no autoriza publicar FROZEN, liberar E ni iniciar R02-07.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Comparación D/L semántica con revisión Owner y provenance** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_06_DL_COMPARISON_AND_REVIEW_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: candidate lifecycle R01-02, route_policy R01-04, eval harness R01-09, context RAG, Product Definition, Settings readiness.
3. Diseña delta específico: UI transparente de alternativas cuando falte, reasons y hashes, evaluaciones semánticas humanas + evidencias grounded; sin sancionar D sólo por no generar prosa equivalente. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Dataset D/L repetible; caso con contenido contrario a fuente y sin grounding; browser Owner selects, restart lineage, seguridad y foco accesible. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
No prometer equivalencia D cuando MODEL_REQUIRED, no autorizar al L a aprobar, no cruzar documentos/otro workspace, deny fallback no permitido y modelo offline.

## Límites
No evaluación LLM juez presentada como verdad absoluta. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.

## Rebind y alcance específico — 2026-10-16

- Sprint y prompt formalizados por instrucción individual del Owner. R02-05: `CLOSED / PASS_WITH_FINDINGS`, evidencia Windows y commit `0386c29b7e07d89b732ac1d3eb80451688026283`.
- R02-03: evidencia real Ollama 3 candidatos, pero su dataset es sintético; se requieren candidatos NUEVOS vinculados al `business_need` y al SHA de Project Context B0.
- D: referencia extractiva (sin fingir cobertura RF). L: inferencia REAL Ollama local, opt-in único y sin fallback silencioso. E: prohibido.
- La revisión del Owner es solamente selección humana de candidato y clasificación justificada, **no** aprobación documental ni FROZEN. Las 3 etapas requieren prueba Windows independiente.
- La ejecución de Windows y sus validaciones continúan pendientes; el bundle aquí es un candidate, no un sucesor Git promovido.
