---
title: "Contrato CLI inicial de DevPilot Local"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
related_projects:
  - "DevPilot Local"
---
# Contrato CLI inicial de DevPilot Local

## 1. Propósito

Definir contratos de entrada, salida, artefactos y quality gates para los comandos futuros de DevPilot Local.

## 2. Convenciones generales

- Todo comando soporta `--dry-run` por defecto cuando pueda modificar archivos.
- Todo comando que escriba requiere `--execute`.
- Toda salida máquina-legible debe poder emitirse con `--json`.
- Todo comando debe emitir `run_id`.
- Toda acción sensible debe pasar por `policy gate`.

## 3. Contratos por comando

| Comando | Propósito | Entradas mínimas | Salidas | Artefactos | Gates |
|---|---|---|---|---|---|
| `devpilot init-project` | Inicializar proyecto bajo MIASI. | `--path`, `--name`, `--profile` | Project manifest | `.devpilot/project.yaml` | Estructura válida |
| `devpilot new-agent` | Crear Agent Card y scaffolding. | `--name`, `--type`, `--autonomy` | Agent Card | `agents/<name>/agent_card.md` | Agent Card completa |
| `devpilot validate-agent` | Validar agente contra MIASI. | `--agent` | Reporte pass/fail | `outputs/evals/*` | MIASI-AGT/EVAL/SEC |
| `devpilot register-tool` | Registrar herramienta. | `--tool`, `--risk`, `--side-effects` | Tool Card | `tools/<tool>/tool_card.md` | MIASI-TOOL |
| `devpilot run-evals` | Ejecutar evaluación offline. | `--agent`, `--dataset` | Eval report | `outputs/evals/*` | MIASI-EVAL |
| `devpilot check-security` | Ejecutar security gates. | `--scope` | Security report | `outputs/security/*` | MIASI-SEC/POL |
| `devpilot generate-adr` | Crear ADR. | `--title`, `--decision` | ADR draft | `docs/adrs/*` | MIASI-DOC |
| `devpilot generate-runbook` | Crear runbook. | `--agent` | Runbook | `docs/runbooks/*` | MIASI-OPS |
| `devpilot readiness-check` | Validar readiness. | `--project`, `--target-level` | Readiness report | `outputs/readiness/*` | Production checklist |

## 4. Salida JSON común

```json
{
  "run_id": "run_20260530_001",
  "command": "devpilot validate-agent",
  "target": "CodeReviewAgent",
  "dry_run": true,
  "passed": true,
  "quality_gates": [
    {"id": "MIASI-AGT-001", "status": "pass"},
    {"id": "MIASI-EVAL-001", "status": "pass"}
  ],
  "artifacts": [
    "outputs/evals/codereviewagent_eval.json"
  ],
  "warnings": [],
  "blocked_reasons": []
}
```

## 5. Criterios de bloqueo

- Comando con side effects sin `--execute`.
- Tool sin Tool Card.
- Agente sin Agent Card.
- Falta de `run_id`.
- Output no serializable cuando se solicita `--json`.
- Secreto detectado en artefacto.
