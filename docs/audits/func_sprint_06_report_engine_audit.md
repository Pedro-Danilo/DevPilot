---
title: "FUNC-SPRINT-06 Audit — Report Engine y contrato de evidencias"
doc_id: "DEVPL-AUDIT-FUNC-006"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-06"
updated: "2026-06-07"
approval: "approved_by_owner_direction"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# FUNC-SPRINT-06 Audit — Report Engine y contrato de evidencias

## 1. Propósito

Este artefacto registra la auditoría técnica de `FUNC-SPRINT-06 — Report Engine y contrato de evidencias`. Su propósito es dejar trazabilidad sobre lo implementado, cómo se integra con DevPilot Local, qué comandos se agregan o modifican, qué pruebas se ejecutaron, qué riesgos permanecen y bajo qué criterios el sprint puede cerrarse.

## 2. Alcance

El sprint implementa una primera versión local-first del motor central de reportes para evidencias de gates documentales. La implementación cubre:

- modelo `EvidenceReport`;
- estados `PASS`, `FAIL`, `BLOCK`, `ERROR`;
- generación JSON y Markdown;
- escritura segura bajo `outputs/reports`;
- integración con `readiness-check`, `validate-frontmatter`, `validate-artifact` y `checklist-pre-code`;
- pruebas unitarias y de CLI;
- sincronización de README, runbook y backlog funcional.

No incluye todavía EventLog JSONL, firma criptográfica, persistencia SQLite, retención de reportes, redacción avanzada de secretos ni observabilidad centralizada.

## 3. Componentes creados

| Componente | Propósito | Rol dentro de DevPilot |
|---|---|---|
| `src/devpilot_core/reports/models.py` | Define `EvidenceReport`, `ReportStatus` y `ReportFormat`. | Contrato estable de evidencia local para auditoría y futura persistencia. |
| `src/devpilot_core/reports/report_engine.py` | Implementa `ReportEngine`, serialización JSON y render Markdown. | Motor central para reportes reproducibles de gates. |
| `src/devpilot_core/reports/__init__.py` | Expone API pública del paquete de reportes. | Boundary importable para otros módulos del core. |
| `tests/test_report_engine.py` | Valida contrato, serialización, snapshot Markdown y CLI con `--write-report`. | Quality gate automatizado del sprint. |
| `docs/functional_sprint_06_manifest.json` | Manifiesto del sprint. | Evidencia docs-as-code de cambios y criterios. |

## 4. Componentes modificados

| Componente | Ajuste | Motivo |
|---|---|---|
| `src/devpilot_core/cli.py` | Agrega `--write-report` a validadores/checklist y helper de reporte. | Integrar gates con ReportEngine sin duplicar lógica. |
| `src/devpilot_core/validators/readiness.py` | `write_readiness_reports()` delega en ReportEngine. | Mantener compatibilidad con `readiness_check.*` usando contrato central. |
| `README.md` | Actualiza estado, comandos y evidencia. | Entrada operativa rápida sincronizada. |
| `docs/05_operations/runbook.md` | Documenta operación y riesgos del ReportEngine. | Guía local de ejecución y recuperación. |
| `docs/functional_backlog_after_precode.md` | Marca Sprint 06 implementado y mueve `next_sprint` a Sprint 07. | Trazabilidad del backlog funcional. |

## 5. Funcionamiento técnico

`ReportEngine` recibe un `CommandResult`, lo envuelve en un `EvidenceReport` y escribe dos archivos bajo `outputs/reports`:

```text
<report_id>.json
<report_id>.md
```

El JSON conserva el contrato máquina-legible completo. El Markdown resume metadatos, mensaje, summary y findings para revisión humana.

El contrato mínimo es:

```text
report_id
command
status
ok
exit_code
message
generated_at
summary
findings
data
subject opcional
project_root opcional
metadata opcional
```

## 6. Comandos de uso

```powershell
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict --json --write-report
python -m devpilot_core validate-artifact docs/01_requirements/requirements_specification.md --strict --json --write-report
python -m devpilot_core checklist-pre-code --json --write-report
python -m pytest -q
```

## 7. Criterios PASS

El sprint se considera PASS si:

- `pytest -q` pasa completo;
- `readiness-check --strict --json` sigue generando `outputs/reports/readiness_check.json` y `.md`;
- `validate-frontmatter ... --write-report` genera JSON/Markdown parseable;
- `validate-artifact ... --write-report` genera JSON/Markdown parseable;
- `checklist-pre-code --write-report` genera JSON/Markdown parseable;
- los reportes incluyen `report_id`, `command`, `status`, `exit_code`, `generated_at`, `summary` y `findings`;
- la escritura de reportes queda limitada al project root.

## 8. Criterios BLOCK

El sprint debe bloquearse si:

- un reporte puede escribirse fuera del project root;
- el JSON generado no es parseable;
- el Markdown omite campos críticos de auditoría;
- se rompe compatibilidad con los comandos previos;
- se agrega una dependencia externa no justificada;
- se requiere API key o red externa;
- `pytest -q` falla.

## 9. Pruebas aplicadas

Pruebas automatizadas incorporadas:

- construcción estable de `report_id`;
- creación de `EvidenceReport` desde `CommandResult`;
- escritura JSON/Markdown por `ReportEngine`;
- snapshot estable del Markdown;
- CLI `validate-frontmatter --write-report`;
- CLI `checklist-pre-code --write-report`;
- suite completa de regresión.

Resultado esperado:

```text
pytest -q -> 36 passed
```

## 10. Riesgos y evolución posterior

Esta implementación es una primera versión. Para alcanzar nivel de producción industrial debe evolucionar con:

- EventLog JSONL (`FUNC-SPRINT-07`);
- SecretGuard/Policy Engine para redacción y control de datos sensibles;
- persistencia SQLite de ejecuciones y evidencias;
- retención/rotación de reportes;
- hashes o firma de evidencias;
- correlación entre reportes, eventos y futuros agentes.

## 11. Decisión ADR

No se abre nueva ADR porque el sprint no modifica una decisión arquitectónica de base, no agrega dependencias, no activa servicios externos, no altera seguridad ni persistencia, y se mantiene dentro del contrato ya aprobado de reportes JSON/Markdown previsto en el backlog. Se documenta como evolución funcional del core CLI y de los gates documentales.
