---
doc_id: "DEVPL-POST-H-EVAL-002-UI-OPERATIONAL-CONSOLE-EVOLUTION"
title: "POST-H-EVAL-002 — UI Operational Console Evolution"
status: "approved"
version: "1.6.0"
owner: "Ordóñez"
updated: "2026-08-06"
approval: "approved_by_owner"
approved_at: "2026-08-04"
program: "POST-H-EVAL-002"
priority: "P0"
implementation_status: "UOC-002-closed/PASS"
current_sprint: "UOC-003"
next_sprint: "UOC-003"
completed_sprints: "UOC-000,UOC-001,UOC-002"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
canonical_baseline_commit: "resolved-by-UOC_001_CANONICAL_INTEGRATION.json"
source_corrective_branch: "fix/post-h-eval-002-ui-first-operational-surfaces"
source_corrective_commit: "84789e428246d732cf308d70aa965dfda291b09e"
source_api_security_branch: "fix/post-h-eval-002-api-token-nonascii-401"
source_api_security_commit: "43254e3e61cdafe65e0ed2d773fe9032b0a81f05"
source_acceptance_schema: "devpilot.post_h_eval_002_02_a.ui_first_corrective_acceptance.v1"
workspace_id: "inventory-sales-local"
workspace_root: "D:\Projects\DevPilot_Workspaces\inventory-sales-local"
local_first: true
ui_first: true
dry_run_default: true
external_api_required: false
preliminary: "false"
uoc_001_accepted_source_commit: "e9fe717eb8eafaca40830c691a7efb7bb956b035"
uoc_002_base_commit: "9cb67b023c6ac909a2b492370632a3955a454e39"
uoc_002_implementation_status: "closed/PASS"
---


# POST-H-EVAL-002 — UI Operational Console Evolution

## 1. Estado y propósito

Este backlog propone la evolución secuencial de DevPilot Local desde una Web UI
principalmente orientada a consulta hacia una **consola operacional gobernada**.
La meta no es insertar una terminal web ni duplicar la CLI; la meta es exponer
las capacidades seguras de DevPilot mediante contratos de aplicación tipados,
políticas, aprobaciones, jobs observables y evidencia reproducible.

La baseline canónica aprobada y sincronizada es:

```text
Rama canónica: eval/post-h-eval-002-02-a-onboarding
Commit:        a986f83a7c2da99a734c88feb80bf5d66cde2e4a
UI corrective: CLOSED/PASS
API-GAP-SEC-001: CLOSED/PASS
Windows/local/origin sync: PASS
S0: 0
S1: 0
```

`UOC-000` queda cerrado/PASS en `a986f83...`. `UOC-001` incorpora una primera
versión read-only del explorador documental; UOC-002 permanece bloqueado hasta
la aceptación Windows/API/UI/browser y la nueva baseline exact-tree.

## 2. Problema que resuelve

La UI aceptada dispone de Dashboard, Reports, Traces, Approval Center y
Configuración. Estas superficies permiten observar estados y algunas acciones
acotadas, pero aún no permiten:

- explorar y leer los documentos fuente del workspace;
- validar un documento desde la misma superficie donde se inspecciona;
- planificar una edición y revisar su diff;
- solicitar aprobación sobre un plan inmutable;
- ejecutar una escritura gobernada con rollback;
- operar Git mediante acciones tipadas;
- iniciar, observar, cancelar y reintentar jobs gobernados;
- cubrir de forma explícita la superficie segura que hoy solo expone la CLI;
- correlacionar acción, política, approval, trace, report, evidencia y commit.

Este gap es especialmente relevante para `POST-H-EVAL-002-02-B`, cuyo trabajo
sustantivo gira alrededor de documentos pre-code que hoy deben consultarse y
administrarse principalmente desde IDE/Git.

## 3. Resultado objetivo

Al cerrar el programa, DevPilot debe ofrecer una consola local en la que un
operador pueda:

1. seleccionar un workspace registrado;
2. explorar documentos y metadatos sin acceso arbitrario al filesystem;
3. ejecutar validaciones determinísticas;
4. navegar trazabilidad y findings;
5. proponer cambios sin escribir;
6. revisar un diff reproducible;
7. solicitar y otorgar una aprobación vinculada al mismo hash del plan;
8. ejecutar, validar y revertir cambios autorizados;
9. preparar operaciones Git seguras;
10. lanzar jobs tipados con progreso, cancelación, timeout y evidencia;
11. operar calidad, pruebas, releases, RAG y agentes dentro de políticas;
12. conocer qué capacidades CLI tienen paridad UI, cuáles siguen como bridge y
    cuáles permanecen prohibidas.

## 4. Modelo arquitectónico obligatorio

```text
UI intent
  → API contract tipado
  → Application Service existente o nuevo boundary de aplicación
  → PolicyEngine / CostGuard / PathGuard
  → dry-run o plan inmutable
  → approval binding, cuando corresponda
  → governed job / executor
  → validación postcondición
  → trace + report + evidence
  → commit o rollback gobernado
```

### 4.1 Regla de paridad

La paridad con la CLI se alcanza reutilizando la misma capa de aplicación. No
se considera paridad válida que la UI ejecute subprocess con una cadena de
comandos arbitraria.

Cada capacidad debe registrarse en una matriz con:

```text
capability_id
CLI command
Application Service
API route
UI surface
read/write
risk class
policy
requires_dry_run
requires_approval
supports_cancel
supports_rollback
evidence contract
parity status
```

Estados permitidos:

```text
UI-NATIVE
UI-READ-ONLY
CLI-BRIDGE-REGISTERED
POLICY-BLOCKED
NOT-APPLICABLE
PLANNED
DEPRECATED
```

## 5. Invariantes de programa

1. Local-first y sin API externa obligatoria.
2. API, UI y workspace solo en roots permitidos.
3. Ninguna terminal web ni shell arbitrario.
4. Ninguna ruta absoluta recibida del navegador se usa directamente.
5. Identificadores documentales y de jobs son opacos.
6. `PathGuard` bloquea traversal, junctions, symlinks fuera de root y ADS.
7. Escrituras deshabilitadas por defecto.
8. Dry-run obligatorio antes de cualquier mutación.
9. Approval vinculado a plan, hash, scope, actor, TTL y policy.
10. Optimistic concurrency antes de escribir.
11. Backup reversible y rollback explícito.
12. Jobs con timeout, límite de reintentos y cancelación.
13. No loops autónomos ilimitados.
14. Tokens, secretos, `.env`, SQLite operativa y HAR bruto no entran en evidencia.
15. Findings S0/S1 bloquean avance.
16. Cada sprint usa worktree/branch/commit y evidencia separados.
17. No se corrigen validators para hacer pasar una implementación inválida.
18. CLI continúa disponible como bridge gobernado hasta lograr paridad real.

## 6. Dependencias y secuencia

```text
API-GAP-SEC-001
  ↓
UOC-000 — Charter, inventario y contratos
  ↓
UOC-001 — Explorador documental read-only
  ↓
UOC-002 — Metadatos, Git y búsqueda
  ↓
UOC-003 — Validación y trazabilidad documental
  ↓
Gate mínimo para ejecución sustantiva de POST-H-EVAL-002-02-B
  ↓
UOC-004 — Plan de edición y diff
  ↓
UOC-005 — Approval, apply y rollback
  ↓
UOC-006 — Operaciones Git gobernadas
  ↓
UOC-007 — Catálogo de paridad CLI y framework de jobs
  ↓
UOC-008 — Job Console y observabilidad operacional
  ↓
UOC-009 — Calidad, pruebas y release desde UI
  ↓
UOC-010 — RAG, agentes, tools y handoffs gobernados
  ↓
UOC-011 — Hardening, accesibilidad, rendimiento y release
```

No se adelanta un sprint si el anterior no tiene manifest y gate de cierre
aceptados.

---

# 7. Sprint UOC-000 — Charter, capability inventory y contratos base

## Objetivo

Congelar alcance, arquitectura y contratos antes de ampliar la UI.

## Entradas

- commit aceptado `84789e4...`;
- cierre PASS de `API-GAP-SEC-001`;
- route registries, policy matrix, TCR v1/v2 y Project State vigentes;
- inventario real de comandos CLI y Application Services;
- capturas aceptadas de las cinco superficies actuales.

