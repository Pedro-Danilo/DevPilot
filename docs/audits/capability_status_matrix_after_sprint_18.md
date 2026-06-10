---
title: "Capability Status Matrix after Sprint 18 — DevPilot Local"
doc_id: "DEVPL-AUDIT-CAPABILITY-STATUS-AFTER-SPRINT-18-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-20"
updated: "2026-06-10"
approval: "approved_by_owner"
source_sprint: "FUNC-SPRINT-20"
source_backlog: "docs/devpilot_backlog_fase_A_baseline_industrial_minima.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---
# Capability Status Matrix after Sprint 18 — DevPilot Local

## 1. Propósito

Este artefacto materializa `FUNC-20-001`: una matriz reconciliada para que un nuevo desarrollador distinga con precisión qué capacidades de DevPilot están `implemented`, `implemented-initial`, `partial`, `planned`, `disabled` o `future` después del cierre `FUNC-SPRINT-19`.

La matriz evita que el README, el roadmap histórico, C4 o el runbook sobredeclaren capacidades. También sirve como fuente de transición para Fase A, donde se implementarán contratos versionados y trazabilidad ejecutable.

## 2. Estado

| Campo | Valor |
|---|---|
| Sprint que crea el artefacto | `FUNC-SPRINT-20` |
| Baseline técnica reconciliada | `FUNC-SPRINT-00..FUNC-SPRINT-19` |
| Release técnico interno vigente | `v0.1.0` |
| Tipo de cambio | Documental-operativo |
| Cambios de core | Ninguno |
| Dependencias nuevas | Ninguna |
| APIs externas | No usadas |

## 3. Leyenda de estados

| Estado | Significado operativo |
|---|---|
| `implemented` | Existe código/comando/documento probado para el alcance prometido. |
| `implemented-initial` | Existe primera versión funcional, deliberadamente limitada y sujeta a evolución industrial. |
| `partial` | Existe base técnica o contrato, pero faltan piezas para el alcance completo. |
| `planned` | Está definido en backlog/roadmap/registry, pero no implementado. |
| `disabled` | Está declarado, pero bloqueado por política, seguridad, costo o ausencia de aprobación. |
| `future` | Es visión post-MVP o fase posterior; no debe presentarse como disponible. |

## 4. Matriz consolidada

