---
doc_id: "POSTH-ROADMAP-001"
id: "POST-H-EVAL-001-F"
title: "Roadmap priorizado post-H y decisiones arquitectónicas"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "approved_by_owner"
micro_sprint: "POST-H-EVAL-001-F"
phase: "POST-FASE-H"
local_first: true
dry_run: true
no_runtime_features_added: true
no_remote_execution_enabled: true
---

# Roadmap priorizado post-H y decisiones arquitectónicas

## 1. Propósito

Este documento materializa `POST-H-EVAL-001-F — Roadmap priorizado post-H y decisiones arquitectónicas`.
Su función es convertir los hallazgos de los micro-sprints A-E en una hoja de ruta ejecutable, priorizada y gobernada para DevPilot Local después de Fase H y `POST-H-001`.

Este artefacto no implementa features runtime. Es una decisión de producto/arquitectura para ordenar los siguientes hitos con criterios de entrada explícitos, dependencias, riesgos, límites de seguridad y condiciones de madurez.

## 2. Fuente de verdad y evidencias de entrada

| Insumo | Rol en el roadmap | Evidencia usada |
|---|---|---|
| `docs/audits/post_h_eval_001_baseline_assessment.md` | Baseline cuantitativo y matriz de madurez | Capacidades por dominio, estado, riesgos y prioridades |
| `.devpilot/evals/post_h_eval_001_decision_matrix.json` | Fuente machine-readable de madurez | Conteos `production-ready-local`, `implemented`, `implemented-initial`, `experimental` |
| `docs/02_architecture/post_h_current_architecture_map.md` | Mapa arquitectónico real | CLI monolítico, capas, paquetes, acoplamientos y refactors recomendados |
| `docs/03_security/post_h_security_risk_register.md` | Risk register industrial | Remote execution crítica, connectors write, plugin execution, runtime artifacts y compliance |
| `.devpilot/evals/post_h_eval_001_security_risk_register.json` | Fuente machine-readable de riesgos | Prioridades P0/P1/P2, severidades y criterios de cierre |
| `docs/04_quality/post_h_test_cost_assessment.md` | Evaluación de testing/costos | Registry v1, gaps del impact analyzer y propuesta de Test Contract Registry 2.0 |
| `.devpilot/evals/post_h_eval_001_test_cost_assessment.json` | Fuente machine-readable de testing | 187 tests, 893 casos recolectables, 84 contratos, 103 tests no mapeados |
| `docs/post_h_eval_001_manifest.json` | Trazabilidad del hito | Entregables A-E, decisiones y validaciones |
| `Informe de onboarding DevPilot — Hasta POST-H-EVAL-001.docx` | Onboarding humano y reverse engineering consolidado | Preguntas 1-16: core domain, runtime, workspace, validadores, MIASI, agentes, gap analysis, capability maturity, reverse engineering y guía de operador |

## 3. Principios de priorización

1. **Local-first antes de remote:** DevPilot debe madurar como producto local industrial antes de habilitar ejecución remota, conectividad distribuida o conectores write-enabled.
2. **Seguridad y testing antes de features:** los próximos hitos deben reducir deuda de seguridad, contratos, testing, arquitectura y documentación antes de ampliar autonomía.
3. **Diagnóstico ejecutable antes de dashboard:** `POST-H-002` debe consumir la matriz de madurez y no construir un dashboard ornamental.
4. **Dry-run por defecto:** ninguna oleada puede relajar dry-run ni aprobar acciones destructivas por acumulación incremental.
5. **Evidencia antes de claims:** los documentos deben diferenciar `production-ready-local`, `implemented`, `implemented-initial`, `experimental`, `planned`, `defined/no implementado` y `future`.
6. **Costos controlados:** no se activan APIs externas ni ejecuciones costosas sin CostGuard, budget, trazabilidad y aprobación.
7. **Contratos antes de acoplamientos nuevos:** toda nueva superficie de API/UI/agent/tools debe tener schema, test contract, policy y verificación.
8. **Onboarding operable antes de declarar producción:** DevPilot no debe declararse `production-ready` completo sin playbooks de operador, bootstrap de proyectos nuevos y un gate explícito de declaración basado en evidencia.

