---
doc_id: "ADR-UOC-000-NO-ARBITRARY-SHELL"
title: "ADR UOC-000 — No arbitrary shell from Web UI"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-04"
approval: "approved_by_owner"
created_by: "UOC-000"
canonical_commit: "43254e3e61cdafe65e0ed2d773fe9032b0a81f05"
local_first: true
external_api_required: false
preliminary: false
decision: "prohibit-arbitrary-shell"
---

# ADR UOC-000 — No arbitrary shell from Web UI

## Estado

Aprobada. La Web UI no expondrá terminal, shell, `subprocess` genérico ni un
campo que acepte comandos libres.

## Contexto

La CLI contiene 193 comandos y varias capacidades ejecutan subprocess o mutan
estado. Reutilizar la CLI mediante una cadena arbitraria evitaría los contratos
de aplicación, la policy, el Test Impact y la evidencia.

## Decisión

Cada acción UI se implementará como un contrato tipado con `capability_id`,
schema de request, policy, timeout, dry-run, approval y evidence contract. Un
bridge CLI temporal solo puede existir como adaptador interno allowlisted y no
acepta texto libre proveniente del navegador.

## Consecuencias

- No se implementa terminal web.
- No se permite `shell=True` en handlers UI.
- No se permiten argumentos sin schema/allowlist.
- Comandos sensibles permanecen `CLI-BRIDGE-REGISTERED` o `POLICY-BLOCKED`.
- Cancelación, logs y errores se modelan como jobs, no como consolas remotas.

## Reversibilidad

Modificar esta decisión requiere ADR nueva, threat model, approval del owner,
pruebas adversariales y evidencia de no regresión de los no-go gates.
