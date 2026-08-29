---
doc_id: "DEVPL-GSDLC-07-ACTIVATION-REBIND-FINAL-ADJUDICATION"
title: "DEVPL-GSDLC-07 activation rebind v1.2.0 — final adjudication"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner_evidence"
---

# DEVPL-GSDLC-07 activation rebind v1.2.0 — final adjudication

## 1. Decisión

`DEVPL-GSDLC-07-ACTIVATION-GUIDE-WINDOWS-V1-2-0 = CLOSED/PASS`.

## 2. Evidencia Windows autoritativa

- source inicial Windows: repo378 / `718fa0da5d552f8bf6def39c102f0124ac7fa922`;
- candidate materializado: semantic match PASS, mismatch=0, stale=0;
- RBAC focal: `2/2 PASS`;
- Project State / Documentation Governance / TCR v1/v2: PASS;
- browser runs: `0`;
- full regression runs: `0`;
- successor commit: `2378296abe194431894d9f25bdd1f59a81205013`;
- promoción remote: normal push PASS, no force;
- tres estados oficiales reconciliados al mismo commit: `HEAD == official/devpilot-local == origin/official/devpilot-local`;
- ZIP limpio `git archive HEAD`: SHA-256 `841d0cd1c3f9e5edba21d3e14e42d75a067d9bbfbab90af1ddf48293b7a967b4`.

## 3. Gaps 06-E

- `S2-DOC-06E-002 = CLOSED`: README ya conserva la verdad `FAIL/TIMEOUT/1-of-1/PRESERVED + composite recovery PASS`.
- `S2-EVIDENCE-06E-001 = CLOSED`: captura histórica preservada e invalidada únicamente para el claim 403/RBAC; enforcement corroborado por dos contratos RBAC determinísticos PASS.

## 4. Autoridad resultante

El ZIP repo380 Windows-validated y commit `2378296...` son la entrada del Full Regression Execution v2.1 activation enabler. Repo379 permanece como fuente técnica histórica de 06-E y provenance del rebind.

## 5. Próximo gate

07-A funcional continúa BLOCK hasta que Full Regression Execution v2.1 sea implementado, validado en Windows y owner-adjudicated. La full única de DEVPL-GSDLC-07 permanece reservada a 07-E.