## 4. Resumen ejecutivo de prioridades

| Prioridad | Enfoque | Justificación |
|---|---|---|
| P0 | Cerrar `POST-H-EVAL-001`, higiene de repo, maturity dashboard, Test Contract Registry 2.0 y Policy/MIASI semantic validation | Reduce riesgos críticos y convierte el diagnóstico en señales operables |
| P1 | CLI modularization, ApplicationService boundary, runtime state lifecycle, observabilidad, approval/RBAC, UI/API shell industrial y onboarding operativo | Reduce acoplamiento, fortalece operación local, prepara producto visual seguro y habilita adopción controlada por operadores |
| P2 | Portfolio/multiworkspace, release reproducibility, operator/project bootstrap, connector sandbox, plugin sandbox design y compliance packs | Expande capacidades controladas sin adelantar remote/enterprise |
| P3 | Remote runner ADR-2, enterprise deployment threat model y secure transport design | Permanece como diseño hasta que existan garantías P0/P1 suficientes |

## 5. Roadmap priorizado por oleadas

### Oleada 0 — Baseline limpio y diagnóstico

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P0 | `POST-H-EVAL-001` | Completar evaluación integral, roadmap, ADRs, manifest final y prueba documental de cierre | A-E implementados y validados | A-E PASS focal; no runtime features | G cerrado con manifest final, pruebas documentales y ZIP limpio |
| P0 | Repo hygiene final | Garantizar fuente ZIP limpia sin runtime artifacts | Risk register D, export hygiene | Working tree limpio; `.gitignore` vigente | ZIP sin `outputs/`, `.git/`, `.venv/`, `.devpilot/devpilot.db`, caches ni `node_modules/` |

### Oleada 1 — Gobernanza de madurez y testing

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P0 | `POST-H-002 — Maturity dashboard local basado en assessment post-H` | Dashboard local read-only sobre madurez, riesgos, testing, quality gates e industrial readiness | `POST-H-EVAL-001` cerrado | Matriz de madurez, risk register, test/cost assessment, architecture map y manifest final | Dashboard consume fuentes POST-H-EVAL-001 y diferencia madurez por dominio |
| P0 | `POST-H-003 — Test Contract Registry 2.0` | Evolucionar contratos por dominio, criticidad, riesgo, costo, trigger e impacto | Assessment E, ADR-POSTH-002 | Registry v1 PASS; gaps identificados | Schema v2, migración controlada, impact analyzer más granular y tests P0/P1 mapeados |
| P0 | `POST-H-004 — Policy/MIASI semantic validator ampliado` | Validar coherencia semántica entre policy matrix, tools, agents, approvals, RBAC y security guards | Risk register D, maturity matrix B | MIASI structural validation PASS | Validator detecta permisos contradictorios, approvals faltantes y capacidades sensibles mal clasificadas |
| P0 | `POST-H-005 — Architecture map executable / dependency ownership` | Convertir mapa C en inventario ejecutable de paquetes, ownership, dependencias y acoplamientos | Architecture map C, ADR-POSTH-003 | Mapa actual aprobado | Reporte reproducible de ownership/dependencies y baseline para CLI modularization |

### Oleada 2 — Mantenibilidad y arquitectura interna

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P1 | `POST-H-006 — CLI command registry y desacoplamiento de handlers` | Reducir riesgo de CLI monolítico mediante registry de comandos y handlers por dominio | ADR-POSTH-003, POST-H-005 | Paquetes/ownership inventariados | CLI conserva contratos y tests; handlers desacoplados sin cambiar semántica |
| P1 | `POST-H-007 — ApplicationService boundary hardening` | Fortalecer frontera CLI/API/UI con DTOs, schemas, errores y capabilities estables | POST-H-006 recomendado | App contract actual PASS | Frontera estable para UI/API sin duplicar lógica core |
| P1 | `POST-H-008 — Runtime state lifecycle policy` | Definir retención, export, backup, limpieza y exclusión de runtime state | Risk register D | `.devpilot` runtime paths identificados | Política y checks impiden distribuir DB, sesiones, outputs y traces sensibles |
| P1 | `POST-H-009 — Documentation governance y canonical sources` | Reducir drift entre README, runbook, backlog, manifests, ADRs y audit docs | A-E, roadmap F | Docs POST-H-EVAL sincronizados | Mapa de fuentes canónicas, owners, actualización mínima y tests documentales menos frágiles |

