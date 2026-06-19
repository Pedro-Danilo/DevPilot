---
title: "Auditoría FUNC-SPRINT-97 — Compliance packs y policy packs"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-97"
version: "1.0.0"
updated: "2026-06-19"
status: "approved"
approval: "internal"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-97"
---

# Auditoría FUNC-SPRINT-97 — Compliance packs y policy packs

## Estado

Implementado como `implemented-initial`.

## Propósito

Agregar compliance packs y policy packs locales para agrupar reglas, checklists, schemas y reportes en perfiles ejecutables de evidencia.

## Alcance implementado

- `CompliancePackRegistry` para validar/listar `.devpilot/compliance/packs.json`.
- `CompliancePackRunner` para ejecutar el pack `baseline` sobre gates internos allowlisted.
- Schema `SCHEMA-DEVPL-COMPLIANCE-PACK-V1`.
- CLI `compliance list` y `compliance run`.
- Suite `compliance-pack-integrity`.
- Integración MIASI y QualityGate CI.

## Funcionamiento

El registry define packs declarativos. El runner no ejecuta comandos del JSON: traduce runners conocidos a llamadas internas ya gobernadas (`SchemaRegistry`, `ValidationGateway`, readiness strict, Standards Registry y MIASI). Antes de evaluar checks, ejecuta preflight con `PolicyEngine`.

## Integración

La capacidad se integra con CLI, SchemaValidator, PolicyEngine, MIASI, EvalRunner, QualityGate, ReportEngine, README, runbook, backlog Fase H, changelog y manifiesto funcional del sprint.

## Criterios PASS

- Registry validable por schema.
- Pack baseline declarativo.
- `compliance list --json` funciona.
- `compliance run --pack baseline --json --write-report` produce PASS/BLOCK por check y gaps por pack.
- `quality-gate ci` consume `compliance-pack-integrity`.

## Criterios BLOCK

- Packs ejecutan acciones no declaradas.
- Compliance reemplaza `PolicyEngine` en vez de usarlo.
- Registry referencia policies o schemas inexistentes.
- Runner permite shell, red, APIs externas, deploy, publish o acciones destructivas.

## Riesgos

La versión es preliminar: no equivale a certificación externa, no incluye catálogos regulatorios completos, no firma evidencias ni cifra paquetes. La calidad industrial futura requiere perfiles normativos revisados y criterios de auditoría externos.

## Comandos de verificación

```powershell
python -m devpilot_core compliance list --json
python -m devpilot_core compliance run --pack baseline --json --write-report
python -m devpilot_core eval run --suite compliance-pack-integrity --json
python -m devpilot_core schema validate --schema docs\schemas\compliance_pack.schema.json --instance .devpilot\compliance\packs.json --json
python -m pytest tests\test_compliance_packs.py tests\test_sprint_97_documentation.py -q
```

## Veredicto

Sprint implementado como base local-first, declarativa, segura y auditable para compliance/policy packs.
