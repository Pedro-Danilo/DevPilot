---
doc_id: "DEVPL-GSDLC-02-E-CLOSURE-REPORT"
title: "DEVPL-GSDLC-02-E — Closure report / composite recovery candidate"
status: "pass-candidate/composite-windows-validated/pending-owner-adjudication"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "pending_owner_adjudication"
---
# DEVPL-GSDLC-02-E — Closure report / composite recovery candidate

## Estado
`COMPOSITE-RECOVERY-CANDIDATE / WINDOWS-RETEST-REQUIRED`. **No es CLOSED/PASS**.

## Implementación y aceptación ya demostradas

- First-run owner, login/logout, sesión expirada/revocada, protected-route guard, banner persistente de identidad/roles y Account/Role están implementados.
- C4 pre-browser v1.0.3 quedó PASS, incluyendo build Vite, gobernanza, TCR y Test Impact.
- La aceptación browser real quedó PASS con 10 screenshots sanitizados, evidencia machine-readable, `S0=0` y `S1=0`.
- El legacy local token permanece como compatibilidad de transporte y no como principal humano ni autoridad de approval.

## Full regression exactamente una vez

La única full regression autorizada del backlog se ejecutó en Windows una sola vez y **no se repetirá**. Resultado autoritativo:

```text
2345 passed
62 failed
0 errors
3 skipped
status=FAIL-COMPOSITE-RECOVERY-REQUIRED
second_run_allowed=false
```

El log original y `FULL_REGRESSION_EXACTLY_ONCE.json` son evidencia inmutable. La política del backlog exige desde este punto `validation_mode=composite-full-regression-selective-retest`.

## Causa de los residuals

Los 62 fallos se concentran principalmente en contratos históricos/current-active que no habían sido reconciliados con el successor de autenticación local: separación de rutas auth frente al registry operacional UI, lineage de package metadata UOC, autoridad human-session frente a legacy token, frozen snapshot GSDLC-00-C, API security header successor, ApplicationService security/control-plane boundary y falsos positivos del scanner de secretos sobre identificadores de código.

No se autoriza cambiar asserts históricos solo para hacer pasar pruebas. Cada ajuste debe conservar el hecho histórico o crear un successor explícito.

## Recuperación obligatoria

1. Aplicar únicamente el delta de reconciliación compuesto.
2. Verificar que el marker de full regression conserva `run_number=1` y `second_run_allowed=false`.
3. Ejecutar los **62 nodeids residuals exactos**, no la suite completa.
4. Ejecutar retest impactado acotado y validadores de gobernanza/contratos.
5. Generar Historical Regression Guard y `COMPOSITE_REGRESSION_RECOVERY.json`.
6. Cerrar solo si residuals e impactados quedan PASS, `S0=0`, `S1=0`, browser acceptance sigue válida y no se ejecutó una segunda full regression.

## Riesgos residuales

El rate limiting de login es process-local y apropiado al alcance local single-installation inicial; no es IAM distribuido. La separación entre registry operacional UI y registry de entrada/auth es un successor contractual y debe permanecer gobernada. El finding previo de supply-chain npm se conserva separado y no se corrige mediante `npm audit fix` dentro de esta recuperación.

## PASS/BLOCK

**PASS candidate:** 62/62 residuals PASS + impacted retest PASS + gobernanza/TCR/schema PASS + browser acceptance heredada válida + segunda full regression no ejecutada + S0/S1=0.

**BLOCK:** cualquier residual persistente, bypass auth/RBAC, secret leak, alteración del log/marker original, segunda full regression, relajación de no-go gates o mutación del piloto.

## 12. Windows composite recovery result

- Exact residual retest: `62/62 PASS`.
- Bounded impacted retest: `PASS`.
- Browser R1: `PASS`, inherited after bounded recovery; no login/session page logic changed.
- Original full regression remains historical `2345 passed / 62 failed / 0 errors / 3 skipped`; it was **not repeated**.
- Validation mode: `composite-full-regression-selective-retest`.
- Candidate decision: `PASS-CANDIDATE/OWNER-ADJUDICATION`.
- GSDLC-03 remains blocked until owner adjudication.