### Oleada 3 — Observabilidad, RAG y seguridad operacional

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P1 | `POST-H-010 — Observability retention local` | Establecer retención, rotación, redacción y consulta local de trazas/eventos | POST-H-008 | Trace store/event logs actuales documentados | Retention policy y reportes locales sin exponer secretos |
| P1 | `POST-H-011 — RAG groundedness evals` | Evaluar groundedness, redacciones, citas y límites del RAG lexical/local | RAG local implemented-initial, risk SEC-010 | RAG index local PASS | Evals de groundedness y riesgo de respuesta no fundamentada |
| P1 | `POST-H-012 — Approval/RBAC hardening` | Endurecer approval, actor identity, RBAC y policy binding | Risk SEC-004/SEC-007 | Tests actuales de approval/RBAC PASS | Contratos P0 para acciones sensibles y límites de actor spoofing local |
| P1 | `POST-H-013 — Audit pack signing/encryption local opcional` | Diseñar evidencia local con integridad opcional sin cloud obligatoria | Runtime lifecycle, compliance risks | Audit packs actuales PASS | Checksums/firma local opcional y no-certification disclaimer |

### Oleada 4 — Producto local industrial

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P1 | `POST-H-014 — UI/API industrial shell` | Shell local seguro para consumir status, maturity, reports, traces y settings | POST-H-002, POST-H-007, POST-H-012 | API/UI threat model y app boundary PASS | UI/API read-only/dry-run con auth local y sin acciones críticas |
| P1 | `POST-H-015 — Local operator dashboard` | Dashboard operativo para gates, riesgos, traces, test contracts y roadmap | POST-H-014 | UI/API shell estable | Vista de operación local con criterios PASS/BLOCK y drill-down documental |
| P2 | `POST-H-016 — Workspace portfolio hardening` | Gestionar múltiples workspaces con límites de path, estado y reportes | Multiworkspace baseline | Policy/PathGuard fortalecidos | Portfolio local sin mezclar runtime state ni permisos entre workspaces |
| P2 | `POST-H-017 — Release reproducibility pack` | Empaquetado reproducible con checksums, manifest, changelog y verificación de higiene | Repo hygiene, release dry-run | ZIP limpio y release docs actuales | Release pack reproducible sin artifacts prohibidos |
| P1 | `POST-H-024 — Operator onboarding playbook y project bootstrap workflow` | Convertir el informe de onboarding y la guía de operador en playbooks, plantillas y flujo verificable para iniciar proyectos nuevos con DevPilot | POST-H-002, POST-H-009, POST-H-014 | Dashboard de madurez y fuentes canónicas disponibles | Playbook aprobado, templates de proyecto nuevo, checklist de operador y evidencia de uso en un proyecto piloto local sin remote/write/plugins |

### Oleada 5 — Extensibilidad controlada

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P2 | `POST-H-018 — Connector sandbox avanzado` | Diseñar sandbox/replay para conectores antes de write-enabled | SEC-002, POST-H-012 | Conectores read-only PASS | Sandbox/replay tests; writes siguen deshabilitados por defecto |
| P2 | `POST-H-019 — Plugin sandbox design sin ejecución arbitraria` | Definir sandbox de plugins y prohibir ejecución arbitraria no aislada | SEC-003, POST-H-012 | Plugin registry metadata-only PASS | Diseño, schemas y tests de denegación; no ejecución real todavía |
| P2 | `POST-H-020 — Compliance mapping packs ampliados` | Mapear controles internos a packs de evidencia sin claim certificable | SEC-009, POST-H-013 | No-certification disclaimer vigente | Packs ampliados con gaps explícitos y sin declarar cumplimiento certificado |

