---
doc_id: "DEVPL-GSDLC-13-C-01-PRECODE-STRUCTURE-DERIVATION-CORRECTIVE-PROJECTION"
title: "DEVPL-GSDLC-13-C-01 — Corrective Pre-code structure + material deterministic derivation"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-24"
approval: "approved-by-owner-direction-2026-09-24"
active_authority: "repo441/d249737d8e76c713747e4ba5cf1d9258f7b21537"
proposed_successor: "repo442"
implementation_authorized: true
implementation_shape: "single-bounded-micro-sprint/single-entry"
full_regression: "0"
---

# Corrective aprobado — DEVPL-GSDLC-13-C-01

## 1. Decisión

Se aprueba un único corrective bounded para restaurar el contrato real:

`greenfield neutral bootstrap → Product Vision → Scope → Requirements`

La implementación se autoriza en **un solo micro-sprint y una sola entrada** porque los dos S1 descubiertos pertenecen al mismo vertical slice y comparten la misma frontera contractual B-02 → C-01:

1. el bootstrap Greenfield no materializa los namespaces documentales que Pre-code exige;
2. la derivación Vision → Scope → Requirements registra upstream provenance, pero no consume materialmente el upstream al producir el siguiente artefacto.

El delta adicional de UX es pequeño, está directamente ligado al mismo critical path y no requiere una evolución separada.

No se autoriza Full Regression. No se autoriza Agent/RAG real dentro de este corrective.

## 2. Objetivo

Restaurar el recorrido C-01 sin project writes externos, sin oracle de ChatGPT, sin API externa obligatoria y sin debilitar PathGuard, symlink protection, RBAC, CSRF ni approval boundaries.

El corrective debe dejar una base determinística reproducible que posteriormente pueda coexistir con rutas agentic reales sin modificar el artifact lifecycle gobernado.

## 3. Autoridades y compatibilidad histórica

### 3.1 Baseline de entrada

- repo autoritativo: `repo441`;
- commit: `d249737d8e76c713747e4ba5cf1d9258f7b21537`;
- Run Card: `13-C-01`;
- retest bloqueado: `13-C-01-retest-01-00`;
- punto de reanudación posterior al corrective: Product Vision.

### 3.2 Bootstrap catalogs

El catálogo histórico B-02 `bootstrap_planning_catalog_gsdlc13_v2.json` se conserva sin reinterpretar su contrato congelado.

Se introduce `BootstrapPlanningCatalog v3` como autoridad actual para nuevos Greenfield. El cambio de versión evita extender silenciosamente un contrato histórico.

### 3.3 Generador determinístico

No se reutiliza `deterministic-context-template-v1` con semántica nueva.

El corrective introduce:

`deterministic-context-template-v2`

para expresar que Scope y Requirements ahora dependen materialmente de los artefactos FROZEN upstream y que los inputs son canonizados de forma explícita.

## 4. Corrective B1 — Governed document parent contract

### 4.1 Future bootstrap

`greenfield-neutral-shell` debe materializar como estructura neutral, sin contenido:

- `docs/00_product/`;
- `docs/01_requirements/`;
- `docs/02_architecture/`;
- `docs/02_architecture/adrs/`;
- `docs/03_security/`;
- `docs/04_quality/`.

Debe mantener:

- cero artefactos preconstruidos;
- stack `undecided/deferred`;
- cero `.venv`;
- cero dependency jobs;
- cero API externa obligatoria;
- cero selección tecnológica implícita.

Las carpetas son namespaces documentales gobernados, no decisiones de arquitectura.

### 4.2 Reconciliación de Greenfield ya existente

DevPilot debe proporcionar un reconciliador bounded e idempotente que:

1. resuelva el workspace exclusivamente desde runtime authority validada;
2. use PathGuard para comprobar que cada parent permanece bajo el workspace;
3. rechace symlinks, file collisions y path escape;
4. cree exclusivamente los directorios faltantes de la allowlist contractual;
5. no cree `.md`, `.gitkeep` ni contenido funcional;
6. escriba el receipt en platform `outputs`, fuera del project source;
7. reporte `operator_project_writes=0`;
8. reporte `project_content_files_written=0`;
9. reporte `directories_created=[...]`;
10. reporte `network_used=false` y `external_api_used=false`;
11. preserve Git clean antes/después de la reconciliación estructural.

Queda prohibido usar `mkdir` manual del operador para desbloquear C-01.

## 5. Corrective C1 — Integración real B-02 → C-01

El fixture principal C-01 no puede precrear los parents gobernados.

Debe existir un integration test que ejecute la composición real:

1. intake Greenfield;
2. `greenfield-neutral-shell` vigente;
3. activación de runtime context;
4. apertura de Pre-code;
5. generación Product Vision con `DEVPL_MOCK`;
6. DRAFT runtime-only;
7. cero source write antes de apply.

### 5.1 Invariante de parents directos