| Dominio | Capacidad | Estado reconciliado | Evidencia actual | Límite explícito |
|---|---|---|---|---|
| Core CLI | Entry point `python -m devpilot_core` | `implemented` | `src/devpilot_core/__main__.py`, `cli.py`, tests CLI | No equivale a binario instalador final. |
| Resultado común | `CommandResult`, `Finding`, `Severity`, `ExitCode` | `implemented` | `src/devpilot_core/cli_models.py` | Falta schema JSON formal hasta Sprint 21/22. |
| Frontmatter | `validate-frontmatter` | `implemented` | Validator + CLI + tests | Parser YAML mínimo, no YAML completo. |
| Artifact validation | `validate-artifact` | `implemented` | Perfiles Python + tests | Validación estructural, no semántica. |
| Checklist | `checklist-pre-code` | `implemented` | Parser Markdown + readiness | No reemplaza juicio técnico humano. |
| Readiness | `readiness-check --strict` | `implemented` | Gate compuesto | Warnings recomendados no bloquean. |
| Standards Registry | `standards status` | `implemented` | MIPSoftware + MIASI locales | No descarga estándares externos. |
| Report Engine | Reportes JSON/Markdown por comando | `implemented` | `outputs/reports` generado en runtime | No hay índice/visor de reportes. |
| Observabilidad | `EventLogger` JSONL | `implemented-initial` | `outputs/traces/events.jsonl` | No hay spans jerárquicos ni OpenTelemetry. |
| Workspace | `workspace init/status` | `implemented-initial` | `.devpilot/project.yaml` | No hay perfiles, migraciones ni multiworkspace. |
| Policy | `PolicyEngine`, `PathGuard`, `SecretGuard`, `CostGuard` | `implemented` | `src/devpilot_core/policy` | No cubre aún sandbox ni approval workflow completo. |
| Persistencia | `LocalStore` SQLite v0 | `implemented-initial` | `state init/status`, `history list` | Tablas approvals/cost_events existen sin flujo operativo completo. |
| MIASI Registry | Agent/Tool/Policy registries | `implemented` | `.devpilot/miasi/*.json`, `miasi validate` | Algunos agentes/tools están planned/future. |
| Agentes documentales | `documentation-audit`, `precode-documentation` | `implemented-initial` | `agent run` | No son agentes LLM-driven ni multiagente. |
| Evaluation Harness | `eval run` | `implemented-initial` | Fixtures offline | No hay juez LLM ni red teaming avanzado. |
| Git | `git-status` read-only | `implemented-initial` | GitAdapter | Branches/tags/log/diff-report dedicado siguen pendientes. |
| Repo Inventory | `repo-inventory` | `implemented-initial` | Inventario por tipo/riesgo | No hay dependency graph ni arquitectura/código drift. |
| Patch Review | `patch-review` | `implemented-initial` | Dry-run parser/reviewer | No aplica patches ni ejecuta `git apply --check`. |
| Code Review | `code-review` | `implemented-initial` | Reglas estáticas locales | No es review semántico ni SAST industrial. |
| Refactor | `refactor-plan` | `implemented-initial` | Plan-only | No ejecuta refactors ni rollback automático. |
| ModelAdapter | Mock provider + router | `partial` | `model providers/generate/classify/embed` mock | Ollama/LM Studio/API externas no tienen cliente real. |
| APIs externas | OpenAI/Gemini externos | `disabled` | CostGuard/ProviderRegistry | No llamar sin ADR, presupuesto, SecretGuard y approval. |
| ApplicationService | DTOs + `app contract` | `implemented-initial` | `src/devpilot_core/application` | No hay UI, API HTTP, IPC ni auth. |
| Desktop/Web | Shell visual | `future` | Contrato lógico solamente | No documentar como implementado. |
| Schema Registry | Catálogo de schemas | `planned` | Backlog Sprint 21 | No existe comando `schema list` todavía. |
| Traceability Engine | Validación SDLC ejecutable | `planned` | Backlog Sprint 25-27 | Solo existe matriz documental histórica. |
| Approval workflow | Request/list/approve/deny | `planned` | Policy/LocalStore preparatorio | No hay comandos operativos. |
| CI/CD/release packaging | Quality gate/release industrial | `planned` | Sprint 19 release interno | No hay pipeline remoto ni firma. |
| RAG/MCP/Multiagente | Capacidades avanzadas | `future` | Backlogs posteriores | No iniciar antes de contratos, schemas y trazabilidad. |

## 5. Funcionamiento del artefacto

Este documento no ejecuta lógica. Funciona como matriz de reconciliación revisable por humanos y como contrato documental para evitar drift entre:

- `README.md`;
- `docs/05_operations/runbook.md`;
- `docs/00_product/product_roadmap.md`;
- vistas C4;
- backlogs Fase A/B/C;
- MIASI registries.

## 6. Integración y rol dentro de DevPilot

La matriz se integra como artefacto de auditoría en `docs/audits/`. Su rol es servir de frontera entre el ciclo 00–19 y la Fase A. Los sprints posteriores deben actualizar esta matriz o crear una nueva versión si cambian estados relevantes.

## 7. Comandos de uso y verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core validate-frontmatter docs/audits/capability_status_matrix_after_sprint_18.md --strict --json
python -m devpilot_core validate-artifact docs/audits/capability_status_matrix_after_sprint_18.md --strict --json
python -m pytest -q
```

## 8. Criterios PASS

- Cada capacidad crítica tiene un estado explícito.
- Las capacidades futuras no se declaran como implementadas.
- ModelAdapter se marca como `partial`, no como cliente real local/API.
- Desktop/Web se marca como `future` o contract-only.
- La matriz es coherente con README, runbook y C4.

## 9. Criterios BLOCK

- Clasificar UI real como implementada.
- Clasificar APIs externas reales como implementadas.
- Omitir el estado `disabled` para proveedores externos bloqueados.
- Presentar patch apply, refactor execution, approval workflow, RAG, MCP o multiagentes como disponibles.

## 10. Riesgos y evolución posterior

Esta matriz es una reconciliación documental. No sustituye validadores ejecutables ni schemas. En Sprint 21–24 debe evolucionar hacia contratos versionados y validables. En Sprint 25–27 debe conectarse con Traceability Engine para dejar cobertura SDLC ejecutable.

## 11. Pruebas implementadas

`tests/test_sprint_20_documentation_reconciliation.py` verifica que este documento exista, tenga frontmatter mínimo y que los estados principales estén presentes en la documentación reconciliada.
