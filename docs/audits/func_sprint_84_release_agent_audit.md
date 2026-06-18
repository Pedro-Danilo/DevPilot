---
title: "Auditoría FUNC-SPRINT-84 — ReleaseAgent MVP dry-run y cierre Fase G"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-84"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
sprint: "FUNC-SPRINT-84"
updated: "2026-06-17"
approval: "approved_by_func_sprint_84_validation"
---

# Auditoría FUNC-SPRINT-84 — ReleaseAgent MVP dry-run y cierre Fase G

## Estado

`implemented-initial` / PASS focalizado.

## Propósito

Validar que DevPilot cuenta con un ReleaseAgent MVP gobernado, estrictamente dry-run, capaz de consolidar evidencia local de release y producir recomendaciones sin publicar, desplegar, firmar ni crear tags Git.

## Alcance implementado

- Registro MIASI de `release.assistant` con estado `implemented-initial`.
- Módulo `src/devpilot_core/agents/release_agent.py`.
- Integración con AgentRuntime v2 monoagente.
- Perfil `quality-gate run --profile release`.
- Tool calls auditables para quality gate, release manifest, changelog, package dry-run, SBOM, install plan y upgrade check.
- Reporte formal de cierre de Fase G.

## Funcionamiento

`python -m devpilot_core agent run release-assistant --dry-run --json` ejecuta el agente a través de AgentRuntime. Antes de cada consulta de evidencia, el agente genera un `AgentToolCall` y consulta `PolicyEngine`. Las consultas son locales y determinísticas; no ejecutan acciones de publicación, despliegue, firma, tagging, auto-update ni cambios de fuente.

El agente consolida un checklist de release con evidencia de Fase G y devuelve recomendaciones estructuradas.

## Criterios PASS

- `agent run release-assistant --dry-run --json` retorna PASS.
- `quality-gate run --profile release --json` retorna PASS.
- El agente produce checklist y recomendaciones.
- Los tool calls quedan auditables.
- El cierre de Fase G resume `FUNC-SPRINT-74` a `FUNC-SPRINT-84`.
- No se publica, no se despliega, no se firma y no se etiqueta Git.

## Criterios BLOCK

- ReleaseAgent ejecuta publicación, despliegue, firma o Git tagging.
- El agente no pasa por MIASI/PolicyEngine.
- El agente no produce evidencia o recomendaciones trazables.
- No existe reporte formal de cierre Fase G.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-84-001 | Agente con demasiado poder | Dry-run obligatorio y bloqueo de execute. |
| RISK-FUNC-84-002 | Recomendaciones sin evidencia | Uso de builders/gates locales y tool calls auditables. |
| RISK-FUNC-84-003 | Confusión release/deploy | Deploy, publish, signing y Git tags fuera de alcance. |

## Comandos de verificación

```powershell
python -m devpilot_core agent run release-assistant --dry-run --json --write-report
python -m devpilot_core quality-gate run --profile release --json
python -m pytest tests\test_release_agent.py tests\test_sprint_84_documentation.py -q
```

## Límite operacional explícito

ReleaseAgent no publica, no despliega, no firma y no etiqueta Git. Cualquier capacidad futura que haga estas acciones requerirá ADR, PolicyEngine, aprobación humana y evidencia adicional.

## Veredicto

Sprint implementado como MVP industrial preliminar: aporta asistencia de release gobernada y cierre formal de Fase G, sin habilitar acciones destructivas o remotas.