### Oleada 6 — Remote/enterprise solo como diseño

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P3 | `POST-H-021 — Remote Runner ADR-2` | Reabrir decisión remote solo a nivel ADR, sin ejecución activa | P0/P1 completados, SEC-001 mitigado parcialmente | Threat model local completo y approval/RBAC hardening | ADR aceptada o rechazada; remote sigue disabled |
| P3 | `POST-H-022 — Enterprise deployment threat model` | Threat model de despliegue enterprise antes de cualquier control plane | POST-H-021 | No hay remote execution activa | Riesgos, límites, controles, actores y criterios de no-go |
| P3 | `POST-H-023 — Secure transport design sin implementación activa` | Diseñar transporte seguro sin habilitar red ni workers remotos | POST-H-022 | ADR/threat model aprobados | Diseño comparativo y criterios para un futuro spike aislado |

### Oleada 7 — Declaración local production-ready

| Prioridad | Hito | Objetivo | Dependencias | Criterio de entrada | Criterio de salida |
|---|---|---|---|---|---|
| P0 | `POST-H-025 — DevPilot Local production-ready declaration gate` | Ejecutar un gate final de declaración local `production-ready` basado en evidencia, sin claims enterprise/remote/compliance certificada | POST-H-002 a POST-H-017 y POST-H-024; remote/connector/plugin gates cerrados | P0/P1 completados, riesgos críticos mitigados o explícitamente bloqueados, suite y contracts PASS | Declaración `production-ready-local` o `BLOCK` con gaps; no habilita remote, connector write ni plugin execution |

## 6. Decisiones arquitectónicas mínimas

| ID | Decisión | Estado | ADR |
|---|---|---|---|
| DEC-POSTH-001 | DevPilot continuará como producto local-first industrial antes de ampliar autonomía, conectividad remota o ejecución distribuida. | Aceptada | `docs/adr/ADR-POSTH-001-local-first-before-remote.md` |
| DEC-POSTH-002 | `POST-H-002` se mantiene, pero debe basarse en matriz de madurez y roadmap definidos por `POST-H-EVAL-001`. | Aceptada | Este roadmap |
| DEC-POSTH-003 | No se habilitará remote execution real sin ADR nueva, threat model, RBAC fuerte, sandbox, auditoría y aprobación humana. | Aceptada | `docs/adr/ADR-POSTH-001-local-first-before-remote.md` |
| DEC-POSTH-004 | El CLI monolítico entra al roadmap de refactor arquitectónico. | Aceptada | `docs/adr/ADR-POSTH-003-cli-modularization.md` |
| DEC-POSTH-005 | El Test Contract Registry debe evolucionar hacia contratos por dominio, criticidad, riesgo e impacto. | Aceptada | `docs/adr/ADR-POSTH-002-test-contract-registry-2.md` |
| DEC-POSTH-006 | Los audit packs, ZIPs y fuentes de verdad futuras deben excluir runtime artifacts. | Aceptada | Este roadmap + risk register D |
| DEC-POSTH-007 | `POST-H-EVAL-001` debe permanecer cerrado y estable antes de iniciar `POST-H-002`; cualquier ajuste posterior al roadmap debe conservar no-go gates. | Aceptada | Manifest G + este roadmap |
| DEC-POSTH-008 | El onboarding de operadores y el bootstrap verificable de proyectos nuevos son requisitos de madurez antes de declarar DevPilot productivo localmente. | Aceptada | Este roadmap |
| DEC-POSTH-009 | La declaración `production-ready-local` debe producirse por un gate explícito basado en evidencia, no por afirmación documental. | Aceptada | Este roadmap |

## 7. Refinamiento obligatorio de POST-H-002

Nombre refinado:

```text
POST-H-002 — Maturity dashboard local basado en assessment post-H
```

