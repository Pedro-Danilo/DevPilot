---
doc_id: "DEVPL-UOC-005-APPROVAL-APPLY-ROLLBACK-REPORT"
title: "UOC-005 — Approval binding, atomic apply y rollback gobernado"
status: "implemented-initial"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-09"
approval: "approved_by_uoc005_closure_gate"
---

# UOC-005 — Approval binding, apply y rollback

## 1. Objetivo y base

UOC-005 implementa, únicamente sobre los planes inmutables de UOC-004, la primera escritura documental gobernada de la UI Operational Console. La base autoritativa es `repo_DevPilot_Local_332_POST_H_EVAL_002_UOC_004.zip`, closure commit `12334ffa5ea181f7d72fd66e55fb383baed2195f`.

Esta es una **primera versión `implemented-initial`**, local-first y deliberadamente estrecha. No convierte DevPilot en un editor arbitrario ni habilita `patch.apply`, rollback genérico, shell, Git stage/commit/push, remote execution, connector write o plugin execution.

## 2. Arquitectura

```text
DocumentEditPlanner
→ API tipada UOC-005
→ ApplicationService
→ WorkspaceEditExecutionApplicationService
→ PolicyEngine + StrongApprovalBinding
→ recheck plan/base hash
→ backup externo de control
→ atomic replace
→ post-validation
→ execution record + trace/report
→ rollback compensatorio o rollback manual approval-bound
```

El servicio comparte la instancia process-local de `WorkspaceEditPlanApplicationService` para impedir que un `plan_id` sea reconstruido fuera del runtime que lo creó.

## 3. Approval binding

La solicitud de apply queda ligada a:

- `plan_id`;
- `plan_hash`;
- SHA-256 base del documento;
- SHA-256 propuesto;
- `document_id` opaco;
- workspace activo;
- actor y role-at-decision;
- tool y action exactos;
- scope serializado;
- reason;
- TTL acotado al TTL del propio plan;
- interfaz UI.

`PolicyEngine` vuelve a validar el approval al aplicar. Approval ausente, expirado, denegado, reutilizado para otro scope, otro actor, otro plan/hash o un blob base modificado produce `BLOCK` antes de escribir.

## 4. Apply atómico

Antes de escribir se vuelve a resolver el documento por ID opaco y se verifica optimistic concurrency. El servicio:

1. obtiene el blob base exacto;
2. crea backup byte-exact en un control root externo al workspace;
3. verifica el SHA-256 del backup;
4. escribe en un temporal del mismo directorio;
5. hace `fsync`;
6. preserva permisos;
7. realiza `os.replace` atómico;
8. verifica SHA-256 post-apply;
9. ejecuta validación postcondición;
10. persiste un execution record y un reporte JSON sanitizado dentro del control root autorizado;
11. emite eventos de trazabilidad; la evidencia solo expone referencias relativas al control root.

La API no expone la ruta absoluta del backup; solamente `backup_ref` relativo al control root.

## 5. Rollback

Existen dos mecanismos diferentes:

### 5.1 Rollback automático compensatorio

Si el write atómico termina pero la post-validación bloquea, el mismo flujo aprobado restaura inmediatamente el backup exacto y devuelve `BLOCK`. Esta restauración es una compensating transaction, no una segunda operación discrecional.

### 5.2 Rollback manual acotado

Después de un apply PASS, el operador puede solicitar una **segunda aprobación** para rollback. Solo se permite mientras:

- el documento conserva exactamente el SHA post-apply;
- Git lo reporta como modificación unstaged;
- no fue staged;
- no fue committed;
- el backup conserva exactamente el SHA pre-apply.

Si existe stage/commit/drift, UOC-005 falla cerrado. Operaciones Git gobernadas pertenecen a UOC-006.

## 6. UX

La superficie `/workspace/documents` usa progressive disclosure:

- plan UOC-004 y diff antes de cualquier mutación;
- reason explícito;
- solicitud de approval;
- botones humanos separados Aprobar/Denegar;
- Apply deshabilitado hasta aprobación válida;
- evidencia pre/post SHA y execution ID después de apply;
- rollback como flujo independiente con nueva aprobación;
- mensajes NO-GO persistentes;
- relectura del documento tras mutación.

El S3 cosmético de `Recargar trazabilidad` se corrige eliminando styling especial y usando la misma clase `validation-action-button` que las acciones vecinas de validación.


### 6.1 Recuperación de estado UI después de apply

