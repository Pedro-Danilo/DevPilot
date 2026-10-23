---
doc_id: MP132-R02-03-SPRINT
version: "0.1.0-DRAFT-172"
status: "DRAFT_EXECUTION_GATED"
execution_authority: false
owner_approval: "PENDING_INDIVIDUAL_APPROVAL"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REQUIRE_REBIND_TO_WINDOWS_ADJUDICATED_HEAD"
owner_wave: "R02"
---
# R02_03_OLLAMA_REAL_CANDIDATE — Primera generación real Ollama opt-in para Product Definition

## A. Objetivo y criterios de aceptación
Ejecutar verdaderas requests Ollama por loopback para Vision/Scope/Requirements, devolver CandidateEnvelope tipado y provenance, validar schema y preservar D cuando L falle; no publicar FROZEN aún.

**IDs propietarios:** MP131-R2-02.
**Precondición:** R02-02 evidencia readiness, modelo/version seleccionados por Owner. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** modeling/ollama_adapter.py, modeling/contracts.py, modeling/negotiation.py, generation/contracts.py, generation/product_definition.py, candidate_harness.py, route_policy.py.
**Delta admisible (sujeto al diff real):** Conexión UI→API→servicio→modelo real si la ruta está ausente; control de recursos/timeouts, budget local, dataset y métricas; guardar candidate persistente sin source write.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_03_OLLAMA_REAL_CANDIDATE.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Timeout, contexto insuficiente, JSON inválido, modelo ausente, respuesta alucinada, doble request y fallback REDUCED/MODEL_REQUIRED sin falso EQUIVALENT; offline D y sin cloud.

## E. Matriz focal de pruebas y laboratorio Windows
Dataset versionado mínimo con al menos 3 prompts/2 negativas, health real (nombre versión, hardware, duración medidos), pruebas contrato, seguridad y browser; no mocking en gate REAL.

**Verificación manual del Owner:** El Owner instala/ejecuta voluntariamente Ollama, selecciona modelo explícito; captura sesión sin credenciales, candidate, rechazo y hash; si no hay modelo real BLOCK/NOT_TESTED, no inventar report.

**Entregables de este incremento:** Recibo REAL_OLLAMA, casos dataset+trazas redactadas, candidatos JSON/Markdown de prueba, evidencia browser y ZIP Windows.

## F. Exclusiones y errores comunes
No autorizar auto-start, descarga de pesos, ni envío remoto por operador.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.
