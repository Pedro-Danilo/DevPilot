---
doc_id: "DEVPL-GSDLC-02"
title: "DEVPL-GSDLC-02 — Local Identity, authenticated sessions and RBAC approval authority"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_353_DEVPL_GSDLC_01_E_PROJECT_STATUS_BACKLOG_CLOSURE.zip"
source_git_commit: "a0b503ae36cdfda77279bb66c40b4f6b32f8856f"
source_repo_sha256: "0c235819633b7e34fa47ed2c28e5dc6028e7e21655e54eb35ac5f6749f08816a"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
design_source_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_source_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_source_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
source_authority_rebound: true
predecessor_backlog: "DEVPL-GSDLC-01"
predecessor_closure_authority: "DEVPL_GSDLC_01_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-02"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
approved_at: "2026-08-16"
validation_policy: "cumulative-selective A-D; exactly-one-full-regression in E"
---


# 0. Aprobación, rebind y autoridad de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

Esta versión `1.2.0` aprueba el alcance de `v1.1.0`, incorpora los refinamientos de seguridad/compatibilidad descritos en este documento y rebindea la ejecución a la fuente canónica cerrada por GSDLC-01:

```text
repo
repo_DevPilot_Local_353_DEVPL_GSDLC_01_E_PROJECT_STATUS_BACKLOG_CLOSURE.zip

commit
a0b503ae36cdfda77279bb66c40b4f6b32f8856f

SHA-256
0c235819633b7e34fa47ed2c28e5dc6028e7e21655e54eb35ac5f6749f08816a

canonical branch
eval/post-h-eval-002-02-a-onboarding
```

La fuente repo341 del diseño original queda preservada como `design_source` histórica. No se presenta como baseline de ejecución.

## 0.1 Precondiciones verificadas para aprobar

Repo353 contiene literalmente:

- `docs/backlogs/POST-H-012_approval_rbac_hardening.md` con `implementation_status=closed`;
- `docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md` aprobado como `continue-blocked`;
- `docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md` como diseño successor local-only todavía no runtime;
- `.devpilot/identity/identity_registry.json`;
- RBAC inicial;
- StrongApprovalBinding;
- API local protegida;
- Project Status de GSDLC-01.

La aprobación de GSDLC-02 **no habilita por sí misma runtime auth**. `02-A` debe cerrar el threat model/ADR antes del primer endpoint de login.

## 0.2 Frontera histórica obligatoria

`ADR-POSTH-034-D` permanece congelado:

```text
multiuser.auth = continue-blocked
production_multiuser_enabled = false
iam_enterprise_enabled = false
oidc/sso = false
tenancy = false
public_api = false
```

GSDLC-02 habilita únicamente un successor:

```text
local.operator_auth
single-installation
localhost-only
human authenticated principal
revocable local session
server-side RBAC
```

No es enterprise IAM ni SaaS multiuser.

## 0.3 Política de ejecución acumulativa

A→E se ejecutan secuencialmente. Cada micro-sprint:

- parte del baseline canónico cerrado por su predecesor;
- genera delta exacto, `historical_contract_sweep`, evidence Windows y owner adjudication;
- usa feature branch propia y promoción `ff-only`;
- no autoriza el siguiente hasta `CLOSED/PASS`;
- preserva el piloto `inventory-sales-local`;
- no almacena passwords, session tokens, cookies, CSRF secrets ni credential hashes en Git/evidence;
- usa operadores Python state-aware y dry-run por defecto.


# DEVPL-GSDLC-02 — Local Identity, authenticated sessions and RBAC approval authority

## 1. Objetivo

Implementar login local, sesiones y autorización por roles para que toda acción/approval quede vinculada a una identidad humana no spoofable dentro del alcance local-first.

## 2. Invariante de producto que esta ola debe demostrar

> Al abrir DevPilot, después del bootstrap inicial, el usuario se autentica; la UI y API aplican RBAC real, y solo roles autorizados pueden aprobar acciones del riesgo correspondiente.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-01 CLOSED/PASS
- POST-H-012 approval/RBAC baseline
- ADR-POSTH-034-D historical boundary

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- local operator identities
- first-run owner bootstrap
- session lifecycle
- RBAC endpoint/action/workspace
- approval actor binding
- login/logout UI

### 4.2 Fuera de alcance

- enterprise IAM
- SSO/OIDC enterprise
- tenancy/cloud
- public/non-local API

## 5. Superficies y fuentes que probablemente serán afectadas

