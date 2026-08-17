---
doc_id: "ADR-GSDLC-005"
title: "ADR-GSDLC-005 — Local operator authentication bounded runtime enablement"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "pending_owner_gsdlc_02_a_adjudication"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-02"
micro_sprint: "DEVPL-GSDLC-02-A"
runtime_implemented: false
runtime_enabled: false
remote_login_enabled: false
public_api_enabled: false
enterprise_iam_enabled: false
tenancy_enabled: false
---

# ADR-GSDLC-005 — Local operator authentication bounded runtime enablement

## Contexto

Repo353 cierra GSDLC-01 con Project Status actor-neutral. El baseline ya contiene un `identity_registry.json` metadata-only, RBAC inicial, token de API local y StrongApprovalBinding. Esos controles no constituyen una sesión humana autenticada. `ADR-POSTH-034-D` mantiene correctamente `multiuser.auth=continue-blocked`, y `ADR-GSDLC-003` diseñó el successor local-only sin implementarlo.

GSDLC-02 necesita introducir identidad humana autenticada para que RBAC y approvals no confíen en un `actor_id` suministrado por el cliente, pero debe conservar el producto single-installation/local-first y bloquear enterprise IAM, tenancy, SSO/OIDC y acceso remoto.

## Decisión

Diseñar y habilitar **solo como contrato**, no como runtime en 02-A, la capability sucesora `local.operator_auth`.

### Trust boundary

```text
single DevPilot installation
+ loopback API/UI
+ local human operator
→ human-session principal
→ server-derived roles/workspace scopes
→ RBAC
→ approval authority
```

No forma parte del boundary:

- remote login;
- public API;
- enterprise IAM;
- OIDC/SSO;
- tenancy;
- federation;
- cloud identity synchronization.

### Principal taxonomy

1. `human-session`: único principal humano autoritativo para decisiones identity-bound.
2. `legacy-local-token`: compatibilidad local acotada. No representa una persona y no puede autorizar approvals identity-bound ni escalar roles.
3. `agent/service-principal`: principal no humano; no hereda autoridad humana ni approval rights salvo contrato posterior explícito.

Unknown principal, unknown role, unknown action o scope ausente ⇒ `DENY`.

## First-run owner

El primer owner se crea una sola vez durante bootstrap gobernado en 02-B. Debe existir evidencia durable de que el bootstrap quedó consumido. No puede reabrirse por simple borrado de cookie/UI state. Recovery del owner requiere mecanismo separado, auditado y fail-closed.

## Credential strategy

02-B debe tomar una decisión versionada entre:

- Argon2id con dependencia explícita, auditada y compatible con Windows; o
- `hashlib.scrypt` con parámetros versionados y salt criptográficamente aleatorio como ruta sin nueva dependencia.

Quedan prohibidos plaintext, password reversible, hash rápido simple y cualquier credencial en Git/log/evidence.

## Session contract

La sesión objetivo será opaca, emitida por servidor y ligada a `actor_id`, roles efectivos, workspace scopes y timestamps de seguridad. Debe soportar:

- create;
- rotate;
- idle timeout;
- absolute timeout;
- revoke;
- logout;
- restart recovery gobernado;
- reevaluación/invalidation ante role change.

Para browser, el secreto de sesión no se almacena en localStorage/sessionStorage. Mutaciones requieren estrategia CSRF explícita. CORS se mantiene local-only. Login debe rotar session identity para impedir fixation.

## Approval actor binding

```text
request
→ authenticated session
→ AuthenticatedPrincipal
→ server-side effective roles/scopes
→ RBAC
→ approval policy
→ AuthenticatedApprovalBinding
```

El request puede transportar un campo `actor` legado únicamente como dato no autoritativo/deprecado. Nunca puede sustituir al principal autenticado.

## Role model y migración

La matriz canónica de 02-A define nueve roles: owner, product-owner, architect, security-reviewer, developer, qa-reviewer, release-manager, operator y agent-supervisor.

El baseline histórico usa `reviewer`, y el sensitive action catalog referencia además `maintainer` para tres acciones críticas bloqueadas. No se hace rename silencioso:

- `reviewer` → candidato `qa-reviewer`, sujeto a validación de permisos;
- `maintainer` → `NO_DIRECT_MAPPING` mientras patch/refactor/delete permanezcan bloqueados; 02-C debe asignar cada acción a una autoridad canónica explícita antes de habilitarla.

## Separation of duties

- no role self-escalation;
- cambio de roles requiere autoridad separada y revoca/reevalúa sesiones;
- critical approvals no pueden quedar autorizados por wildcard no acotado;
- por defecto el requester no decide su propia acción critical; excepciones de recovery requieren política explícita y evidencia;
- workspace scope se valida server-side.

## Threat controls

La autoridad threat→control→test está en `.devpilot/identity/auth_threat_matrix.json`. Todos los controles de 02-A son `DESIGNED`; ninguno se declara runtime-enforced antes de B/C/D/E.

## Audit y redaction

Eventos de auth futuros registran actor estable, event type, timestamps, outcome y reason codes, nunca password, verifier material, session token, cookie o CSRF secret. Evidence debe usar identificadores sintéticos/redactados.

## Restart semantics

Credential/identity/session stores serán RuntimeOperationalState/local durable stores fuera de source ZIP. Restart no debe reactivar una sesión revocada ni reabrir first-run. Store corrupto/tampered ⇒ fail-closed + recovery explícito.

## Consecuencias

- 02-A no agrega endpoints, UI, credenciales ni sesiones.
- 02-B puede implementar identidad/credential/session lifecycle bajo este boundary.
- 02-C puede convertir role/action matrices en enforcement real.
- 02-D puede eliminar actor spoofing en approvals.
- 02-E puede cerrar login/browser journey.

## Preservación histórica

`ADR-POSTH-034-D` permanece `continue-blocked` para multiuser/enterprise auth. `ADR-GSDLC-003` permanece como design predecessor. Este ADR es successor; no los reescribe.

## PASS/BLOCK

PASS de 02-A requiere threat coverage 100%, role authority completa, migration map explícito, runtime auth=false y no-go enterprise/remoto=false.

BLOCK si login/session runtime aparece antes de 02-B, legacy token adquiere autoridad humana, se habilita remote/public auth, o una acción crítica obtiene autoridad mediante un rol no definido.
