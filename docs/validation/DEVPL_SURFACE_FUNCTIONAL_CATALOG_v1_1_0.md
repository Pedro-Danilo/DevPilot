---
doc_id: "DEVPL-SURFACE-FUNCTIONAL-CATALOG"
title: "DevPilot Local — Catálogo incremental de fichas funcionales de superficies"
status: "reviewed"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-22"
approval: "working-catalog/source-grounded"
active_authority: "repo437/d9d120c26a0e38487d353bd8715d5b1935f7fa6b"
execution_program: "DEVPL-GSDLC-13"
---

# Catálogo incremental de fichas funcionales de superficies — DevPilot Local

## 1. Propósito

Mantener una explicación verificable de **cada superficie de DevPilot observada durante el piloto**, cubriendo:

- objetivo de usuario;
- subsistema/backend real;
- autoridad y RBAC;
- estado que consulta;
- qué puede mutar;
- qué no debe mutar;
- persistencia y security boundary;
- límites/preliminary capabilities;
- riesgos UX/funcionales;
- recomendaciones.

Este documento se actualiza paulatinamente. No sustituye ADRs, contratos de API ni Run Cards.

## 2. Método

Una ficha solo se declara `OBSERVED` cuando existe evidencia UI del piloto. Las superficies relacionadas que se conocen por source pero no se han usado todavía se documentan como `RELATED-NOT-YET-ACCEPTED`.

---

## FICHA-001 — Login

- Estado: `OBSERVED / 13-B-01`.
- Surface/route: Login local.
- Objetivo: autenticar una identidad humana local existente antes de acceder al shell de producto.

### Subsistema debajo

- Web UI consulta bootstrap/session status.
- Identity/session runtime crea `AuthenticatedPrincipal` desde una human-session verificada.
- Credential/session state vive en store runtime local y no en browser localStorage.
- API aplica CORS/origin/CSRF y server-side authority.

### Autoridad

- El browser no decide roles.
- Roles/scopes provienen del principal resuelto por sesión server-side.
- `legacy-local-token` no representa una identidad humana con autoridad de approval.

### Qué muta

- Login válido crea/rota sesión y cookies de sesión/CSRF según contrato.
- Logout/revoke invalidan sesión.

### Qué no muta

- No cambia roles ni workspace scopes.
- No crea proyectos.
- No crea usuarios adicionales.
- No debe persistir password, raw session token o raw CSRF token.

### Límites

- Capability `local.operator_auth` sigue siendo local-only y más estrecha que IAM enterprise.
- Multiuser enterprise/SSO/OIDC/remote login permanecen fuera del boundary vigente.

### Recomendaciones

- Branding DevPilot visible.
- Copy orientado a tarea; seguridad técnica bajo disclosure.
- No añadir `Crear usuario` hasta existir lifecycle gobernado de identidades adicionales.

### Fuente principal

`LoginView.ts`, `local_identity_session_contract.md`, `rbac_role_workspace_semantics.md`, `ADR-GSDLC-005-local-operator-auth-enablement.md`.

---

## FICHA-002 — Project Home

- Estado: `OBSERVED / 13-B-01`.
- Objetivo: presentar el estado de entrada al producto y permitir elegir crear, abrir, importar o retomar contexto.

### Subsistema debajo

- `ProjectHomeEntryPanel.ts` representa las entradas de proyecto.
- El journey browser conserva metadata de navegación/resume en sessionStorage, pero esa metadata no es authority del proyecto.
- La autoridad real de workspace/proyecto proviene de los servicios/context resolver y `.devpilot/project.yaml` cuando existe proyecto activo.

### Autoridad

- Home es affordance/navigation; no debe inventar authority.
- La opción `Retomar` debe reconciliarse con contexto server-authoritative/recoverable.

### Qué muta

- Los clics de entrada pueden actualizar estado de journey del browser/navegación.

### Qué no muta

- Home por sí sola no debe materializar workspace, Git ni artifacts del proyecto.

### Límites

- Actualmente el CTA de `Retomar proyecto activo` puede aparecer con semántica insuficientemente vinculada al estado visible de un proyecto recuperable.

### Recomendaciones

- Diferenciar `Abrir existente` de `Retomar activo` con estado y project identity explícitos.
- Ocultar/inhabilitar Retomar cuando no exista contexto recuperable o mostrar exactamente qué se retomará.
- Sustituir labels internos tipo `GSDLC-03-E` por lenguaje de producto en Guided.

### Fuente principal

`ProjectHomeEntryPanel.ts`, `UiWorkspaceContextResolver`, evidence `02_home_authenticated.png`.

---

## FICHA-003 — Global → Cuenta / Roles

- Estado: `OBSERVED / supplemental 13-B-01`.
- Objetivo: mostrar identidad autenticada, roles efectivos, workspace scopes, método de auth y capabilities derivadas.

