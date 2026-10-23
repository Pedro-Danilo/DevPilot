---
doc_id: MP132-R02-08-SPRINT
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
# R02_08_PRODUCT_COVERAGE_SEMANTIC — PESP y Coverage Gate para Product Definition contextual

## A. Objetivo y criterios de aceptación
Evaluar aplicabilidad MIPSoftware y MIASI condicional a B0/B1, completitud/groundedness de Vision/Scope/Requirements, bloqueos significativos, N/A justificado y waivers con autoridad; no exigir arquitectura/tech antes de tiempo.

**IDs propietarios:** MP132-R2-09.
**Precondición:** R02-07 pre-code FROZEN, profile provisional de B0. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** artifact_coverage_gate.py, PESP service R01-05, candidate_harness.py, Source Registry, registro de normas.
**Delta admisible (sujeto al diff real):** Reglas semánticas de Product Definition con fuentes reales y revisión Owner, sin duplicar evaluador; evidencia de referencias verificadas, missing required y diferencias de juicio del modelo.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_08_PRODUCT_COVERAGE_SEMANTIC.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Plantillas vacías, N/A automático, waiver sin Owner, hallucination source, MIASI obligatorio sin componente IA en app y falsos FAIL históricos deben bloquear o clasificarse bien.

## E. Matriz focal de pruebas y laboratorio Windows
Positive/negative cases, 1 waiver razonado, 1 NO_APLICA, 1 grounding negativo; browser Guided/Expert si UI cambia; test impacto.

**Verificación manual del Owner:** El Owner revisa claramente qué falta y por qué; captura en el momento exacto del Coverage plan y de resolución del bloqueo.

**Entregables de este incremento:** Reporte Coverage-PESP real de Pilot B B1, evidencias de calidad, decisiones Owner, documentación vigente.

## F. Exclusiones y errores comunes
No prometer calidad semántica absoluta mediante reglas D.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

---

## Enmienda programática post-R02-06 · 187

**Aplicabilidad:** esta sección redefine las pruebas de aceptación y la ruta de autoría **solo para este sprint futuro**, manteniendo su `status: DRAFT_EXECUTION_GATED`, los ID de backlog, la prohibición de ejecutar sin aprobación Owner específica y el gate técnico de preflight rebindeado a Git. Referencia de entrada R02-06 Windows `b666c5641c1b8231c5b609216f64490a72ff1763` (la fuente efectiva se revalida al ejecutar).

**Objetivo de aceptación específico:** Coverage Gate extendido después de que R02-07 haya aplicado quality mínimo **antes** de FROZEN; comprobar semántica transversal Vision→Scope→Requirements, PESP vigente, fuentes/decisiones sin inventar y mecanismos de successor para errores reales. Evaluar `coverage RF`, exclusiones justificadas, reglas de negocio comprobables, AC observables, idioma requerido, riesgos normativos y consistencia; registrar calidad de modelo sin fingir certeza automática. Los defectos graves ya existentes que afecten a FROZEN requieren plan de successor/impacto, nunca edición in-place ni repetición de approvals inocuos. No introducir gate humano para verificaciones de hashes/índices.

---

## Adenda A188 — contexto de diseño futuro, sprint NO activado

Norma Owner aprobada: `0_program/12_ENMIENDA_188_APROBADA.md`, ADR-016 y contrato transversal de calidad. **Conservar estado de sprint `DRAFT_EXECUTION_GATED`, ejecución no autorizada por esta adenda**. Al solicitar ejecución, anclar a Git `3a0a170f3c646e9955966576dd9212d3f87450e6` y FROZEN Pilot B `04ca8f83618176f5b14470bcaa092f979e3b6e72`, verificar Source Registry y código vigente. Demostrar segundo dominio sintético, `REQUIRED/CONDITIONAL/NOT_APPLICABLE`, grounding y cross-artifact material con reglas proporcionales. No generalizar Architecture/Planning/Construction aquí, no reabrir FROZEN in-place, no forzar E ni full regression.
