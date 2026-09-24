---
doc_id: "SPRINT-DEVPL-GSDLC-13-C-01-PRECODE-STRUCTURE-DERIVATION-CORRECTIVE"
title: "Sprint bounded — 13-C-01 Pre-code structure + material deterministic derivation"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-24"
approval: "approved-by-owner-direction-2026-09-24"
source_authority: "repo441/d249737d8e76c713747e4ba5cf1d9258f7b21537"
target_candidate: "repo442"
full_regression: "0"
---

# Sprint bounded — DEVPL-GSDLC-13-C-01

## 1. Objetivo

Cerrar en una sola entrada el defecto de composición B-02 → C-01 y la derivación determinística no material detectados durante `13-C-01-retest-01-00`, manteniendo intactos los boundaries de seguridad y el lifecycle gobernado.

## 2. Justificación de una sola entrada

Los cambios pertenecen al mismo vertical slice y no requieren una nueva capacidad autónoma:

- BootstrapPlanningCatalog v3;
- reconciliación estructural bounded;
- parser Project Context acotado;
- generator `deterministic-context-template-v2`;
- pruebas contractuales e integración real;
- pequeño delta UX del mismo critical path;
- reconciliación ADR/documentación.

Separarlos produciría estados intermedios inválidos: estructura corregida sin derivación contractual, o derivación corregida sobre un bootstrap que todavía bloquea el DRAFT.

## 3. Fuera de alcance

- Agent/RAG real;
- Ollama/LM Studio integration;
- external provider APIs;
- C-02/C-03/C-04 funcional;
- cambio de stack;
- Full Regression;
- remediación standalone del endpoint `/guided-sdlc/step-actions` si no bloquea Pre-code.

## 4. Source delta autorizado

### 4.1 Workspace/bootstrap

- `.devpilot/workspaces/bootstrap_planning_catalog_gsdlc13_v3.json` — nuevo;
- `docs/schemas/bootstrap_planning_catalog_gsdlc13_v3.schema.json` — nuevo;
- `docs/schemas/schema_catalog.json` — modificar;
- `src/devpilot_core/workspace/environment_discovery.py` — autoridad v3;
- `src/devpilot_core/workspace/manager.py` — parser bounded de nested mappings.

El catálogo v2 histórico permanece intacto.

### 4.2 Pre-code

- `.devpilot/gsdlc/pre_code_wizard_catalog.json` — coherencia Product Vision/IMPORT y versionado;
- `src/devpilot_core/application/pre_code_wizard_service.py` — reconciliador + derivación v2 + canonical hashing;
- `src/devpilot_core/application/services.py` — surface de reconciliación;
- `ui/web/src/api/types.ts` — provenance type;
- `ui/web/src/pages/PreCodeWizardView.ts` — agrupación/copy/visibility UX.

### 4.3 Tests

- `tests/test_workspace_manager.py`;
- `tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py`;
- `tests/test_devpl_gsdlc_13_c_01_pre_code_derived_authoring_corrective.py`.

### 4.4 Ingeniería/documentación

- ADR C-01 actualizado;
- Architecture Document actualizado;
- corrective projection v1.0.1 APPROVED;
- este sprint;
- proyección independiente de multi-model authoring.

## 5. Secuencia de implementación

1. introducir catálogo/schema v3 sin modificar v2;
2. rebind del profile actual a v3;
3. extender parser bounded del Project Context;
4. introducir reconciliación estructural segura;
5. introducir generator v2 y canonical input;
6. hacer Scope/Requirements dependientes materialmente del upstream FROZEN;
7. reconciliar Product Vision Import;
8. ajustar UX Pre-code;
9. actualizar tests para eliminar fixture artificial;
10. actualizar ADR/documentación;
11. ejecutar validación focal/affected;
12. empaquetar candidato y operador Windows.

## 6. Pruebas mínimas obligatorias

- workspace manager/parser;
- B-02 greenfield intake/bootstrap corrective;
- C-01 derived authoring corrective;
- pre-code wizard historical affected tests;
- schema validation v3;
- UI smoke Pre-code;
- Vite build.

No ejecutar Full Regression.

## 7. PASS

PASS solo si:

- tests focales/affected sin FAIL/ERROR;
- catalog/schema v3 válidos;
- v2 histórico intacto;
- B-02 real puede llegar a Product Vision DRAFT;
- reconciliación no escribe contenido de proyecto;
- Git del proyecto no cambia por la reconciliación;
- same input → same hash;
- Vision delta → Scope material delta;
- Scope delta → Requirements material delta;
- upstream no FROZEN → BLOCK;
- upstream FROZEN con source drift respecto de `approved_sha256` → BLOCK;
- UI build/smoke PASS;
- documentation synchronized;
- Full Regression = 0.

## 8. BLOCK

BLOCK ante:

- unknown preimage durante aplicación Windows;
- workspace escape/symlink/collision;
- manual mkdir requerido;
- external API requerida;
- regresión de tests afectados;
- cambio semántico no versionado de generador o bootstrap catalog;
- drift entre Artifact Lifecycle y Pre-code;
- source write antes de apply.

## 9. Riesgos

- el baseline determinístico no cubre razonamiento agentic profundo;
- el parser YAML es intencionalmente acotado;
- la calidad semántica del template v2 requiere evolución futura y evaluación contra casos reales.

## 10. Comandos de verificación

Suite de cierre focal (PowerShell, una sola línea):

```powershell
Set-Location 'D:\Projects\DevPilot_Local'; & '.\.venv\Scripts\python.exe' -m pytest -q -rs tests/test_workspace_manager.py tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py tests/test_devpl_gsdlc_13_b_03_runtime_project_context_corrective.py tests/test_devpl_gsdlc_13_c_01_pre_code_derived_authoring_corrective.py tests/test_devpl_gsdlc_05_e_pre_code_wizard.py tests/test_devpl_gsdlc_02_b_api_auth.py tests/test_devpl_gsdlc_02_c_api_rbac.py tests/test_devpl_gsdlc_02_c_server_rbac.py tests/test_devpl_gsdlc_05_c_miasi_applicability.py tests/test_post_h_028_local_auth_cors_hardening.py
```

UI smokes + build:

```powershell
Set-Location 'D:\Projects\DevPilot_Local'; npm --prefix ui/web run test; npm --prefix ui/web run test:step-action-advisor; npm --prefix ui/web run test:miasi-applicability; npm --prefix ui/web run test:ux-p0-c; npm --prefix ui/web run build
```

No ejecutar Full Regression en este micro-sprint.

## 11. Cierre

El cierre de este sprint bounded autoriza únicamente el **retest de 13-C-01 desde Product Vision**. No autoriza C-02 hasta que la Run Card C-01 complete sus propios criterios PASS.
