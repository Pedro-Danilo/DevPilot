---
doc_id: "DEVPL-GSDLC-00"
title: "DEVPL-GSDLC-00 — Program activation, canonical rebaseline and pilot pause"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-13"
approval: "approved_by_owner"
approved_by: "Ordóñez"
approved_at: "2026-08-13"
approval_decision: "APPROVE"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
source_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
source_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-00"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
---

# DEVPL-GSDLC-00 — Program activation, canonical rebaseline and pilot pause

## 1. Objetivo

Convertir la decisión de producto en fuentes de verdad canónicas antes de introducir runtime nuevo, pausar formalmente POST-H-EVAL-002 en la entrada de 02-B y producir un baseline sucesor gobernado de repo341.

## 2. Invariante de producto que esta ola debe demostrar

> Después del cierre de esta ola existe una única narrativa canónica: DevPilot evoluciona a Guided SDLC, el piloto queda PAUSED en 02-B, y los contratos históricos no pueden congelar repo341 ni las nueve rutas UOC como límites futuros.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- repo341 CLOSED/PASS
- owner approval de roadmap/backlogs DEVPL-GSDLC v1.1.0

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- evolución de Product Vision, Requirements, Architecture, Security, Test Strategy y Traceability
- ADRs de Guided SDLC, WorkspaceEngineeringState, local operator auth boundary y UI-complete journey
- reconciliación Project State, Source Registry, TCR y roadmap vigente
- decisión administrativa de pausa del piloto

### 4.2 Fuera de alcance

- código funcional Guided SDLC
- habilitación de autenticación, providers o filesystem write nuevos
- modificación del workspace inventory-sales-local

## 5. Superficies y fuentes que probablemente serán afectadas

