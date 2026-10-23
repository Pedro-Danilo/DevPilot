---
doc_id: MP132-R02-09-PROMPT
version: "0.1.0-DRAFT-172"
status: "DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL"
execution_authority: false
linked_sprint: "R02_09_LOCAL_FAILURE_RESILIENCE_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REBIND_REQUIRED"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---
# Prompt de implementación — R02_09_LOCAL_FAILURE_RESILIENCE

**NO EJECUTAR** hasta orden Owner individual de este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Negativas de modelo local y reanudación segura Product Definition** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_09_LOCAL_FAILURE_RESILIENCE_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: candidate lifecycle, route_policy, provider health, eval harness, current Git three-state policy and retry receipts.
3. Diseña delta específico: Solo fallas reproducibles, guardando checkpoints y causal; probar cancel/retry no duplicado y no fake success después de reinicio. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Foco acumulativo con fault injection controlado, 1 test real local failure, fixtures para escenarios más costosos, repositorios/sandbox temporales, nunca destruir workspace Pilot B. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Kill server durante request, JSON malicioso, caída API, stale workspace, double-submit, reinicio UI y egress deny; no loops autónomos.

## Límites
No ejecutar pruebas destructivas sobre repositorio canónico ni enviar prompt a Internet. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.

---

## Enmienda programática post-R02-06 · 187

**Esta enmienda sustituye las instrucciones heredadas incompatibles con L-first/Markdown para ejecución futura; no activa el prompt (`DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL`).** La lectura literal de repo y garantías de audit-first, dry-run, approval de cambios, Git 3-state y evidencia Windows siguen siendo obligatorias. Baseline de referencia: `b666c5641c1b8231c5b609216f64490a72ff1763`, rebindeo de HEAD real obligatorio.

Implementar pruebas focales de fault injection sobre copia aislada: fallo modelo local, JSON corrupto, expiración de sesión con draft Markdown, reentrada de generación, cancelación, cambio de contexto, reinicio API/UI y egress DENY. Mantener candidate/ref/hash estables y no ejecutar auto-compare ni E. PASS solo si recuperación no duplica inferencias costosas/decisiones, ni altera FROZEN. Operador Windows no repite cambios por estado sobreviviente y valida Git semánticamente ante CRLF/LF.
