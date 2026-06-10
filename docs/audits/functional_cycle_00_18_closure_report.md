---
title: "Cierre formal ciclo funcional 00-18 — DevPilot Local"
doc_id: "DEVPL-AUDIT-FUNC-CYCLE-00-18-CLOSURE"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-A-OLA-0"
sprint: "FUNC-SPRINT-19"
updated: "2026-06-10"
approval: "approved_by_owner_for_internal_release"
source_repo: "repo_DevPilot_Local_23.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_log: "Log_consola_sprint_18.txt"
---

# Cierre formal ciclo funcional 00-18 — DevPilot Local

## 1. Propósito

Este documento cierra formalmente el ciclo funcional `FUNC-SPRINT-00` a `FUNC-SPRINT-18` de **DevPilot Local** y habilita el inicio controlado de la **Fase A — Baseline industrial mínima**.

El cierre no introduce capacidades nuevas del core. Su función es consolidar el estado real del producto, clasificar capacidades, registrar evidencias, declarar brechas y dejar una base auditada para los sprints posteriores.

## 2. Alcance del cierre

| Elemento | Decisión |
|---|---|
| Ciclo cerrado | `FUNC-SPRINT-00` a `FUNC-SPRINT-18` |
| Sprint de cierre | `FUNC-SPRINT-19 — Cierre formal del ciclo 00-18 y release técnico interno` |
| Release técnico interno | `v0.1.0` |
| Tipo de release | interno, local-first, reproducible, no productivo final |
| Fuente técnica principal | `repo_DevPilot_Local_23.zip` |
| Fuente documental consolidada | `Informe de avance DevPilot - sprint 0 - 18.docx` |
| Evidencia operativa de referencia | `Log_consola_sprint_18.txt` |
| Siguiente sprint | `FUNC-SPRINT-20 — Reconciliación documental post-18 y roadmap vivo` |

## 3. Principios preservados

- Local-first, no local-only.
- API keys no requeridas por defecto.
- Sin llamadas de red en el release técnico interno.
- Dry-run o plan-only para acciones sensibles.
- PolicyEngine, PathGuard, SecretGuard y CostGuard antes de ampliar capacidades.
- Agentes gobernados por MIASI, no agentes autónomos libres.
- Reportes, trazas y pruebas como evidencia mínima de cierre.
- Sin inclusión de outputs runtime, caches, `.git`, `.venv` ni `.devpilot/devpilot.db` en paquetes limpios.

## 4. Sprints implementados y evidencia

| Sprint | Título | Estado declarado | Manifest |
|---|---|---|---|
| FUNC-SPRINT-00 | higiene del repo y sincronización de baseline | approved | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_00_manifest.json` |
| FUNC-SPRINT-01 | Arquitectura interna del CLI y modelo común de resultados | approved | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_01_manifest.json` |
| FUNC-SPRINT-02 | Validador de frontmatter y metadatos documentales | approved | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_02_manifest.json` |
| FUNC-SPRINT-03 | FUNC-SPRINT-03 Manifest | approved | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_03_manifest.json` |
| FUNC-SPRINT-04 | Standards Registry y carga local de reglas | implemented | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_04_manifest.json` |
| FUNC-SPRINT-05 | Checklist pre-code y readiness estricto | implemented | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_05_manifest.json` |
| FUNC-SPRINT-06 | Report Engine y contrato de evidencias | implemented | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_06_manifest.json` |
| FUNC-SPRINT-07 | Event Log JSONL y observabilidad local | implemented | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_07_manifest.json` |
| FUNC-SPRINT-08 | Workspace Manager mínimo | implemented_initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_08_manifest.json` |
| FUNC-SPRINT-09 | Policy Engine, PathGuard, SecretGuard y CostGuard determinísticos | implemented | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_09_manifest.json` |
| FUNC-SPRINT-10 | Persistencia local SQLite y estado operativo | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_10_manifest.json` |
| FUNC-SPRINT-11 | MIASI ejecutable: Agent Registry, Tool Registry y Policy Matrix | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_11_manifest.json` |
| FUNC-SPRINT-12 | Agent Runtime mock/local para agentes documentales MVP | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_12_manifest.json` |
| FUNC-SPRINT-13 | Evaluation Harness para validadores y agentes | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_13_manifest.json` |
| FUNC-SPRINT-14 | Git read-only y repo inventory MVP+ | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_14_manifest.json` |
| FUNC-SPRINT-15 | Patch review y code review en dry-run | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_15_manifest.json` |
| FUNC-SPRINT-16 | Safe Refactor Planner | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_16_manifest.json` |
| FUNC-SPRINT-17 | ModelAdapter híbrido, proveedores y CostGuard | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_17_manifest.json` |
| FUNC-SPRINT-18 | Preparación de Desktop/Web sin implementar UI completa | implemented-initial | `/mnt/data/work_devpilot/repo_23/docs/functional_sprint_18_manifest.json` |

