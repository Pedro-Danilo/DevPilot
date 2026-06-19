---
title: "Auditoría FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-98"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
sprint: "FUNC-SPRINT-98"
approval: "implemented-initial"
---

# Auditoría FUNC-SPRINT-98 — Remote runners experimentales y enterprise reporting

## Estado

`FUNC-SPRINT-98` queda implementado como `implemented-initial`. La capacidad es local-first, read-only para reporting y con remote runners deshabilitados por defecto.

## Propósito

Preparar contratos enterprise y un reporte agregado local sin habilitar ejecución remota, cloud, shell, APIs externas ni credenciales.

## Alcance implementado

- ADR `ADR-0017-remote-runners-experimental.md`.
- Registry local `.devpilot/remote/runner_registry.json`.
- Schema `docs/schemas/remote_runner.schema.json`.
- Módulo `src/devpilot_core/remote/runner.py`.
- Módulo `src/devpilot_core/enterprise/report.py`.
- CLI `remote runner status --json`.
- CLI `enterprise report --json --write-report`.
- Suite safety `remote-enterprise`.
- Manifest funcional Sprint 98.

## Funcionamiento

`remote runner status` valida el registry contra schema, pasa por `PolicyEngine` y confirma que todo runner está en estado `disabled`. Cualquier intento de ejecución queda bloqueado por `RemoteRunnerStub.execute()`.

`enterprise report` agrega evidencia local de schemas, MIASI, identidad/RBAC, portfolio, compliance packs, audit/compliance manifests y estado de remote runner. El reporte no lee secretos, no lee `.devpilot/devpilot.db`, no ejecuta remoto y no usa red.

## Integración

La capacidad queda integrada con:

- `PolicyEngine`;
- `PathGuard`;
- `SchemaValidator`;
- `MIASI`;
- `EvalRunner`;
- `QualityGate`;
- `ReportEngine`;
- artefactos de Fase H.

## Criterios PASS

- `remote runner status --json` retorna `ok=true` con `remote_runner_enabled=false`.
- `enterprise report --json --write-report` retorna `ok=true` en modo local/read-only.
- `remote-enterprise` pasa con `safety_score >= 90` y `false_negatives=0`.
- No hay shell, red, APIs externas, cloud ni mutaciones de fuente.
- ADR Sprint 98 existe y documenta límites.

## Criterios BLOCK

- Remote runner ejecuta comandos reales.
- Algún runner queda habilitado por defecto.
- Se requiere cloud, red, API externa o credenciales.
- Enterprise report muta fuente o reemplaza `PolicyEngine`.
- No existe ADR o no existe suite safety.

## Riesgos

- `implemented-initial`: no es remote execution real.
- No hay transport security, firma, cifrado ni trust model distribuido.
- Enterprise report es un agregado local inicial; no reemplaza observabilidad enterprise completa.
- Futuras capacidades remotas deberán abrir ADR nueva y ampliar safety tests.

## Comandos de verificación

```powershell
python -m devpilot_core schema validate --schema docs\schemas\remote_runner.schema.json --instance .devpilot\remote\runner_registry.json --json
python -m devpilot_core remote runner status --json
python -m devpilot_core enterprise report --json --write-report
python -m devpilot_core eval run --suite remote-enterprise --json
python -m devpilot_core validate all --json
python -m devpilot_core quality-gate run --profile ci --json
```

## Veredicto

`PASS focalizado`: Sprint 98 implementa reporting enterprise local y remote runner stub experimental deshabilitado. No habilita ejecución remota real.