La aceptación browser v1.0.6 demostró que el apply backend completaba correctamente y persistía `execution_id`, backup, pre/post hashes, policy y evidence/report refs, pero la UI podía perder el estado `execution` durante la relectura del documento. La causa era un `setDocument(undefined)` transitorio emitido por `WorkspaceDocumentsView.loadDocument()` mientras el documento se recargaba después de la mutación; `DocumentEditPlanner` lo interpretaba como cambio real de documento y ejecutaba `resetExecutionState()`.

La revisión UI v1.0.1 corrige ese comportamiento sin repetir el apply:

- un `undefined` transitorio durante la recarga del mismo documento no borra la ejecución;
- el `execution_id` se guarda como hint no sensible en `sessionStorage` y en el query param `execution`;
- una ejecución persistida puede rehidratarse mediante el endpoint read-only `GET /workspace/edit-executions/{execution_id}`;
- la rehidratación exige coincidencia exacta de `document_id`, ruta relativa y SHA pre/post;
- el panel de governance puede renderizar una ejecución recuperada aun cuando el plan process-local ya no esté disponible;
- la recovery path nunca invoca `applyWorkspaceEdit` ni `rollbackWorkspaceEdit` automáticamente;
- execution card expone Approval ID, pre/post/restored SHA y refs de backup/evidence/report.

Este recovery es deliberadamente fail-closed y está pensado para continuidad browser tras reload/restart. No amplía permisos ni crea una mutación adicional.

## 7. Seguridad y no-go gates

Se preservan:

- no arbitrary shell;
- no generic `patch.apply`;
- no generic rollback executor;
- no Git write;
- no remote execution;
- no connector write;
- no plugin execution;
- no API externa obligatoria;
- no ruta absoluta recibida del browser como autoridad;
- actor/approval/hash/scope/TTL obligatorios;
- control root fuera del workspace.

UOC-005 registra exclusivamente dos sensitive actions nuevas: `filesystem.workspace_document_apply` y `filesystem.workspace_document_rollback`.

## 8. Evidencia técnica local de implementación

La validación de desarrollo debe incluir como mínimo:

- unit tests del servicio apply/rollback;
- API flow y API route-policy contracts;
- UI source contract UOC-004/UOC-005;
- TypeScript `--noEmit`;
- schema registry;
- API contract drift;
- UI route enforcement;
- TCR v1/v2;
- Project State;
- Documentation Governance;
- Vite build y smokes en Windows;
- browser acceptance real de apply y rollback sobre fixture controlado.

La validación local controlada del candidato registró: `24/24` pruebas focales UOC-005 PASS; `135/135` pruebas acumulativas de alto riesgo PASS; MIASI, Validation Gateway, API contract drift, UI route enforcement, TCR v1/v2, Project State y Documentation Governance PASS; cuatro smokes Node PASS y TypeScript `--noEmit` PASS. Test Impact v2 inicial clasificó 58 paths contra 153 contratos; tras la reconciliación heredada v1.0.2 el contrato final de implementación es 60 paths contra los mismos 153 contratos, con `0` paths sin cobertura. Por esta transversalidad, la regresión general es obligatoria en Windows antes del cierre. La corrida full-suite del sandbox Linux no se adjudica porque el entorno agotó su ventana de ejecución; tampoco se declara Vite build local porque el mirror npm del sandbox devolvió 404 para `vite@6.4.3`. Ambos gates quedan explícitamente en la validación Windows.

La adjudicación final y los conteos autoritativos se registran en `docs/audits/uoc_005_closure_report.md` y `docs/post_h_eval_002_uoc_005_manifest.json` después de la corrida Windows.

## 9. Criterios PASS/BLOCK

### PASS

- apply PASS sobre fixture con approval exacto;
- rollback manual PASS sobre fixture antes de stage/commit;
- rollback automático PASS cuando post-validation bloquea;
- approval ausente/expirado/denegado/hash distinto/scope distinto bloquea;
- stale source bloquea;
- backup exacto y externo al workspace;
- zero writes outside active workspace excepto control/evidence roots autorizados;
- Git stage/commit permanecen `false`;
- S0=0 y S1=0;
- browser confirma el flujo visible y comprensible;
- contratos globales y documentación sincronizados.

### BLOCK

Cualquier escritura sin approval válido, pérdida de atomicidad, backup inválido, rollback fuera de su ventana pre-commit, drift de hash, exposición de rutas/secretos, acción genérica habilitada, S0/S1 o fallo de contrato acumulativo bloquea el cierre.

## 10. Riesgos y limitaciones

- Los planes UOC-004 siguen process-local con TTL corto; persistencia autoritativa de jobs pertenece a UOC-007/UOC-008.
- El primer UOC-005 solo muta Markdown/JSON/YAML permitidos por UOC-004.
- El rollback manual termina antes de Git stage/commit; UOC-006 implementará operaciones Git gobernadas.
- El control root runtime debe estar fuera del workspace; no forma parte del ZIP fuente limpio.
- Esta implementación no sustituye un journal transaccional industrial ni durability multi-process; requiere evolución posterior.

