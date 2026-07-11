---
title: "POST-H-033-A — Validator inventory and migration plan report"
doc_id: "POST-H-033-A-VALIDATOR-INVENTORY-MIGRATION-PLAN-REPORT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-11"
approval: "approved_by_owner"
---

# POST-H-033-A — Validator inventory and migration plan

## Decision

PASS — POST-H-033-A introduces an implemented-initial inventory and migration plan for schema-backed validators without changing runtime validator behavior.

## Scope

This sprint inventories deterministic validators and classifies hardcoded elements as `migrate`, `keep`, `fallback`, `parser` or `security-core`.

## Artifacts

- `.devpilot/validation/validator_inventory.json`
- `.devpilot/validation/validator_migration_plan.json`
- `docs/schemas/validator_inventory.schema.json`
- `docs/schemas/validator_migration_report.schema.json`
- `src/devpilot_core/validation/validator_inventory.py`
- `tests/test_post_h_033_validator_inventory_migration_plan.py`
- `docs/post_h_033_a_manifest.json`

## Safety and limits

POST-H-033-A is inventory-only and read-only. It does not alter frontmatter, readiness, MIASI semantic, docs governance, policy guard or schema validator runtime behavior. It does not introduce LLM judge behavior, network calls, external APIs, connector write, plugin execution, remote execution or source mutations.

Critical security-core guards are explicitly non-removable. Later POST-H-033 micro-sprints may add registries/catalogs, but they must not allow local JSON to disable no-go gates or downgrade critical severities.

## PASS/BLOCK summary

PASS criteria covered:

- minimum validator set inventoried;
- every validator has owner, domain, criticality, inputs, outputs, schemas, tests and migration status;
- every hardcoded element has a migration decision;
- migration waves are defined for POST-H-033-B through POST-H-033-F;
- no runtime behavior change is introduced;
- no LLM judge or external dependency is required.

BLOCK criteria avoided:

- no critical validator without owner;
- no hardcoded element without decision;
- no plan to disable critical defenses;
- no plan to replace deterministic validators with LLM judging.