## Alcance

1. inventariar comandos y subcomandos CLI;
2. identificar Application Services reutilizables;
3. clasificar capacidades read-only, mutating, sensitive y forbidden;
4. crear el `UI Capability Registry`;
5. definir schemas de documento, plan, approval, job y evidence reference;
6. definir budgets de tamaño, latencia, timeout y paginación;
7. definir ADRs de no-shell, opaque identifiers y job execution;
8. establecer Test Impact por clase de capacidad;
9. diseñar feature flags y kill switches.

## Entregables

```text
docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md
docs/07_interfaces/ui_capability_registry.md
.devpilot/interfaces/ui_capability_registry.json
docs/architecture/adr_ui_no_arbitrary_shell.md
docs/architecture/adr_ui_opaque_resource_identifiers.md
docs/architecture/adr_governed_job_execution.md
docs/audits/uoc_000_capability_inventory_report.md
docs/post_h_eval_002_uoc_000_manifest.json
```

## Pruebas y gates

- registry schema PASS;
- toda ruta UI existente mapeada;
- todo command CLI clasificado;
- cero capacidad mutating sin policy;
- cero capacidad sensible marcada UI-NATIVE sin approval;
- docs governance, Project State y TCR PASS;
- S0=0, S1=0.

## Fuera de alcance

No se añade aún una nueva ruta UI ni se habilita escritura.

## Criterio de cierre

`UOC-001` se autoriza solo cuando la matriz de paridad y los ADRs estén
versionados, validados y aprobados.

---

# 8. Sprint UOC-001 — Workspace Documents: explorador read-only

## Objetivo

Permitir que el operador consulte desde la UI los documentos fuente del
workspace sin acceso arbitrario al filesystem.

## Nueva superficie

```text
/workspace/documents
```

## Alcance funcional

- árbol paginado de carpetas/documentos permitidos;
- selección de workspace activo;
- visor Markdown sanitizado;
- visor JSON estructurado y raw seguro;
- breadcrumbs;
- búsqueda por nombre;
- filtros por extensión y categoría;
- loading, empty, ready, error y BLOCK states;
- deep-link mediante identificador opaco;
- enlaces desde Dashboard hacia documentos requeridos.

## Seguridad

- root resuelto desde registry, no desde input del browser;
- allowlist inicial: `.md`, `.json`, `.yaml`, `.yml`, `.txt`;
- exclusión de `.git`, `.env`, `.venv`, `node_modules`, caches y outputs sensibles;
- límite de tamaño por archivo;
- bloqueo de binarios y encoding no permitido;
- resolución segura de symlink/junction;
- sanitización Markdown/HTML;
- Content Security Policy compatible con la UI local.

## Contratos API

```text
GET /api/v1/workspace/documents
GET /api/v1/workspace/documents/{document_id}
GET /api/v1/workspace/documents/{document_id}/metadata
```

Los endpoints son read-only, exigen token/policy y nunca reciben una ruta
absoluta como autoridad.

## Entregables

```text
src/.../workspace_documents_service.py
src/.../workspace_document_routes.py
schemas/workspace_document_*.json
ui/web/src/pages/WorkspaceDocumentsView.tsx
ui/web/src/components/DocumentTree.tsx
ui/web/src/components/DocumentViewer.tsx
tests/test_workspace_document_service.py
tests/test_api_workspace_documents.py
tests/test_web_ui_workspace_documents.py
docs/audits/uoc_001_read_only_documents_report.md
docs/post_h_eval_002_uoc_001_manifest.json
```

## Evidencia

- árbol de `inventory-sales-local`;
- `product_vision.md` y los documentos 02-B visibles;
- negative cases de traversal, UNC, junction y symlink;
- capturas browser de desktop y viewport reducido;
- manifest de rutas leídas;
- prueba de cero escritura.

## Criterio de cierre

- documentos requeridos visibles;
- cero lectura fuera del root;
- cero mutación;
- rutas/errores tipados;
- API/UI contracts PASS;
- S0=0, S1=0.

---

# 9. Sprint UOC-002 — Metadata, Git history y búsqueda documental

## Objetivo

Convertir el visor en una superficie de inspección técnica útil para revisión y
auditoría.