## 11. Comandos de verificación

Los comandos operativos autoritativos para Windows están centralizados en la guía de implementación entregada con el sprint. No deben copiarse desde versiones anteriores del runbook.

## 12. Correctivo de regresión de gobernanza — v1.0.1

La primera regresión general Windows de UOC-005 alcanzó aproximadamente 20% antes de que el watchdog histórico de 7200 s terminara pytest. Antes del timeout ya se habían observado fallos en gates históricos de Approval/RBAC, MIASI semantic y perfiles de Quality/Industrial Readiness. El diagnóstico determinista identificó dos incompatibilidades introducidas por la primera materialización UOC-005:

1. `.devpilot/approval/sensitive_action_catalog.json` alteró la procedencia `created_by` y añadió `updated`, incumpliendo `SensitiveActionCatalog` schema v1. El correctivo conserva `created_by=POST-H-012-A`, elimina la propiedad no permitida y mantiene las dos acciones UOC-005 como extensión gobernada por manifest/TCR.
2. Las reglas `WORKSPACE_DOCUMENT_APPLY_APPROVAL_GATED` y `WORKSPACE_DOCUMENT_ROLLBACK_APPROVAL_GATED` declaraban aprobación obligatoria pero el texto de gate no hacía explícito `ApprovalPolicyChecker`/RBAC, por lo que `SEM-APPROVAL-SCOPE-001` las clasificaba como aprobación genérica. El correctivo documenta los checkers reales ya usados por `PolicyEngine`: `ApprovalPolicyChecker`, `StrongApprovalBindingValidator` y `RBAC(owner)`.

No se relajó ningún schema, validator, no-go gate ni política. Se añadieron guards de regresión al contrato UOC-005 para impedir que ambos drifts reaparezcan. La regresión general Windows debe repetirse sobre este payload corregido antes de browser acceptance y cierre.



## 13. Correctivo pre-full de gobernanza heredada — source payload v1.0.2

La verificación pre-full Windows v1.0.3 confirmó que los correctivos de Sensitive Action Catalog y MIASI ya estaban PASS, pero expuso tres inconsistencias acumulativas independientes: (1) `DocumentationSyncValidator._roadmap_sync_passed()` filtraba el `counterpart_path` con el identificador del JSON fuente y por tanto devolvía `false` aunque los tres checks roadmap fueran `ok=true`; (2) `docs/audits/uoc_004_closure_report.md` conservaba status `approved` sin campo `approval`, generando un warning histórico; y (3) `.devpilot/release/local_release_candidate_criteria.json` declaraba repo 332 en `expected_current_repo` pero aún esperaba repo 331 dentro de `project-state-current-repo.expected_fields.current_repo`, haciendo stale la evidencia crítica del Local Release Candidate.

El correctivo v1.0.2 no relaja validators ni quality gates. Corrige la detección del par roadmap usando `source_path` o `counterpart_path`, completa el frontmatter UOC-004 con `approval: approved_by_owner` y sincroniza la freshness del release candidate con el repo 332 autoritativo. Los dos paths heredados fuera del delta UOC-005 original se incorporan formalmente al source contract, que pasa de 58 a 60 paths. La regresión general permanece obligatoria y debe ejecutarse con `maxfail=1` y evidencia de primer fallo antes de browser acceptance.


## 14. Reconciliación de contratos históricos y estrategia incremental — source payload v1.0.4

La corrida Windows v1.0.4 acreditó `625 passed` antes de detenerse en `tests/test_post_h_014_api_route_contracts.py::test_post_h_014_a_mutating_routes_are_explicitly_justified_and_local_only`. El fallo no demostraba una ruta insegura: el contrato POST-H-014-A congelaba por igualdad exacta las tres mutaciones de ApprovalStore existentes cuando se creó, mientras UOC-003 y UOC-005 añadieron mutaciones locales tipadas y dos source writes estrechos approval-bound. El contrato histórico se evoluciona para preservar invariantes de seguridad y, hasta UOC-006, exigir que las únicas rutas `source_mutation_allowed=true` sean apply y rollback UOC-005.

El barrido histórico focal detectó además dos freezes de lifecycle: el test de perfiles TCR v2 fijaba `mutations_allowed_total=0/source_mutations_allowed_total=1`, y UOC-000 seguía exigiendo `current_sprint=UOC-002`, runtime execution siempre false y feature flags posteriores deshabilitados aunque UOC-003..005 ya fueron autorizados. Esos tests ahora distinguen el snapshot histórico UOC-000 de los registries lifecycle actuales.

