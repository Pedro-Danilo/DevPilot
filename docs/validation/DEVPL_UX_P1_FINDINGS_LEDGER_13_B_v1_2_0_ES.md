---
doc_id: "DEVPL-UX-P1-FINDINGS-LEDGER-13-B"
title: "DEVPL-UX-P1 — Registro de hallazgos del piloto — 13-B"
status: "reviewed"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-09-22"
approval: "working-ledger/not-source-authority"
execution_program: "DEVPL-GSDLC-13"
source_template: "docs/validation/DEVPL_UX_P1_FINDINGS_LEDGER_TEMPLATE_v1_1_0.md"
source_backlog: "docs/backlogs/DEVPL_UX_P1_FRONTEND_IMPROVEMENT_BACKLOG_v1_1_0_APPROVED.md"
language: "es"
---

# DEVPL-UX-P1 — Registro de hallazgos — 13-B

## 1. Regla operativa

Este artefacto es incremental y `OBSERVE_ONLY`. No modifica el source de DevPilot y no autoriza por sí mismo un corrective.

Clasificación:

- `UX`: presentación, copy, jerarquía, discoverability, densidad de información o arquitectura de información.
- `FUNCTIONAL_BUG`: violación reproducible de un contrato implementado; pausa el checkpoint y puede activar `ACTIVE-CORRECTIVE`.
- `CAPABILITY_GAP`: comportamiento deseable que el contrato vigente no promete/implementa; requiere backlog/ADR/alcance explícito y no debe disfrazarse de bug.
- `ARCHITECTURE_GAP`: responsabilidad o boundary de producto incoherente/insuficientemente gobernado que requiere diseño antes de implementación.

Política UX-P1 vigente:

- UX-S0: BLOCK inmediato + corrective obligatorio.
- UX-S1: BLOCK del checkpoint + corrective obligatorio.
- UX-S2: corrective antes de cerrar segmento solo si afecta critical path; en otro caso decisión del Owner.
- UX-S3: registrar y diferir por defecto, salvo cambio trivial/bajo riesgo.

---

## UX-P1-02-B01-001 — Login: identidad visual y copy excesivamente técnico

- Checkpoint: `13-B-01`.
- Superficie: Login.
- Clasificación: `UX`.
- First-attempt: PASS.
- Observación: la pantalla es operacional y focalizada, pero no presenta una identidad visual clara de DevPilot y prioriza copy técnico (`cookie HttpOnly + CSRF`, `Project Shell`) sobre lenguaje orientado a la tarea.
- Resultado esperado: identificar inmediatamente el producto, comprender qué credencial se solicita y qué ocurrirá después del login sin necesitar vocabulario de implementación web.
- Impacto: bajo/moderado; no produjo wrong path ni bloqueo.
- Severidad: `S3`.
- Owner metric relevante: critical task completo; `owner_confidence=4/5` global; `confused_moments=0` en la tarea.
- Evidencia: `01_auth_entry.png`; `ui/web/src/pages/LoginView.ts`.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY`.
- Recomendación futura: branding DevPilot; copy user-centered; detalles de seguridad detrás de progressive disclosure/Ayuda/Expert; sustituir `Project Shell` por lenguaje de tarea.
- Corrective activo: no.

---

## UX-P1-02-B01-002 — Home: semántica `Retomar proyecto activo` vs `Abrir proyecto existente`

- Checkpoint: `13-B-01`.
- Superficie: Project Home.
- Clasificación: `UX`.
- First-attempt: PASS.
- Observación: `Crear nuevo proyecto` es inequívocamente primario y Home explica crear/abrir/importar. Sin embargo, también muestra `¿Ya estabas trabajando en un proyecto?` + `Retomar proyecto activo →` aunque en B-01 no existía el greenfield y el Owner señaló que la diferencia frente a `Abrir proyecto existente` no era evidente.
- Resultado esperado: distinguir con lenguaje inequívoco:
  - abrir un workspace existente elegido por el usuario;
  - retomar el proyecto/contexto que DevPilot ya tiene autoritativamente activo/recuperable.
- Impacto: ambigüedad semántica real, sin desviar el critical path; el Owner identificó la siguiente acción en ~10 s.
- Severidad: `S2`, no bloqueante en B-01.
- Evidencia: `02_home_authenticated.png`; `ui/web/src/components/ProjectHomeEntryPanel.ts`; nota cualitativa del Owner.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY`; volver a medir en `13-B-03`, donde resume/recovery será funcionalmente relevante.
- Recomendación futura: mostrar `Retomar` solo cuando exista contexto recuperable autoritativo o explicar explícitamente qué proyecto se retomará; diferenciar semántica y estado respecto de `Abrir existente`.
- Corrective activo: no.