## Alcance

- SHA-256 y tamaño;
- estado Git staged/unstaged/untracked;
- último commit, autor y fecha;
- historial paginado limitado al documento;
- diff read-only contra HEAD o commit seleccionado;
- búsqueda full-text local con índice incremental;
- frontmatter parseado;
- enlaces salientes y entrantes;
- badges de required/recommended/optional;
- cache invalidable por mtime/hash.

## Controles

- no ejecutar `git` con argumentos construidos desde texto libre;
- usar adapter Git tipado;
- limitar cantidad de commits y bytes de diff;
- bloquear archivos secretos aunque estén versionados;
- no persistir contenido de documentos en una base externa.

## Contratos API

```text
GET /api/v1/workspace/documents/{id}/history
GET /api/v1/workspace/documents/{id}/diff
GET /api/v1/workspace/documents/search
GET /api/v1/workspace/documents/{id}/links
```

## Pruebas

- repositorio limpio, sucio y detached;
- archivo untracked, renombrado y eliminado;
- historial vacío;
- diff grande truncado con finding explícito;
- actualización incremental del índice;
- búsqueda sin fuga entre workspaces.

## Criterio de cierre

El operador puede explicar desde la UI qué documento observa, qué hash tiene,
qué cambió, quién lo cambió y qué relaciones documentales posee.

---

# 10. Sprint UOC-003 — Validación y trazabilidad documental

## Objetivo

Ejecutar desde la UI las validaciones determinísticas necesarias para la
baseline pre-code de 02-B.

## Alcance

- frontmatter validation;
- artifact profile validation;
- links validation;
- MIASI validation;
- readiness strict;
- checklist pre-code;
- visualización de findings por severidad;
- navegación finding → documento → sección;
- matriz requisito → historia → riesgo/control → prueba;
- ejecución como job read-only con trace/report.

## Arquitectura

La UI no reimplementa validators. Invoca Application Services existentes o
facades nuevas que devuelven `DevPilotApplicationResponse` y evidence refs.

## APIs

```text
POST /api/v1/workspace/validations/plan
POST /api/v1/workspace/validations/execute
GET  /api/v1/workspace/validations/{job_id}
GET  /api/v1/workspace/traceability
```

Aunque sean read-only, se usa `plan → execute` para uniformar presupuesto,
timeout y evidencia.

## Gate especial 02-B

Este sprint es el mínimo requerido antes de ejecutar sustantivamente
`POST-H-EVAL-002-02-B` desde una estrategia UI-first.

PASS exige:

- los ocho artefactos pre-code consultables;
- validaciones lanzables desde UI;
- findings navegables;
- readiness strict visible;
- trazabilidad inicial visible;
- bridge CLI residual inventariado;
- S0=0, S1=0.

---

# 11. Sprint UOC-004 — Governed edit planning y diff

## Objetivo

Permitir propuestas de edición sin mutación.

## Flujo

```text
open document
→ create edit proposal
→ validate syntax/frontmatter
→ generate immutable plan
→ render full diff
→ calculate risk/policy
→ no write
```

## Alcance

- edición de Markdown/JSON/YAML permitidos;
- plan con `document_sha_before`;
- diff unificado;
- preview renderizado;
- validaciones pre-apply;
- expiración del plan;
- optimistic concurrency;
- guardado de draft en session-local storage sin secretos;
- exportación de patch como evidencia no ejecutada.

## No-go

- auto-save al filesystem;
- edición de `.env`, secrets, binarios o archivos fuera de allowlist;
- plan sin hash base;
- plan mutable después de aprobación.

## Pruebas

- stale plan;
- documento modificado durante la edición;
- frontmatter inválido;
- diff vacío;
- documento eliminado;
- plan excesivamente grande;
- cambio fuera de scope.

## Criterio de cierre

Toda propuesta es reproducible, validada, no mutante y vinculada al blob base.

---

# 12. Sprint UOC-005 — Approval binding, apply y rollback

## Objetivo

Ejecutar cambios documentales exclusivamente después de aprobación válida.

## Flujo

```text
immutable plan
→ approval request
→ human review
→ approve/deny
→ recheck hash and policy
→ backup
→ atomic apply
→ post-validation
→ PASS or rollback
→ trace/report/evidence
```