El barrido reveló además un drift de inventario real: `ui_capability_registry.summary.api_routes_total` permanecía en 50 mientras el API Route Registry vigente contiene 58 rutas; se reconcilia dinámicamente con el inventario autoritativo. También reveló dos drifts de schema reales: `ui_capability_registry.schema.json` mantenía `runtime_execution_enabled const=false` pese a la evolución tipada UOC-003..005, y `ui_operational_console_flags.schema.json` no admitía `notes` en kill switches aunque el registry lifecycle ya las usa. Ambos schemas evolucionan de forma backward-compatible; no se relaja ningún no-go de shell, remote execution, connector write, plugin execution ni external API.

Por costo y trazabilidad, a partir de v1.0.5 no se reinicia la suite completa de 2117 tests. Se reutilizan criptográficamente los 625 PASS de v1.0.4 cuya fuente no fue invalidada, se reejecutan todos los tests afectados por el delta correctivo de 12 paths y el source contract total de 67 paths mediante Test Impact y un historical-freeze sweep, y se exige un waiver formal de `HistoricalRegressionGuard` aprobado por el owner para omitir únicamente los tests históricos no impactados. Esta estrategia no convierte una corrida parcial en full-regression PASS: la decisión se registra explícitamente como `waiver/evidence-reuse-selective-completion`.


## 15. Reconciliación adicional v1.0.5 — UOC-002 lifecycle freeze

El barrido selectivo posterior detectó dos assertions del recovery UOC-002 congeladas en el lifecycle UOC-003 (`current_repo` y `last_registered_sprint`). Se evolucionan para derivar el baseline y la identidad documental desde el sprint UOC más avanzado realmente presente. El source contract final UOC-005 pasa a **67 paths** (9 added, 58 modified, 0 deleted). Esta corrección no altera runtime de apply/rollback ni relaja validators.


## 16. Reconciliación adicional v1.0.5 — 01-C documentation registry lifecycle

El barrido ampliado encontró que `tests/test_post_h_eval_002_01_c_api_ui_startup_security_posture.py` conservaba una allowlist de `last_registered_sprint` detenida en UOC-002. El snapshot histórico de 01-C permanece congelado, pero el registry global puede avanzar legítimamente hasta UOC-005. El test ahora deriva el estado permitido desde Project State. El source contract acumulativo UOC-005 queda en **67 paths** (9 added, 58 modified, 0 deleted); el delta respecto al checkpoint Windows v1.0.4 es de **12 paths**.


## 17. Test Impact final v1.0.5

El delta correctivo real desde el checkpoint Windows v1.0.4 contiene **12 paths**, selecciona **53 contratos** (P0=34, P1=18), recomienda 110 tests y tiene **0 unmatched paths**. El contrato acumulativo UOC-005 contiene **67 paths**, selecciona **154 contratos** (P0=61, P1=82), recomienda 220 tests y también tiene **0 unmatched paths**. Estas recomendaciones se usan como mapa de impacto, no como instrucción para repetir wrappers equivalentes: la selección ejecutable se deduplica por superficie autoritativa y evidencia previa compatible.


## 18. Validación controlada final del sweep histórico

El sweep histórico/lifecycle consolidado ejecutado sobre el payload v1.0.4 obtuvo **113 passed, 0 failed, 0 errors, 0 skipped**. El audit estático ampliado inspeccionó **399 archivos de test**, clasificó **39 candidatos** sensibles a lifecycle/repos/rutas/runtime/counts y dejó **0 unresolved**. Documentation Governance pasó con 637 documentos revisados, 0 warnings, 0 blocking y `roadmap_markdown_json_sync_passed=true`. Los dos registries UOC-000 evolucionados validan contra sus schemas actuales sin errores.

## 13. Evidencia autoritativa de cierre

HistoricalRegressionGuard `waiver/evidence-reuse-delta5-ui-recovery`, recuperación UI post-apply, browser apply/rollback y canonical integration cerraron PASS sobre source commit `ee9e4ddda7b7e49a65ed8ce495f0fecd82541156`. El baseline autoritativo se genera como `repo_DevPilot_Local_333_POST_H_EVAL_002_UOC_005.zip`. La capacidad continúa declarada `implemented-initial`; el cierre del sprint no elimina sus límites de primera versión. El correctivo de lifecycle `v1.0.11` modifica únicamente el contrato de prueba para hacerlo consciente del estado pre/post cierre; no cambia runtime y reutiliza la evidencia browser ya PASS.
