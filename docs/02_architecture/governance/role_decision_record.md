---
doc_id: "DEVPL-GSDLC-02-A-ROLE-DECISION-RECORD"
title: "DEVPL-GSDLC-02-A — Local role authority decision record"
status: "pass-candidate/pre-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
---

# Role authority decision record

## Decision

Adoptar como **diseño canónico no ejecutado aún** los nueve roles de GSDLC-02: owner, product-owner, architect, security-reviewer, developer, qa-reviewer, release-manager, operator y agent-supervisor.

## Historical baseline

El identity registry de repo353 contiene owner, architect, developer, reviewer, operator y agent-supervisor. No guarda credenciales y declara remote auth false. El sensitive action catalog usa además `maintainer` para patch.apply, refactor.execute y filesystem.delete; las tres acciones están bloqueadas/no ejecutables.

## Migration decisions

- owner/architect/developer/operator: preserve IDs, permissions reevaluated in 02-C.
- reviewer: proposed alias to qa-reviewer only; no automatic security-reviewer authority.
- agent-supervisor: preserve ID, but critical permissions are narrowed by domain during 02-C.
- maintainer: no direct mapping. Its current critical actions remain fail-closed until 02-C assigns explicit canonical authority.
- product-owner/security-reviewer/release-manager: new GSDLC-02 roles with no fabricated legacy equivalence.

## Why not mutate identity_registry in 02-A

02-A is design/governance. Updating runtime role behavior before auth threat model owner adjudication would violate the backlog gate. The registry therefore remains byte-identical to repo353 and a frozen `gsdlc02a_at_close` snapshot records its historical state.

## Separation of duties

No role may self-grant authority. Critical requester/approver separation is the default. Any single-installation owner recovery exception must be separately governed, logged and narrowly scoped.
