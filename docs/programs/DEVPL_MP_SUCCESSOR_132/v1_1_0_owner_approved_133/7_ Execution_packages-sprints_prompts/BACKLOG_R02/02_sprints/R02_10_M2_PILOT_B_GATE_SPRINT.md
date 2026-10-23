---
doc_id: MP132-R02-10-SPRINT
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
# R02_10_M2_PILOT_B_GATE — Cierre M2: Pilot B B0–B1 y modelo local real

## A. Objetivo y criterios de aceptación
Evaluar Pilot B B0→B1 por UI normal con tres documentos FROZEN, ruta L competente real (comparación D/L no obligatoria), lineage, PESP, Coverage y aceptación de negativas; concluir PASS/PASS_WITH_FINDINGS/PARTIAL/BLOCK honesto.

**IDs propietarios:** MP131-R2-05 [milestone B1]; gate M2 R02 completo.
**Precondición:** R02-01..09 aceptados o diferidos con razón compatible; B0 único real. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** R01M1Gate como evidencia de entrada, Program maturity matrix, Product Definition, Workspace stores, Browser receipt y Git manifests.
**Delta admisible (sujeto al diff real):** M2AcceptanceReport con pruebas de extremo a extremo de Product Definition, no nuevo workflow; carpeta y documentos portables y control de scripts operator_project_writes=0.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_10_M2_PILOT_B_GATE.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
No modelo real, documento no FROZEN, objeto Pilot B regenerado, write via operator, falta de consentimiento, proveedor externo o grounding no verificado: impedir M2 PASS.

## E. Matriz focal de pruebas y laboratorio Windows
Recibos R02-01..09 y hashes, modelo real hardware/model/version/dataset, browser navegable y restart, replay negativo; full regression solo con excepción explícita documentada si gate lo exige.

**Verificación manual del Owner:** Journey continuo Owner desde Project Home a Requirements FROZEN con capturas en puntos exactos de la guía, sin terminal para negocio ni stack prematuro.

**Entregables de este incremento:** M2_REPORT, evidencia B0/B1 real y Git ZIP/SHA, cierre R02 sujeto a adjudicación Owner separada.

## F. Exclusiones y errores comunes
No autoriza R03, R08 external, agentes write o MP-1B.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

---

## Enmienda programática post-R02-06 · 187

**Aplicabilidad:** esta sección redefine las pruebas de aceptación y la ruta de autoría **solo para este sprint futuro**, manteniendo su `status: DRAFT_EXECUTION_GATED`, los ID de backlog, la prohibición de ejecutar sin aprobación Owner específica y el gate técnico de preflight rebindeado a Git. Referencia de entrada R02-06 Windows `b666c5641c1b8231c5b609216f64490a72ff1763` (la fuente efectiva se revalida al ejecutar).

**M2 gate actualizado:** comprobar B0 UI persistido y el B1 real con Vision, Scope y Requirements `.md` versionados/revisados/FROZEN, cada etapa con L real elegido por capacidad, contexto/provenance/hardware/model/prompt y quality específico. **No se exige D/L para el mismo artefacto**: los receipts D/L de R02-06 se archivan como evaluación anterior, nunca como Quality PASS de nuevos docs. Verificar lineage up/downstream, 3 approval/freeze, idempotencia tras API/UI restart, cobertura profesional/MIASI aplicable y `operator_project_writes=0`. Prohibido elevar M2 si los tres textos son resúmenes de B0 o si solo existe mock/manual sin demostración generativa local competente. No habilita E, R3 ni release.
