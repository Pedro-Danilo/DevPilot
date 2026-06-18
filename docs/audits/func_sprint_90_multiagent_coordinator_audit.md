---
title: "Auditoría FUNC-SPRINT-90 — MultiAgentCoordinator MVP y handoffs gobernados"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-90"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-90"
updated: "2026-06-18"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-90 — MultiAgentCoordinator MVP y handoffs gobernados

## Estado

`implemented-initial`.

## Propósito

Validar que DevPilot incorpora un coordinador multiagente inicial sin habilitar autonomía abierta, planificación libre, ejecución destructiva, red externa ni APIs externas. La capacidad queda limitada a workflows locales allowlisted, secuenciales, en `--dry-run`, con handoffs explícitos, PolicyEngine y trazas obligatorias.

## Alcance implementado

- `src/devpilot_core/multiagent/handoff.py`: modelo `HandoffRecord` como evidencia explícita de delegación entre agentes.
- `src/devpilot_core/multiagent/coordinator.py`: `MultiAgentCoordinator` secuencial/gobernado para workflow `repo-review`.
- `src/devpilot_core/multiagent/__init__.py`: export público del paquete multiagent.
- CLI `multiagent run --workflow repo-review --dry-run --json`.
- MIASI Agent Registry: `multiagent.coordinator` pasa a `implemented-initial` con autonomía acotada A3 para este MVP.
- MIASI Tool Registry: `multiagent.coordinator.run` y `multiagent.handoff`.
- MIASI Policy Matrix: reglas `MULTIAGENT_COORDINATOR_DRY_RUN_ALLOW`, `MULTIAGENT_EXECUTE_DENY` y `MULTIAGENT_HANDOFF_TRACE_REQUIRED`.
- `tests/test_multiagent_coordinator.py`: pruebas de PASS, bloqueo y CLI.

## Funcionamiento

`MultiAgentCoordinator` carga MIASI, valida que `multiagent.coordinator` esté implementado, comprueba que el workflow esté en la allowlist local y exige `--dry-run`. Antes de ejecutar cada agente hijo crea un `HandoffRecord`, evalúa `PolicyEngine` sobre el target y emite un evento `multiagent.handoff.evaluated`. Luego invoca `AgentRuntime` sobre agentes ya implementados o `implemented-initial`.

El workflow inicial `repo-review` encadena `repo.analysis`, `code.review` y `security.agent` sobre un target local controlado. Los resultados de agentes hijos se consolidan como evidencia de reporte, pero Sprint 90 no convierte el flujo multiagente en quality gate ni autoriza correcciones automáticas.

## Integración

- CLI: `src/devpilot_core/cli.py`.
- Runtime de agentes: `AgentRuntime` existente.
- Seguridad: `PolicyEngine`, MIASI Agent Registry y workflow allowlist.
- Observabilidad: `EventLogger` con eventos `multiagent.handoff.evaluated` y `multiagent.workflow.evaluated`.
- Reportes: `--write-report` genera evidencia bajo `outputs/reports`.
- Documentación: README, runbook, backlog H, functional backlog, changelog, audit y manifest funcional.

## Criterios PASS

- `multiagent run --workflow repo-review --dry-run --json` retorna PASS.
- Todos los handoffs son explícitos mediante `HandoffRecord`.
- Cada handoff genera evento local antes del agente hijo.
- El coordinador solo usa agentes con estado MIASI `implemented` o `implemented-initial`.
- El modo `--dry-run` es obligatorio.
- No se modifican archivos del workspace productivo.
- No se usa red, API externa, shell ni ejecución remota.

## Criterios BLOCK

- Ejecutar sin `--dry-run`.
- Referenciar workflows no registrados en la allowlist local.
- Usar agentes `planned`, `future` o `disabled`.
- Omitir `PolicyEngine` antes del handoff.
- Omitir traza de handoff.
- Modificar archivos, ejecutar acciones críticas, usar shell, red externa o API externa.

## Riesgos

- La capacidad es un MVP secuencial; no implementa graph orchestration, planner autónomo ni memoria compartida semántica.
- Los hallazgos de agentes hijos se reportan, pero el comando no sustituye un quality gate especializado.
- Falta evaluación adversarial multiagente avanzada, prevista para sprints posteriores.
- Falta UI/API para inspeccionar workflows y handoffs de forma visual.

## Comandos de verificación

```powershell
python -m devpilot_core multiagent run --workflow repo-review --dry-run --json
python -m devpilot_core multiagent run --workflow repo-review --dry-run --json --write-report
python -m devpilot_core schema validate-miasi --json
python -m devpilot_core miasi validate --json
python -m devpilot_core validate-artifact docs\audits\func_sprint_90_multiagent_coordinator_audit.md --json
python -m devpilot_core schema validate-manifest docs\functional_sprint_90_manifest.json --json
python -m pytest tests\test_multiagent_coordinator.py tests\test_sprint_90_documentation.py -q
```

## Veredicto

PASS focalizado. Sprint 90 habilita un `MultiAgentCoordinator` inicial y gobernado, con handoffs trazados, dry-run obligatorio y sin autonomía destructiva. La capacidad queda `implemented-initial` y debe evolucionar en Sprint 91 hacia workflows SDLC más completos, manteniendo policy, evals y observabilidad.
