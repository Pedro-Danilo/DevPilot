---
doc_id: MP132-R02-06-SPRINT
version: "0.1.1-APPROVED-179-REBIND-0386c29"
status: "SPRINT_EXECUTION_APPROVED"
execution_authority: true
owner_approval: "OWNER_APPROVED_INDIVIDUAL_R02_06_2026-10-16"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "0386c29b7e07d89b732ac1d3eb80451688026283"
owner_wave: "R02"
---
# R02_06_DL_COMPARISON_AND_REVIEW — Comparación D/L semántica con revisión Owner y provenance

## A. Objetivo y criterios de aceptación
Comparar candidate Vision/Scope/Requirements D vs L real sobre mismo contexto Pilot B, con identidad, rationale, status EQUIVALENT/REDUCED/MODEL_REQUIRED y confirmación Owner; candidato persiste separado de documento aprobado.

**IDs propietarios:** MP131-R2-04 [comparación y decisión, FROZEN se completa en R02-07].
**Precondición:** R02-03 real Ollama PASS; R02-05 Pilot B B0 existente. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** candidate lifecycle R01-02, route_policy R01-04, eval harness R01-09, context RAG, Product Definition, Settings readiness.
**Delta admisible (sujeto al diff real):** UI transparente de alternativas cuando falte, reasons y hashes, evaluaciones semánticas humanas + evidencias grounded; sin sancionar D sólo por no generar prosa equivalente.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_06_DL_COMPARISON_AND_REVIEW.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
No prometer equivalencia D cuando MODEL_REQUIRED, no autorizar al L a aprobar, no cruzar documentos/otro workspace, deny fallback no permitido y modelo offline.

## E. Matriz focal de pruebas y laboratorio Windows
Dataset D/L repetible; caso con contenido contrario a fuente y sin grounding; browser Owner selects, restart lineage, seguridad y foco accesible.

**Verificación manual del Owner:** Tomar imágenes al comparar, rechazar, elegir y recargar, con versión de modelo y desidentificación de prompts si hay secretos.

**Entregables de este incremento:** Candidate comparison receipts, human decisions, positive/negative eval, 3 candidates no FROZEN automático.

## F. Exclusiones y errores comunes
No evaluación LLM juez presentada como verdad absoluta.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

## Rebind y alcance específico — 2026-10-16

- Sprint y prompt formalizados por instrucción individual del Owner. R02-05: `CLOSED / PASS_WITH_FINDINGS`, evidencia Windows y commit `0386c29b7e07d89b732ac1d3eb80451688026283`.
- R02-03: evidencia real Ollama 3 candidatos, pero su dataset es sintético; se requieren candidatos NUEVOS vinculados al `business_need` y al SHA de Project Context B0.
- D: referencia extractiva (sin fingir cobertura RF). L: inferencia REAL Ollama local, opt-in único y sin fallback silencioso. E: prohibido.
- La revisión del Owner es solamente selección humana de candidato y clasificación justificada, **no** aprobación documental ni FROZEN. Las 3 etapas requieren prueba Windows independiente.
- La ejecución de Windows y sus validaciones continúan pendientes; el bundle aquí es un candidate, no un sucesor Git promovido.