## Requisitos de approval

- `plan_id`;
- hash del plan;
- hash del documento base;
- actor;
- scope;
- reason;
- TTL;
- policy decision;
- decisión y timestamp.

## Ejecución

- escritura atómica mediante archivo temporal y replace;
- permisos conservados;
- backup en root de control permitido;
- rollback automático si post-validation bloquea;
- rollback manual acotado antes de commit;
- no silent success.

## Evidencia

- plan;
- diff;
- approval;
- pre/post hashes;
- validator results;
- rollback record, cuando aplique;
- trace/report;
- actor y duración.

## Criterio de cierre

- apply PASS y rollback PASS en fixtures;
- approval ausente/expirado/hash distinto bloquean;
- zero writes outside workspace;
- S0=0, S1=0.

---

# 13. Sprint UOC-006 — Git operations gobernadas

## Objetivo

Cubrir desde UI el ciclo seguro de revisión y commit sin exponer Git arbitrario.

## Alcance

- status y diff;
- staging plan por archivos allowlisted;
- revisión de commit plan;
- validaciones pre-commit;
- aprobación cuando policy lo exija;
- commit con identidad explícita;
- comprobación post-commit;
- historial y compare;
- branch creation controlada para workspaces.

## Prohibido

- `reset --hard` libre;
- rebase interactivo;
- force push;
- delete branch sin workflow separado;
- argumentos Git libres;
- staging de secretos o archivos prohibidos.

## Criterio de cierre

Un cambio documental puede pasar desde propuesta hasta commit, con una cadena
completa de hashes, aprobación, validaciones y evidencia.

---

# 14. Sprint UOC-007 — CLI capability registry y governed job framework

## Objetivo

Crear la infraestructura común para llevar capacidades CLI a la UI de forma
segura y observable.

## Alcance

- registry de capacidades;
- schemas de input/output;
- risk class;
- policy binding;
- budgets;
- dry-run/approval/rollback flags;
- job lifecycle;
- cancel token;
- heartbeat;
- artifact/evidence references;
- idempotency key;
- correlation ID.

## Estados de job

```text
planned
pending-approval
approved
queued
running
pass
pass-with-gaps
block
error
cancel-requested
cancelled
rollback-running
rolled-back
expired
```

## Gate

No se incorpora una capacidad nueva a UI si no está registrada y no tiene
contrato, policy, pruebas negativas y evidence mapping.

---

# 15. Sprint UOC-008 — Job Console y observabilidad operacional

## Objetivo

Eliminar operaciones invisibles y consolas ocupadas sin progreso observable.

## Nueva superficie

```text
/jobs
/jobs/{job_id}
```

## Alcance

- jobs activos e históricos;
- progreso por fases;
- heartbeat y duración;
- logs sanitizados en streaming/polling local;
- findings;
- artifacts;
- traces;
- cancelación;
- retry gobernado;
- timeout visible;
- relación con approval y commit;
- filtros por workspace, capability y estado.

## Requisitos de operación

- ninguna tarea larga sin heartbeat;
- subprocess tree controlado;
- cancelación mata descendientes de forma segura;
- log con tamaño máximo y redacción;
- reinicio de UI no pierde el estado autoritativo;
- jobs huérfanos se reconcilian al iniciar.

## Criterio de cierre

Las tareas largas muestran avance, pueden cancelarse y producen una conclusión
explicable, sin requerir inspección manual de procesos Windows.

---

# 16. Sprint UOC-009 — Quality, tests y release operations

## Objetivo

Llevar a UI las operaciones determinísticas de calidad y release con Test
Impact y budgets.

## Capacidades prioritarias

- Test Impact plan;
- focused test execution;
- TCR v1/v2;
- Project State;
- Docs Governance;
- quality gate profiles;
- readiness;
- release verification dry-run;
- evidence packaging;
- baseline/manifest inspection.

## Reglas

- full regression requiere confirmación explícita y presupuesto;
- no se ejecuta automáticamente después de una prueba focal;
- tests se seleccionan por IDs/registry, no por shell text;
- resultados muestran passed/failed/errors/skipped;
- timeout y heartbeat obligatorios;
- failure replay preserva evidencia previa sin falsear adjudicación.

