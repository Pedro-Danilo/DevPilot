---
doc_id: MP132-R02-02-PROMPT
version: "0.2.0-APPROVED-175"
status: "OWNER_APPROVED"
execution_authority: true
linked_sprint: "R02_02_LOCAL_MODEL_READINESS_SPRINT.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "4a4443f1631acdbfcd19e1e2fca4be36f707daf9"
---
# Prompt de implementación — R02_02_LOCAL_MODEL_READINESS

**NO EJECUTAR** hasta orden Owner individual de este sprint, y no usar aprobación programática R02 como autorización de código.

Actúa como ingeniero de DevPilot Local en Windows. Tu objetivo único es **Readiness/Settings y descubrimiento seguro de modelos locales** y respetar la lectura literal de `4_backlogs/BACKLOG_R02_132.md`, `01_REGLAS_R02_172.md`, `02_sprints/R02_02_LOCAL_MODEL_READINESS_SPRINT.md`, contratos/ADRs del programa y la fuente viva Git. Nunca sustituir la lectura literal por la lista candidata de rutas.

## Acciones obligatorias y secuenciales
1. Confirma el veredicto Windows del predecesor, `evolution/multiprovider-v2`, HEAD real, worktree, staged, untracked y upstream. Baseline de planificación `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` solo para R02-01; rebindea a la evidencia publicada más reciente para los sucesores. Si falta evidencia, `BLOCK` y reporta.
2. Recorre el contrato de sprint, auditoría literal del repo y pruebas existentes; registra `REUSE/NO_OP/EXTEND` y los responsables de cada efecto. En particular: modeling/local_provider_discovery.py, local_provider_health.py, health.py, local_endpoint_policy.py, model_gateway_settings_service.py, settings_service.py, UI Settings existente.
3. Diseña delta específico: Datos de readiness desde comprobaciones reales loopback, timeout y hardware medido; UI Guided/Expert con estado y motivo, sin hacer egress. Config persistente no equivale a enable operativo. Presenta allowlist final exacta basada en inspección, estados recuperables y seguridad; no realizar writes antes de aprobación individual y dry-run.
4. Implementa en copia aislada con Python modular, `ModelAdapter` desacoplado, D/mock primero; usa L real únicamente si el AC y Owner lo permiten, nunca E. Incluye módulos/config/tests/documentación/ADR cuando cambia frontera.
5. Ejecuta pruebas focales y negativas: Mocks negativos y positivos + pruebas de loopback real bajo Owner, proceso/hardware reportado sin valores inventados; RBAC, CSRF, secuencias UI y browser 375. Deben quedar claras llamadas reales vs fixtures y costo/latencia observados vs `NOT_AVAILABLE`.
6. Ejecuta validación Windows en una `GUIA_UNICA_WINDOWS.md` autocontenida y consecutiva. Cada instrucción PowerShell ocupa una línea y termina PASS verde/BLOCK rojo; cuando exista UI, navegación desde Home y capturas en el **mismo numeral** que provoca el estado, no agruparlas al final. Nunca escrituras del operador sobre los artefactos de negocio de Pilot B.
7. Comprueba Git allowlist/recovery/commit/push normal, ZIP evidencia y Git archive SHA/CRC; entrega recibos, errores, limitations y último checkpoint. No iniciar el sprint siguiente ni elevar M2 por mock.

## Negativas de aceptación
Sin Ollama/LM Studio: `UNAVAILABLE/NOT_TESTED`, ruta D usable y cero costos; endpoints públicos o SSRF rechazados; secretos no mostrados; preferencia nunca concede permiso.

## Límites
No afirmar EVALUATED sin dataset y output, no proveedor cloud. Sin `reset --hard`, `clean`, `stash` ni force push; no comparisons físicas LF/CRLF para contenido; full regression sólo por excepción justificada; agente con dry-run por defecto. `PASS` sólo si los AC exigidos se han demostrado en el nivel correcto.

## Salida requerida
Bundle ZIP Windows con código/patches/tests/operador/guía única/ADR cuando aplique, `REUSE_DELTA`, manifest, pruebas positivas/negativas, reporte actual vs esperado y lista exacta de evidencias a devolver. **Estado antes de Windows** `LOCAL_PASS/WINDOWS_PENDING`, no `CLOSED`.


## Rebind y límites de ejecución — COR-175

- Owner autoriza R02-02 exclusivamente mediante solicitud de 16-10-2026, no R02-03.
- Baseline acreditado R02-01: `4a4443f1631acdbfcd19e1e2fca4be36f707daf9`; `evolution/multiprovider-v2`; 134/134 focal, push normal PASS.
- El **reporte de readiness** separa SUPPORTED/CONFIGURED/HEALTHY/EVALUATED/ELIGIBLE por tarea.
- Sin proveedor instalado, prueba negativa `NOT_TESTED/UNAVAILABLE` es válida para esta vertical de diagnóstico; NO se certifica inferencia real.
- Probe solo por acción Owner en browser, HTTP POST autenticado+CSRF+RBAC y loopback; timeout 2s/proveedor; sin inferencia/source writes.
- No se publica código hasta gate de UI/browser Windows; next R02-03 NOT_AUTHORIZED.
