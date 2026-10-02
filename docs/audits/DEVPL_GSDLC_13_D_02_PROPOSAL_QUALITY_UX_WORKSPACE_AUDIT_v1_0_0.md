---
doc_id: "DEVPL-GSDLC-13-D-02-PROPOSAL-QUALITY-UX-WORKSPACE-AUDIT"
title: "DEVPL-GSDLC-13-D-02 — Proposal quality, UX and Pilot A workspace audit"
status: "ACTIVE-CORRECTIVE"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_for_owner_validation"
checkpoint_id: "13-D-02"
run_id: "RUN_02"
source_authority: "repo456/38452b16604535d85e9263530298423472473f51"
full_regression_runs: 0
---

# 1. Adjudicación

`RUN_02` se detuvo correctamente **antes de ACCEPT**. La propuesta v1 es suficientemente visible para auditarla, pero **no es suficientemente coherente para materializarla como Draft Set**.

Estado:

- Story `story-rf-001`: `IN_PROGRESS`;
- proposal v1: `PROPOSED`, no aceptada;
- drafts creados: `0`;
- source mutations: `0`;
- Full Regression: `0`.

## 2. Hallazgo funcional principal

### `FUNC-13D02-IMPLEMENTATION-QUALITY-002` — proposal v1 no materializa adecuadamente ARC-C02/C03/C04

Severidad: `S1 / ACTIVE-CORRECTIVE`.

La proposal v1 crea:

- `application/story_rf_001.py`;
- `infrastructure/sqlite_story_rf_001_repository.py`;
- `tests/test_story_rf_001.py`.

Problemas:

1. Architecture asigna RF-001 a `ARC-C02 / ARC-C03 / ARC-C04`, pero no existe módulo/domain artifact explícito para ARC-C03.
2. `StoryRepository` y tabla `story_rf_001_records` acoplan la persistencia al identificador de la Story. RF-002/RF-003/RF-004 necesitan operar sobre el mismo concepto Product; ese storage no es un baseline reusable de dominio.
3. El payload genérico `Mapping[str, Any]` se guarda como JSON story-specific; cumple un smoke de persistencia pero no expresa el aggregate/product boundary aprobado.
4. El test usa `{"name": "sample"}` aunque `name` no está definido por Requirements; la proposal no debe inventar business fields.
5. El docstring del application artifact incorpora un requirement recortado a 500 caracteres y queda truncado en mitad de palabra, degradando revisión humana.
6. Los docstrings de infrastructure/tests son demasiado mínimos para explicar propósito, responsabilidades, boundaries y trazabilidad.

## 3. Corrective técnico

El generator v2 produce un slice product-oriented y reusable:

```text
src/inventory_sales_local_greenfield/
├── domain/
│   └── product.py
├── application/
│   └── create_product.py
└── infrastructure/
    └── sqlite_product_repository.py

tests/
└── test_create_product.py
```

Reglas:

- `Product` + `ProductRepository` materializan ARC-C03 y el port ARC-C04;
- `CreateProductService` materializa ARC-C02;
- SQLite usa tabla reusable `products`, no `story_rf_001_records`;
- no se inventan `name`, SKU, price, stock o minimum_stock;
- atributos de producto permanecen opacos hasta que un Requirement gobernado especialice el data contract;
- todos los Python artifacts deben tener module docstring con `Purpose`, `Responsibilities`, `Boundaries`, `Traceability`;
- internal quality gate debe pasar antes de habilitar ACCEPT;
- proposal v1 queda obsoleta y no puede aceptarse después del corrective.

## 4. UX

### `UX-P1-13D02-004` — proposal panel duplica Source tree/editor

Severidad: `S2`, absorbido por el corrective S1.

La captura `02_implementation_proposal_review.png` muestra una sección completa adicional que expande los tres archivos inline y luego vuelve a presentar `Source tree` + `Editor de draft`. Aunque revisable, obliga a scroll excesivo y duplica el modelo mental.

Diseño objetivo:

- eliminar la sección separada;
- integrar botones/status de proposal en `Source tree`;
- mostrar archivos virtuales `PROPOSAL` en árbol de filesystem;
- click en un nodo `PROPOSAL` → contenido read-only en `Editor de draft`;
- después de ACCEPT, nodos cambian a `DRAFT` y editor se vuelve editable;
- provenance/quality/safety detrás de disclosure expandible;
- source real después de apply aparece como `SOURCE` en el mismo árbol.

