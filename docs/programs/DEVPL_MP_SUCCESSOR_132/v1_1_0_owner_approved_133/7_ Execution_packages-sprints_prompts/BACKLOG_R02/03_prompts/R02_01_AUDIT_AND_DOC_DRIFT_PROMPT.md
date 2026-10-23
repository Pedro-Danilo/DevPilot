---
doc_id: MP132-R02-01-PROMPT
version: "0.1.0-DRAFT-172"
status: "DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL"
execution_authority: false
linked_sprint: "R02_01_AUDIT_AND_DOC_DRIFT_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REBIND_REQUIRED"
---
# Prompt de implementación — R02_01_AUDIT_AND_DOC_DRIFT

**NO EJECUTAR** hasta orden Owner individual de este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Rebind M1, inventario R2 y reconciliación documental activa** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_01_AUDIT_AND_DOC_DRIFT_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: generation/product_definition.py; application/project_entry_planning_service.py; workspace/project_layout.py; docs_governance; project_state.json; source_registry.json; modeling/* y tests. Comparar fuentes reales antes de aceptar nombres.
3. Diseña delta específico: Ledger de drift con clasificación ACTIVE/HISTORICAL/OBSERVE_ONLY; reconciliar TODOS los ACTIVE que afecten autoridad/status/anchors, documentos de programa actualmente instalados, enlaces del Source Registry y pruebas con identificador de sprint hardcoded. No cambiar snapshots sellados ni 1752 entradas semánticas por búsqueda global. Solo rutas auditadas con preimages Git. Si drift material no se puede reparar sin romper contratos: BLOCK, no certificar limpieza ni iniciar 02. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Pruebas focales Product Definition D, Doc Authority, Source Registry, 1752 parity, tests de R01 afectados; verificación Git staged/partial/restart; igualdad de contenido canónico (no bytes CRLF/LF). Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Sin modelo L instalado funciona ruta D; tokens/sesión ajena no habilitan escritura; no borrar documentos FROZEN, ni mutar `external_api_allowed`; rechazo de drift no clasificado y de cambios externos a allowlist.

## Límites
No inferencia L/E, no bootstrap Pilot B, no cambio externo ni nuevas autorizaciones de backlog. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.
