---
doc_id: "DEVPL-GSDLC-06-E-CLOSURE-REPORT"
title: "DEVPL-GSDLC-06-E — Provider Settings UX and controlled model evaluation — implementation report"
status: "closed/PASS-WITH-GAPS"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-27"
approval: "approved_by_owner"
---

# DEVPL-GSDLC-06-E — Implementation report

## Estado

`PASS-CANDIDATE / WINDOWS-COMPOSITE-VALIDATED / PENDING-OWNER-ADJUDICATION`. El browser run histórico fue declarado 13/13 y Predictive Pre-Full quedó PASS; posteriormente se detectó que una captura RBAC no demostraba el claim descrito y queda gobernada por `DEVPL_GSDLC_06_E_EVIDENCE_ERRATUM_v1_0_0.md`. La full única fue consumida `1/1` y terminó `FAIL/TIMEOUT`; su evidencia permanece inmutable y no se repitió. El cierre técnico continúa únicamente por `composite-full-regression-selective-retest` y todavía **no** declara `CLOSED/PASS` hasta la adjudicación owner.

## Capacidades implementadas

- `AIControlCenterView` como shell de administración IA con fronteras explícitas;
- `ModelSettingsView` para provider/model/access-route, disposition, enabled/health, capabilities, privacy/data class, region, auth-adapter, freshness, tokens/cost, budget y fallback;
- proyección server-side `ModelGatewaySettingsService` con credenciales reference-only/masked;
- evaluación hermética `mock`, `fake-local`, `fake-external`; API real no requerida;
- hard-stop de presupuesto visible y probado;
- `disable/revoke` desde navegador reutilizando el enablement runtime owner-only de 06-C;
- endpoints `GET /api/v1/settings/model-gateway` y `POST /api/v1/settings/model-gateway/evaluate`;
- RBAC human-session, sin legacy token para la nueva superficie;
- `ModelRouteDecision` permanece separado de `ToolExecutionDecision`;
- lazy capability composition para no convertir 06-E en requisito de fixtures/workspaces históricos.

## Validación local

- nuevos contratos 06-E: `6/6 PASS`;
- matriz selectiva/acumulativa local: `155/155 PASS`;
- UI model-settings static smoke: `8/8 PASS`;
- full regression local: `0`; Windows authoritative full: `FAIL/TIMEOUT/1-of-1/PRESERVED`; composite recovery: `PASS`;
- browser local: `0`; Windows browser acceptance: `PASS/13`;
- external network/API real: `0`.

## Riesgos y limitaciones

1. El browser acceptance de 13 casos debe ejecutarse sobre Windows con sesión humana real y evidencia screenshot.
2. El build Vite/TypeScript se valida en Windows usando dependencias ya provisionadas; el bundle no instala dependencias automáticamente.
3. La única full regression del backlog no se consume en este entorno. Si falla en Windows, está prohibido repetirla.
4. El costo real de APIs externas no se presupone: valores `unknown` permanecen `null` y enablement real conserva ADR/freshness/RBAC/budget/approval.
5. Esta es la primera versión industrializable de Provider Settings UX; tuning visual, benchmarking real y proveedores adicionales pueden evolucionar después.

## Criterios PASS/BLOCK

**PASS de implementación local:** 6/6 nuevos + 155/155 selectivas/acumulativas + static smoke, S0/S1=0, secrets=0, red=0 y full=0.  
**PASS final del sprint:** browser 13/13, predictive PASS, full `1/1 PASS` o composite recovery válida, post-finalize validators PASS, repo-review clean y owner adjudication.  
**BLOCK:** credential visible, costo ausente/engañoso, route→tool escalation, remote-as-local, provider habilitado sin gates, drift pre-full conocido o intento de rerun de full.

## Comandos de verificación

Los comandos autoritativos para Windows se entregan únicamente en `GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_06_E_v1_0_0.md` dentro del bundle, para evitar instrucciones paralelas contradictorias.


## 10. Windows composite recovery v1.0.7

La full autoritativa fue consumida exactamente una vez y agotó el timeout de 4 horas alrededor del 82 %, con 21 marcas FAIL observadas, 5 skips Windows y 487 tests no ejecutados. No se ejecutó una segunda full. El recovery reconstruyó en Windows la colección original de 2742 nodeids y materializó 21 failed nodeids + 487-node unexecuted tail.

El corrective reconcilia dos raíces: ocho rutas GSDLC-06 ausentes del OpenAPI estático y un contrato histórico 05-A que comparaba un snapshot cerrado contra `gsdlc_current_micro_sprint` mutable. La recuperación exige exact failed-nodeid retest `21/21`, tail no ejecutado `487/487`, bounded impact `14/14`, ApiContractDriftGuard PASS, Historical Regression Guard PASS, Documentation Governance / Project State / TCR v1/v2 PASS, S0=0/S1=0 y runtime DB limpio.

El modo final es `composite-full-regression-selective-retest = PASS`. La historia original `FAIL/TIMEOUT/1-of-1` permanece inmutable y `rerun_allowed=false`.


## 11. Owner adjudication incorporated by GSDLC-07 activation rebind

Estado final: `CLOSED/PASS-WITH-GAPS`. Se aceptaron exclusivamente `S2-EVIDENCE-06E-001` y `S2-DOC-06E-002`. El activation rebind los resuelve sin reabrir runtime: README se corrige y la evidencia RBAC defectuosa se invalida para ese claim mediante erratum + contratos determinísticos focales. La full original permanece `FAIL/TIMEOUT/1-of-1/PRESERVED`; no existe rerun.