- src/devpilot_core/identity/*
- approval binding
- API auth middleware
- local credential store
- UI login/session

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

**Refinamiento aprobado v1.2.0.** La implementación debe mantener una frontera explícita entre:
- `human-session`: principal humano autenticado y fuente autoritativa para RBAC/approvals;
- `legacy-local-token`: compatibilidad local acotada; nunca puede convertirse en autoridad para approvals identity-bound ni escalar roles;
- `agent/service principal`: fuera de la autoridad humana salvo contrato explícito posterior.

La transición desde el token local de GSDLC-01 no puede crear un bypass de la sesión humana.

## 6. Micro-sprints secuenciales

### GSDLC-02-A — Auth threat model and bounded enablement ADR

**Objetivo.** Crear un successor ADR para `local.operator_auth` sin declarar enterprise multiuser.

**Entradas obligatorias**
- GSDLC-01 PASS
- POST-H-034-D histórico
- POST-H-012 Approval/RBAC baseline

**Actividades**
1. Modelar amenazas de credenciales, sesiones, CSRF, session fixation, escalation de roles y spoofing del actor de approval.
2. Definir un trust boundary estrictamente local: localhost, sin public API ni acceso remoto.
3. Definir la taxonomía inicial de roles: owner, product-owner, architect, security-reviewer, developer, qa-reviewer, release-manager, operator y agent-supervisor. El rol histórico `reviewer` debe clasificarse y migrarse mediante un `legacy_role_migration_map`; no renombrarlo silenciosamente ni asumir equivalencia sin comparar permisos.
4. Definir separación de funciones configurable y la autoridad máxima de cada rol.
5. Emitir un ADR successor de runtime enablement, preferentemente `ADR-GSDLC-005-local-operator-auth-enablement.md`, que consuma sin reescribir `ADR-GSDLC-003` y mantenga `ADR-POSTH-034-D` como hecho histórico `continue-blocked` para multiuser/enterprise IAM.

**Entregables verificables**
- ADR-GSDLC local operator auth
- auth_threat_model.md
- role_authority_matrix.json

**Pruebas / validadores**
- validación de ADR/schema
- coverage amenaza→control→test
- consistencia con no-go de POST-H-034-D

**Evidencia mínima**
- auth_threat_matrix.json
- role_decision_record.md

**Seguridad operacional específica**
- localhost only
- no remote login
- no credenciales versionadas

**PASS**
- successor ADR explícito
- enterprise/multiuser remoto permanece false
- cada rol tiene autoridad definida

**BLOCK**
- `production_multiuser_enabled=true`
- rol sin permisos/limits definidos
- login habilitado antes del threat model

**Salida / autorización**
- autoriza GSDLC-02-B


### GSDLC-02-B — Identity store, credentials and session lifecycle

**Objetivo.** Implementar autenticación local segura, first-run owner bootstrap y sesiones revocables.

**Entradas obligatorias**
- GSDLC-02-A PASS

**Actividades**
1. Implementar first-run bootstrap del primer owner local.
2. Elegir e implementar almacenamiento seguro de credenciales: hash adaptativo aprobado o integración con secret store del SO; nunca password reversible.
3. Implementar session create, rotate, idle timeout, absolute timeout, revoke y logout.
4. Vincular cada sesión a actor_id, roles efectivos, workspace scopes y timestamps de seguridad.
5. Implementar audit trail de login/logout/revoke sin registrar secretos.

**Entregables verificables**
- IdentityStore
- SessionService
- credential/session schemas
- auth runbook

**Pruebas / validadores**
- password/hash verification
- invalid credential negative
- expired session
- revoked session
- session rotation
- secret redaction

**Evidencia mínima**
- auth_session_test_report.json
- session_lifecycle_matrix.md

**Seguridad operacional específica**
- raw passwords nunca se loguean
- cookies HttpOnly/SameSite y CSRF strategy
- runtime auth store excluido de source ZIP

**PASS**
- login solo con credencial válida
- revoke invalida inmediatamente la sesión
- restart recovery definido

**BLOCK**
- plaintext credential
- token/session en logs
- sesión revocada continúa autorizando

**Salida / autorización**
- autoriza GSDLC-02-C


### GSDLC-02-C — RBAC enforcement by endpoint, action and workspace

**Objetivo.** Convertir el RBAC inicial en enforcement real del servidor, no en decoración de UI.

**Entradas obligatorias**
- GSDLC-02-B PASS
- .devpilot/identity/identity_registry.json como baseline conceptual

**Actividades**
1. Mapear roles a typed actions, endpoints y workspace scopes.
2. Aplicar deny-by-default a acciones desconocidas o sin policy.
3. Ejecutar autorización server-side en ApplicationService/API antes de side effects.
4. Hacer que cambios de rol invaliden o reevalúen privilegios de la sesión.
5. Exponer al frontend un capability view derivado del servidor para mostrar/ocultar opciones sin convertir el frontend en autoridad.

**Entregables verificables**
- RBAC policy catalog
- RBACEnforcer
- role/capability API

**Pruebas / validadores**
- matriz exhaustiva role×action
- privilege escalation negatives
- cross-workspace access
- UI-hidden/API-403 parity

**Evidencia mínima**
- rbac_coverage.json
- negative_access_matrix.json

**Seguridad operacional específica**
- no role self-escalation
- workspace scope obligatorio
- owner recovery gobernado

**PASS**
- 100% de acciones sensibles mapeadas
- API devuelve deny/403 al rol no autorizado
- UI refleja la misma autoridad

**BLOCK**
- UI oculta acción pero API la permite
- acción crítica unmapped
- workspace scope omitido

**Salida / autorización**
- autoriza GSDLC-02-D


### GSDLC-02-D — Approval binding to authenticated actor and role

**Objetivo.** Eliminar approvals spoofables por parámetro `actor` y ligarlos a la sesión autenticada.

**Entradas obligatorias**
- GSDLC-02-C PASS
- StrongApprovalBinding baseline

**Actividades**
1. Derivar actor_id y roles exclusivamente de la sesión autenticada.
2. Vincular approval a role_at_decision, workspace, action, subject hash, command_id/tool_call_id cuando aplique.
3. Definir qué roles pueden aprobar low/medium/high/critical y qué operaciones requieren separación de funciones.
4. Revocar/revalidar approvals ante expiración, revocación de sesión o cambio de rol según policy.
5. Mostrar en Approval Center quién solicita, quién puede decidir y por qué.

**Entregables verificables**
- AuthenticatedApprovalBinding
- approval_authority_matrix.json
- Approval Center role UX

**Pruebas / validadores**
- actor spoof negative
- wrong role negative
- expired approval
- session revoked
- role changed
- scope mismatch

**Evidencia mínima**
- approval_binding_security_report.json
- approval_role_matrix.md

**Seguridad operacional específica**
- caller nunca suministra actor autoritativo
- critical actions limitadas a roles designados

**PASS**
- actor binding no spoofable
- autoridad por rol enforced server-side
- scope mismatch bloquea

**BLOCK**
- approval aceptado desde sesión no autorizada
- actor libre trusted
- role escalation indirecta

**Salida / autorización**
- autoriza GSDLC-02-E


### GSDLC-02-E — Login, first-run and browser security acceptance

**Objetivo.** Cerrar la experiencia autenticada de entrada y comprobarla con navegador real.

**Entradas obligatorias**
- GSDLC-02-D PASS

**Actividades**
1. Implementar first-run owner bootstrap UI.
2. Implementar login, logout, session-expired y revoked-session views.
3. Mostrar identidad y roles activos de forma persistente.
4. Proteger rutas de proyecto y redirigir a login cuando no existe sesión.
5. Ejecutar matriz browser como mínimo con owner, developer, security-reviewer/qa-reviewer conforme la matriz aprobada, y actor no autorizado. Si `reviewer` histórico continúa como alias de compatibilidad, debe probarse como alias explícito y no como rol canónico nuevo.

**Entregables verificables**
- LoginView
- FirstRunOwnerView
- SessionBanner
- Account/Role view
- browser acceptance matrix

**Pruebas / validadores**
- frontend auth tests
- API auth contract
- CSRF/session negative tests
- real-browser role matrix

**Evidencia mínima**
- redacted login screenshots
- role_access_browser_matrix.json
- session_browser_log.md

**Seguridad operacional específica**
- password/secret nunca visible en captura/evidencia
- lock/rate policy apropiada para local app
- no auth bypass por URL directa

**PASS**
- login obligatorio después del first-run
- rol visible
- Approval Center refleja autoridad
- S0=0
- S1=0

**BLOCK**
- ruta protegida abre anónimamente
- credential leak
- role bypass

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-03


## 7. Alcance transversal específico de esta ola

- Esta ola responde directamente a la exigencia de approvals por perfil adecuado.
- Los roles son locales al producto; enterprise IAM/tenancy siguen fuera de alcance.

## 8. Política de contratos históricos específica

- POST-H-034-D debe quedar congelado como decisión histórica `multiuser.auth continue-blocked`; crear una capability sucesora acotada `local.operator_auth`. Tests históricos no pueden bloquearla por extrapolación.
- POST-H-012 RBAC initial se migra a enforcement productivo local sin reescribir su evidencia.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

## 9. Seguridad operacional específica

- Threat model auth obligatorio antes del primer endpoint de login.
- Sesiones/credenciales nunca se versionan.
- CSRF/CORS/session fixation/privilege escalation son superficies S0/S1.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- unit auth/session
- RBAC matrix exhaustive
- approval binding negatives
- API auth contract
- browser auth matrix

Regla de regresión owner-approved:

- `02-A` a `02-D`: `validation_mode=cumulative-selective`; Test Impact se ejecuta siempre en dry-run/analyze y sus recomendaciones P0/P1 son inputs de selección.
- **No se ejecuta full regression en A→D por rutina**, aunque Test Impact marque `full_regression_required=true`.
- Una full intermedia solo se permite por un hard trigger de riesgo sistémico explícito, documentado y aprobado antes de ejecutarla.
- `02-E`, como micro-sprint de cierre, ejecuta la **única full regression del backlog exactamente una vez**, después de schema/API/UI, npm/build, governance, Test Impact y browser acceptance real.
- Si esa full falla: preservar el log original, corregir exclusivamente las causas, ejecutar selective retest de fallidos + contratos impactados, registrar `validation_mode=composite-full-regression-selective-retest` y **no repetir la full regression**.

## 11. Evidencia autoritativa esperada

- auth threat report
- RBAC coverage
- approval binding report
- redacted screenshots/logs

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- login local
- sesión revocable
- RBAC server-side
- approval actor binding
- roles visibles
- S0/S1=0

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-03 solo si una sesión autenticada puede acceder al Project Shell y las acciones se evalúan server-side.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.