## Criterio de cierre

Un operador puede planear, aprobar y observar validaciones sin copiar comandos
de CLI, manteniendo exactamente los mismos contratos de resultado.

---

# 17. Sprint UOC-010 — RAG, agentes, tools y handoffs gobernados

## Objetivo

Exponer capacidades de IA sin convertir la UI en un loop autónomo irrestricto.

## Alcance

- ModelAdapter y proveedor visible;
- ruta mock obligatoria;
- modelos locales opt-in;
- APIs externas deshabilitadas por defecto;
- RAG index/query con citas y freshness;
- insufficient-evidence state;
- memoria opt-in y retención;
- tool calls allowlisted;
- dry-run de herramientas;
- approval para mutaciones;
- handoffs con supervisor;
- límites de turnos, tiempo y costo;
- trace por step.

## No-go

- herramientas no registradas;
- ejecución remota;
- connector write por defecto;
- plugin execution sin sandbox;
- uso de memoria como evidencia formal;
- loops sin límites;
- ocultamiento de costo o proveedor.

## Criterio de cierre

Los casos mock/local son reproducibles y cualquier capability sensible se
mantiene bloqueada o gobernada por policy/approval.

---

# 18. Sprint UOC-011 — Hardening, accesibilidad, rendimiento y release

## Objetivo

Cerrar la evolución como producto operable, no como prototipo funcional.

## Alcance

- threat model actualizado;
- API route drift guard;
- UI route registry;
- CSP y security headers;
- session/token lifecycle;
- rate/size limits locales;
- WCAG keyboard/focus/contrast;
- responsive layout;
- performance budgets;
- caching e invalidación;
- chaos/error states;
- backup/restore del estado operacional;
- instalación limpia y upgrade/rollback;
- runbook de operador;
- release notes y soporte.

## Matriz browser mínima

```text
Dashboard
Documents
Reports
Traces
Approval Center
Jobs
Quality/Tests
Configuration
```

Cada vista debe probar:

```text
loading
empty
ready
warn
block
error
API down
401
403
timeout
cancelled
stale data
```

## Criterio final de programa

- capability registry completo;
- paridad UI declarada y medible;
- bridges residuales justificados;
- cero shell arbitrario;
- seguridad/path traversal PASS;
- escritura/rollback PASS;
- jobs observables PASS;
- accesibilidad y performance gates PASS;
- instalación/upgrade/rollback PASS;
- S0=0, S1=0;
- declaración de release local aprobada.

---

# 19. Estrategia de pruebas por sprint

Cada sprint debe ejecutar, como mínimo:

1. `git diff --check`;
2. `py_compile`/typecheck/lint aplicables;
3. pruebas unitarias del servicio;
4. pruebas API contract;
5. pruebas UI contract;
6. negative security cases;
7. Test Impact;
8. validators de gobernanza;
9. browser acceptance cuando cambie una superficie visible;
10. full regression solo cuando el alcance transversal o el riesgo lo exija.

La reutilización de evidencia previa solo es válida si:

- el hash del artefacto previo coincide;
- los tests no impactados están identificados por Test Impact;
- se ejecutan todos los tests afectados;
- no se suma evidencia incompatible;
- la adjudicación queda registrada.

# 20. Modelo de evidencia

Cada sprint produce un único paquete autoritativo:

```text
<SPRINT>_CURRENT.json
<SPRINT>_CURRENT.json.sha256
<SPRINT>_EVIDENCE.zip
<SPRINT>_EVIDENCE.zip.sha256
```

Contenido mínimo:

- identidad Git;
- manifest del sprint;
- test impact;
- logs de pruebas;
- validators;
- API/UI contracts;
- browser acceptance, cuando corresponda;
- security negative cases;
- performance measurements;
- files changed;
- risks y residual gaps;
- rollback instructions;
- decision PASS/PASS-WITH-GAPS/BLOCK.

# 21. Política de ramas e integración

Cada sprint parte del commit canónico aceptado y usa una rama propia:

```text
feat/post-h-eval-002-uoc-000-...
feat/post-h-eval-002-uoc-001-...
...
```