- docs/00_product/product_vision.md
- docs/01_requirements/requirements_specification.md
- docs/02_architecture/architecture_document.md
- docs/03_security/security_threat_model.md
- docs/04_quality/test_strategy.md
- docs/01_requirements/traceability_matrix.md
- .devpilot/project_state.json
- .devpilot/docs_governance/source_registry.json
- .devpilot/testing/test_contract_registry*.json
- docs/adr/*

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-00-A — Program charter, pilot PAUSE and repo341 freeze

**Objetivo.** Congelar las precondiciones y declarar la pausa como decisión auditable, sin reescribir evidencia histórica.

**Entradas obligatorias**
- repo341 hash/commit verificados
- POST-H-EVAL-002 01-A→01-D y 02-A cerrados
- 02-B aún no ejecutado

**Actividades**
1. crear charter DEVPL-GSDLC con objetivos/no-go/roles
2. registrar repo341 como parent immutable
3. marcar 02-B PAUSED/superseded-for-execution en documentos activos, no en evidencia histórica
4. catalogar artefactos 02-B v1.0.1 como REFERENCE/ORACLE
5. emitir matriz KEEP/EXTEND/REFACTOR/DEPRECATE

**Entregables verificables**
- program_charter.md
- pilot_pause_decision.md
- repo341_parent_manifest.json
- legacy_preservation_matrix.md

**Pruebas / validadores**
- hash/commit verification
- docs-governance focal
- project-state focal

**Evidencia mínima**
- freeze_report.json
- pilot_pause_evidence.md

**Seguridad operacional específica**
- cero mutaciones al workspace piloto
- no borrar ni reempaquetar evidencia previa

**PASS**
- parent identity exacta
- PAUSE explícita y reversible
- S0/S1=0

**BLOCK**
- repo341 no coincide
- 02-B ya fue ejecutado o workspace mutó sin evidencia

**Salida / autorización**
- autoriza GSDLC-00-B y R01-A en paralelo


### GSDLC-00-B — Canonical product and requirements evolution

**Objetivo.** Reescribir la intención de producto y requisitos para que 'wizard de ingeniería' sea contrato verificable, no aspiración.

**Entradas obligatorias**
- GSDLC-00-A PASS
- fuentes canónicas repo341

**Actividades**
1. actualizar visión con journey idea→release
2. agregar requisitos UI-complete, authenticated roles, Project Status y StepActionAdvisor
3. definir requisitos manual/import/agent-assisted
4. definir métricas de cero-PowerShell en normal journey
5. actualizar trazabilidad requirement→future backlog

**Entregables verificables**
- product_vision.md vNext
- requirements_specification.md vNext
- traceability_matrix.md vNext

**Pruebas / validadores**
- frontmatter/schema
- requirements contradiction checks
- traceability coverage

**Evidencia mínima**
- requirements_delta_report.md
- traceability_delta.json

**Seguridad operacional específica**
- no declarar capabilities ya implementadas si aún son planned
- separar local operator auth de enterprise IAM

**PASS**
- todos los nuevos FR/NFR tienen aceptación y backlog owner
- 0 requisitos huérfanos

**BLOCK**
- requisitos contradictorios con no-go sin ADR
- rutas UI críticas sin criterio de aceptación

**Salida / autorización**
- autoriza GSDLC-00-C


### GSDLC-00-C — Architecture/state/auth ADRs and target C4

**Objetivo.** Fijar las decisiones estructurales antes del código.

**Entradas obligatorias**
- 00-B PASS

**Actividades**
1. definir GuidedSDLCService/WorkflowEngine boundary
2. separar PlatformState, WorkspaceEngineeringState y RuntimeState
3. ADR de local authenticated operator sessions sin enterprise tenancy
4. definir ProjectShell y navegación proyecto-céntrica
5. definir StepActionAdvisor como servicio determinístico
6. actualizar C4 context/container/component

**Entregables verificables**
- ADR-GSDLC-001 Guided SDLC
- ADR-GSDLC-002 Workspace state separation
- ADR-GSDLC-003 local operator auth boundary
- ADR-GSDLC-004 UI-complete journey
- C4 target

**Pruebas / validadores**
- architecture lint/manual review
- ApplicationService boundary tests impact analysis

**Evidencia mínima**
- architecture_decision_register.md
- c4_delta.md

**Seguridad operacional específica**
- no shell arbitrario
- auth no habilita remote/public API
- LLM no decide transitions

**PASS**
- ADRs APPROVED/proposed-for-owner según gate
- C4 sin bypass UI→core

**BLOCK**
- arquitectura deja mutaciones directas desde React
- auth se confunde con enterprise IAM

**Salida / autorización**
- autoriza 00-D


### GSDLC-00-D — Security, test, traceability and historical-contract reconciliation

**Objetivo.** Preparar controles y test contracts para que la evolución no reactive falsas regresiones históricas.

**Entradas obligatorias**
- 00-C PASS

**Actividades**
1. actualizar threat model con auth/session/import/dependency/agent/code-write threats
2. definir test strategy por olas y full-regression policy
3. clasificar assertions históricas que congelan repo/rutas/no-go
4. crear contract migration plan
5. registrar nuevos test domains y evidence expectations

**Entregables verificables**
- security_threat_model.md vNext
- test_strategy.md vNext
- historical_contract_migration_plan.json
- TCR delta

**Pruebas / validadores**
- TCR v1/v2 validate
- security focal
- docs governance

**Evidencia mínima**
- historical_contract_sweep.json
- test_impact_baseline.json

**Seguridad operacional específica**
- fail-closed para auth/approval
- no debilitar no-go históricos sin successor ADR

**PASS**
- 0 contratos globales no acotados a hito histórico
- gates de seguridad definidos

**BLOCK**
- un test histórico impide explícitamente nuevos estados futuros sin scope
- threats críticos sin controles/tests

**Salida / autorización**
- autoriza 00-E


### GSDLC-00-E — Windows validation and baseline successor

**Objetivo.** Materializar la reconciliación en Git real y producir el primer baseline DEVPL-GSDLC.

**Entradas obligatorias**
- 00-D PASS
- working tree limpio en rama gobernada

**Actividades**
1. aplicar solo delta documental/contract
2. ejecutar pruebas focales y validators
3. decidir full regression por Test Impact; si se requiere, ejecutarla una sola vez
4. commit/push/ff-only canónico
5. generar ZIP limpio y BASELINE_CURRENT

**Entregables verificables**
- repo successor ZIP
- BASELINE_CURRENT.json
- evidence package
- closure report

**Pruebas / validadores**
- focal suites
- Project State
- Docs Governance
- TCR v1/v2
- full regression si escalado

**Evidencia mínima**
- Windows logs
- Git identity
- ZIP SHA
- closure adjudication

**Seguridad operacional específica**
- backups antes de apply
- artifact hygiene

**PASS**
- CLOSED/PASS
- S0/S1=0
- nuevo baseline autoritativo

**BLOCK**
- working tree dirty inesperado
- contract drift
- regression blocker

**Salida / autorización**
- autoriza GSDLC-01 y continuidad R01


## 7. Alcance transversal específico de esta ola

- La ola es exclusivamente de gobernanza/contratos; no debe colar runtime funcional.
- Toda nueva capacidad futura debe tener owner, status y test domain antes de implementarse.

## 8. Política de contratos históricos específica

- Congelar UOC-000→011 y POST-H-EVAL-002 01/02-A como hechos históricos; actualizar tests para que validen esos campos históricos, no que `current_repo`/route count permanezcan eternamente iguales.
- Revisar especialmente tests de activación POST-H-EVAL-002, UOC final reconciliation, no-go globales y source registry.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

## 9. Seguridad operacional específica

- No activar auth, network, provider API ni source write durante esta ola.
- El threat model puede ampliarse documentalmente sin habilitar capabilities.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- focal docs/contracts
- TCR v1/v2
- Project State
- Docs Governance
- security/schema validators
- full regression solo por decisión Test Impact

Regla de regresión:

- Test Impact y pruebas focales en A→D.
- Browser acceptance en el micro-sprint que introduce/cierra UX.
- Full regression solo si Test Impact lo exige o en el cierre industrial expresamente indicado; no se repite por rutina.

## 11. Evidencia autoritativa esperada

- paquete de evidencia de reconciliación
- matriz de contratos históricos
- baseline successor manifest
- owner approval record

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- fuentes canónicas reconciliadas
- piloto PAUSED de forma explícita
- repo341 preservado como parent
- S0/S1=0
- ninguna feature runtime nueva

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-01 solo tras baseline successor autoritativo; R01 puede comenzar tras 00-A pero no habilita providers.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.
