---
doc_id: "DEVPL-GSDLC-06-B-CLOSURE-REPORT"
title: "GSDLC-06-B — Local provider discovery and OpenAI-compatible hardening closure report"
status: "pass-candidate/windows-validated/pending-owner-adjudication"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-26"
approval: "pending_windows_and_owner"
---

# GSDLC-06-B closure report

## 1. Decisión actual

`PASS-CANDIDATE / WINDOWS-VALIDATED / PENDING-OWNER-ADJUDICATION`.

06-B endurece las rutas locales Ollama, LM Studio y generic OpenAI-compatible sin habilitarlas por discovery. El generic route exige allowlist loopback explícita; el wire protocol OpenAI no confiere localidad ni autorización.

## 2. Capacidades implementadas

- `LocalEndpointPolicy` tipada y fail-closed.
- loopback IPv4/IPv6/localhost normalizado; DNS/host ambiguo, userinfo, query, fragment, base path y esquema inválido bloqueados.
- redirects no seguidos; timeout, payload y número de modelos acotados.
- `OpenAICompatibleLocalAdapter` v2.
- `LocalProviderDiscoveryService` con estados separados `configured`, `reachable`, `healthy`, `model_discovered`, `enabled`.
- discovery read-only: nunca cambia `enabled`.
- hardware-fit R01 advisory/non-authoritative.
- fallback explícito y auditable a Mock; no silent fallback.
- metadata Settings redactada; sin raw secrets.

## 3. Validación local

73/73 pruebas selectivas PASS, por grupos bounded: 13 nuevas 06-B + 13 compatibilidad 06-A + 17 adapters/hardening históricos + 11 governance/reconciliation + 8 provider schema + 10 Settings API + 1 historical current-pointer guard. Los fake servers solo usan loopback; no hay API externa ni proveedor real como requisito.

Historical Contract Sweep y Contract Reconciliation Sweep locales: PASS. Documentation Governance / Project State / TCR v1 / TCR v2: PASS (`295` contratos). `full_regression_runs=0`; la full única del backlog permanece reservada para 06-E. Browser no es requisito de 06-B porque no se introduce una nueva vista ni journey UI; se valida el contrato Settings API/metadata.

## 4. Riesgos y limitaciones

Esta es una primera versión endurecida local. No prueba rendimiento real de Ollama/LM Studio, disponibilidad de modelos del host ni ajuste de hardware en producción. Esas verificaciones reales son opcionales y no constituyen criterio PASS. Provider enablement externo pertenece a 06-C.

## 5. PASS / BLOCK

PASS: Mock + fake-local, remote nunca local, calls bounded, redirects fail-closed, discovery no habilita, fallback explícito, secretos ausentes, 06-A preservado, S0/S1=0.

BLOCK: SSRF/remote-as-local, call unbounded, discovery cambia `enabled`, raw secret, silent fallback, ruptura de contratos 06-A/históricos o full regression ejecutada sin excepción aprobada.

## 6. Gate restante

Windows reprodujo 73/73 selectivas, 2 schemas y Documentation Governance / Project State / TCR v1 / TCR v2 en PASS. Repo-review y candidate successor limpio deben completarse antes de empaquetar evidencia; 06-C permanece bloqueado hasta owner adjudication independiente.

## 7. Comandos de verificación

La fuente operativa única de comandos Windows es la guía incluida en el bundle 06-B. Este documento no duplica el procedimiento operativo.