## 5. Capacidades implementadas

### 5.1 Plataforma y CLI

- CLI local ejecutable mediante `python -m devpilot_core`.
- Versión de paquete `devpilot-local 0.1.0`.
- Contrato común `CommandResult`, `Finding`, `Severity` y `ExitCode`.
- Salidas `--json` en comandos principales.
- Manejo estructurado de findings y exit codes.
- Suite `pytest` vigente con 122 pruebas en PASS antes del Sprint 19.

### 5.2 Validación, estándares y readiness

- `validate-frontmatter`.
- `validate-artifact`.
- `checklist-pre-code`.
- `readiness-check --strict`.
- `standards status`.
- Perfiles documentales MIPSoftware/MIASI en validadores determinísticos.
- Baseline documental aprobada para producto, requisitos, arquitectura, seguridad, calidad, operación y MIASI.

### 5.3 Evidencia, observabilidad y persistencia

- `ReportEngine` para reportes JSON/Markdown.
- `EventLogger` JSONL para eventos locales.
- `LocalStore` SQLite v0 para runs, findings, gates, events, approvals y cost_events iniciales.
- Comandos `state init`, `state status` y `history list`.

### 5.4 Seguridad operacional local

- `PolicyEngine` determinístico.
- `PathGuard` para evitar rutas fuera del workspace.
- `SecretGuard` para detectar/redactar secretos sintéticos.
- `CostGuard` para bloquear costos externos no autorizados.
- Configuración local `.devpilot/policy.yaml`.
- Bloqueo por defecto de proveedores externos.

### 5.5 MIASI y agentes iniciales

- MIASI Agent Registry ejecutable.
- MIASI Tool Registry ejecutable.
- MIASI Policy Matrix ejecutable.
- `miasi validate`, `miasi validate-registry`, `miasi validate-tools`, `miasi validate-policy-matrix`.
- `AgentRuntime` mock/local para agentes documentales.
- Agentes implementados: `precode.documentation` y `precode.audit`.
- `EvalRunner` offline para casos documentales.

### 5.6 Repositorio, revisión y refactor seguro

- `git-status` read-only.
- `repo-inventory`.
- `patch-review` en dry-run.
- `code-review` en dry-run.
- `refactor-plan` en plan-only.
- No existe aplicación de patches ni refactor automático en este ciclo.

### 5.7 ModelAdapter y frontera futura UI

- `ModelAdapter` contract.
- `MockModelAdapter` determinístico y offline.
- `ProviderRegistry` con placeholders seguros.
- `ModelAdapterRouter` con CostGuard.
- `ApplicationService` como frontera interna para CLI/Desktop/Web futuros.
- DTOs serializables `ApplicationRequest`, `ApplicationResponse`, `ServiceCapability` e `InterfaceRouteContract`.
- `app contract` para exponer capacidades lógicas sin implementar UI.

## 6. Capacidades implementadas iniciales

Estas capacidades existen y funcionan para el alcance del ciclo, pero requieren endurecimiento posterior para considerarse industriales:

| Capacidad | Estado de cierre | Límite explícito |
|---|---|---|
| Workspace Manager | implementado inicial | sin schema formal, migraciones ni perfiles |
| SQLite LocalStore | implementado inicial | sin workflow operativo de approvals/costos |
| EventLogger JSONL | implementado inicial | sin spans, trace report ni OpenTelemetry |
| MIASI executable registry | implementado inicial | valida declaraciones, no coordina multiagentes |
| AgentRuntime documental | implementado inicial | solo agentes documentales locales, sin LLM |
| Evaluation Harness | implementado inicial | casos sintéticos documentales, sin judge avanzado |
| GitAdapter | implementado inicial | status/diff stats read-only, sin ramas/tags/log completo |
| RepoInventory | implementado inicial | inventario estructural básico, sin análisis semántico profundo |
| Code/Patch Review | implementado inicial | heurístico local, sin sandbox ni aplicación |
| Safe Refactor Planner | implementado inicial | plan-only, sin ejecución ni rollback real |
| ModelAdapter | implementado inicial | mock real, proveedores locales/API como planned/disabled |
| ApplicationService | implementado inicial | contrato interno, sin HTTP, IPC, Desktop ni Web real |

