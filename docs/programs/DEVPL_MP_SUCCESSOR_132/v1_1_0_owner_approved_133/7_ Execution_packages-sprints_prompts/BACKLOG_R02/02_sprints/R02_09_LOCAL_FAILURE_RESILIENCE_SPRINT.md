---
doc_id: MP132-R02-09-SPRINT
version: "0.1.0-DRAFT-172"
status: "DRAFT_EXECUTION_GATED"
execution_authority: false
owner_approval: "PENDING_INDIVIDUAL_APPROVAL"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REQUIRE_REBIND_TO_WINDOWS_ADJUDICATED_HEAD"
owner_wave: "R02"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---
# R02_09_LOCAL_FAILURE_RESILIENCE — Negativas de modelo local y reanudación segura Product Definition

## A. Objetivo y criterios de aceptación
Endurecer fallos reales de servidor local: desconexión, timeout, JSON corrupto, capability unavailable y sesión expirada; garantizar cero cambios sin permiso, sin candidatos dobles ni pérdida de docs aprobados.

**IDs propietarios:** MP131-R2-06.
**Precondición:** R02-03/04, R02-06..08; B0/B1 vigente. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** candidate lifecycle, route_policy, provider health, eval harness, current Git three-state policy and retry receipts.
**Delta admisible (sujeto al diff real):** Solo fallas reproducibles, guardando checkpoints y causal; probar cancel/retry no duplicado y no fake success después de reinicio.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_09_LOCAL_FAILURE_RESILIENCE.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Kill server durante request, JSON malicioso, caída API, stale workspace, double-submit, reinicio UI y egress deny; no loops autónomos.

## E. Matriz focal de pruebas y laboratorio Windows
Foco acumulativo con fault injection controlado, 1 test real local failure, fixtures para escenarios más costosos, repositorios/sandbox temporales, nunca destruir workspace Pilot B.

**Verificación manual del Owner:** Captura inmediatamente antes/durante/después de fallo inducido, usando copia o entorno de prueba separado y preservando B0/B1.

**Entregables de este incremento:** Matrix de riesgos y evidencia negativa cerrada, reporte replay/no data loss, guía segura.

## F. Exclusiones y errores comunes
No ejecutar pruebas destructivas sobre repositorio canónico ni enviar prompt a Internet.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

---

## Enmienda programática post-R02-06 · 187

**Aplicabilidad:** esta sección redefine las pruebas de aceptación y la ruta de autoría **solo para este sprint futuro**, manteniendo su `status: DRAFT_EXECUTION_GATED`, los ID de backlog, la prohibición de ejecutar sin aprobación Owner específica y el gate técnico de preflight rebindeado a Git. Referencia de entrada R02-06 Windows `b666c5641c1b8231c5b609216f64490a72ff1763` (la fuente efectiva se revalida al ejecutar).

**Resiliencia L-first:** simular local model unhealthy/offline, timeout, respuesta truncada/no-español, JSON/schema inválido, intento E sin egress, session expiry en edición Markdown, reintento doble, API/worker crash y cambio de contexto entre candidate y approve. Mantener un candidato inicial por defecto, retries limitados y no auto-alternatives. Candidatos, revisiones y decisiones ya persistidos son idempotentes tras restart; ninguna salida no aprobada se convierte FROZEN. `FULL_REGRESSION=0` salvo excepción por impacto documentada. Reusar operator Python robusto, Git content normalization y una guía secuencial sin falsas preimages LF/CRLF.