Objetivo refinado:

```text
Construir un dashboard local read-only que consuma project_state, industrial readiness, quality gates, test contracts, risk register, architecture map y matriz de evaluación POST-H-EVAL-001 para visualizar madurez, riesgos, deuda, evidencia y roadmap.
```

### Fuentes mínimas que debe consumir POST-H-002

```text
.devpilot/project_state.json
.devpilot/evals/post_h_eval_001_decision_matrix.json
.devpilot/evals/post_h_eval_001_security_risk_register.json
.devpilot/evals/post_h_eval_001_test_cost_assessment.json
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
docs/audits/post_h_eval_001_baseline_assessment.md
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/backlogs/post_h_prioritized_roadmap.md
docs/post_h_eval_001_manifest.json
```

### Lo que POST-H-002 no debe ser

```text
No debe ser un dashboard ornamental.
No debe ser solo un score agregado.
No debe reemplazar el roadmap ni los ADRs.
No debe habilitar remote execution, connector write ni plugin execution.
No debe consumir outputs runtime como fuente canónica.
```

## 8. Criterios de entrada para POST-H-002

`POST-H-002` solo puede iniciar si:

| Criterio | Estado esperado |
|---|---|
| `POST-H-EVAL-001` cerrado con micro-sprint G | Obligatorio |
| Roadmap priorizado existe | Obligatorio |
| Matriz de madurez existe | Obligatorio |
| Baseline assessment existe | Obligatorio |
| Risk register existe | Obligatorio |
| Test/cost assessment existe | Obligatorio |
| Architecture map existe | Obligatorio |
| ADRs POSTH-001/002/003 existen | Obligatorio |
| ZIP fuente limpio de runtime artifacts | Obligatorio |
| `project-state validate` PASS | Obligatorio |
| `test-contracts validate` PASS | Obligatorio |
| `quality-gate hardening` PASS | Obligatorio |
| Remote execution sigue disabled | Obligatorio |
| Connector write sigue denied-by-default | Obligatorio |

## 9. Dependencias y no-go gates

### Dependencias P0

```text
POST-H-EVAL-001-G -> POST-H-002
POST-H-EVAL-001-E -> POST-H-003
POST-H-EVAL-001-D -> POST-H-004
POST-H-EVAL-001-C -> POST-H-005
POST-H-005 -> POST-H-006
POST-H-012 -> cualquier capacidad write/sensible posterior
POST-H-009 + POST-H-014 -> POST-H-024
POST-H-002..POST-H-017 + POST-H-024 -> POST-H-025
```

### No-go gates

```text
BLOCK si remote execution se habilita antes de POST-H-021/022/023 y sus controles.
BLOCK si connector write se habilita antes de sandbox/replay/approval/rollback.
BLOCK si plugin execution se habilita antes de sandbox formal.
BLOCK si POST-H-002 se construye sin usar las fuentes POST-H-EVAL-001.
BLOCK si se declaran claims enterprise/compliance certificada.
BLOCK si se distribuyen ZIPs con runtime artifacts.
BLOCK si se declara production-ready completo sin POST-H-025 PASS.
```

## 10. Comandos de verificación

### Verificación focal de este micro-sprint

```powershell
$env:PYTHONPATH="src"
python -m pytest tests	est_post_h_eval_001_f_prioritized_roadmap.py -q
python -m devpilot_core validate-frontmatter docsacklogs\post_h_prioritized_roadmap.md --json
python -m devpilot_core validate-frontmatter docsdr\ADR-POSTH-001-local-first-before-remote.md --json
python -m devpilot_core validate-frontmatter docsdr\ADR-POSTH-002-test-contract-registry-2.md --json
python -m devpilot_core validate-frontmatter docsdr\ADR-POSTH-003-cli-modularization.md --json
```