## 7. Capacidades parcialmente implementadas

| Capacidad | Evidencia existente | Pendiente |
|---|---|---|
| Traceability | matriz documental y manifests | Traceability Engine ejecutable |
| Schema Engine | schemas en estándares y contratos documentales | Schema Registry/Validator formal |
| MIASI detector avanzado | `miasi-required` y registry | explicación avanzada y reglas de activación más profundas |
| Human approval | cards, flags y tablas | CLI/workflow request-list-approve-deny |
| ModelAdapter híbrido completo | mock y providers metadata | clientes reales Ollama/LM Studio/OpenAI/Gemini bajo política |
| Desktop/Web | DTOs y app contract | UI, API local, IPC, auth/RBAC |
| Release/operación | runbook y comandos smoke | release command, changelog automatizado, tagging, firma |

## 8. Capacidades definidas pero no implementadas

- Env Builder/Validator.
- `tests.run` como tool gobernada.
- Approval workflow operativo.
- Patch apply sandbox.
- Refactor execution.
- Clientes reales Ollama y LM Studio.
- Clientes reales OpenAI, Gemini, Mistral y Hugging Face.
- RequirementsAgent, ArchitectureAgent, SecurityAgent, TestPlannerAgent.
- RepoAnalysisAgent avanzado, CodeReviewAgent, PatchReviewAgent y SafeRefactorAgent operativos.
- ReleaseAgent y OperationsAgent.
- MultiAgentCoordinator.
- CI/CD local como quality gate formal.
- Release/deploy assist.

## 9. Capacidades no iniciadas

- Aplicación desktop real.
- Aplicación web real.
- Servidor HTTP/API local.
- IPC desktop-core.
- Dashboard visual.
- Autenticación, autorización y RBAC.
- Colaboración multiusuario.
- RAG documental industrial.
- MCP/conectores externos.
- SAST/SCA externo.
- SBOM y supply-chain security.
- OpenTelemetry/spans.
- AgentOps dashboard.
- Sandbox real de ejecución.
- Rollback automático.
- Instalador, auto-update o distribución productiva.

## 10. Estado de pruebas y comandos de verificación

### 10.1 Estado probado antes del cierre

El log de Sprint 18 dejó la suite en PASS:

```text
DEVPL TEST SUMMARY: 122 passed, 0 failed, 0 errors, 0 skipped
```

### 10.2 Comandos smoke mínimos del release interno

```powershell
$env:PYTHONPATH="src"
python -m pytest -q
python -m devpilot_core --version
python -m devpilot_core workspace status --json
python -m devpilot_core standards status --json
python -m devpilot_core readiness-check --strict --json
python -m devpilot_core miasi validate --json
python -m devpilot_core eval run --json
python -m devpilot_core app contract --json
```

### 10.3 Verificación automatizada opcional

```powershell
$env:PYTHONPATH="src"
python scripts/verify_release_v0_1_0.py --json
```

## 11. Evidencias del cierre

| Evidencia | Ruta |
|---|---|
| Reporte de cierre ciclo 00-18 | `docs/audits/functional_cycle_00_18_closure_report.md` |
| Release manifest v0.1.0 | `docs/release/release_manifest_v0.1.0.json` |
| Release notes v0.1.0 | `docs/release/release_notes_v0.1.0.md` |
| Manifest Sprint 19 | `docs/functional_sprint_19_manifest.json` |
| Script smoke interno | `scripts/verify_release_v0_1_0.py` |
| Prueba de manifest | `tests/test_release_manifest.py` |
| Runbook actualizado | `docs/05_operations/runbook.md` |
| README actualizado | `README.md` |

## 12. Deuda técnica reconocida

| Área | Deuda | Severidad |
|---|---|---|
| CLI | `cli.py` concentra demasiada orquestación | media |
| Schemas | contratos sin JSON Schema formal | media |
| Trazabilidad | existe matriz documental, falta motor ejecutable | alta para Fase A |
| Persistencia | SQLite v0 sin migraciones ni consultas avanzadas | media |
| Aprobación humana | contrato sin workflow operativo | alta antes de acciones críticas |
| Observabilidad | JSONL sin spans ni reportes agregados | media |
| Git/repo | análisis read-only básico | media |
| Release | release interno no firmado | media-baja |
| UI | solo contrato, sin interfaz real | esperada por diseño |
| Modelos | mock real, proveedores reales pendientes | esperada por diseño |

