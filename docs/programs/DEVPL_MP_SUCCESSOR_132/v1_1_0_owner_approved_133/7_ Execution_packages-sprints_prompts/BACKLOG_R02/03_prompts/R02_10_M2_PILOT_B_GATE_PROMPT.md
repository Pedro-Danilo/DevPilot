---
doc_id: MP132-R02-10-PROMPT
version: "0.1.0-DRAFT-172"
status: "DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL"
execution_authority: false
linked_sprint: "R02_10_M2_PILOT_B_GATE_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REBIND_REQUIRED"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---
# Prompt de implementación — R02_10_M2_PILOT_B_GATE

**NO EJECUTAR** hasta orden Owner individual de este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Cierre M2: Pilot B B0–B1 y modelo local real** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_10_M2_PILOT_B_GATE_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: R01M1Gate como evidencia de entrada, Program maturity matrix, Product Definition, Workspace stores, Browser receipt y Git manifests.
3. Diseña delta específico: M2AcceptanceReport con pruebas de extremo a extremo de Product Definition, no nuevo workflow; carpeta y documentos portables y control de scripts operator_project_writes=0. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Recibos R02-01..09 y hashes, modelo real hardware/model/version/dataset, browser navegable y restart, replay negativo; full regression solo con excepción explícita documentada si gate lo exige. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
No modelo real, documento no FROZEN, objeto Pilot B regenerado, write via operator, falta de consentimiento, proveedor externo o grounding no verificado: impedir M2 PASS.

## Límites
No autoriza R03, R08 external, agentes write o MP-1B. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.

---

## Enmienda programática post-R02-06 · 187

**Esta enmienda sustituye las instrucciones heredadas incompatibles con L-first/Markdown para ejecución futura; no activa el prompt (`DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL`).** La lectura literal de repo y garantías de audit-first, dry-run, approval de cambios, Git 3-state y evidencia Windows siguen siendo obligatorias. Baseline de referencia: `b666c5641c1b8231c5b609216f64490a72ff1763`, rebindeo de HEAD real obligatorio.

Comprobar mediante UI que Pilot B B0 persiste y B1 publica tres Markdown profesionales FROZEN tras una generación L real por etapa, revisión Owner, Coverage y lineage; observar negativos, reinicio y portabilidad. No usar R02-06 D/L como equivalencia semántica y no obligar dos candidatos por artefacto. Emisión M2 refleja cada limitación real; Full Regression solo por excepción y con evidencia. No autorizar R3 hasta dictamen M2.