## 5. Docstrings

### `DOC-13D02-DOCSTRING-005`

Todo artifact Python generado por el provider debe incluir un module docstring que permita a un Owner/reviewer comprender el archivo sin inferirlo desde el código.

Contrato mínimo obligatorio:

- `Purpose:`;
- `Responsibilities:`;
- `Boundaries:`;
- `Traceability:`.

El quality gate bloquea ACCEPT si falta alguno.

# 6. Auditoría de `inventory-sales-local-greenfield`

## 6.1 Contenido válido

Se verificó presencia y coherencia básica de:

- Product Vision;
- MVP Scope;
- Requirements RF-001..RF-011;
- Architecture con ARC-C01..ARC-C05;
- ADR-001..ADR-004 standalone;
- Security Threat Model;
- Test Strategy TEST-001..TEST-011;
- Traceability;
- Roadmap/Backlog/Sprint FROZEN;
- StoryExecution `story-rf-001 IN_PROGRESS`;
- implementation proposal store runtime-only.

La asignación RF-001 → `ARC-C02/ARC-C03/ARC-C04`, `SEC-001/SEC-002` y `TEST-001` es consistente con la proposal v2.

## 6.2 Gaps carry-forward

### `META-13D02-001` — `.devpilot/project.yaml` conserva stack undecided

Architecture/ADR-003 ya aprobó `react-ts-fastapi-sqlite`, pero `project.yaml` mantiene `technology_decision_status=deferred-to-architecture` y stack `undecided`.

Clasificación: `S2 / PROJECT-METADATA-PROJECTION`.

No mutar el archivo manualmente durante D02. Architecture FROZEN sigue siendo la authority técnica. Debe existir reconciliation/versioned projection en un workflow posterior.

### `DOC-13D02-002` — frontmatter de documentos FROZEN conserva `status: draft`

Vision/Scope/Requirements/Architecture/Security/Test Strategy/Traceability físicos conservan metadata `draft` mientras runtime authority los trata como FROZEN.

Clasificación: `S2 / DOCUMENT-LIFECYCLE-METADATA`, carry-forward histórico.

No reescribir documentos aprobados in-place solo para corregir metadata.

### `GIT-13D02-003` — baseline FROZEN no está versionado todavía en Git del proyecto

`git ls-tree HEAD` contiene únicamente bootstrap/standards; `docs/00_product..04_quality` y `outputs/**` aparecen untracked.

Clasificación: `FORWARD-RISK / RECHECK-D04`.

D04 debe demostrar que el commit gobernado no mezcla runtime stores accidentalmente y que existe una estrategia explícita para versionar/publish el baseline documental durable.

### `HYGIENE-13D02-004` — runtime outputs no están cubiertos por `.gitignore`

`outputs/story_execution/**` y `outputs/story_implementation/**` son runtime authority/evidence, pero `.gitignore` actual no excluye `outputs/`.

Clasificación: `FORWARD-RISK / GIT-HYGIENE`.

No modificar `.gitignore` como side-effect de RF-001. D04 debe proteger exact staging y una evolución posterior debe clasificar qué outputs son runtime-only vs durable planning artifacts.

### `ARCH-13D02-005` — Technical Scaffold aún no está materializado

Architecture aprobó React/TypeScript + FastAPI/Python + SQLite, pero el workspace no contiene manifests/dependency lock/scaffold técnico. El current Story no requiere ARC-C01, por lo que no es necesario inventar frontend/FastAPI files para RF-001. Sin embargo, antes de release local debe existir un workflow gobernado para materializar packaging/dependencies/runtime entrypoints.

Clasificación: `S2 / FORWARD-HARDENING`.

# 7. PASS/BLOCK

La proposal v1 no debe aceptarse.

Después del corrective, RUN_02 puede continuar sobre la misma Story y mismo estado si:

- proposal v2 model id es `deterministic-story-implementation-template-v2`;
- quality gate = PASS;
- árbol virtual contiene domain/application/infrastructure/test;
- cada archivo es revisable desde Source tree → Editor;
- docstring contract PASS para 4/4;
- source/draft mutations continúan en cero antes de ACCEPT.

BLOCK si cualquiera de esos invariants falla.
