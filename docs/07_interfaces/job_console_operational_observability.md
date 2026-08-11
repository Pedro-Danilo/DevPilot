---
doc_id: "DEVPL-UOC-008-JOB-CONSOLE-OPERATIONAL-OBSERVABILITY"
title: "UOC-008 — Job Console y observabilidad operacional"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-11"
approval: "approved_by_owner"
---

# UOC-008 — Job Console y observabilidad operacional

## 1. Objetivo

UOC-008 expone el lifecycle tipado de UOC-007 mediante `/jobs` y `/jobs/{job_id}` sin convertir la Web UI en terminal. La autoridad sigue siendo `GovernedJobFramework` y su estado local bajo `outputs/runtime/governed_jobs`.

## 2. Superficie

- `/jobs`: índice filtrable por workspace, capability y estado.
- detalle operacional: estado, fase, progreso, duración, heartbeat, stale state, correlation id, artifacts/evidence y errores.
- logs: lectura cursor-based, bounded y sanitizada.
- cancelación: solicitud gobernada; si existe worker PID registrado, la terminación de árbol usa argv fija y nunca shell text.
- retry: crea un nuevo job gobernado desde un job terminal respetando `retry_limit`; no autoejecuta la capability.
- reconciliación: jobs activos sin heartbeat fresco se marcan `error` o `cancelled`; nunca se convierten silenciosamente en PASS.

## 3. Seguridad

PASS exige `arbitrary_shell=false`, remote execution=false, connector write=false, plugin execution=false, external API required=false y cero exposición de cancel token, idempotency hash o request fingerprint en la UI.

BLOCK si un browser puede proporcionar comando, PID arbitrario, path absoluto o argumentos libres; si un retry ignora budget; si cancelación opera fuera de estados válidos; o si logs pueden exponer tokens/secretos.

## 4. Persistencia y límites

La primera versión usa JSON local atómico. La metadata operacional se separa del schema UOC-007 v2 para no mutar un contrato histórico. El log por job tiene límite de 512 KiB y máximo de 500 entradas por lectura. El polling UI predeterminado es de 3 s.

## 5. Reconciliación de huérfanos

Al iniciar/operar la capa de jobs, una reconciliación bounded identifica estados `queued/running/cancel-requested/rollback-running` sin heartbeat fresco. Los jobs se adjudican `error` o `cancelled` según el estado; se añade evidencia/log local de reconciliación.

## 6. Limitaciones

Esta implementación es `implemented-initial`. No habilita adapters canónicos de UOC-009 ni ejecución genérica. La robustez multi-proceso, el worker supervisor y telemetría más rica requieren evolución posterior; UOC-011 realizará hardening final de accesibilidad/rendimiento/chaos.

## 7. Criterios PASS/BLOCK

PASS: API/UI contracts, negative security tests, focal tests, Test Impact, gobernanza, browser acceptance `/jobs`, 401/403/API-down/empty/stale/cancelled y S0=0/S1=0.

BLOCK: shell arbitrario, secrets en logs, stale interpretado como PASS, cancelación sin policy, retry fuera de budget, ruta UI/API sin registry o evidencia browser incompleta.

## 8. Comandos de verificación

Los comandos operativos Windows se mantienen únicamente en la guía de implementación UOC-008 entregada con el operador; este documento registra el contrato técnico y no duplica el runbook ejecutable.
