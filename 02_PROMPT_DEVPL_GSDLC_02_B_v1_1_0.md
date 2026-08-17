---
doc_id: "DEVPL-PROMPT-GSDLC-02-B"
prompt_number: "02"
title: "Prompt operativo — DEVPL-GSDLC-02-B — Identity store, credentials and session lifecycle"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-02"
micro_sprint: "DEVPL-GSDLC-02-B"
execution_rule: "solo este micro-sprint; 02-C bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
source_repo: "repo_DevPilot_Local_354_DEVPL_GSDLC_02_A_AUTH_THREAT_BOUNDARY.zip"
source_git_commit: "6f338a25b5463742576c82aa7dbee958fbca8587"
source_repo_sha256: "17f193313ee186478c1b39bd168aecd94481c636e6b3070478a74d874efde95d"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_backlog: "DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md"
local_first: true
dry_run_default: true
external_api_required: false
external_network_required: false
pilot_workspace_mutation_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-02-B

## Rebind de autoridad 02-B

Autoridad ejecutable:

```text
repo: repo_DevPilot_Local_354_DEVPL_GSDLC_02_A_AUTH_THREAT_BOUNDARY.zip
commit: 6f338a25b5463742576c82aa7dbee958fbca8587
SHA-256: 17f193313ee186478c1b39bd168aecd94481c636e6b3070478a74d874efde95d
predecessor owner adjudication MD SHA-256: 8bcc098f97566f4d186281aae0a6b6f2a9711a3737da7416b48fd62c21d92449
predecessor owner adjudication JSON SHA-256: c89bcb9abe04faa96cb59d45f69f70ac55f611eb3628d8c492c516af267e0471
```

La implementación debe usar identidad canónica Git blob/archive para comparar fuentes versionadas; working-tree CRLF/LF es diagnóstico, no autoridad.


## 1. Mandato

Implementa **solo** `GSDLC-02-B — Identity store, credentials and session lifecycle` sobre 02-A `CLOSED/PASS`.

La autoridad debe rebinderse al baseline canónico generado por 02-A. Repo353 queda como design/base ancestor, no sustituye al predecesor cerrado.


## Fuentes obligatorias de autoridad

Antes de proyectar cualquier cambio, consultar literalmente como mínimo:

- `repo_DevPilot_Local_354_DEVPL_GSDLC_02_A_AUTH_THREAT_BOUNDARY.zip` como baseline canónico de ejecución de 02-B;
- repo353 se conserva únicamente como ancestor/design context;
- `DEVPL_GSDLC_02_A_FINAL_OWNER_ADJUDICATION_v1_0_0.md` como autoridad `CLOSED/PASS` del predecesor;
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


## 2. Contratos de identidad

Implementar tipos separados:

- `AuthenticatedPrincipal`;
- `LocalIdentity`;
- `CredentialRecord`;
- `SessionRecord`;
- `SessionContext`;
- `SessionRevocation`.

Nunca reutilizar un `actor_id` del request como principal.

## 3. Credential store

Antes de persistir credenciales, emitir decisión técnica KDF:

- preferencia: Argon2id cuando se adopte una dependencia explícita y validada;
- alternativa sin nueva dependencia: `hashlib.scrypt` con parámetros versionados y salt aleatorio;
- nunca SHA simple, password reversible o plaintext.

El credential/session runtime store:

- queda fuera de Git;
- queda fuera de repo ZIP y evidence;
- tiene schema/version/migration;
- soporta restart recovery;
- aplica atomic/transactional update cuando corresponda.

No introducir una dependencia nueva silenciosamente: documentar costo, licencia, plataforma y rollback.

## 4. First-run bootstrap y sesiones

Implementar server-side:

- detectar instalación sin owner;
- bootstrap del primer owner exactamente una vez;
- login;
- session create;
- rotation;
- idle timeout;
- absolute timeout;
- revoke;
- logout;
- session inspect;
- audit trail sanitizado.

Definir endpoints/API contract necesarios, pero **no implementar todavía la experiencia UI completa de login**; pertenece a E.

## 5. Transporte browser y CSRF

Definir e implementar una estrategia coherente:

- cookie de sesión HttpOnly;
- Secure cuando el transporte lo permita; documentar localhost HTTP development semantics;
- SameSite apropiado;
- CSRF token/origin strategy para mutaciones;
- CORS local-only;
- session fixation prevention;
- token rotation tras login/privilege change.

El browser no debe guardar password/session secret en `localStorage` o `sessionStorage`.

## 6. Compatibilidad con token local

El token local heredado puede mantenerse solo como compatibility principal acotado.

Debe demostrarse:

- no representa una identidad humana;
- no puede aprobar;
- no puede autoasignarse roles;
- no puede omitir la sesión en endpoints que GSDLC-02 marque `human-session-required`.

## 7. Tests obligatorios

- valid/invalid credentials;
- duplicate first-run bootstrap negative;
- KDF verify/migration metadata;
- expired/revoked/rotated session;
- idle/absolute timeout;
- restart recovery;
- fixation negative;
- CSRF negative;
- CORS non-local negative;
- secret/log/evidence redaction;
- corrupted store behavior fail-closed;
- legacy-token human-authority negative;
- A+B cumulative regression.


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


Para 02-B: **full regression = NO** salvo hard trigger owner-approved previo.


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


## 8. Evidencia mínima

- `auth_session_test_report.json`;
- `session_lifecycle_matrix.md/json`;
- credential KDF decision;
- first-run bootstrap evidence sanitizada;
- secret scan report;
- runtime store exclusion proof.

## 9. PASS / BLOCK

PASS-CANDIDATE si:

- login solo con credencial válida;
- raw password nunca persiste/loguea;
- revoke invalida inmediatamente;
- restart recovery definido/probado;
- session authority server-side;
- legacy token no puede actuar como humano;
- S0/S1=0.

BLOCK ante plaintext/reversible password, session secret en evidence, revoked session autorizando, first-run repetible o remote/public auth.

## 10. Git

Feature: `feat/devpl-gsdlc-02-b-local-identity-sessions`

Commit: `feat(gsdlc-02-b): add local identity and revocable sessions`


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
