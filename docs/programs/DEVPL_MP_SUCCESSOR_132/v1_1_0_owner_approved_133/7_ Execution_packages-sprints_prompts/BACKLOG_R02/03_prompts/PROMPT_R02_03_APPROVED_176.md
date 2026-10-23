---
doc_id: MP132-R02-03-PROMPT
version: "1.0.0-APPROVED-176"
status: "OWNER_APPROVED"
execution_authority: true
linked_sprint: "R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc"
---
# Prompt de implementación — R02_03_OLLAMA_REAL_CANDIDATE

**AUTORIZACIÓN OWNER INDIVIDUAL RECIBIDA** para este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Primera generación real Ollama opt-in para Product Definition** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: modeling/ollama_adapter.py, modeling/contracts.py, modeling/negotiation.py, generation/contracts.py, generation/product_definition.py, candidate_harness.py, route_policy.py.
3. Diseña delta específico: Conexión UI→API→servicio→modelo real si la ruta está ausente; control de recursos/timeouts, budget local, dataset y métricas; guardar candidate persistente sin source write. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Dataset versionado mínimo con al menos 3 prompts/2 negativas, health real (nombre versión, hardware, duración medidos), pruebas contrato, seguridad y browser; no mocking en gate REAL. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Timeout, contexto insuficiente, JSON inválido, modelo ausente, respuesta alucinada, doble request y fallback REDUCED/MODEL_REQUIRED sin falso EQUIVALENT; offline D y sin cloud.

## Límites
No autorizar auto-start, descarga de pesos, ni envío remoto por operador. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.


## Rebind de ejecución COR-176

Owner aprueba individualmente R02-03; solo este incremento. Fuente Git Windows R02-02/COR175: `8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc` en `evolution/multiprovider-v2`. Llamada Ollama real queda pendiente de validación Windows con modelo expresamente confirmado por el Owner; modelos no descargados ni habilitados automáticamente. Sprint siguiente R02-04 NOT_AUTHORIZED. R02-03 no publica FROZEN ni selecciona candidatos para Product Definition real.