### Subsistema debajo

- Session principal server-side.
- Endpoint de capabilities/RBAC.
- UI `AccountRoleView.ts`.

### Autoridad

- Vista de solo lectura; no es fuente de autoridad.
- Roles/scopes son derivados por servidor.

### Qué muta

- Ninguna mutación de role/scope desde esta superficie en el contrato actual.

### Qué no muta

- No asigna/revoca roles.
- No crea/desactiva identidades.
- No modifica workspace scope.

### Límites

- No existe role self-service endpoint.
- Identity Administration multi-operador no está implementado.

### Recomendaciones

- Guided: resumen semántico de permisos y scopes.
- Expert: JSON/capabilities detalladas.
- Evolución futura de Identity Administration requiere ADR/backlog/security scope propio.

### Fuente principal

`AccountRoleView.ts`, `rbac_role_workspace_semantics.md`, ADR local operator auth.

---

## FICHA-004 — Global → Configuración

- Estado: `OBSERVED / supplemental 13-B-01`.
- Objetivo declarado por UI: configuración local en modo lectura y planificación.

### Subsistemas debajo

La página agrega múltiples dominios:

- workspace settings/context;
- policy;
- provider registry/configuration projection;
- security posture;
- Model Gateway;
- external-provider enablement runtime;
- Agent Runtime;
- RAG context;
- agent execution/evals/traces;
- portfolio/otros estados operacionales.

### Autoridad y persistencia

No existe una única semántica de escritura:

1. `workspace()/providers()/policy()` exponen proyecciones read-only/plan-only.
2. Provider editor genera un plan y declara que no escribe el archivo local ni activa APIs externas.
3. External-provider enablement posee workflows separados, owner/approval-gated cuando aplican, y estado runtime.
4. `disable/revoke` sí pueden mutar estado runtime gobernado y auditado.
5. Guided/Expert mode se persiste como preferencia browser-local y no altera RBAC/authority.

### Qué muta

- Determinados controles runtime, por ejemplo disable/revoke de provider habilitado.
- Acciones controladas según contratos específicos.

### Qué no muta

- El editor plan-only de providers no escribe por sí mismo `.devpilot/providers.yaml`.
- Las proyecciones workspace/policy históricas no son un editor general persistente.
- No debe activar external API accidentalmente.

### ¿Dónde están hoy los defaults/configuración?

La autoridad está distribuida:

- project/workspace: `.devpilot/project.yaml`;
- policy: `.devpilot/policy.yaml`;
- provider config: `.devpilot/providers.yaml`/contrato equivalente y runtime enablement separado;
- UX mode Guided/Expert: browser localStorage;
- diversos defaults de bootstrap y runtime permanecen en contratos/código y no son configurables desde una única superficie.

### Evaluación profesional

Una superficie `Configuración` debería ser el centro de **opciones que gobiernan comportamiento**, pero debe diferenciar claramente:

- global persistent config;
- project config;
- security/policy;
- runtime controls;
- diagnostics/observability.

Mezclarlos sin labels de scope/persistencia/authority degrada el modelo mental aunque el backend siga seguro.

### Recomendaciones

- Diseñar Configuration Ownership Model versionado.
- Para cada control: scope, current value, source, persistence target, authority, effect, approval, restart, reversibility.
- Separar o agrupar explícitamente `Configuración`, `Políticas`, `Runtime` y `Diagnóstico`.
- Guided debe comenzar por `readiness para empezar`; Expert conserva detalle técnico.

### Fuente principal

`SettingsView.ts`, `settings_service.py`, settings API routes, ModelSettingsView.

---

## FICHA-005 — Global → Ayuda

- Estado: `OBSERVED / supplemental 13-B-01`.
- Objetivo: soporte contextual, diferencias Guided/Expert, recuperación/errores/glosario y orientación.

### Subsistema debajo

- `HelpSystemView.ts` y contenido de ayuda UI.
- La preferencia Guided/Expert se gestiona separadamente mediante `experienceMode.ts`.

### Autoridad

- Ayuda es informativa; no debe ser authority técnica ni modificar permisos.

### Qué muta

- La navegación y, si se usa el selector de experiencia desde otras superficies, la preferencia local del browser.

### Qué no muta

- No cambia RBAC, policy, modelos, providers, project state ni approvals.

### Límites

- La ayuda no debe convertirse en requisito para descubrir acciones fundamentales que deberían ser autoexplicativas en Guided.

### Recomendaciones

- Mantener ayuda contextual y searchable.
- Enlazar desde conceptos técnicos específicos con progressive disclosure.
- Evitar duplicar contratos técnicos completos dentro de la UI.

### Fuente principal

`HelpSystemView.ts`, `experienceMode.ts`, evidence `03_home_entry_options_ayuda.png`.

---

## FICHA-006 — First Run / bootstrap del primer Owner

