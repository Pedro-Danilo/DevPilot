---
doc_id: MP132-R02-04-SPRINT
version: "0.1.0-DRAFT-172"
status: "DRAFT_EXECUTION_GATED"
execution_authority: false
owner_approval: "PENDING_INDIVIDUAL_APPROVAL"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REQUIRE_REBIND_TO_WINDOWS_ADJUDICATED_HEAD"
owner_wave: "R02"
---
# R02_04_LM_STUDIO_PARITY — Paridad opcional LM Studio sin degradar la ruta determinista

## A. Objetivo y criterios de aceptación
Validar el adapter local LM Studio OpenAI-compatible por loopback con health, JSON estructurado, timeout, error y fallback; comparar mismas tareas con Ollama si ambos existen, sin exigir ambos para gate M2.

**IDs propietarios:** MP131-R2-03.
**Precondición:** R02-03 PASS local o fixture D, readiness y modelo real disponible sólo si se solicita validar LM Studio. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** modeling/lmstudio_adapter.py, openai_compatible_local_adapter.py, local_endpoint_policy.py, negotiation.py y evaluadores R01.
**Delta admisible (sujeto al diff real):** Mejorar compatibilidad solo a partir de trazas observadas; registrar `DEFERRED_WITH_REASON/NOT_TESTED` si no está instalado, sin publicarlo como REAL PASS.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_04_LM_STUDIO_PARITY.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Host externo bloqueado, response malformado, health engañoso, capacidades falsas, cruce de perfiles, copia de API key por error; no fallback silencioso.

## E. Matriz focal de pruebas y laboratorio Windows
Pruebas locales reales cuando habilitado, tests mock de fallo siempre y paridad semántica controlada; medir latencia/costo real o NOT_AVAILABLE.

**Verificación manual del Owner:** Owner confirma servidor LM Studio localhost ya instalado, no instalar ni arrancar silenciosamente; comparar variantes en UI con capturas secuenciales; ausencia documentada no bloquea progreso M2 con Ollama PASS.

**Entregables de este incremento:** Recibo LM Studio real o disposición `DEFERRED_WITH_REASON`, matriz de paridad y evidencia funcional/negativa.

## F. Exclusiones y errores comunes
No hacer API externas OpenAI por usar contrato OpenAI-compatible.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.
