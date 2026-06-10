---
title: "Roadmap Reconciliation after Sprint 18 — DevPilot Local"
doc_id: "DEVPL-AUDIT-ROADMAP-RECONCILIATION-AFTER-SPRINT-18-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-20"
updated: "2026-06-10"
approval: "approved_by_owner"
source_sprint: "FUNC-SPRINT-20"
source_roadmap: "docs/00_product/product_roadmap.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---
# Roadmap Reconciliation after Sprint 18 — DevPilot Local

## 1. Propósito

Este artefacto implementa `FUNC-20-002`: reconciliar el roadmap histórico con el estado real del código después de cerrar `FUNC-SPRINT-19`. Su objetivo es preservar la intención original sin presentar nombres planeados como comandos ya disponibles.

## 2. Estado

| Campo | Valor |
|---|---|
| Sprint que crea el artefacto | `FUNC-SPRINT-20` |
| Roadmap reconciliado | `docs/00_product/product_roadmap.md` |
| Baseline evaluada | `FUNC-SPRINT-00..FUNC-SPRINT-19` |
| Tipo de intervención | Documental, no funcional |
| Cambios de core | Ninguno |
| Dependencias nuevas | Ninguna |

## 3. Regla de lectura del roadmap histórico

`docs/00_product/product_roadmap.md` queda clasificado como **roadmap histórico + direccional**. Las tablas de comandos esperados conservan intención de producto, pero el estado operativo vigente debe consultarse en:

- este documento;
- `docs/audits/capability_status_matrix_after_sprint_18.md`;
- `README.md`;
- `docs/05_operations/runbook.md`;
- backlogs Fase A/B/C.

## 4. Mapeo de nombres planeados vs comandos reales

| Nombre en roadmap histórico | Estado real | Comando real vigente | Decisión de reconciliación |
|---|---|---|---|
| `report generate` | No existe comando genérico | Reportes integrados por `--write-report` | Mantener como intención futura de Report Index/Report CLI. |
| `validate-schema` | No implementado | Ninguno todavía | Queda para `FUNC-SPRINT-22` como `schema validate` si el backlog lo confirma. |
| `miasi-required --explain` | Parcial | `miasi-required --json`, `miasi validate --json` | Mantener detector avanzado como pendiente. |
| `policy-check` | Reconciliado | `policy check ... --json` | Usar nombre real con subcomando. |
| `git-branches` | No implementado | `git-status --json` incluye alcance read-only limitado | Marcar branches/tags/log como pendientes. |
| `git-diff-report` | No implementado como comando dedicado | `git-status --json`, diff stats iniciales | Mantener como pendiente de Git Adapter completo. |
| `repo-scan` | Reconciliado | `repo-inventory --json` | Usar nombre real. |
| `patch-review --dry-run` | Reconciliado | `patch-review --patch-file <file> --json` | El motor es dry-run por diseño. |
| `review-code --dry-run` | Reconciliado | `code-review --target <path> --json` | El motor es dry-run por diseño. |
| `refactor-plan --dry-run` | Reconciliado | `refactor-plan --target <path> --goal "..." --json` | El planner es plan-only por diseño. |
| `agent review --dry-run` | Parcial | `agent run documentation-audit`, `agent run precode-documentation` | Solo agentes documentales MVP están implementados. |
| `trace report` | No implementado | Eventos JSONL runtime | Mantener como pendiente de observabilidad avanzada. |
| `approval request/list/approve` | No implementado | Ninguno | Mantener como planned; tablas/policies son preparatorias. |
| `devpilot init-project` | No existe como binario separado | `python -m devpilot_core workspace init` | Documentar forma real hasta packaging. |
| `devpilot repo-scan` | No existe como binario separado | `python -m devpilot_core repo-inventory --json` | Documentar forma real. |

## 5. Funcionamiento del artefacto

Este documento actúa como puente entre intención histórica y operación real. No borra el roadmap; agrega una capa de interpretación para que sprints futuros no hereden nombres incorrectos.

## 6. Integración y rol dentro de DevPilot

- README usa los comandos reales como entrada rápida.
- Runbook agrupa comandos reales por dominio.
- C4 marca estados `implemented`, `partial`, `planned`, `disabled` y `future`.
- Fase A usa esta reconciliación para no construir Schema Engine o Traceability Engine sobre premisas obsoletas.

## 7. Comandos de uso y verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core validate-frontmatter docs/audits/roadmap_reconciliation_after_sprint_18.md --strict --json
python -m devpilot_core validate-artifact docs/audits/roadmap_reconciliation_after_sprint_18.md --strict --json
python -m devpilot_core --version
python -m pytest -q
```

## 8. Criterios PASS

- Los nombres planeados no se presentan como comandos implementados.
- Las equivalencias reales están documentadas.
- Las capacidades no implementadas quedan marcadas como planned/future/disabled.
- El roadmap histórico preserva intención y remite a esta reconciliación.

## 9. Criterios BLOCK

- Reemplazar la historia del roadmap sin trazabilidad.
- Documentar `validate-schema`, `git-diff-report`, `approval request` o UI real como comandos disponibles.
- Presentar proveedores externos como habilitados.

## 10. Riesgos y evolución posterior

Esta reconciliación es una primera versión documental. Debe evolucionar cuando `FUNC-SPRINT-21` a `FUNC-SPRINT-27` creen schemas, ValidationGateway y Traceability Engine. En producción industrial, la reconciliación debería ser parcialmente verificable por un Command Catalog ejecutable.

## 11. Pruebas implementadas

`tests/test_sprint_20_documentation_reconciliation.py` verifica la existencia de este documento y la presencia de mapeos críticos como `policy-check` → `policy check`, `repo-scan` → `repo-inventory`, `review-code --dry-run` → `code-review` y `git-diff-report` como pendiente.