Debe demostrarse:

`parents(pre_code_catalog) ⊆ directories(greenfield-neutral-shell-v3)`

### 5.2 Invariante de namespaces estructurales

Además de los parents directos, debe demostrarse:

`required_structural_namespaces ⊆ directories(greenfield-neutral-shell-v3)`

incluyendo explícitamente:

`docs/02_architecture/adrs/`

Esto evita que un directorio requerido por C-02 quede fuera solo porque no sea parent directo de un artifact C-01.

## 6. Corrective D1 — Derivación material y realmente secuencial

### 6.1 Product Vision

Inputs mínimos canónicos:

- `business_need`;
- project identity;
- `project_constraints`;
- `model_policy`;
- versión del generador.

### 6.2 Scope

Inputs mínimos canónicos:

- Product Vision FROZEN exacta;
- `business_need`;
- project constraints;
- model policy;
- versión del generador.

Scope debe extraer y usar materialmente capacidades/secciones gobernadas de Vision. No es suficiente almacenar el hash de Vision en provenance.

### 6.3 Requirements

Inputs mínimos canónicos:

- Scope FROZEN exacto;
- Product Vision FROZEN como contexto trazable;
- `business_need`;
- constraints/model policy;
- versión del generador.

Requirements debe generar requisitos desde capacidades MVP del Scope. No es suficiente registrar el hash de Scope.

### 6.4 Lectura de Project Context

El parser bounded de `.devpilot/project.yaml` debe leer, sin dependencia YAML externa:

- campos escalares existentes;
- `model_policy`;
- `project_constraints`;
- `stack` cuando corresponda.

Se mantiene como parser acotado del formato escrito por DevPilot; no se convierte en parser YAML general.

## 7. Canonical input y hashing

La entrada determinística debe tener contrato explícito.

### 7.1 Texto

Para hashing lógico:

- encoding: UTF-8;
- `CRLF` y `CR` se normalizan a `LF`;
- la comparación semántica nunca bloquea por representación física LF/CRLF.

### 7.2 Estructura

El canonical input se representa como objeto estable que incluye como mínimo:

- derivation schema/version;
- generator version;
- stage id;
- workspace id;
- project identity;
- business need;
- constraints;
- model policy;
- upstream artifact refs/hashes/contenido canónico requerido.

La serialización debe usar orden de claves y separadores estables antes de calcular:

`canonical_input_sha256`

### 7.3 Provenance obligatoria

Persistir:

- generator version;
- derivation schema;
- source refs;
- source canonical hashes;
- `canonical_input_sha256`;
- generated canonical content hash;
- network/API/cost;
- `human_review_required=true`.

El timestamp operativo pertenece a runtime/provenance y no debe introducir variación gratuita en el contenido generado. Si el documento necesita una fecha contractual, debe derivarse de una fuente estable del workspace/bootstrap, no del reloj del turno.

## 8. Contrato de determinismo y materialidad

Tests obligatorios:

- mismos inputs canónicos + misma versión → mismo contenido/hash;
- Vision materialmente diferente → Scope materialmente diferente;
- Scope materialmente diferente → Requirements materialmente diferentes;
- Vision no FROZEN → Scope BLOCK;
- Scope no FROZEN → Requirements BLOCK.

No es suficiente cambiar únicamente un hash o una línea de provenance para declarar materialidad.

## 9. Corrective UX incluido

Este delta es S2/S3 pero pertenece al mismo critical path.

### 9.1 Agrupación

La superficie Pre-code se organiza en:

1. **Cómo crear el DRAFT**
   - DevPilot local;
   - Manual/Paste;
   - Import.
2. **Herramientas auxiliares**
   - Abrir Documentos / preparar edición externa;
   - Validate current step, contextualizado respecto al gate canónico.
3. **IA avanzada**
   - Agent;
   - RAG.

Copy canónico:

`Las tarjetas muestran rutas y acciones disponibles; el selector Modo de autoría controla cómo se produce el DRAFT de esta etapa.`

### 9.2 Baseline recomendado

`DevPilot local` es la ruta recomendada para acceptance C-01.

### 9.3 Import

Se resuelve la contradicción a favor de la autoridad Artifact Lifecycle:

`Product Vision IMPORT = allowed`

porque `import_allowed=true` ya estaba establecido en Artifact Lifecycle.

### 9.4 File picker

El selector de archivo se muestra únicamente cuando el modo activo es `IMPORT`.

### 9.5 External editor

CTA:

`Abrir Documentos / preparar edición externa`

Debe aclarar que DevPilot no lanza ni controla el editor y que al regresar se exige reconciliation.

### 9.6 Validate

`Validar y preparar diff` permanece gate canónico del artefacto. La tarjeta typed-operation no puede aparecer como una segunda validación equivalente.

## 10. Agent/RAG fuera de alcance

No habilitar `AGENT` ni `RAG` reales en este corrective.