---

## UX-P1-02-B01-003 — Cuenta/Roles: payload técnico crudo en modo Guided

- Checkpoint: `13-B-01` (evidencia suplementaria).
- Superficie: Global → Cuenta / Roles.
- Clasificación: `UX`.
- Observación: los datos humanos de identidad/roles/scopes son comprensibles, pero la misma vista expone un payload JSON amplio de capabilities incluso en Guided mode.
- Resultado esperado: Guided debe explicar autoridad efectiva por grupos de capacidad y razones de permit/deny; el JSON route-level debe quedar como detalle Expert/diagnóstico.
- Impacto: densidad cognitiva significativa para usuario beginner/medio; función correcta.
- Severidad: `S2`.
- Evidencia: `03_home_entry_options.png`; `ui/web/src/pages/AccountRoleView.ts`.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY`.
- Recomendación futura: cards/resumen de rol y scopes, capability groups y `¿Por qué puedo/no puedo hacer esto?`; JSON detrás de disclosure Expert.
- Corrective activo: no.

---

## UX-P1-02-B01-004 — Configuración: densidad y ausencia de jerarquía pre-proyecto

- Checkpoint: `13-B-01` (evidencia suplementaria).
- Superficie: Global → Configuración.
- Clasificación: `UX`.
- Observación: la vista concentra workspace/policy/security/providers/Model Gateway/Agent Runtime/RAG/skills-tools/evals/traces y otros estados en un scroll muy largo. No distingue suficientemente `necesario antes de comenzar`, `opcional`, `solo lectura`, `plan-only`, `acción runtime` y `diagnóstico`.
- Resultado esperado: un Owner debe poder responder rápidamente `¿DevPilot está listo para iniciar un proyecto?` y saber qué decisiones son obligatorias, opcionales o avanzadas.
- Impacto: moderado; el Owner explícitamente esperaba configurar opciones principales antes de crear el proyecto.
- Severidad: `S2`.
- Evidencia: `03_home_entry_options_configuracion.png`; `ui/web/src/pages/SettingsView.ts`; `src/devpilot_core/application/settings_service.py`.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY`.
- Recomendación futura: readiness/preflight Guided resumido, badges por scope/efecto/persistencia, progressive disclosure y separación de detalles Expert.
- Corrective activo: no.

---

## UX-P1-02-B01-005 — Home: exposición de identificador interno `GSDLC-03-E`