### Verificación de no regresión recomendada

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core project-state validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core industrial-readiness check --json
python -m pytest tests	est_post_h_eval_001_b_assessment.py tests	est_post_h_eval_001_c_architecture_map.py tests	est_post_h_eval_001_d_security_risk_register.py tests	est_post_h_eval_001_e_test_cost_assessment.py tests	est_post_h_eval_001_f_prioritized_roadmap.py -q
python -m pytest tests	est_project_global_state.py tests	est_test_contract_registry.py tests	est_test_impact.py -q
```

## 11. Criterios PASS

```text
PASS si el roadmap contiene prioridades P0/P1/P2/P3.
PASS si cada hito tiene objetivo claro.
PASS si se explicitan dependencias.
PASS si POST-H-002 queda refinado con fuentes de evaluación obligatorias.
PASS si remote/enterprise queda pospuesto hasta condiciones explícitas.
PASS si existen ADR-POSTH-001, ADR-POSTH-002 y ADR-POSTH-003.
PASS si no se agregan features runtime ni APIs externas.
PASS si README, runbook, backlog y manifest quedan sincronizados.
PASS si el roadmap incluye onboarding operativo y un gate explícito de declaración production-ready-local.
```

## 12. Criterios BLOCK

```text
BLOCK si el roadmap prioriza features sobre seguridad/testing/arquitectura.
BLOCK si remote execution queda antes del hardening local.
BLOCK si no hay decisiones arquitectónicas explícitas.
BLOCK si POST-H-002 puede iniciarse sin cierre de POST-H-EVAL-001-G.
BLOCK si el roadmap permite connectors write o plugin execution sin sandbox.
BLOCK si se sobredeclara DevPilot como enterprise production-ready.
BLOCK si se intenta declarar DevPilot production-ready-local sin evidencia consolidada, playbook de operador y gate POST-H-025.
```

## 13. Riesgos y limitaciones

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Roadmap demasiado amplio para ejecución lineal | Media | Mantener oleadas y criterios de entrada; commitear por hito |
| Dashboard superficial en POST-H-002 | Alta | Obligar consumo de matrices y documentos POST-H-EVAL-001 |
| CLI monolítico frena mantenibilidad | Alta | Ejecutar POST-H-005/006 antes de ampliar comandos complejos |
| Registry v2 subestimado | Alta | Tratar POST-H-003 como P0, no como mejora opcional |
| Remote/enterprise presionado por roadmap aspiracional | Crítica | Mantener P3 como diseño, con no-go gates explícitos |
| Drift documental | Media-alta | Usar pruebas documentales y manifest G para cierre |
| Onboarding no operacionalizado | Alta | Convertir informe de onboarding y guía de operador en POST-H-024 con plantillas, checklist y proyecto piloto local |
| Declaración productiva prematura | Alta | Exigir POST-H-025 como gate final con evidencia y no-go gates cerrados |

## 14. Backlogs ejecutables derivados del roadmap definitivo

Estos son los backlogs ejecutables que deben elaborarse para continuar el desarrollo. Cada backlog debe tener objetivo, alcance, entregables, criterios PASS/BLOCK, comandos de validación, riesgos, no-go gates y entregable verificable.

| Orden | Backlog ejecutable a crear | Hito cubierto | Prioridad | Propósito |
|---:|---|---|---|---|
| 1 | `docs/backlogs/POST-H-002_maturity_dashboard_local.md` | POST-H-002 | P0 | Dashboard local read-only sobre madurez, riesgos, tests, gates y roadmap. |
| 2 | `docs/backlogs/POST-H-003_test_contract_registry_2.md` | POST-H-003 | P0 | Evolución del Test Contract Registry por dominio, criticidad, riesgo, costo e impacto. |
| 3 | `docs/backlogs/POST-H-004_policy_miasi_semantic_validator.md` | POST-H-004 | P0 | Validator semántico agent/tool/policy/approval/RBAC/observability/evals. |
| 4 | `docs/backlogs/POST-H-005_architecture_map_executable.md` | POST-H-005 | P0 | Mapa ejecutable de arquitectura, ownership, dependencias y hotspots. |
| 5 | `docs/backlogs/POST-H-006_cli_command_registry.md` | POST-H-006 | P1 | Modularización progresiva del CLI. |
| 6 | `docs/backlogs/POST-H-007_application_service_boundary.md` | POST-H-007 | P1 | Endurecimiento de frontera CLI/API/UI con ApplicationService y DTOs. |
| 7 | `docs/backlogs/POST-H-008_runtime_state_lifecycle.md` | POST-H-008 | P1 | Retención, limpieza, export y exclusión de runtime state. |
| 8 | `docs/backlogs/POST-H-009_documentation_governance.md` | POST-H-009 | P1 | Fuentes canónicas, owners, sincronización y pruebas documentales robustas. |
| 9 | `docs/backlogs/POST-H-010_observability_retention.md` | POST-H-010 | P1 | Retención, redacción y consulta local de trazas/eventos. |
| 10 | `docs/backlogs/POST-H-011_rag_groundedness_evals.md` | POST-H-011 | P1 | Evaluaciones de groundedness del RAG local. |
| 11 | `docs/backlogs/POST-H-012_approval_rbac_hardening.md` | POST-H-012 | P1 | Approval/RBAC por acciones sensibles, actor binding y scopes. |
| 12 | `docs/backlogs/POST-H-013_audit_pack_integrity.md` | POST-H-013 | P1 | Integridad local opcional de audit packs y disclaimers. |
| 13 | `docs/backlogs/POST-H-014_ui_api_industrial_shell.md` | POST-H-014 | P1 | Shell local seguro UI/API read-only/dry-run. |
| 14 | `docs/backlogs/POST-H-015_local_operator_dashboard.md` | POST-H-015 | P1 | Dashboard operativo con gates, riesgos, traces y roadmap. |
| 15 | `docs/backlogs/POST-H-016_workspace_portfolio_hardening.md` | POST-H-016 | P2 | Hardening multiworkspace y aislamiento de estado. |
| 16 | `docs/backlogs/POST-H-017_release_reproducibility_pack.md` | POST-H-017 | P2 | Empaquetado reproducible e higiene de release. |
| 17 | `docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md` | POST-H-024 | P1 | Playbook de operador, plantillas y bootstrap de proyectos nuevos. |
| 18 | `docs/backlogs/POST-H-018_connector_sandbox.md` | POST-H-018 | P2 | Sandbox/replay de conectores; writes siguen deshabilitados. |
| 19 | `docs/backlogs/POST-H-019_plugin_sandbox_design.md` | POST-H-019 | P2 | Diseño de sandbox de plugins sin ejecución arbitraria. |
| 20 | `docs/backlogs/POST-H-020_compliance_mapping_packs.md` | POST-H-020 | P2 | Packs compliance-like ampliados sin claim certificable. |
| 21 | `docs/backlogs/POST-H-021_remote_runner_adr2.md` | POST-H-021 | P3 | ADR-2 de remote runner sin ejecución activa. |
| 22 | `docs/backlogs/POST-H-022_enterprise_deployment_threat_model.md` | POST-H-022 | P3 | Threat model enterprise antes de cualquier control plane. |
| 23 | `docs/backlogs/POST-H-023_secure_transport_design.md` | POST-H-023 | P3 | Diseño de transporte seguro sin habilitar red. |
| 24 | `docs/backlogs/POST-H-025_production_ready_declaration_gate.md` | POST-H-025 | P0 | Gate final para declarar `production-ready-local` o bloquear con gaps. |

## 15. Entregables de F

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-002-test-contract-registry-2.md
docs/adr/ADR-POSTH-003-cli-modularization.md
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
tests/test_post_h_eval_001_f_prioritized_roadmap.py
```

## 16. Estado de cierre del micro-sprint F

`POST-H-EVAL-001-F` queda clasificado como `implemented` a nivel documental/metadata y `PASS focal` cuando pasan las pruebas documentales y los gates de no regresión definidos. El hito completo `POST-H-EVAL-001` no queda cerrado hasta ejecutar `POST-H-EVAL-001-G` con manifest final y prueba documental global.