El hallazgo `CAP-13C01-AI-001` ya existe en `DEVPL_UX_P1_FINDINGS_LEDGER_13_B_v1_9_0_ES.md` y no debe duplicarse.

Se crea una proyección independiente para la arquitectura multi-modelo futura. `DEVPL_MOCK` permanece ruta determinística, sin costo, útil para acceptance, tests y fallback.

## 11. 403 standalone

El endpoint standalone `/guided-sdlc/step-actions` permanece fuera del alcance salvo que bloquee el critical path C-01.

Este corrective solo debe verificar que Pre-code puede cargar y completar su recorrido sin depender de ese endpoint standalone. No se abre un correctivo lateral S2 durante C-01.

## 12. Pruebas y forward audit

Antes de candidate:

- B-02 real → Product Vision DEVPL_MOCK PASS;
- Vision DRAFT runtime-only y sin source write;
- Scope/Requirements encadenados materialmente;
- parents de las siete etapas disponibles;
- `docs/02_architecture/adrs/` disponible;
- parser de constraints/model policy probado;
- canonical hashing probado;
- Product Vision Import coherente;
- MIASI continúa DEFERRED en C-01;
- no `.venv`/stack;
- no stale RBAC session;
- Pre-code critical path no bloqueado por 403;
- UI smoke/build PASS;
- focal/affected tests PASS;
- Full Regression = 0.

## 13. Operador Windows

Debe ser pequeño y resume-aware:

1. preflight exacto contra repo441 + Git clean;
2. clasificar cada archivo del source delta por hash canónico: `OLD`, `NEW`, `ABSENT_EXPECTED` o `UNKNOWN`;
3. BLOCK solo ante `UNKNOWN`, nunca por CRLF/LF físico;
4. hacer backup runtime antes de reemplazar archivos existentes;
5. aplicar source delta de forma atómica;
6. ejecutar pruebas focales/affected;
7. ejecutar Vite build/smoke sin instalar dependencias ni acceder a red;
8. verificar invariantes estructurales;
9. producir evidence receipt bajo `outputs/`;
10. no modificar `.git`, no commit automático, no acciones destructivas;
11. empaquetado/promoción a repo442 se realiza después de PASS.

## 14. Criterios PASS

PASS requiere conjuntamente:

- estructura v3 válida;
- reconciliación idempotente y segura;
- integration test B-02 → C-01 sin fixture artificial;
- Product Vision DRAFT funcional;
- material sequential derivation;
- canonical input reproducible;
- upstream FROZEN gate fail-closed y source hash exacto contra `approved_sha256`;
- UX contractual coherente;
- documentation/ADR reconciliados;
- pruebas focales/affected + UI build/smoke PASS;
- network/API = 0;
- Full Regression = 0.

## 15. Criterios BLOCK

BLOCK si ocurre cualquiera de los siguientes:

- requiere `mkdir` manual;
- requiere copy/paste desde ChatGPT para cumplir C-01;
- requiere API externa;
- un operator escribe contenido funcional en el project source;
- los tests vuelven a preparar artificialmente parents;
- Scope/Requirements solo registran upstream hashes sin consumir contenido;
- un upstream FROZEN deriva aunque el archivo físico ya no coincida con su `approved_sha256`;
- symlink/path escape puede eludir el workspace boundary;
- Git del Greenfield cambia por reconciliación estructural;
- aparece drift documental entre bootstrap, Pre-code y Artifact Lifecycle;
- pruebas focales/affected o UI build fallan por regresión del delta.

## 16. Riesgos residuales

- la derivación determinística v2 es un baseline de ingeniería, no sustituto de razonamiento agentic de alta calidad;
- el parser YAML sigue deliberadamente bounded y solo soporta el contrato escrito por DevPilot;
- futuras modificaciones de templates requieren versionar el generador para preservar reproducibilidad;
- Agent/RAG, groundedness y provider-specific behavior quedan para evolución posterior.

## 17. Comandos de verificación

Validación focal del corrective (PowerShell, una sola línea):

```powershell
Set-Location 'D:\Projects\DevPilot_Local'; & '.\.venv\Scripts\python.exe' -m pytest -q -rs tests/test_workspace_manager.py tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py tests/test_devpl_gsdlc_13_c_01_pre_code_derived_authoring_corrective.py tests/test_devpl_gsdlc_05_e_pre_code_wizard.py
```

Build UI requerido en Windows, sin instalar dependencias durante el corrective:

```powershell
Set-Location 'D:\Projects\DevPilot_Local'; npm --prefix ui/web run build
```

Full Regression queda expresamente fuera de esta validación intermedia (`0`).

## 18. Gate de implementación

`APPROVED / IMPLEMENTATION AUTHORIZED`.

Se autoriza implementación en **un único micro-sprint bounded y una única entrada**, con source authority repo441 y candidato previsto repo442.