La integración debe ser fast-forward cuando sea posible. Un conflicto crea un
nuevo cambio no probado y exige revalidación proporcional. No se hace squash de
manifests/evidencia que destruyan trazabilidad.

# 22. Riesgos principales

| Riesgo | Control |
|---|---|
| UI convertida en shell | Registry tipado y no-shell ADR |
| Path traversal | Opaque ID + PathGuard + negative tests |
| Escritura accidental | Read-only first + plan/diff/approval |
| Stale plan | Optimistic concurrency por hash |
| Approval reutilizado | Binding a plan/hash/scope/TTL |
| Job huérfano | Reconciliation + heartbeat + timeout |
| Logs con secretos | Redaction + size limits + tests |
| Drift CLI/API/UI | Capability registry + contract guard |
| Regresión costosa | Test Impact + tiers + evidence reuse gobernada |
| UI excesivamente compleja | Progressive disclosure y roles operativos |
| Falsa paridad | Matriz con estados y evidencia por capability |

# 23. Decisión de secuenciación con POST-H-EVAL-002-02-B

`POST-H-EVAL-002-02-B` está formalmente autorizado por el cierre de 02-A. Sin
embargo, para cumplir la prioridad UI-first se recomienda:

```text
cerrar API-GAP-SEC-001
→ UOC-000
→ UOC-001
→ UOC-002
→ UOC-003
→ iniciar ejecución sustantiva de 02-B
```

La autoría continuará en IDE/Git durante esta primera ola; la UI será la
superficie de consulta, validación, trazabilidad, revisión y aprobación. Los
sprints UOC-004–006 incorporarán posteriormente la autoría gobernada.

# 24. Definition of Done del programa

El programa no se considera cerrado hasta que:

- toda capacidad CLI esté clasificada;
- la UI cubra las capacidades seguras de mayor valor;
- los bridges restantes estén registrados y justificados;
- las capacidades prohibidas permanezcan bloqueadas;
- documentos, validaciones, approvals, jobs, Git y evidencia estén integrados;
- la trazabilidad end-to-end sea navegable;
- no existan S0/S1;
- exista runbook de instalación, operación, diagnóstico y rollback;
- el release local sea reproducible y verificable.


## UOC-001 browser acceptance clarification

UOC-001 precedes POST-H-EVAL-002-02-B and remains strictly read-only. Its
browser gate requires visibility parity for every currently materialized
document that satisfies the authoritative UOC-001 allow/deny policy. Files
excluded by that policy, including private `.devpilot` control-plane registries,
must remain absent from API/UI and are verified as negative security cases.
`traceability_matrix.md` and authored ADR documents are classified as
`PLANNED-FOR-02-B` when they do not yet exist as UI-eligible documents. Responsive evidence must
show a genuine portrait viewport with legible controls and document access, not
a scaled desktop screenshot.


## Adjudicación UOC-001

UOC-001 queda cerrado/PASS como sprint read-only. La capacidad sigue siendo una primera versión preliminar: no incluye Git metadata, full-text search, validaciones, edición, approval, escritura ni rollback.

- Accepted source commit: `e9fe717eb8eafaca40830c691a7efb7bb956b035`.
- Closure commit y baseline `repo_329`: resueltos por `UOC_001_CANONICAL_INTEGRATION.json` y `BASELINE_CURRENT.json`.
- Browser acceptance: sequence-aware y policy-aligned v3; exige paridad exacta con documentos UI-eligible y confirma que los archivos control-plane excluidos no se exponen.
- `traceability_matrix.md` y ADRs authored permanecen `PLANNED-FOR-02-B` cuando todavía no existen como documentos UI-eligible; UOC-001 no fabrica documentos futuros.

## 25. Estado de implementación UOC-002 — 2026-08-05

UOC-001 queda cerrado `PASS` sobre el commit canónico `9cb67b023c6ac909a2b492370632a3955a454e39` y el baseline
exact-tree `repo_329`. UOC-002 se implementa sobre ese árbol como candidato
`implemented-initial`, sin declarar aún cierre ni autorizar UOC-003.

La implementación añade metadata SHA-256/frontmatter/clasificación, estado e
historial Git tipados, diff read-only acotado, búsqueda full-text local con
índice incremental exclusivamente en memoria y enlaces documentales internos.
Todos los endpoints conservan los IDs opacos de UOC-001 y no aceptan rutas o
argumentos Git libres.

