---
doc_id: "DEVPL-PROMPT-GSDLC-02-E"
prompt_number: "05"
title: "Prompt operativo — DEVPL-GSDLC-02-E — Login, first-run and browser security acceptance"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-17"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-02"
micro_sprint: "DEVPL-GSDLC-02-E"
execution_rule: "cierre de backlog; GSDLC-03 bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
source_repo: "repo_DevPilot_Local_358_DEVPL_GSDLC_02_D_AUTHENTICATED_APPROVAL_BINDING.zip"
source_git_commit: "c2ac010b89e17f19229b2d833071e61030a33e10"
source_repo_sha256: "f1241fc82acd90647ae368060f2487203154bb4b73b7b5f7e137423621293183"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_backlog: "DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md"
local_first: true
dry_run_default: true
external_api_required: false
external_network_required: false
pilot_workspace_mutation_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-02-E

## 1. Mandato

Implementa **solo** `GSDLC-02-E — Login, first-run and browser security acceptance` sobre 02-D `CLOSED/PASS` y ejecuta el cierre industrial A→E.

Rebind obligatorio al baseline canónico D: `repo_DevPilot_Local_358_DEVPL_GSDLC_02_D_AUTHENTICATED_APPROVAL_BINDING.zip` (`c2ac010b89e17f19229b2d833071e61030a33e10`, SHA-256 `f1241fc82acd90647ae368060f2487203154bb4b73b7b5f7e137423621293183`).


## Fuentes obligatorias de autoridad

Antes de proyectar cualquier cambio, consultar literalmente como mínimo:

- `repo_DevPilot_Local_358_DEVPL_GSDLC_02_D_AUTHENTICATED_APPROVAL_BINDING.zip` como baseline canónico inmediato, ya adjudicado `GSDLC-02-D CLOSED/PASS`;
- `DEVPL_GSDLC_02_D_FINAL_OWNER_ADJUDICATION_v1_0_0.md` y `.json` como autoridad de entrada de 02-E;
- `repo_DevPilot_Local_353_DEVPL_GSDLC_01_E_PROJECT_STATUS_BACKLOG_CLOSURE.zip` únicamente como baseline histórico inicial de la ola;
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


## 2. Experiencia UI requerida

Implementar o cerrar:

- `FirstRunOwnerView`;
- `LoginView`;
- logout;
- session-expired;
- session-revoked;
- persistent identity/role banner;
- Account/Role view;
- protected route guard;
- redirect al login cuando no hay human-session;
- Approval Center con autoridad derivada de sesión.

La experiencia debe ser coherente con Project Status y las rutas UOC actuales.

## 3. Journey normal

```text
first install
→ bootstrap owner
→ login
→ authenticated Project Shell
→ role/capability visible
→ Project Status
→ Approval Center / operations governed by RBAC
→ logout / expiry / revoke → login
```

Después del first-run, no debe existir una ruta normal que permita entrar anónimamente al Project Shell.

## 4. UX/security states

Como mínimo:

- first-run;
- login idle;
- invalid credentials;
- authenticated owner;
- authenticated developer;
- reviewer role(s) según matriz;
- unauthorized/forbidden;
- session expired;
- session revoked;
- logout;
- CSRF failure;
- API unavailable;
- rate/lock feedback local apropiado;
- unknown/corrupted auth state fail-closed.

Password, credential hashes, session cookie, CSRF secret y tokens nunca son visibles.

## 5. Browser acceptance real

Usar por defecto **tres consolas**:

1. General/control;
2. API foreground;
3. UI/Vite foreground.

No usar una única consola que deba mantener API/UI y aceptar comandos interactivos.

Generar screenshots full-page sanitizados, como mínimo:

1. first-run owner;
2. login;
3. owner authenticated shell con rol visible;
4. developer con capability sensible denegada;
5. security-reviewer/qa-reviewer conforme matriz;
6. direct protected URL without session → login;
7. expired session;
8. revoked session;
9. logout redirect;
10. Approval Center authority/deny.

Agregar:

- scenario metadata;
- state/API/UI parity;
- role_access_browser_matrix.json;
- accessibility result;
- browser console summary;
- sanitized HAR summary sin headers/cookies/token;
- screenshot hash manifest;
- secret scan.

No aceptar únicamente fixtures DOM.

## 6. Tests antes de la full regression

Orden obligatorio:

1. auth/session schemas/unit;
2. RBAC matrix;
3. approval binding negatives;
4. API auth contract;
5. frontend auth tests;
6. npm build;
7. Project State / Docs Governance / TCR;
8. Test Impact;
9. browser acceptance real;
10. historical contract sweep;
11. **full regression exactamente una vez**;
12. review/package/publish.

## 7. Full regression de cierre

La única full regression del backlog se ejecuta aquí.

Crear marker durable **antes** de lanzar `python -m pytest -q`.

Si PASS:
- continuar cierre.

Si FAIL:
- conservar log original inmutable;
- no repetir `pytest -q`;
- clasificar residuals;
- corregir causas;
- exact residual retest;
- bounded impacted retest;
- Historical Regression Guard con evidencia compuesta;
- `validation_mode=composite-full-regression-selective-retest`.


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


## 8. Historical contracts

Especial atención a:

- ADR-POSTH-034-D: historical `continue-blocked`;
- ADR-GSDLC-003: historical planning boundary;
- POST-H-012 evidence;
- legacy identity roles/aliases;
- GSDLC-01 actor-neutral Project Status;
- local API token compatibility;
- UOC route history.

Crear successors; no reescribir snapshots para fingir que login/sessions siempre existieron.

## 9. PASS / BLOCK

CLOSED/PASS candidate solo si:

- first-run owner controlado;
- login obligatorio después del first-run;
- sesión revocable;
- roles visibles;
- server-side RBAC;
- approval actor no spoofable;
- direct URL bypass bloqueado;
- CSRF/session negatives PASS;
- browser role matrix PASS;
- no credential/session secret en evidence;
- full regression/composite evidence válida;
- S0=0, S1=0;
- pilot preservado.

BLOCK ante route bypass, credential leak, stale/revoked session autorizando, role bypass, actor spoof, segunda full regression o habilitación enterprise/remote.

## 10. Cierre y autorización

Tras owner adjudication `CLOSED/PASS` de E y del backlog GSDLC-02:

- generar baseline canónico sucesor;
- actualizar autoridad sucesora sin destruir snapshots históricos;
- autorizar GSDLC-03.

Feature: `feat/devpl-gsdlc-02-e-login-browser-closure`

Commit: `feat(gsdlc-02-e): close authenticated local operator journey`


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
