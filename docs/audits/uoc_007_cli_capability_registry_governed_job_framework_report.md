---
doc_id: "DEVPL-UOC-007-CAPABILITY-JOB-FRAMEWORK-REPORT"
title: "UOC-007 — CLI Capability Registry and Governed Job Framework Report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-10"
approval: "approved_by_owner"
---

# UOC-007 — CLI Capability Registry and Governed Job Framework Report

## 1. Resultado de implementación

Estado de source: **IMPLEMENTED / PENDING AUTHORITATIVE WINDOWS CLOSURE**.

El baseline utilizado es exclusivamente `repo_DevPilot_Local_334_POST_H_EVAL_002_UOC_006.zip`, SHA-256 `b5b4ae70682a7da57de585b58e4b764f96a2d148b150f9d0c5deae2ac63b0b3a`.

## 2. Capacidades incorporadas

- registry governed-job para el inventario completo de 193 capacidades CLI/UI;
- input/output envelopes versionados;
- job state contract v2 sin modificar el schema UOC-000 histórico v1;
- budgets por capability;
- policy y approval binding declarativos;
- lifecycle completo de jobs;
- idempotency key con persistencia hash-only;
- correlation ID;
- cancel token hash-only;
- heartbeat;
- artifact/evidence references;
- atomic runtime state store;
- typed executor boundary sin shell arbitrario;
- execution hard-disabled en el registry canónico hasta que existan adapters tipados posteriores.

## 3. Reconciliación heredada UOC-006

La evidencia autoritativa UOC-006 cerró Windows/browser/Git en PASS. Repo334 conservaba tres marcadores preliminares/pending obsoletos. UOC-007 los reconcilia documentalmente sin reabrir ni alterar la funcionalidad Git UOC-006:

- `uoc_006_preliminary=false` en Project State;
- `uoc_006_preliminary=false` en UI Capability Registry;
- manifest UOC-006 actualizado para reflejar los PASS Windows ya demostrados por la evidencia final.

## 4. Seguridad

No se habilita:

- nueva ruta UI;
- arbitrary shell;
- ejecución remota;
- connector write;
- plugin execution;
- external API obligatoria;
- ejecución genérica de las 193 capacidades.

Todas las capacidades del nuevo registry empiezan con `execution_enabled=false` y `adapter_bound=false`. Este diseño evita convertir el catálogo en un router accidental.

## 5. Riesgos y limitaciones

El store de UOC-007 asume un único writer local. UOC-008 debe añadir locking/reconciliation y observabilidad operacional antes de considerar jobs de larga duración production-grade. Los parameter values no se persisten, por lo que el caller de un typed adapter debe volver a suministrarlos y el framework verifica que correspondan al fingerprint planificado.

## 6. Criterio de cierre

UOC-007 solo puede cambiar a `closed/PASS` y autorizar UOC-008 cuando la ejecución Windows entregue:

- exact source delta aplicado;
- tests focales PASS;
- schema/TCR/Project State/Docs Governance PASS;
- no-go gates intactos;
- git diff check PASS;
- source commit + fast-forward canonical;
- repo335 limpio y hash registrado;
- S0=0, S1=0.
## 7. Pruebas ejecutadas en entorno controlado

- focal UOC-006/UOC-007 + schema/global-state: `57 passed, 0 failed, 0 errors, 0 skipped`;
- capability registry structural/semantic validation: PASS, 193/193, errors=0;
- cuatro schemas nuevos: meta-schema PASS; registry instance PASS;
- TCR v1: PASS, 259 contratos;
- TCR v2: PASS, 259 contratos, dos warnings `needs-review` preexistentes;
- Project State: PASS;
- Documentation Governance: PASS, 650 documentos, 0 drift bloqueante;
- Test Impact v2: PASS, 30 changed paths, 148 matched contracts, 213 tests recomendados, 0 unmatched;
- simulación Git Windows con `core.autocrlf=true`: diff-check PASS y staging exacto 30/30.

La regresión completa se inició en el sandbox, pero excedió el presupuesto de 300 s de la herramienta antes de producir una adjudicación final; no se contabiliza como PASS ni como FAIL. Test Impact exige full regression por el alcance de Project State/docs/schema registries, por lo que el cierre Windows debe ejecutarla completa y conservar su log.