El cierre de UOC-002 permanece condicionado a la aplicación y validación
autoritativa en Windows, build Vite, aceptación browser, integración Git,
sincronización local/origin y generación del baseline limpio siguiente.

## 26. Recuperación de regresión UOC-002 — v1.0.1

La regresión general Windows obtuvo `1987 PASS / 58 FAIL / 0 ERROR / 0 SKIP`. Los 58 fallos se adjudican a cuatro contratos acumulativos: reconciliación `current_repo`/Evidence Freshness, conteos históricos congelados, schemas UOC-000 no evolutivos y confusión entre dependencias locales ignoradas y artefactos versionados.

El correctivo v1.0.1 no modifica la funcionalidad documental UOC-002 ni relaja seguridad. Se autoriza reutilizar las 1987 pruebas PASS y ejecutar verificación selectiva sobre las causas raíz y una sola instancia de cada gate compuesto costoso. UOC-003 continúa bloqueado hasta aceptación browser, integración y baseline repo 330.

## UOC-002 regression recovery v1.0.2 — RAG runtime isolation

The full-regression test `tests/test_rag_local.py::test_rag_cli_index_and_query_json` is isolated in a disposable workspace. A previously regenerated `.devpilot/rag/docs_index.json` is accepted only when a complete in-memory rebuild produced by the checkout's real `LocalRagIndexer`, `PathGuard` and `SecretGuard` matches every field and chunk except the timestamp; the operator then restores the exact `HEAD` blob. The runtime index is never carried into the UOC-002 commit. Unknown, staged or tampered changes remain blocking.

## UOC-002 regression recovery v1.0.3 — portable preimage validation

The recovery preflight bundles the 42 v1.0.0 source preimages and accepts either byte-exact identity or UTF-8 content differing only by LF/CRLF materialization. This is required for Windows Git checkouts. BOM changes, whitespace/content edits, staged changes, unknown paths and non-UTF-8 mismatches remain blocking. Per-file equivalence is recorded in the apply report.

## UOC-002 regression recovery v1.0.5 — Git-native RAG reconciliation and durable resume

The v1.0.4 dry-run correctly detected `.devpilot/rag/docs_index.json` as an additional source change, but its expected-state contract was incomplete: it modeled the 71 v1.0.3 payload files and omitted the tracked RAG path present after the selective stop. The earlier recovery had restored raw `HEAD` bytes and the selective runner checked only hash stability, not Git worktree cleanliness. v1.0.5 classifies the index as either `HEAD`-equivalent or a canonically rebuilt local regeneration, backs it up, restores it with Git-native worktree materialization, refreshes and verifies the index/worktree state, and rolls back partial operator writes on failure. The selective runner now requires the RAG path to be Git-clean before execution and after every case. The accepted `5/5` RAG evidence is reused; verification resumes from `state_history_and_freshness`. UOC-002 remains open pending the resumed suite, browser acceptance and canonical closure.

## UOC-002 closure continuation v1.0.6

- Browser workspace authority uses filesystem identity, not raw slash-sensitive string comparison.
- The manual observations template is fail-closed (`PENDING`) until all checks are observed.
- Closure identity is lifecycle-aware: recovery identity while open; `UOC-002-CLOSURE` only after closure.
- Repo 330 is generated only by `git archive` from the canonical closure commit.

## 2026-08-06 — UOC-002 closure

- Decision: `PASS`.
- Accepted source commit: `bcb46779470d86d19a87e55a9f6d38297e2f7534`.
- Regression adjudication: `1987 PASS` reused; selective recovery `16/16 PASS`, validators `7/7 PASS`, prior RAG `5/5 PASS`.
- Browser acceptance: `PASS`, four screenshots, zero-write, `S0=0`, `S1=0`.
- Selective evidence SHA-256: `c0ee693921e36de62d2acbc20d11255aad312726170dc27e40620d9548567cdd`.
- Browser evidence SHA-256: `4fa6ef0f8857de34de2bf04fedf989464504f72bb7f1b50a7c0262cce2341674`.
- Next authorized sprint: `UOC-003`.