- Estado: `RELATED-NOT-YET-ACCEPTED` en 13-B-01 porque la instalación ya tenía Owner.
- Objetivo: crear una sola vez la identidad Owner inicial en una instalación local sin identidades.
- Authority: bootstrap server-side consumible una vez; no puede reabrirse solo borrando cookies.
- Mutación: identity/credential store local gobernado.
- No muta: no crea proyecto; no es mecanismo general de alta de usuarios.
- Límite: owner recovery debe ser separado, auditado y fail-closed.
- Recomendación: si en el futuro se soportan operadores adicionales, separar claramente `First Run Owner Bootstrap` de `Identity Administration`.

---

## Superficies siguientes previstas

Al avanzar B-02 se deberán añadir, como mínimo:

- Crear/Abrir/Importar — Project Entry;
- Dry-run / effects review;
- Approval Center aplicado a bootstrap;
- Bootstrap execution/result.

B-03 añadirá:

- Project Status;
- recovery/resume tras restart.

## PASS/BLOCK documental

PASS si cada ficha diferencia UI de authority, mutations de reads, y contrato actual de recomendación futura.

BLOCK si una ficha atribuye a la UI autoridad que reside en backend, afirma write donde el contrato es plan-only, o confunde una capability futura con funcionalidad implementada.

## Riesgos

- Staleness: actualizar `active_authority` al cambiar de repo successor.
- No convertir este catálogo en una segunda fuente de verdad contractual; siempre prevalecen code/ADR/contracts vigentes.
- Toda recomendación futura debe entrar por backlog/ADR/corrective apropiado antes de source mutation.

## Comandos de verificación

No introduce comandos propios. Cada ficha se valida durante el Run Card correspondiente y contra la autoridad técnica vigente.


## FICHA-007 — Crear proyecto / Project Entry

- Estado: `OBSERVED / 13-B-02-00 / BLOCK`.
- Objetivo: crear/abrir/importar proyectos mediante intake tipado, dry-run, revalidación, approval y ejecución gobernada.

### Subsistemas debajo

- UI: `ProjectEntryDryRunView.ts`.
- Contrato: `ProjectEntryContractService` / `ProjectIntake`.
- Discovery/planning: `EnvironmentDiscoveryService`.
- Dry-run/preimage: `ProjectEntryDryRunService`.
- Approval/RBAC: human-session owner + Approval Center + policy.
- Mutación: `ProjectBootstrapExecutor`.

### Autoridad

La UI recoge inputs, pero el backend revalida path, intake, plan/preimage, approval y policy. El browser no es authority de ejecución.

### Evidencia 13-B-02-00

La superficie repo437 solo expuso Modo, Project ID, Nombre y Ruta target. No permitió capturar la necesidad ni confirmar constraints/model policy. Source audit confirmó que CREATE_NEW inyectaba React/FastAPI/SQLite y restricciones/provider sin decisión del Owner.

### Qué debe mutar después del corrective

B-02 puede crear un **Project Shell neutral**: directorio autorizado, Git local, `.devpilot/project.yaml`, registro de workspace, bootstrap evidence y documentación neutral.

### Qué no debe mutar en B-02

- No frontend/backend preseleccionados.
- No `.venv`.
- No `package.json` / `requirements.txt`.
- No dependency install ni dependency jobs.
- No red/API externa.
- No decisión de tecnología antes de Architecture.

### Contexto persistido

Debe incluir business need inicial, `technology_decision_status=deferred-to-architecture`, model policy y project constraints para que 13-C tenga un seed trazable.

### Prompt/model boundary

`business_need` no es un prompt libre ni concede authority. DevPilot puede transformarlo más adelante mediante prompts versionados (`PromptRegistry`) y `prompt_inputs`; las tools continúan gobernadas separadamente.

### Recomendación

Tras Requirements/Architecture, un agente/servicio de Technology Decision puede comparar perfiles soportados y presentar recomendaciones con rationale/trade-offs. El Owner aprueba la decisión; luego un Technical Scaffold separado materializa stack/manifests/dependencias con plan/dry-run/approval.

### Fuente principal

`ProjectEntryDryRunView.ts`, `project_entry_contracts.py`, `environment_discovery.py`, `project_bootstrap_execution.py`, ADR `ADR-DEVPL-GSDLC-13-B-02-neutral-project-shell-before-architecture.md`, evidencia `01_create_project_entry.png`.

## FICHA-008 — Dry-run / effects review

- Estado: `RELATED-NOT-YET-ACCEPTED` en 13-B-02-00 porque el checkpoint se detuvo antes de generar el dry-run.
- Objetivo: presentar plan hash, preimage, efectos, network, writes y approval preview antes de cualquier mutación.
- Próxima aceptación: retest 13-B-02 después del corrective; debe mostrar business need/policies y confirmar que el plan neutral no contiene `.venv`, frontend/backend ni dependency jobs.
