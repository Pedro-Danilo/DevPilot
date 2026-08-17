---
doc_id: "DEVPL-PROMPT-GSDLC-02-D"
prompt_number: "04"
title: "Prompt operativo — DEVPL-GSDLC-02-D — Approval binding to authenticated actor and role"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-02"
micro_sprint: "DEVPL-GSDLC-02-D"
execution_rule: "solo este micro-sprint; 02-E bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
source_repo: "repo_DevPilot_Local_357_DEVPL_GSDLC_02_C_SERVER_RBAC_ENFORCEMENT.zip"
source_git_commit: "1c7789f6a3b67055f6c1811196b006e2d9b989e9"
source_repo_sha256: "ce052373c1864ef0f5c782c4f9d543540ffdb68bc3476ca4d74f012681d41a73"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_backlog: "DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md"
local_first: true
dry_run_default: true
external_api_required: false
external_network_required: false
pilot_workspace_mutation_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-02-D

## 1. Mandato

Implementa **solo** `GSDLC-02-D — Approval binding to authenticated actor and role` sobre 02-C `CLOSED/PASS`.

Rebind satisfecho: ejecutar exclusivamente sobre repo357, commit 1c7789f6a3b67055f6c1811196b006e2d9b989e9, después de adjudicación 02-C CLOSED/PASS.


## Fuentes obligatorias de autoridad

- `DEVPL_GSDLC_02_C_FINAL_OWNER_ADJUDICATION_v1_0_0.md` es la autoridad inmediata de cierre del predecesor;

Antes de proyectar cualquier cambio, consultar literalmente como mínimo:

- `repo_DevPilot_Local_357_DEVPL_GSDLC_02_C_SERVER_RBAC_ENFORCEMENT.zip` como baseline canónico de ejecución de 02-D;
- `DEVPL_GSDLC_01_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- `DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md`;
- `docs/backlogs/POST-H-012_approval_rbac_hardening.md`;
- `docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md`;
- `docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md`;
- `.devpilot/identity/identity_registry.json`;
- `.devpilot/approval/sensitive_action_catalog.json`;
- `src/devpilot_core/identity/`;
- `src/devpilot_core/approval/`;
- `src/devpilot_core/interfaces/api/security.py`;
- `.devpilot/gsdlc/transversal_validation_policy.json`;
- `.devpilot/project_state.json`;
- Source Registry, schema catalog y TCR v1/v2 vigentes.

Si una fuente obligatoria no está disponible, **BLOCK antes de implementar**. No completar documentación por suposición.


## 2. Autoridad de actor

Eliminar el actor spoofable de la cadena de autoridad.

La ruta correcta debe ser:

```text
authenticated session
→ AuthenticatedPrincipal
→ effective roles/workspace scopes
→ RBAC
→ approval request/decision
→ AuthenticatedApprovalBinding
```

El caller no puede suministrar un `actor_id` autoritativo.

Si endpoints/DTO históricos todavía aceptan `actor`, debe:

- quedar ignorado como autoridad o rechazado según contrato;
- nunca sobrescribir el principal;
- generar negative test de spoofing;
- documentar deprecation/migration.

## 3. Binding fuerte

Vincular la decisión como mínimo a:

- authenticated actor_id;
- `role_at_decision`;
- workspace;
- action;
- subject;
- subject hash cuando aplique;
- command_id/tool_call_id cuando aplique;
- request identity;
- session identity/version;
- policy refs;
- expires/revocation semantics.

## 4. Approval authority

Crear `approval_authority_matrix.json`:

- low/medium/high/critical;
- roles autorizados;
- separation of duties;
- self-approval policy;
- requester/approver conflict;
- role change/revocation;
- session revoke/expire;
- scope mismatch.

Critical nunca queda permitido por wildcard no acotado sin justificación explícita.

## 5. Approval Center

Actualizar la UI únicamente en lo necesario para mostrar de forma honesta:

- requester;
- authenticated approver;
- role(s) efectivos;
- riesgo;
- por qué puede/no puede decidir;
- scope;
- stale/revoked state.

No implementar todavía LoginView/FirstRunOwnerView; pertenecen a E.

## 6. Tests obligatorios

- actor spoof negative;
- actor parameter cannot override principal;
- wrong role;
- wrong workspace;
- expired/revoked session;
- role changed;
- stale approval;
- self-approval/SoD;
- command/tool-call mismatch;
- subject hash mismatch;
- Approval Center/API parity;
- A+B+C+D cumulative regression.

Si se modifica UI, ejecutar npm smoke/build focal; browser real completo queda en E.


## Política transversal de validación y regresión

1. Ejecutar L0 integrity/authority antes de mutar.
2. Ejecutar focal del micro-sprint y regresión acumulativa de todos los micro-sprints GSDLC-02 ya cerrados.
3. Ejecutar Test Impact siempre en dry-run/analyze.
4. A→D usan `validation_mode=cumulative-selective`.
5. En A→D, `full_regression_required=true` emitido por Test Impact es señal de escalamiento, no orden automática.
6. Full regression intermedia solo por hard trigger sistémico explícito y owner-approved.
7. E ejecuta la única full regression de GSDLC-02 exactamente una vez, después de los gates baratos y browser acceptance real.
8. Si la full de E falla: conservar log original inmutable; corregir causas; selective retest de fallidos + contratos impactados; **no ejecutar una segunda full**.
9. Historical Regression Guard debe recibir evidencia honesta del modo de validación; no usar waiver para ocultar fallos.
10. Nunca relajar tests históricos solo para obtener verde: clasificar `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`.


Para 02-D: **full regression = NO** salvo hard trigger owner-approved previo.


## Seguridad y límites obligatorios

- localhost/loopback only;
- public API, remote login, tenancy, OIDC/SSO, enterprise IAM permanecen deshabilitados;
- deny-by-default;
- ningún LLM/modelo decide autenticación, roles, RBAC, approvals o session authority;
- passwords/raw credentials nunca en logs/evidence/source;
- session IDs/tokens/cookies/CSRF secrets nunca en source ZIP ni evidence;
- legacy local API token no puede convertirse en principal humano ni autorizar approvals identity-bound;
- no role self-escalation;
- no actor supplied by caller como autoridad de approval;
- toda mutación sigue `plan → dry-run → policy/RBAC → approval → execute → verify → evidence`;
- no `reset --hard`, `clean`, rebase automático ni force push;
- pilot workspace preservado.


## 7. Evidencia mínima

- `approval_binding_security_report.json`;
- `approval_authority_matrix.json`;
- `approval_role_matrix.md`;
- spoofing negatives;
- SoD evidence;
- Approval Center parity report.

## 8. PASS / BLOCK

PASS-CANDIDATE si actor binding es no spoofable, autoridad por rol se aplica server-side, scope mismatch bloquea y session/role revocation invalida la autoridad según policy.

BLOCK si se confía en actor libre, una sesión no autorizada aprueba, existe self-escalation/indirect escalation o critical action queda sin autoridad explícita.

## 9. Git

Feature: `feat/devpl-gsdlc-02-d-authenticated-approval-binding`

Commit: `feat(gsdlc-02-d): bind approvals to authenticated principals`


## Topología y entregables Windows

Usar únicamente las raíces vigentes:

```text
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Workspaces\inventory-sales-local
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
D:\Projects\DevPilot_Local
```

El prompt ejecutado debe producir:

1. package `.zip` con operador Python state-aware, payload exacto, authority inputs y manifest;
2. delta candidate exacto;
3. repo candidate PRE-WINDOWS limpio, explícitamente no canónico;
4. guía única `.md` para personal no experto;
5. sidecars SHA-256;
6. `SOURCE_DELTA_MANIFEST.json`;
7. `ARTIFACT_HASHES.sha256`;
8. `OPERATION_DECLARATION.json`;
9. `CURRENT.json`;
10. closure report;
11. `historical_contract_sweep`;
12. definición exacta de evidence Windows;
13. feature branch y commit convencional;
14. recuperación focal si hay BLOCK, sin resetear el trabajo válido.

La guía Windows debe usar comandos PowerShell de una sola línea física. Debe auditar sus propias rutas para evitar caracteres de control invisibles o concatenaciones inválidas.
