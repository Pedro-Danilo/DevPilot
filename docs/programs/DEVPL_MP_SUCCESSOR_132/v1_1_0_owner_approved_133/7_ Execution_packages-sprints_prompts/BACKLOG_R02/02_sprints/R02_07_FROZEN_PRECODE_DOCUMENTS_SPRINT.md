---
doc_id: MP132-R02-07-SPRINT
version: "0.2.0-APPROVED-187"
status: "SPRINT_EXECUTION_APPROVED"
execution_authority: true
owner_approval: "APPROVED_INDIVIDUALLY_2026-10-17"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
owner_wave: "R02"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
individual_execution_approval: "2026-10-17"
execution_branch: "evolution/multiprovider-v2"
---
# R02_07_FROZEN_PRECODE_DOCUMENTS — Publicación humana Markdown FROZEN de Vision/Scope/Requirements

## A. Objetivo y criterios de aceptación
Publicar en docs/ portables las versiones aprobadas Vision, Scope y Requirements; registrar hashes/provenance, autoridad Source Registry y versionado FROZEN; successor sólo con nuevo gate.

**IDs propietarios:** MP132-R2-08; MP131-R2-04 [completar aprobación FROZEN].
**Precondición:** R02-06 candidates Owner revisados, B0 mismo workspace. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** docs_governance/markdown_publication.py, lifecycle y frozen_successor R01, coverage gate y Document Authority; leer contratos actuales en Git.
**Delta admisible (sujeto al diff real):** Conectar UI Owner review→Markdown publication sin caminos de escritura paralelos; atomicidad, preimages, aprobación real y confirmación archivo/registro.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_07_FROZEN_PRECODE_DOCUMENTS.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobó expresamente R02-07 por instrucción de 2026-10-17; los cambios efectivos mantienen gates de escritura/seguridad.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Sin Owner, schema/grounding defectuoso, cambio tardío o conflicto de hash: ninguna publicación; original FROZEN inmutable; reintento no duplica.

## E. Matriz focal de pruebas y laboratorio Windows
Tres documentos reales con contenido Pilot B, integrity SHA, CSS UI/browser, reload/session, negativos Git lock/denied/stale; no operator write de business docs.

**Verificación manual del Owner:** Una captura inmediatamente antes de autorizar y otra tras cada publicación y recarga; verificar físicamente docs/ del Pilot B como lectura.

**Entregables de este incremento:** 3 documentos FROZEN, hashes/lineage y recibos UI, ZIP evidencia, fallback dry-run.

## F. Exclusiones y errores comunes
No autoaprobar contenido L ni escribir documentación desde operador.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

---

## Enmienda programática post-R02-06 · 187

**Aplicabilidad:** esta sección redefine las pruebas de aceptación y la ruta de autoría **solo para este sprint futuro**, con aprobación individual `status: SPRINT_EXECUTION_APPROVED`, los ID de backlog, la aprobación Owner individual ya acreditada y el gate técnico de preflight rebindeado a Git. Referencia de entrada R02-06 Windows `b666c5641c1b8231c5b609216f64490a72ff1763` (la fuente efectiva se revalida al ejecutar).

**Objeto de aceptación:** tres propuestas profesionales generadas desde la UI Pre-code con modelo local real L: Vision (beneficiarios/propuesta de valor/objetivos/indicadores), Scope (IN/OUT/DEFERRED, límites, prioridades, condiciones de salida) y Requirements (RF individual, reglas, AC, excepciones y trazabilidad). Un candidato inicial por etapa; regeneración/modelo alternativo/comparación solo por elección explícita. La generación D y el laboratorio R02-06 no acreditan B1.

**Lifecycle único:** `ContextPack + upstream FROZEN → L proposal → candidate Markdown .md inmutable y provenance → stage Quality Gate estructural/semántico → edición/revisión Owner versionada → diff/preimage → approval → apply → FROZEN`; no segundo publisher. Falla de idioma/grounding/completitud: candidate `REVIEW_REQUIRED/PARTIAL` con errores específicos, nunca aprobar automáticamente; Manual/Import gobernados pueden permitir continuar tareas si L no sirve, pero M2 exige L real competente. E no está autorizado en este incremento.

**Pruebas mínimas:** respuesta L realmente semántica, no paráfrasis de B0; cambios upstream detectados, tres `.md` FROZEN de calidad aceptable, approval exacto, campos editados en UI preservados, cambio de modelo solo bajo opt-in, no doble apply, timeout/401/JSON inválido/modelo offline y persistencia tras reinicio. La evidencia de Pilot B no puede producirse escribiendo documentos desde la consola. Contratos: ADR-013 + Coverage + Publication; `ModelAdapter` desacoplado. NO publicar si la calidad es insuficiente, aunque alargue el piloto.
