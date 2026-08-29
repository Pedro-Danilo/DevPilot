---
doc_id: "DEVPL-GSDLC-07-ACTIVATION-ENABLER-FULL-REGRESSION-V2"
title: "DEVPL-GSDLC-07 — Activation enabler: close 06 gaps and implement Full Regression Execution v2.1"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-28"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-07"
source_repo: "repo_DevPilot_Local_379_DEVPL_GSDLC_06_E_PROVIDER_SETTINGS_CONTROLLED_EVAL_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "7deeb043840945165205c8c1493b4f7e44d2b2ca"
source_repo_sha256: "859134adf86e3b58ef16434c4db7517be536a9caa08cf3fa493055c69a28d2e2"
role: "pre-functional activation enabler; not counted as 07-A..07-E feature micro-sprint"
validation_policy: "impact/selective/no-full; synthetic and bounded session tests only"
implementation_status: "implemented-initial/pass-candidate-pending-windows-owner-adjudication"
---

# DEVPL-GSDLC-07 — Activation enabler Full Regression v2.1

## A. Objetivo

Antes de 07-A funcional: cerrar los dos gaps S2 heredados de 06-E, reconciliar la autoridad repo379 en los tres estados oficiales e implementar la infraestructura mínima Full Regression Execution v2.1 para que la full de 07-E sea lógica, sharded, resumable y completion-first.

## B. Alcance

Incluye:

- activation rebind administrativo;
- erratum + corroboración RBAC focal mediante contratos existentes;
- README/state/roadmap/source-registry reconciliation;
- `FullRegressionSession`, collection, immutable plan, shard receipts, terminal accounting, resume y aggregate adjudication;
- schemas y CLI local-first;
- tests focales/sintéticos y bounded canary sessions;
- runbook Windows.

Excluye:

- 07-A agent roles/bindings;
- full regression real del backlog 07;
- pytest-xdist;
- parallel workers;
- APIs externas;
- cambio de cobertura;
- UI nueva.

## C. Arquitectura

Autoridad: `DEVPL_TESTING_FULL_REGRESSION_EXECUTION_V2_ARCHITECTURE_v1_0_0.md`.

## D. Validación

**No ejecutar full regression.** La full única de DEVPL-GSDLC-07 permanece reservada a 07-E.

Validar con:

- unit/contract tests de collection/plan/receipts/resume;
- fixture con FAIL funcional y comprobación de completion-first;
- fixture con infra abort y resume del mismo logical session;
- negative de fingerprint mismatch;
- duplicate/missing nodeid guard;
- bounded canary session sobre conjunto selectivo real;
- Documentation Governance, Project State, TCR v1/v2, Historical Contract Sweep, Contract Reconciliation, secret delta y `git diff --check`.

Browser: `0` en este activation rebind. No se modifica runtime UI; el gap de evidencia se corrige mediante erratum + prueba RBAC determinística.

## E. Criterio de salida

PASS habilita rebind de 07-A al successor del enabler. BLOCK si persiste cualquiera de los dos gaps, si el checkout/remote no se reconcilia, si resume mezcla fingerprints, si se reduce cobertura o si se consume una full real.

## F. Evolución posterior

v2.2 (duration registry/hotspots) y v2.3 (parallel-safe workers) no bloquean 07-A. Se implementan después de disponer de telemetría real; cualquier paralelización requiere clasificación explícita de recursos compartidos.


## G. Implementación v2.1 — candidate 2026-08-29

Full Regression Execution v2.1 queda implementada como `implemented-initial/pass-candidate` con superficie pública `tests full-session collect|plan|run|resume|status|adjudicate`. Se reutiliza `tests` para preservar la taxonomía CLI existente; no se crea un namespace paralelo `testing`.

La implementación incluye collector pytest por plugin (nodeids desde `session.items`), collection/plan inmutables, shards secuenciales, receipts/JUnit/hashes, completion-first, resume solo de `UNEXECUTED`, fingerprints de source/environment y adjudicación con 100% accounting.

La validación del enabler consume **0 full regressions** y **0 browser runs**. 07-A queda **autorizado a nivel de programa**, con un único gate temporal de ejecución: la primera mutación funcional requiere que este enabler obtenga owner adjudication `CLOSED/PASS` sobre Windows. Ese gate se autoextingue con la adjudicación; no requiere otro sprint, patch de activación, v2.2 ni v2.3.


## H. Autorización de 07-A

- `gsdlc_07_a_functional_authorized=true`: el backlog y el objetivo funcional están autorizados.
- Gate de ejecución: `activation-enabler-windows-owner-adjudication=CLOSED/PASS`.
- El gate es una condición de promoción de este mismo enabler, no un backlog ni micro-sprint adicional.
- Después de `CLOSED/PASS`, 07-A puede comenzar inmediatamente sobre el successor Windows-validated.
- v2.2 (telemetría/duration balancing) y v2.3 (paralelismo seguro) son optimizaciones posteriores y **no bloquean 07-A**.
