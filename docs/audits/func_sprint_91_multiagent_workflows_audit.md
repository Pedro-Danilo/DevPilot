---
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-91-MULTIAGENT-WORKFLOWS"
title: "Auditoría FUNC-SPRINT-91 — Workflows multiagente SDLC dry-run"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-18"
approval: "approved_after_local_validation"
sprint: "FUNC-SPRINT-91"
---

# Auditoría FUNC-SPRINT-91 — Workflows multiagente SDLC dry-run

## Estado

`implemented-initial`. El sprint implementa workflows multiagente SDLC predefinidos, locales, versionados por JSON y ejecutables únicamente en `dry-run/report-only`.

## Propósito

Mover la coordinación multiagente desde un único allowlist interno hacia definiciones de workflow auditables bajo `.devpilot/workflows/`, sin habilitar autonomía abierta ni acciones destructivas.

## Alcance implementado

- `.devpilot/workflows/sdlc_review.json` define el workflow `sdlc-review`.
- `docs/schemas/multiagent_workflow.schema.json` valida estructura de workflow.
- `src/devpilot_core/multiagent/workflow.py` implementa `MultiAgentWorkflowRunner`.
- `multiagent workflow run --workflow sdlc_review --dry-run --json` ejecuta el workflow.
- `evals/fixtures/multiagent_workflow_sdlc_review_cases.json` documenta fixtures mínimos.
- MIASI registra `multiagent.workflow.run` y políticas específicas de dry-run/deny.

## Funcionamiento

El runner carga el workflow local, valida schema, verifica reglas semánticas de seguridad, valida políticas/agentes contra MIASI y delega los pasos a `MultiAgentCoordinator`. El coordinador conserva `HandoffRecord`, `PolicyEngine` y eventos `multiagent.handoff.evaluated` por paso. El runner agrega un `consolidated_report` con cobertura, riesgos y recomendaciones.

## Integración

La capacidad se integra con:

- `SchemaValidator` para contrato JSON.
- `MiasiRegistryValidator` para agentes y políticas.
- `MultiAgentCoordinator` para ejecución secuencial gobernada.
- `EventLogger` para trazabilidad.
- `ReportEngine` a través de `--write-report`.
- Runbook, README, backlog H, manifests y MIASI cards.

## Criterios PASS

- Workflow definido y validado por schema.
- `multiagent workflow run --workflow sdlc_review --dry-run --json` retorna PASS.
- Cada paso tiene handoff explícito y trazado.
- Todos los agentes usados están `implemented` o `implemented-initial`.
- Reporte consolidado incluye riesgos y recomendaciones.
- Sin mutaciones, red, API externa, shell ni ejecución remota.

## Criterios BLOCK

- Workflow sin schema o schema inválido.
- Ejecución sin `--dry-run`.
- Safety flags que habiliten mutación, red, shell o ejecución remota.
- Agentes no implementados o políticas inexistentes.
- Pasos sin trace obligatorio.
- Intento de convertir hallazgos en cambios automáticos.

## Riesgos

- El reporte consolidado puede contener hallazgos que requieren interpretación humana.
- La ejecución sigue siendo secuencial; no hay graph planner ni routing adaptativo.
- Los workflows son datos confiables del repo; cambios no revisados en `.devpilot/workflows` podrían alterar el orden de revisión.
- Sprint 91 no implementa scoring adversarial; queda para Sprint 92.

## Comandos de verificación

```powershell
python -m devpilot_core multiagent workflow run --workflow sdlc_review --dry-run --json
python -m devpilot_core multiagent workflow run --workflow sdlc_review --dry-run --json --write-report
python -m devpilot_core schema validate --schema docs\schemas\multiagent_workflow.schema.json --instance .devpilot\workflows\sdlc_review.json --json
python -m devpilot_core miasi validate --json
python -m pytest tests\test_multiagent_workflow.py tests\test_sprint_91_documentation.py -q
```

## Veredicto

`FUNC-SPRINT-91` queda implementado como primera versión gobernada de workflows multiagente SDLC. La capacidad es útil para revisión SDLC repetible y trazable, pero no debe presentarse como orquestación autónoma industrial completa hasta incorporar evaluación avanzada, red teaming y safety scoring.
