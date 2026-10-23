---
doc_id: MP132-R02-01-SPRINT
version: "0.1.0-DRAFT-172"
status: "DRAFT_EXECUTION_GATED"
execution_authority: false
owner_approval: "PENDING_INDIVIDUAL_APPROVAL"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "REQUIRE_REBIND_TO_WINDOWS_ADJUDICATED_HEAD"
owner_wave: "R02"
---
# R02_01_AUDIT_AND_DOC_DRIFT — Rebind M1, inventario R2 y reconciliación documental activa

## A. Objetivo y criterios de aceptación
Auditar literalmente Product Definition D/L, rutas UI/API, modelo local, PESP, Source Registry, docs authority y esquemas; corregir antes de abrir R02 todo drift documental activo heredado de R00/R01 y reconciliar el programa sucesor con el HEAD; ejecutar un primer flujo D no mutativo.

**IDs propietarios:** MP131-R2-01.
**Precondición:** M1 COR171 aprobado; sin R02 previo. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** generation/product_definition.py; application/project_entry_planning_service.py; workspace/project_layout.py; docs_governance; project_state.json; source_registry.json; modeling/* y tests. Comparar fuentes reales antes de aceptar nombres.
**Delta admisible (sujeto al diff real):** Ledger de drift con clasificación ACTIVE/HISTORICAL/OBSERVE_ONLY; reconciliar TODOS los ACTIVE que afecten autoridad/status/anchors, documentos de programa actualmente instalados, enlaces del Source Registry y pruebas con identificador de sprint hardcoded. No cambiar snapshots sellados ni 1752 entradas semánticas por búsqueda global. Solo rutas auditadas con preimages Git. Si drift material no se puede reparar sin romper contratos: BLOCK, no certificar limpieza ni iniciar 02.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_01_AUDIT_AND_DOC_DRIFT.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Sin modelo L instalado funciona ruta D; tokens/sesión ajena no habilitan escritura; no borrar documentos FROZEN, ni mutar `external_api_allowed`; rechazo de drift no clasificado y de cambios externos a allowlist.

## E. Matriz focal de pruebas y laboratorio Windows
Pruebas focales Product Definition D, Doc Authority, Source Registry, 1752 parity, tests de R01 afectados; verificación Git staged/partial/restart; igualdad de contenido canónico (no bytes CRLF/LF).

**Verificación manual del Owner:** Sin UI si solo cambia docs/servicios; si corrige navegación o render, prueba browser completa y capturas en el instante indicado.

**Entregables de este incremento:** `R02_01_EVIDENCE.zip`, `repo_R02_01_CLEAN.zip`, `RESULT_R02_01.json`, `DOC_DRIFT_R02_01.md`, índices de hash y guía Windows única.

## F. Exclusiones y errores comunes
No inferencia L/E, no bootstrap Pilot B, no cambio externo ni nuevas autorizaciones de backlog.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.