## 13. Riesgos

| Riesgo | Impacto | Control actual |
|---|---|---|
| Documentación sobredeclare capacidades futuras | confusión de adopción | clasificación implementado/parcial/planned/future |
| Paquete limpio incluya runtime outputs | contaminación de release | exclusiones `.gitignore` y ZIP limpio externo |
| Habilitar agentes antes de políticas completas | riesgo operativo | MIASI, PolicyEngine, dry-run y approval_required |
| Usar APIs externas sin presupuesto | costo o fuga de datos | CostGuard bloquea externos por defecto |
| Aplicar patches/refactors sin sandbox | pérdida de código | no implementado; solo dry-run/plan-only |
| Release sin firma criptográfica | integridad limitada | SHA256 informativo, firma futura |

## 14. Brechas frente al roadmap

| Dominio | Brecha principal | Fase prevista |
|---|---|---|
| Contratos | Schema Registry y Validator | Fase A, Ola 1 |
| Trazabilidad | Traceability Engine y cobertura SDLC | Fase A, Ola 2 |
| Seguridad operacional | Approval workflow, policy hardening | Fase B |
| Ingeniería de repositorio | análisis profundo, patch sandbox | Fase C |
| IA local gobernada | Ollama/LM Studio/API controlada | Fase D |
| AgentOps | trazas avanzadas, métricas, dashboard | Fase E |
| Producto visual | desktop/web real | Fase F |
| Productización | release packaging, CI/CD, distribución | Fase G |
| Capacidades avanzadas | multiagentes, RAG, MCP | Fase H |

## 15. Recomendaciones

1. Ejecutar `FUNC-SPRINT-20` antes de tomar decisiones UI/API para eliminar inconsistencias heredadas.
2. Formalizar schemas en `FUNC-SPRINT-21` y `FUNC-SPRINT-22` antes de ampliar contratos consumidos por UI.
3. Mantener proveedores externos bloqueados hasta que exista ledger de costo, SecretGuard ampliado y política de presupuesto.
4. No implementar patch apply ni refactor execution sin approval workflow, sandbox y rollback.
5. Usar `ApplicationService` como frontera obligatoria de futura UI para evitar duplicación de lógica de CLI.
6. Mantener manifiestos y reportes de sprint como evidencia obligatoria de avance.

## 16. Criterios de cierre

### PASS

- Existe este reporte de cierre.
- Existe release manifest `v0.1.0`.
- Existe release notes `v0.1.0`.
- Existe manifest `FUNC-SPRINT-19`.
- README y runbook referencian el release técnico interno.
- Existe script de verificación smoke interno.
- Existe prueba automatizada para validar el release manifest.
- `pytest -q` pasa.
- Los comandos smoke pasan.
- El release limpio externo excluye outputs/runtime, caches, `.git`, `.venv` y `.devpilot/devpilot.db`.

### BLOCK

- El manifest de release referencia outputs runtime como fuente.
- Se afirma como implementada una capacidad que solo está planned, disabled o future.
- Falla `pytest -q`.
- Falta trazabilidad entre release, sprints 00-18 y Fase A.
- Se introduce dependencia externa o llamada de red sin ADR.

## 17. Criterios para iniciar Fase A

DevPilot puede iniciar Fase A si:

- `FUNC-SPRINT-19` queda en PASS.
- El ciclo 00-18 queda cerrado como baseline de referencia.
- El release técnico interno `v0.1.0` es verificable localmente.
- La documentación diferencia claramente implementado, inicial, parcial, planned, disabled y future.
- Los paquetes entregados no contienen runtime outputs.

## 18. Relación con backlogs posteriores

Este cierre crea la línea base para:

- `FUNC-SPRINT-20`: reconciliación documental post-18.
- `FUNC-SPRINT-21` a `FUNC-SPRINT-24`: contratos y schemas.
- `FUNC-SPRINT-25` a `FUNC-SPRINT-27`: trazabilidad SDLC y cierre de baseline industrial mínima.
- Fases B-H: seguridad operacional, ingeniería de repositorio, IA local gobernada, AgentOps, producto visual, productización y capacidades avanzadas.

## 19. Veredicto

`FUNC-SPRINT-19` puede cerrarse cuando los comandos de verificación y la prueba `tests/test_release_manifest.py` pasen. Este sprint debe considerarse un cierre técnico-documental, no una ampliación funcional del core.
