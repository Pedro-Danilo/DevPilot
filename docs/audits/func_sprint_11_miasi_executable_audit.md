---
title: "FUNC-SPRINT-11 — Auditoría de MIASI ejecutable"
doc_id: "DEVPL-AUDIT-FUNC-011"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-11"
updated: "2026-06-08"
approval: "approved_by_owner_direction"
---

# FUNC-SPRINT-11 — Auditoría de MIASI ejecutable

## 1. Propósito

Este artefacto documenta la implementación de `FUNC-SPRINT-11 — MIASI ejecutable: Agent Registry, Tool Registry y Policy Matrix`. El objetivo fue convertir registros MIASI aprobados en contratos ejecutables, locales y determinísticos que puedan validarse desde la CLI antes de implementar agentes o herramientas reales.

## 2. Naturaleza de la implementación

La implementación es una primera versión ejecutable. Valida declaraciones y consistencia, pero no ejecuta agentes, herramientas, modelos, patches, Git ni operaciones de filesystem. Sigue el enfoque local-first, sin dependencias externas, sin API keys y sin costos.

## 3. Componentes creados

```text
.devpilot/miasi/agent_registry.json
.devpilot/miasi/tool_registry.json
.devpilot/miasi/policy_matrix.json
src/devpilot_core/miasi/registry.py
src/devpilot_core/miasi/__init__.py
tests/test_miasi_registry.py
docs/audits/func_sprint_11_miasi_executable_audit.md
docs/functional_sprint_11_manifest.json
```

## 4. Componentes modificados

```text
.devpilot/project.yaml
src/devpilot_core/cli.py
src/devpilot_core/workspace/manager.py
docs/02_architecture/adrs/ADR-0008-agent-runtime-industrial-bajo-miasi.md
README.md
docs/05_operations/runbook.md
docs/functional_backlog_after_precode.md
```

## 5. Funcionamiento técnico

`MiasiRegistryValidator` carga tres contratos JSON bajo `.devpilot/miasi/` y valida:

- existencia de documentos MIASI requeridos;
- unicidad de agentes, herramientas y reglas;
- fase, estado, nivel de riesgo y autonomía;
- que agentes MVP no superen A2;
- que agentes A4+ requieran aprobación humana;
- que todo agente tenga tools permitidas, evaluación, observabilidad y policy coverage;
- que toda tool tenga side effect, riesgo, aprobación cuando aplica y policy coverage;
- que la Policy Matrix tenga dominios críticos, gates, aprobación y observabilidad;
- que los documentos Markdown aprobados no declaren entidades ausentes en el contrato ejecutable.

## 6. Integración con DevPilot

La CLI agrega:

```powershell
python -m devpilot_core miasi validate --json
python -m devpilot_core miasi validate --json --write-report
python -m devpilot_core miasi validate-registry --json
python -m devpilot_core miasi validate-tools --json
python -m devpilot_core miasi validate-policy-matrix --json
```

Los resultados se emiten como `CommandResult`, se registran en EventLog JSONL, pueden generar reportes JSON/Markdown mediante `ReportEngine` y se persisten de forma best-effort en SQLite mediante `LocalStore`.

## 7. Criterios PASS

```text
Los tres contratos ejecutables existen y son JSON válido.
Agent Registry valida sin BLOCK.
Tool Registry valida sin BLOCK.
Policy Matrix valida sin BLOCK.
Los agentes referencian tools existentes.
Las tools y agentes referencian reglas existentes.
Los agentes MVP no superan A2.
Los agentes A4+ requieren aprobación.
Las reglas deny/block son observables.
pytest -q pasa.
```

## 8. Criterios BLOCK

```text
Falta un JSON ejecutable MIASI.
Un JSON es inválido.
Un agente referencia una tool inexistente.
Una tool referencia una policy inexistente.
Un agente no tiene observabilidad/eval.
Un agente A4+ no requiere aprobación.
Un agente MVP supera A2.
Una regla deny/block no es observable.
Hay drift de entidad documentada pero ausente en el contrato ejecutable.
```

## 9. Pruebas implementadas

```text
tests/test_miasi_registry.py
```

Cobertura:

- validación completa del contrato del repo;
- validación individual de agentes, tools y policy matrix;
- CLI JSON y `--write-report`;
- bloqueo por config faltante;
- bloqueo por tool desconocida;
- bloqueo por agente A4 sin aprobación;
- bloqueo por tool sin policy coverage.

Resultado esperado:

```text
pytest -q -> 79 passed
```

## 10. Riesgos y evolución

```text
No hay Agent Runtime todavía.
No hay Tool Runtime.
No hay eval harness.
No hay aprobación humana persistente.
No hay RBAC/IAM.
No hay firma ni cifrado de contratos.
El parser Markdown es mínimo.
```

Evolución natural: `FUNC-SPRINT-12 — Agent Runtime mock/local para agentes documentales MVP`.
