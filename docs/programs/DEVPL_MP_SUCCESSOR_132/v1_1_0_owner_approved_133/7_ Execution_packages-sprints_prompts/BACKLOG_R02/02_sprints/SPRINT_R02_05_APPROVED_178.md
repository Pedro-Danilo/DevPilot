---
doc_id: MP132-R02-05-SPRINT
version: "0.1.0-DRAFT-172"
status: "SPRINT_EXECUTION_APPROVED"
execution_authority: true
owner_approval: "OWNER_APPROVED_INDIVIDUAL_R02_05"
program_backlog: "BACKLOG_R02_132.md"
planning_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
execution_baseline: "735ecfd82e9604a4755fd7d4e7c386976984ed71"
owner_wave: "R02"
---
# R02_05_PILOT_B_ENTRY_RESUME — Pilot B B0: Project Home/Entry neutral y reanudación

## A. Objetivo y criterios de aceptación
Crear realmente desde UI el único workspace Pilot B B0 para microempresa bienestar/cuidado personal: necesidad y constraints en lenguaje negocio, roots, PESP provisional, sin stack forzado; Project Home debe navegar/resumir con estado persistente.

**IDs propietarios:** MP132-R2-10; MP131-R2-05 [milestone B0 compartido, owner principal R02-10].
**Precondición:** R02-01 documental limpio, settings segura; R02-03 modelo local si se requiere L en intake. Se verifica contra evidencia y Git; si no se cumple, `BLOCK`, sin avanzar por suposición.

## B. Audit-first y arquitectura / responsabilidades
**Rutas candidatas que se DEBEN inspeccionar, no allowlist preaprobada:** workspace/project_entry_contracts.py, project_entry_planning_service.py, project_entry router, neutral bootstrap GSDLC13, ProjectHome y navegación ProjectStatus.
**Delta admisible (sujeto al diff real):** Solo descubribilidad/continuidad faltante verificada: entrada, enlace directo y vuelta, contexto claro de workspace actual, recuperación del mismo ID después de restart.

**Frontera:** no duplicar motor de candidatos, política, publicación, aprobación ni Git. Reuse/Delta `REUSE_AS_IS|EXTEND|NEW|NO_OP` con evidencia. ADR nueva solo si se cambia una autoridad o frontera; jamás autorizar por crear este documento.

## C. Implementación y gates ejecutables
1. **A0:** confirmar rama, HEAD, tres estados Git, upstream, recibo Windows del predecesor, workspace y owner; no modificar baseline.
2. **A1:** abrir literalmente código/tests/docs/UX del HEAD y generar `REUSE_DELTA_R02_05_PILOT_B_ENTRY_RESUME.md`, pruebas existentes, riesgos y backlog exacto.
3. **A2:** seleccionar la mínima allowlist por rutas exactas **después** de auditoría; especificar validación de seguridad, permisos, costo y ADR si aplica. Owner aprobará el incremento individual antes de ejecutar.
4. **A3:** preparar parche y operador Python sobre copia aislada, dry-run con blobs Git, negar cambios ajenos y conservar state reusable.
5. **A4:** aplicar solo scope aprobado y probar contratos positivos, negativos, idempotencia y seguridad antes de commit.
6. **A5:** comprobar UI/browser y proveedor REAL sólo cuando ese resultado forme parte del AC; empacar screenshots inmediatamente según su momento, no al final sin contexto.
7. **A6:** commit, push normal solo tras gates/consentimientos materiales; empaquetar ZIP SHA y Git archive; veredicto `PASS|PASS_WITH_FINDINGS|PARTIAL|BLOCK|NO_OP_ACCEPTED` con limitaciones; siguiente sprint NO autorizado.

## D. Negativas y criterios de seguridad
Ningún comando manual para crear archivos de Pilot B; sin .venv/scaffold/source write; tokens/paths fuera de workspace denegados; no reutilizar inventory-sales-local-greenfield como B0.

## E. Matriz focal de pruebas y laboratorio Windows
UI/API real browser, persistencia 2 sesiones, rol humano, drive pathguard, reinicio, capturas inmediatamente al crear/retomar, mobile 375.

**Verificación manual del Owner:** Owner elige nombre/ruta nueva y redacta necesidad. No usar operadores para crear artefactos de negocio; evidencia del workspace real B0.

**Entregables de este incremento:** Receipt B0 + evidence UI + bootstrap solo autorizado + ZIP; mismo workspace será usado en B1 y olas R3–R10.

## F. Exclusiones y errores comunes
No requisitos RF ni stack precargados, no crear demo artificial.

## G. Checkpoints de continuidad y límites
- C0: documento/HEAD e impacto inspeccionados; C1: contrato/diff; C2: código aislado + negativos; C3: simulación Git; C4: bundle local QA; C5: recepción Windows/Owner; C6: cierre.
- Registro: Fecha / Tema / Laboratorio / Resultado / Errores / Solución / Aprendizaje / Próximo paso; todo evidencia/código publicado con huellas, sin alterar snapshots FROZEN.
- Control presupuestal: D/mock sin costo ni key. L = hardware local y recursos medidos sin API paga. E = denegado. Máximo número de reintentos y límite temporal definidos antes de invocar modelo.
- Ejecución, proveedores y pasos siguientes no autorizados por este DRAFT.

## Rebind COR178 — ejecución individual Owner

Baseline canónico R02-04 Windows: `735ecfd82e9604a4755fd7d4e7c386976984ed71`. R02-05 exclusivamente B0 neutral/reanudación. El runtime registry existente es autoridad, Home es proyección read-only. Al reemplazar el active workspace, el API se reinicia para rebind de variables del servidor; no se fuerzan roles ni se escriben artefactos de negocio desde el operador. R02-06 NO autorizado.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

**COR-179 rebinding de coordinación aprobado por decisión Owner UI-first:** permanece `SPRINT_EXECUTION_APPROVED`, HEAD base `735ecfd82e9604a4755fd7d4e7c386976984ed71`, R02-05 únicamente. Antes de UI, `snapshot` read-only del registry existente; el Owner define ID/nombre/root/need solo en Project Entry; después se descubre único nuevo registro y se enlaza B0 para comparar tras restart. Parent PathGuard aprobado es configuración de instalación, no input de identidad del piloto. COR-178 deja de ser guía ejecutable. Sin iniciar B1/R02-06.
