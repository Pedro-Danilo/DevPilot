---
doc_id: "DEVPL-GSDLC-03-B-CLOSURE-REPORT"
title: "DEVPL-GSDLC-03-B — Environment discovery and bootstrap planning closure report"
status: "closed/PASS"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "CLOSED/PASS"
---

# DEVPL-GSDLC-03-B — Closure report

## Estado

`CLOSED/PASS`. GSDLC-03-C queda autorizado por owner adjudication.

## Capacidad implementada

03-B incorpora discovery read-only tipado de Python, Node, npm, Git, filesystem y Git state; genera un `BootstrapPlan` determinístico con folders/files/Git/venv/dependency jobs/workspace registration, network/approval/side-effect/rollback metadata y una proyección UI read-only. No habilita ejecución.

## Seguridad

- `writes=0` durante discovery/planning.
- subprocess nativo `argv` + `shell=False` con timeout.
- npm en Windows resuelve `npm-cli.js` vía `node.exe`, sin `cmd.exe`.
- executable selection fail-closed ante ambigüedad.
- no environment dump ni secret values.
- remote Git no se contacta.
- rutas API requieren `human-session`; legacy token no es autoridad.
- `inventory-sales-local` no se lee ni usa como fixture.

## Contratos históricos

Se congelan snapshots 03-A-at-close de API/RBAC en 98 entradas. Los contratos current-active evolucionan a 100 mediante successors. No se reescriben freezes para obtener verde.

## Validación

Validación local focal/cumulative, API drift, RBAC, governance/TCR y Test Impact. Full regression no ejecutada por política; queda reservada a 03-E.

## PASS/BLOCK Windows

PASS exige todos los checks cumulative-selective, `writes=0`, `network_used=false`, `external_api_used=false`, `pilot_workspace_accessed=false`, snapshots históricos intactos y `S0=0/S1=0`. Cualquier desviación produce BLOCK y no autoriza 03-C.


## Windows capability recovery v1.0.1

La primera aceptación Windows bloqueó exclusivamente por dos incompatibilidades del resolvedor, no por writes, network ni defects de ApplicationService/API:

- Git de la estación quedó por debajo del `2.40` declarado en 03-A. El contrato 03-A permanece histórico e inmutable; 03-B introduce una compatibilidad successor **solo para discovery/planning**, con piso validado `2.33.0`. GSDLC-03-D debe volver a adjudicar requisitos de Git antes de mutaciones.
- Windows expone múltiples shims `npm`/`npm.cmd`; ya no se interpretan como instalaciones npm independientes. npm se resuelve desde la distribución Node seleccionada mediante `node.exe + npm-cli.js`, sin `cmd.exe`.

La aceptación v1.0.1 conserva diagnóstico completo de tools incluso cuando discovery queda BLOCK.
