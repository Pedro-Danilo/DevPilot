---
doc_id: "DEVPL-FULL-REGRESSION-EXECUTION-V2-1-RUNBOOK"
title: "DevPilot — Full Regression Execution v2.1 operator runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner"
---

# DevPilot — Full Regression Execution v2.1 operator runbook

## 1. Propósito

Este runbook opera una **única sesión lógica de full regression** de forma secuencial, resumible y completion-first. v2.1 no reduce cobertura, no usa `pytest-xdist` y no convierte un reinicio de Windows/pytest en una segunda full mientras source/environment/collection/plan permanezcan idénticos.

## 2. Superficie CLI

La superficie pública gobernada es:

```text
tests full-session collect
tests full-session plan
tests full-session run
tests full-session resume
tests full-session status
tests full-session adjudicate
```

Se usa `tests` —no un nuevo namespace `testing`— para preservar la taxonomía CLI ya existente de DevPilot.

## 3. Modelo operativo

```text
collect → plan → run → status → [resume si quedó UNEXECUTED] → adjudicate
```

- `collect` sella nodeids reales obtenidos del hook de colección de pytest.
- `plan` divide la colección en shards secuenciales sin duplicar nodeids.
- `run` requiere `--execute`; sin él es preview.
- un `FAIL` funcional ordinario no detiene shards posteriores;
- un timeout/infra abort deja nodeids sin outcome terminal y permite `resume` si los fingerprints siguen iguales;
- `resume` ejecuta únicamente nodeids `UNEXECUTED`;
- `adjudicate` solo puede declarar PASS cuando 100% de nodeids tienen outcome terminal y no existen FAIL/ERROR.

## 4. Runtime y seguridad

Runtime: `outputs/testing/full_regression/<session_id>/`.

Reglas:

- no se versiona runtime;
- subprocess recibe argv tipado y `shell=False`;
- no red ni API externa;
- no `.git` mutation;
- source fingerprint antes/después de cada shard;
- source drift = BLOCK;
- receipts, collection, plan y adjudication son inmutables por contenido;
- no almacenar secretos ni tokens.

## 5. Uso Windows

La guía Windows del activation enabler entrega comandos PowerShell de una sola línea con PASS/BLOCK visible. Para la validación del enabler se usa solo un canary acotado; **no se ejecuta la full de GSDLC-07**. La primera full lógica real de ese backlog continúa reservada a `GSDLC-07-E`.

## 6. PASS/BLOCK

**PASS**: collection completa y única, plan determinista, receipts verificables, completion-first, resume sin rerun de terminales, fingerprints iguales y adjudicación con 100% accounting.

**BLOCK**: nodeid omitido/duplicado, receipt reescrito, source/environment drift, resume presentado como nueva sesión, source mutation o adjudicación con `UNEXECUTED`.

## 7. Limitaciones v2.1

- sharding por cantidad fija de nodeids, no por duración histórica;
- ejecución secuencial;
- startup de pytest por shard añade overhead;
- `NodeDurationRegistry` corresponde a v2.2;
- paralelización segura corresponde a v2.3 después de clasificación de recursos compartidos.
