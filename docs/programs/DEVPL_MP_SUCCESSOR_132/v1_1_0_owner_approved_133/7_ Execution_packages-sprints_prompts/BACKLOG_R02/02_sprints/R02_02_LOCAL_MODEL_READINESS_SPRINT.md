---
doc_id: MP132-R02-02-SPRINT
version: "0.1.0-DRAFT-172"
status: "DRAFT_EXECUTION_GATED"
execution_authority: false
owner_approval: "PENDING_INDIVIDUAL_APPROVAL"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REQUIRE_REBIND_TO_WINDOWS_ADJUDICATED_HEAD"
owner_wave: "R02"
---
# R02_02_LOCAL_MODEL_READINESS — Readiness/Settings y descubrimiento seguro de modelos locales

## A. Objetivo y criterios de aceptación
Exponer en Settings `SUPPORTED/CONFIGURED/HEALTHY/EVALUATED/ELIGIBLE` separados; ver configuración de Ollama/LM Studio sin activar servicios y diagnóstico de hardware real cuando haya modelo instalado; model readiness por tarea, no por marca.

**IDs propietarios:** MP132-R2-07; MP132-R0-09 [dependencia diferida, no duplicar propiedad].
**Precondición:** R02-01 CLOSED, clean registry, local-only policy. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** modeling/local_provider_discovery.py, local_provider_health.py, health.py, local_endpoint_policy.py, model_gateway_settings_service.py, settings_service.py, UI Settings existente.
**Delta admisible (sujeto al diff real):** Datos de readiness desde comprobaciones reales loopback, timeout y hardware medido; UI Guided/Expert con estado y motivo, sin hacer egress. Config persistente no equivale a enable operativo.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_02_LOCAL_MODEL_READINESS.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Sin Ollama/LM Studio: `UNAVAILABLE/NOT_TESTED`, ruta D usable y cero costos; endpoints públicos o SSRF rechazados; secretos no mostrados; preferencia nunca concede permiso.

## E. Matriz focal de pruebas y laboratorio Windows
Mocks negativos y positivos + pruebas de loopback real bajo Owner, proceso/hardware reportado sin valores inventados; RBAC, CSRF, secuencias UI y browser 375.

**Verificación manual del Owner:** Capturas Guided y Expert en el momento de observar cada estado, prueba de reload y DevTools Network loopback, no capturar tokens.

**Entregables de este incremento:** Reporte de readiness/hardware y recibos reales; bundle Windows con API/UI foreground, fotos y evidencia de prueba local.

## F. Exclusiones y errores comunes
No afirmar EVALUATED sin dataset y output, no proveedor cloud.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.