- Checkpoint: `13-B-01`.
- Superficie: Project Home.
- Clasificación: `UX`.
- Observación: el Owner reportó confusión por el título `GSDLC-03-E · inicio de proyecto`. Es un identificador de ingeniería/roadmap expuesto en la superficie normal del producto.
- Resultado esperado: Guided debe usar lenguaje estable del dominio de usuario; IDs de sprint/micro-sprint/contrato pueden conservarse como trazabilidad técnica en Expert/evidence.
- Impacto: bajo; no bloqueó la acción.
- Severidad: `S3`.
- Evidencia: `02_home_authenticated.png`; nota del Owner.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY`.
- Recomendación futura: reemplazar título visible por terminología de producto (`Inicio`, `Proyectos`, `Crear o abrir proyecto`) y conservar `GSDLC-03-E` solo en metadata/Expert.
- Corrective activo: no.

---

## UX-P1-02-B01-006 — Configuración: mezcla semántica de configuración, diagnóstico y controles runtime

- Checkpoint: `13-B-01` (source audit + evidencia suplementaria).
- Superficie: Global → Configuración.
- Clasificación: `UX` + señal de arquitectura de información.
- Observación: el encabezado afirma `Configuración local en modo lectura y planificación`, y el editor de provider es `plan-only`; sin embargo, la misma superficie también incluye evaluación controlada y controles `Deshabilitar runtime` / `Revocar referencia runtime` que sí mutan estado runtime gobernado. Además expone diagnósticos, runtime, RAG, evaluaciones y trazas.
- Resultado esperado: una superficie titulada `Configuración` debe dejar inequívoco qué valores gobiernan comportamiento persistente, qué acciones solo generan planes, qué elementos son estado/diagnóstico y qué controles realizan mutaciones runtime.
- Impacto: riesgo de modelo mental incorrecto y de acción equivocada en un área sensible.
- Severidad: `S2`.
- Evidencia: `03_home_entry_options_configuracion.png`; `SettingsView.ts`; `settings_service.py`; rutas settings de provider enablement/disable/revoke.
- Reproducible: sí.
- Disposición: `OBSERVE_ONLY` durante 13-B; requiere diseño antes de corrective visual aislado.
- Recomendación futura: separar por responsibility boundary: `Configuración persistente`, `Políticas`, `Runtime/kill switches`, `Diagnóstico/observabilidad`, o representar cada control con Scope + Persistence + Authority + Effect + Approval/Restart requirements.
- Corrective activo: no.

---

## CAP-13B01-AUTH-001 — Lifecycle gobernado de identidades humanas adicionales

- Checkpoint de descubrimiento: `13-B-01`.
- Superficies relacionadas: Login / First Run / Cuenta-Roles.
- Clasificación: `CAPABILITY_GAP` de producto/seguridad, no bug UX.
- Contrato vigente: DevPilot implementa autenticación local para una instalación, first-run owner único, human sessions, RBAC y nueve roles canónicos; el boundary enterprise/multiuser permanece deliberadamente bloqueado y no existe role self-service endpoint.
- Necesidad planteada: lifecycle explícito para crear/desactivar identidades, asignar/revocar roles y workspace scopes, reset/recovery de credenciales, session invalidation, auditoría y separation of duties.
- Evaluación: pertinente como evolución si DevPilot debe soportar varios operadores humanos reales. No debe resolverse agregando simplemente `Crear usuario` en Login.
- Riesgo de solución superficial: false affordance, escalación/autorización mal definida, sesiones stale, recovery no gobernado y ruptura del boundary local-first.
- Severidad UX: no aplica como S0-S3; prioridad de producto/security a decidir por Owner.
- Disposición: abrir futuro backlog/ADR específico de Identity Administration si el requisito multi-operador es aprobado.
- Corrective activo durante 13-B: no.

Requisitos mínimos de esa evolución futura:

1. identity CRUD gobernado, con desactivación preferida a borrado destructivo;
2. authority matrix para quién crea/desactiva/asigna roles;
3. role/scope assignment + revoke con invalidación atómica de sesiones;
4. credential reset/recovery separado y auditado;
5. workspace scopes y deny-by-default;
6. separation of duties para acciones sensibles;
7. audit trail sin secretos;
8. owner recovery fail-closed;
9. lifecycle de sesiones y revocación global/por identidad;
10. threat model + ADR + tests de escalación, CSRF, cross-workspace y recovery.

---

## CAP-13B01-SETTINGS-001 — Gobierno unificado de configuración persistente

- Checkpoint de descubrimiento: `13-B-01`.
- Superficie: Global → Configuración y contratos relacionados.
- Clasificación: `CAPABILITY_GAP / ARCHITECTURE_GAP`, no bug del contrato actual.
- Observación de source truth:
  - `.devpilot/project.yaml` es autoridad de configuración/contexto del workspace activo;
  - `.devpilot/policy.yaml` contiene policy local;
  - `.devpilot/providers.yaml`/example representa provider configuration;
  - el facade histórico de Settings proyecta workspace/policy/providers en read-only/plan-only;
  - external-provider enablement tiene un workflow gobernado propio y estados runtime mutables;
  - Guided/Expert preference se persiste en browser localStorage y no cambia authority/RBAC;
  - el bootstrap de proyecto actualmente incorpora varios defaults desde el intake/runtime, no desde una pantalla global única.
- Problema de producto: no existe hoy una experiencia unificada y semánticamente limpia desde la cual el Owner pueda consultar **y modificar**, con autoridad/persistencia explícitas, todos los defaults y preferencias del producto.
- Evaluación: es razonable que una superficie denominada `Configuración` sea el centro para opciones que determinan comportamiento global, pero no debe absorber estado operacional, evidencia, diagnósticos y kill switches sin separación conceptual.
- Disposición: mantener OBSERVE_ONLY durante 13-B y diseñar arquitectura de configuración antes de ampliar writes.
- Corrective activo: no.

Recomendación arquitectónica futura:

| Dominio | Ejemplos | Scope/Persistencia recomendada |
|---|---|---|
| Global persistent settings | experiencia, defaults seguros, providers locales habilitados, defaults de model policy | instalación DevPilot, schema/versionado |
| Security/Policy | CostGuard, external API policy, budgets, approvals | policy authority, approval-gated |
| Project settings | workspace, constraints, model policy del proyecto, stack/standards decididos | `.devpilot/project.yaml`/artefacto project-scoped gobernado |
| Runtime controls | disable/revoke provider, kill switches | runtime operational state + audit |
| Diagnostics/Observability | health, traces, evaluations, RAG status | read-only/operational |

Cada control futuro debería declarar visiblemente: `scope`, `authority`, `persistencia`, `default efectivo`, `origen`, `impacto`, `requiere approval`, `requiere restart` y `reversible`.

---

## RISK-13B02-INTAKE-001 — Verificación obligatoria en 13-B-02

- Clasificación: riesgo de acceptance, **todavía no bug adjudicado**.
- Source observation: la vista `ProjectEntryDryRunView.ts` visible en repo437 solicita mode, Project ID, nombre, target y Git source; su `buildIntake()` incorpora actualmente defaults para `project_type`, stack, standards, provider `none` y restricciones.
- Contrato B-02: el User Journey exige que el Owner pueda expresar idea de negocio y definir/confirmar ubicación, restricciones, tipo de aplicación, ejecución y model policy; el Pilot Brief exige que el stack se decida dentro del Guided SDLC, no por ChatGPT externo.
- Disposición: `13-B-02` debe probar la experiencia real sin compensarla externamente. Si la UI no ofrece una ruta normal para expresar/confirmar los inputs obligatorios y el sistema depende de hardcodes invisibles incompatibles con el contrato, detener B-02 y adjudicar con evidencia antes de corregir.

---

## Estado agregado después de 13-B-01

- UX-S0 abiertos: `0`.
- UX-S1 abiertos: `0`.
- UX-S2 OBSERVE_ONLY: `4` (`002`, `003`, `004`, `006`).
- UX-S3 OBSERVE_ONLY: `2` (`001`, `005`).
- Functional bugs demostrados: `0`.
- Capability/architecture gaps registrados: `2`.
- Riesgos explícitos a validar en B-02: `1`.
- Active corrective autorizado: `no`.
- Acceptance puede continuar a `13-B-02`: `sí`.

## PASS/BLOCK del ledger

PASS documental si cada hallazgo mantiene evidencia, clasificación y disposición y no se usa el ledger como autorización implícita de source mutation.

BLOCK documental si se reclasifica una preferencia estética como bug sin contrato, si un S0/S1 se difiere, o si se implementa capability nueva sin backlog/ADR/approval aplicable.

## Riesgos

- No mezclar UX polish con ampliación de seguridad/IAM.
- No convertir Settings en write-anything sin schemas, authority y approvals.
- No usar hallazgos source-audit para anticipar el resultado del acceptance B-02; deben comprobarse en journey real.

## Comandos de verificación

Este ledger no introduce comandos de ejecución. La verificación se realiza mediante los Run Cards/Run Packets del checkpoint correspondiente y lectura literal de repo authority.


## Actualización 13-B-02 — intento 00

## UX-P1-02-B02-001 — Project Entry no captura la necesidad de negocio

- Checkpoint: `13-B-02-00`.
- Superficie: Crear proyecto / Project Entry.
- Clasificación: `FUNCTIONAL_BUG` con impacto UX crítico.
- Evidencia: `01_create_project_entry.png` + source `ProjectEntryDryRunView.ts`.
- Contrato esperado: el Owner debe poder expresar la idea/necesidad antes de Vision, sin diseñar la solución.
- Observado: no existe campo para describir necesidad, problema, objetivo o contexto funcional.
- Importancia: la necesidad inicial es el input autoritativo del que 13-C debe derivar Vision/Scope/Requirements; puede evolucionar, pero no debe aparecer por inferencia posterior sin trazabilidad.
- Severidad: `S1` — bloquea `13-B-02`.
- Disposición: `ACTIVE-CORRECTIVE`.
- Corrective: `business_need` requerido (20..4000), persistido en Project Context y visible en dry-run; lenguaje orientado al problema, no al stack.

## UX-P1-02-B02-002 — Constraints y model policy no son definibles/confirmables

- Clasificación: `FUNCTIONAL_BUG`.
- Contrato esperado: ubicación + restricciones + tipo de aplicación/ejecución + model policy, con baseline local-first/mock-no-API.
- Observado: la UI solo muestra ID/nombre/path; los demás valores llegan hardcoded al intake.
- Severidad: `S1`.
- Disposición: `ACTIVE-CORRECTIVE`.
- Corrective: presentar y exigir confirmación comprensible de local-first, cloud no obligatorio, operator writes=0, no shell arbitrario/red silenciosa/remote Git execute, mock/no-API baseline, local model opt-in y external API solo approval/provenance.

## ARCH-13B02-001 — Stack y dependencias se vinculan antes de Architecture

- Clasificación: `ARCHITECTURE_GAP` + violación funcional del contrato GSDLC-13.
- Observado: repo437 construye CREATE_NEW con React+TypeScript/FastAPI+SQLite y, a partir de ese perfil, templates, `.venv` y dependency jobs. La red se difiere correctamente (`defer-network`), pero los manifests ya materializarían una decisión tecnológica prematura.
- Contrato esperado: el stack se decide dentro del Guided SDLC después de Requirements/Architecture, no por defaults invisibles ni por ChatGPT externo.
- Severidad: `S1` para el critical path greenfield.
- Disposición: `ACTIVE-CORRECTIVE`.
- Corrective: `greenfield-neutral-shell`, stack `undecided`, `technology_decision_status=deferred-to-architecture`, `venv_required=false`, `dependency_jobs=[]`; Technical Scaffold posterior approval-bound.

## UX-P1-02-B02-003 — Project Entry no explica la frontera Project Shell vs Technical Scaffold

- Clasificación: `UX`.
- Observado: el disclosure actual afirma que CREATE_NEW puede crear `.venv`, lo cual refuerza la percepción de que la tecnología ya está decidida.
- Resultado esperado: Guided debe explicar que B-02 crea autoridad/contexto neutral y que Architecture decidirá el stack antes de materializar runtimes/dependencias.
- Severidad: `S2`, absorbido por el corrective funcional.
- Disposición: `ACTIVE-CORRECTIVE` junto con F-13B02-003.

## CAP-13B02-TECH-001 — Recomendación gobernada de perfiles tecnológicos después de Architecture

- Clasificación: `CAPABILITY_GAP / product evolution`.
- Evaluación: pertinente. Una vez Requirements + Architecture definan atributos y restricciones, DevPilot debería poder producir 1..N perfiles soportados con rationale, trade-offs, compatibilidad, costos/operación y gaps; el Owner selecciona/aprueba.
- Regla: `TechnologyCatalog` es catálogo de capacidades soportadas, no oracle. Si solo existe un perfil viable, debe mostrarse como limitación del catálogo, no como recomendación inteligente.
- Materialización: una decisión aprobada dispara un Technical Scaffold gobernado con dry-run/approval, manifests, lock strategy, dependencias y provenance.
- Corrective actual: solo prepara el boundary (`technology_decision_status=deferred-to-architecture`); el recomendador pertenece a 13-C/P1 posterior, no se implementa subrepticiamente en B-02.

## CAP-13B02-PROMPT-001 — Entrada humana para modelos: inputs de dominio, no prompt universal

- Clasificación: `CAPABILITY/UX DESIGN`.
- Source truth: DevPilot ya tiene `PromptRegistry`, `prompt_inputs`, ModelApplicationService y `ArtifactAIPanel` con `Instrucción humana`; `AiOperationsView` usa agente+tarea+target+provider tipados.
- Decisión: no se necesita un prompt box universal en Project Entry. La necesidad de negocio es un input de dominio que puede alimentar prompts versionados internamente. Superficies semánticas futuras pueden ofrecer instrucciones adicionales acotadas, pero el texto nunca debe conceder tools, permisos, red o scope.
- Disposición: documentar y evaluar por superficie; no corrective adicional en B-02.

## Estado agregado después de 13-B-02-00

- Checkpoint `13-B-02`: `BLOCK / ACTIVE-CORRECTIVE`.
- UX-S0 abiertos: `0`.
- UX-S1 / contract blockers: `3`.
- Functional bugs demostrados en B-02: `2`.
- Architecture/contract gap crítico: `1`.
- Capability gaps nuevos: `2`.
- Active corrective autorizado: `sí`, exclusivamente para Project Entry greenfield + neutral bootstrap.
- Full Regression autorizada: `no`; validación focal/cumulativa + browser retest del mismo checkpoint.
