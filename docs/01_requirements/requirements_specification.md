---
title: "Requirements Specification — DevPilot Local"
doc_id: "DEVPL-REQ-001"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "DEVPL-GSDLC-00-B"
updated: "2026-08-14"
approval: "approved_by_owner_direction"
approval_scope: "DEVPL-GSDLC successor requirements under approved roadmap"
source_baseline: "repo341 + DEVPL-GSDLC-00-A CLOSED/PASS"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---
# Requirements Specification — DevPilot Local

## 1. Propósito

Este documento convierte la baseline aprobada de producto de DevPilot Local en requerimientos verificables, priorizados y trazables. Su propósito es impedir que la plataforma avance a desarrollo funcional fuerte sin una especificación clara sobre qué debe hacer, bajo qué restricciones, con qué evidencia, con qué relación con MIPSoftware y con qué activación de MIASI.

DevPilot Local no se concibe como una simple herramienta que revisa si existen archivos. El MVP debe iniciar con validadores determinísticos y agentes controlados para **construir, revisar y auditar documentación pre-code** a partir de una idea de proyecto. El sistema debe evolucionar hacia MVP+ para trabajar con repositorios reales, Git, entornos virtuales, validación de patches, revisión de código, refactor seguro y agentes especializados.

## 2. Fuente de verdad del sprint

| Fuente | Uso en requisitos |
|---|---|
| `docs/00_product/product_vision.md` | Define visión, problema, plataforma local-first, workspaces y compromiso CLI → desktop → web. |
| `docs/00_product/business_case.md` | Justifica el MVP acotado, el MVP+ y el valor estratégico de convertir MIPSoftware/MIASI en gates ejecutables. |
| `docs/00_product/stakeholder_map.md` | Define actores humanos, técnicos, normativos y futuros. |
| `docs/00_product/mvp_scope.md` | Delimita MVP, MVP+, post-MVP y fuera de alcance. |
| `docs/00_product/product_roadmap.md` | Ordena fases de evolución: CLI, validadores, agentes documentales, Git/repo, desktop y web. |
| `docs/00_product/sprint_precode_01_approval_audit.md` | Aprueba la baseline de producto y autoriza SPRINT-PRECODE-02. |
| `docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md` | Define visión Guided SDLC, milestones, no-go y backlogs sucesores. |
| `docs/backlogs/DEVPL-GSDLC-00_program_activation_rebaseline_and_pilot_pause.md` | Define la ola de reconciliación canónica A→E. |
| `docs/00_product/DEVPL_GSDLC_program_charter.md` | Fija alcance, roles de programa, métricas y reglas de pausa/reanudación. |
| Evidencia `DEVPL_GSDLC_00_A_WINDOWS_EVIDENCE_v1_0_1.zip` | Acredita 00-A CLOSED/PASS, commit `5c6d0b2f...`, workspace preservado y piloto pausado. |

## 3. Alcance de requerimientos

| Nivel | Descripción | Estado esperado |
|---|---|---|
| MVP | CLI local, workspace mínimo, validadores documentales, agentes pre-code controlados, readiness, MIASI detection, reportes y trazabilidad. | Implementable en los primeros sprints funcionales. |
| MVP+ | Git, análisis de repos reales, validación de entorno virtual, patch review, code review dry-run, safe refactor, agentes especializados y trazas JSONL. | Diseñable desde ahora, implementable después del core de validación. |
| Post-MVP | Desktop, web, dashboards, colaboración futura, agentes multirol, despliegue controlado y operación ampliada. | Requerimientos direccionales, sujetos a refinamiento. |
| DEVPL-GSDLC successor | Project-centric UI, Guided SDLC state, local auth/RBAC, bootstrap, Artifact Workbench, executable standards, Model Gateway, agent-assisted engineering, planning, coding, quality/Git/evidence y release. | `planned` por backlog; no implica runtime implementado en 00-B. |

## 4. Definiciones funcionales clave

| Concepto | Definición |
|---|---|
| Workspace | Unidad operativa gobernada por DevPilot. Representa un proyecto o repo gestionado con MIPSoftware/MIASI, documentos, políticas, reportes, gates, trazas y estado local. |
| Gate | Control verificable que produce PASS/FAIL/WARN/BLOCK y evidencia. |
| Artifact | Documento, reporte, checklist, schema, archivo de configuración, patch o salida generada por DevPilot. |
| Dry-run | Modo de ejecución que analiza y propone sin modificar archivos, repos o entornos. |
| Agent-assisted | Capacidad en la que un agente sugiere, evalúa, redacta o coordina, pero no sustituye los gates determinísticos ni la aprobación humana. |
| Documentation Agent | Agente controlado que ayuda a crear, completar o auditar documentos pre-code a partir de una idea, plantilla o baseline. |
| MVP+ | Expansión inmediata del MVP hacia repos reales, Git, patches, revisión, refactor y agentes controlados. |
| Normal journey | Camino soportado por UI que un usuario sigue para crear/abrir/importar y avanzar un proyecto sin PowerShell obligatorio. |
| Workspace Engineering State | Estado persistente del proyecto gestionado: fase, paso, artifacts, gates, planning, sprint/story y progress; separado del Platform State. |
| StepActionAdvisor | Servicio determinístico que ofrece modos de ejecución según step/state/role/policy/provider/budget y explica disabled reasons. |
| Operator-free project authorship | Los harnesses externos pueden auditar/empacar evidencia, pero no escribir el contenido del proyecto durante acceptance. |

## 5. Requerimientos funcionales del MVP

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-MVP-001 | El sistema debe ejecutarse como CLI local desde el workspace del proyecto. | Alta | Product Vision | `python -m devpilot_core --version` responde versión. |
| FR-MVP-002 | El sistema debe detectar o registrar un workspace DevPilot mínimo. | Alta | Product Vision / Workspace | El workspace tiene raíz, `docs/`, `outputs/` y metadata mínima. |
| FR-MVP-003 | El sistema debe inventariar artefactos mínimos pre-code. | Alta | MVP Scope | `readiness-check` reporta PASS/FAIL por artefacto. |
| FR-MVP-004 | El sistema debe validar frontmatter YAML mínimo en documentos Markdown. | Alta | MIPSoftware | Documento sin `doc_id`, `status`, `version` u `owner` falla. |
| FR-MVP-005 | El sistema debe validar estructura mínima de artefactos MIPSoftware. | Alta | MIPSoftware | Cada artefacto obligatorio tiene secciones mínimas exigidas. |
| FR-MVP-006 | El sistema debe validar checklists pre-code. | Alta | MIPSoftware | Checklist produce PASS/FAIL/WARN/BLOCK con evidencia. |
| FR-MVP-007 | El sistema debe detectar si MIASI aplica al proyecto. | Alta | MIASI | `miasi-required` devuelve `true` para DevPilot Local. |
| FR-MVP-008 | El sistema debe generar reportes locales en JSON y Markdown. | Alta | Product Vision | Se crean reportes en `outputs/reports/`. |
| FR-MVP-009 | El sistema debe operar sin API keys obligatorias en MVP y preparar proveedores externos opcionales bajo CostGuard. | Alta | Local-first híbrido | Tests y CLI pasan sin `.env` con secretos; cualquier proveedor externo exige configuración explícita. |
| FR-MVP-010 | El sistema debe funcionar en dry-run por defecto. | Alta | Seguridad | Ningún comando modifica archivos críticos sin confirmación. |
| FR-MVP-011 | El sistema debe producir mensajes de error accionables. | Media | UX/Operación | Error indica archivo, campo, severidad y corrección sugerida. |
| FR-MVP-012 | El sistema debe construir una matriz de trazabilidad producto → requisito → prueba. | Alta | MIPSoftware | La matriz conecta objetivos, requisitos, historias, casos, criterios y tests. |
| FR-MVP-013 | El sistema debe incluir un agente documental controlado para ayudar a crear documentos pre-code a partir de una idea. | Alta | Product Vision / MIASI | El agente genera borradores en dry-run usando plantillas, sin llamadas externas obligatorias. |
| FR-MVP-014 | El sistema debe incluir un agente auditor controlado para revisar brechas documentales pre-code. | Alta | MIPSoftware / MIASI | El agente produce hallazgos con severidad, evidencia y recomendación, sin aprobar automáticamente. |
| FR-MVP-015 | El sistema debe registrar evidencias locales de validación. | Alta | Operación | Reportes y/o eventos quedan bajo `outputs/`. |
| FR-MVP-016 | El sistema debe separar claramente validación determinística y asistencia agentic. | Alta | MIASI | Los agentes recomiendan; los gates determinísticos deciden PASS/FAIL. |

## 6. Requerimientos funcionales MVP+

| ID | Requerimiento | Prioridad | Fuente | Criterio de aceptación resumido |
|---|---|---:|---|---|
| FR-PLUS-001 | El sistema debe crear/usar `.devpilot/project.yaml` como descriptor de workspace. | Alta | Workspace Vision | Descriptor válido y versionable según política. |
| FR-PLUS-002 | El sistema debe consultar estado Git en modo read-only. | Alta | Product Vision | Reporta branch, commit, dirty state y cambios sin modificar repo. |
| FR-PLUS-003 | El sistema debe analizar estructura de repos reales. | Alta | MVP+ | Detecta módulos, docs, tests, configuración, riesgos y brechas. |
| FR-PLUS-004 | El sistema debe validar entorno virtual de desarrollo. | Alta | User prompt / MVP+ | Reporta Python, venv, dependencias y comandos reproducibles. |
| FR-PLUS-005 | El sistema debe validar patches en dry-run. | Alta | MVP+ | Evalúa patch sin aplicarlo y genera reporte de impacto. |
| FR-PLUS-006 | El sistema debe realizar revisión de código asistida. | Alta | MVP+ | Produce hallazgos con evidencia, severidad y recomendación. |
| FR-PLUS-007 | El sistema debe proponer refactor seguro. | Media | MVP+ | Plan de refactor incluye tests, riesgo y rollback. |
| FR-PLUS-008 | El sistema debe incorporar agentes especializados controlados. | Alta | MIASI | RequirementsAgent, ArchitectureAgent, SecurityAgent, TestPlannerAgent y CodeReviewAgent operan con cards/policies/evals. |
| FR-PLUS-009 | El sistema debe registrar trazas JSONL de ejecuciones relevantes. | Media | Observabilidad | Eventos guardan acción, actor, resultado, severidad y correlación. |
| FR-PLUS-010 | El sistema debe exigir aprobación humana para acciones sensibles. | Alta | MIASI | Ninguna escritura, patch o refactor se ejecuta sin aprobación explícita. |

## 7. Requerimientos funcionales post-MVP

| ID | Requerimiento | Prioridad | Criterio de aceptación direccional |
|---|---|---:|---|
| FR-POST-001 | El sistema debe ofrecer app de escritorio sobre el mismo core. | Alta | Desktop UI consume DevPilot Core sin duplicar lógica. |
| FR-POST-002 | El sistema debe ofrecer interfaz web controlada. | Media | Web UI incluye auth, permisos, trazas y threat model propio. |
| FR-POST-003 | El sistema debe mostrar dashboards de workspaces, gates, riesgos y trazas. | Alta | Dashboard resume estado del ciclo de vida. |
| FR-POST-004 | El sistema debe incorporar agentes multirol y orquestación avanzada. | Media | Multiagentes sujetos a MIASI, evals, policies y human approval. |
| FR-POST-005 | El sistema debe asistir despliegues y releases controlados. | Media | Release checklist, rollback, evidencia y gates de seguridad. |

## 8. Requerimientos no funcionales

| ID | Requerimiento | Prioridad | Criterio de aceptación |
|---|---|---:|---|
| NFR-001 | Local-first por defecto. | Alta | Todos los comandos MVP funcionan sin red. |
| NFR-002 | Costo externo controlado. | Alta | Cero costo externo por defecto; cualquier costo externo exige presupuesto, proveedor configurado, consentimiento y trazabilidad. |
| NFR-003 | Portabilidad Windows-first con diseño portable. | Alta | Funciona en `D:\Projects\DevPilot_Local`; evita rutas hardcoded internas salvo ejemplos. |
| NFR-004 | Seguridad por defecto. | Alta | Dry-run, no overwrite, no secretos, límites de rutas. |
| NFR-005 | Trazabilidad. | Alta | Cada gate produce evidencia local. |
| NFR-006 | Testabilidad. | Alta | `pytest -q` cubre validadores core. |
| NFR-007 | Separación de responsabilidades. | Alta | CLI, core, validators, agents, policies y reports son módulos separables. |
| NFR-008 | Extensibilidad UI. | Media | Desktop/web futuros consumen core común. |
| NFR-009 | Observabilidad local. | Media | Reportes JSON/Markdown y eventos JSONL progresivos. |
| NFR-010 | Mensajes accionables. | Media | Todo FAIL indica causa y corrección sugerida. |

## 9. Requerimientos sucesores DEVPL-GSDLC

Los siguientes requisitos **no reescriben** los requisitos MVP/MVP+/post-MVP históricos. Definen el contrato sucesor aprobado por DEVPL-GSDLC. Todos permanecen `planned` hasta que el backlog owner correspondiente produzca implementación y evidencia.

| ID | Tipo | Statement verificable | Rationale | Precondiciones | Criterio de aceptación | Owner backlog | Milestone | Estrategia inicial de prueba/evidencia | Relación MIPSoftware/MIASI | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| GSDLC-FR-001 | FR | El sistema debe mantener un `Project Status` persistente con proyecto, fase actual, paso actual, avance MIPSoftware, estado MIASI, artefactos pendientes/listos, blockers, approvals, quality, Git, presupuesto IA, próxima acción y modos disponibles. | El usuario necesita una fuente visible y única de orientación. | Proyecto registrado y `WorkspaceEngineeringState` disponible. | Al abrir o reanudar un proyecto la UI muestra todos los campos mínimos y el next action coincide con el workflow determinístico. | DEVPL-GSDLC-01 | M1 | Focal state-engine + browser Project Status + snapshot de estado. | MIPSoftware lifecycle; MIASI observability | planned |
| GSDLC-FR-002 | FR | El sistema debe persistir `WorkspaceEngineeringState` separado de Platform State y Runtime Operational State. | Evita mezclar madurez de DevPilot, progreso del proyecto y sesiones/jobs. | Workspace registrado. | Restart conserva fase/paso; estados de plataforma/runtime no sobrescriben el estado de ingeniería. | DEVPL-GSDLC-01 | M1 | State transition tests + restart/reload evidence. | MIPSoftware lifecycle; MIASI state/evidence | planned |
| GSDLC-FR-003 | FR | El sistema debe ofrecer first-run/login para operadores locales autenticados antes de acciones gobernadas. | Los approvals y mutaciones deben tener actor real no spoofable. | GSDLC-01 state boundary aprobado. | Login/logout/session expiry/revocation PASS; identidad del actor deriva de sesión. | DEVPL-GSDLC-02 | M1 | Auth/session negative tests + browser login acceptance. | MIPSoftware governance; MIASI human approval | planned |
| GSDLC-SEC-001 | SEC | Los approvals deben estar vinculados server-side a actor, rol efectivo, workspace, acción y subject hash; solo roles autorizados pueden decidir. | Impide spoofing y approvals sin autoridad. | Operador local autenticado. | Wrong role, revoked/expired session, scope mismatch y actor spoofing quedan BLOCK; approval válido queda auditado. | DEVPL-GSDLC-02 | M1 | RBAC/approval negative matrix + audit evidence. | MIASI Policy/Human Approval | planned |
| GSDLC-SEC-002 | SEC | La autenticación local GSDLC no debe declarar ni habilitar enterprise IAM, tenancy, SSO o API pública. | Preserva la frontera POST-H-034-D. | GSDLC-02 local auth design. | Bind local-only; enterprise capabilities continúan POLICY-BLOCKED y tests históricos PASS. | DEVPL-GSDLC-02 | M1 | Security focal + successor ADR tests. | MIPSoftware security; MIASI policy | planned |
| GSDLC-FR-004 | FR | Home debe ofrecer `Crear nuevo proyecto`, `Abrir proyecto existente` e `Importar repositorio Git`. | Es la entrada natural al Guided SDLC. | Sesión local válida. | Las tres opciones son accesibles desde UI y conducen a flujos tipados sin shell arbitrario. | DEVPL-GSDLC-03 | M1 | Browser acceptance + typed-operation contract tests. | MIPSoftware inception/workspace | planned |
| GSDLC-FR-005 | FR | Crear proyecto debe gobernar ruta, stack, Git init, `.venv`, estructura y dependencias mediante plan → dry-run → approval → execute → verify. | El proyecto debe nacer dentro de DevPilot, no por inyección externa. | Usuario autenticado con rol permitido y ruta válida. | Dry-run no muta; execute solo dentro del workspace; Git/venv/deps verificados; rollback/evidence disponibles. | DEVPL-GSDLC-03 | M1 | Bootstrap positive/negative tests + filesystem boundary evidence. | MIPSoftware environment/reproducibility; MIASI tool safety | planned |
| GSDLC-SEC-003 | SEC | Toda mutación de workspace debe usar typed operations; arbitrary shell permanece bloqueado en el normal journey. | Reduce superficie de ejecución y command injection. | Operation catalog/policy disponible. | No existe endpoint/UI que acepte comandos arbitrarios; path traversal y command injection quedan BLOCK. | DEVPL-GSDLC-03 | M1 | Security negative tests + capability registry evidence. | MIPSoftware security; MIASI tool policy | planned |
| GSDLC-FR-006 | FR | Artifact Workbench debe permitir crear y editar artefactos MIPSoftware/MIASI manualmente desde UI con lifecycle `MISSING→DRAFT→VALIDATING→FINDINGS→READY_FOR_REVIEW→APPROVAL_REQUIRED→APPROVED→FROZEN`. | DevPilot debe conducir la autoría, no solo inspeccionar documentos externos. | Proyecto bootstrap y perfiles de artefacto disponibles. | Editor guarda draft gobernado, validators actualizan lifecycle y no se puede saltar un gate obligatorio. | DEVPL-GSDLC-04 | M2 | Artifact lifecycle tests + browser authoring acceptance. | MIPSoftware docs-as-code; MIASI governed artifacts | planned |
| GSDLC-FR-007 | FR | Artifact Workbench debe soportar `PASTE` y `UPLOAD_IMPORT` con provenance, tipo/tamaño allowlist, staging y validación antes de promover contenido. | Permite fuentes externas sin perder control ni trazabilidad. | Artifact Workbench activo. | Import no sobrescribe aprobado sin review; archivos inválidos/maliciosos quedan bloqueados; provenance persistida. | DEVPL-GSDLC-04 | M2 | Import security suite + provenance evidence. | MIPSoftware evidence; MIASI data/tool safety | planned |
| GSDLC-FR-008 | FR | Ediciones realizadas con `EXTERNAL_EDITOR` deben reconciliarse por hash/Git y degradar el artefacto a `REVALIDATION_REQUIRED` cuando invaliden una aprobación previa. | No se debe encerrar al desarrollador en DevPilot ni confiar en estado obsoleto. | Workspace monitor/reconciliation disponible. | Cambio externo detectado; aprobación no permanece vigente silenciosamente; diff y revalidación visibles. | DEVPL-GSDLC-12 | M6 | External-edit/restart reconciliation tests. | MIPSoftware change control; MIASI evidence integrity | planned |
| GSDLC-GOV-001 | GOV | MIPSoftware debe expresarse como workflow machine-readable de fases, artefactos, dependencias, validators, approvals, gates y next actions. | Convierte el estándar documental en sistema ejecutable. | Artifact lifecycle disponible. | No se avanza a un step con prerequisitos/gates incumplidos; registry versionado y validado. | DEVPL-GSDLC-05 | M2 | Workflow registry tests + transition negative matrix. | MIPSoftware core | planned |
| GSDLC-GOV-002 | GOV | MIASI debe expresarse como policy/workflow ejecutable para capacidades agentic, tools, risk, approval y evaluación. | La IA debe operar dentro del estándar y no como chat lateral. | MIPSoftware executable workflow y policy engine disponibles. | Agent/tool no registrado o sin policy/eval queda bloqueado; human approval se respeta. | DEVPL-GSDLC-05 | M2 | MIASI registry/policy validators + negative tests. | MIASI core | planned |
| GSDLC-FR-009 | FR | `StepActionAdvisor` debe ofrecer, cuando aplique, `MANUAL`, `PASTE`, `UPLOAD_IMPORT`, `EXTERNAL_EDITOR`, `AGENT`, `RAG` y `TYPED_OPERATION`, con disabled reasons derivados determinísticamente de state+role+policy+provider+budget. | El usuario debe saber cómo completar cada paso y por qué una opción no está disponible. | Executable standards y role/policy context disponibles. | Advisor nunca inventa capabilities; opciones bloqueadas explican razón; salida estable para mismo estado. | DEVPL-GSDLC-05 | M2 | Advisor determinism/permissions tests + browser action chooser. | MIPSoftware guidance; MIASI policy/cost | planned |
| GSDLC-NFR-001 | NFR | El flujo pre-code manual/import debe ser completo sin LLM, sin API key y sin red externa. | La IA es asistencia opcional; local-first debe ser funcional, no declarativo. | GSDLC-05 cerrado. | Proyecto puede alcanzar PRE_CODE_READY por Manual/Paste/Upload con network_used=false y external_cost=0. | DEVPL-GSDLC-05 | M2 | Offline end-to-end pre-code acceptance. | MIPSoftware; MIASI local-first | planned |
| GSDLC-FR-010 | FR | Model Gateway v2 debe enrutar tareas por capabilities, privacidad, disponibilidad y presupuesto a mock, modelos locales o APIs externas opcionales. | Evita lock-in y permite calidad/costo controlados. | R01 research + executable standards disponibles. | Sin provider configurado existe fallback mock/local; rutas externas requieren opt-in/policy y dejan trazabilidad. | DEVPL-GSDLC-06 | M3 | Provider routing matrix + offline fallback tests. | MIASI model/provider governance | planned |
| GSDLC-NFR-002 | NFR | El sistema debe estimar, limitar y registrar tokens/costo por request, artifact, story, sprint y project antes y después de una ejecución agentic. | El usuario debe controlar gasto y contexto. | Model Gateway v2. | Budget excedido bloquea o requiere approval según policy; UI muestra estimación y consumo. | DEVPL-GSDLC-06 | M3 | CostGuard/token budget tests + cost ledger evidence. | MIASI cost budget/observability | planned |
| GSDLC-FR-011 | FR | Los agentes contextuales deben poder proponer drafts/cambios para el step actual sin auto-aplicar ni auto-aprobar. | La asistencia IA debe integrarse al workflow manteniendo control humano. | Model Gateway + Artifact Workbench + approvals. | Draft incluye provenance/model/context; apply requiere review/policy/approval; agent self-approval bloqueado. | DEVPL-GSDLC-07 | M3 | Agent draft/apply negative tests + approval traces. | MIASI Agent/Tool/Policy/Human Approval | planned |
| GSDLC-FR-012 | FR | RAG debe aportar fuentes/citas/freshness e `insufficient-evidence` al agente cuando el step requiera grounding. | Reduce alucinaciones y mantiene evidencia auditable. | RAG index/bindings disponibles. | Respuesta sin evidencia suficiente no promueve afirmación a artefacto aprobado; citations navegables. | DEVPL-GSDLC-07 | M3 | Grounding/citation/freshness evals. | MIASI RAG grounding | planned |
| GSDLC-GOV-003 | GOV | LLM/agentes nunca deben decidir PASS/BLOCK, transición de workflow, permisos ni autoridad de approval. | La gobernanza debe ser determinística y auditada. | Agent-assisted flows disponibles. | Tests demuestran que outputs LLM no pueden sobreescribir gate/policy/state machine. | DEVPL-GSDLC-07 | M3 | Adversarial/negative governance tests. | MIASI human authority | planned |
| GSDLC-FR-013 | FR | Planning Workbench debe derivar y permitir revisar/aprobar roadmap, backlog y sprints desde requisitos/arquitectura/riesgos con trazabilidad `REQ→EPIC→STORY→SPRINT`. | Convierte baseline pre-code en plan de ejecución gobernado. | PRE_CODE_READY. | Coverage de requisitos planificados =100% o gaps explícitos; owner puede editar/rechazar antes de freeze. | DEVPL-GSDLC-08 | M4 | Planning traceability tests + browser acceptance. | MIPSoftware planning/change control; MIASI optional assistance | planned |
| GSDLC-FR-014 | FR | Story Workbench debe cargar requisito, aceptación, arquitectura, riesgos, archivos y tests relevantes y permitir `plan→review→apply` por historia. | La implementación incremental debe nacer del backlog gobernado. | Sprint/story aprobados. | Cada story mantiene context pack, plan, diff y estado; no aplica cambios fuera de manifest. | DEVPL-GSDLC-09 | M5 | Story lifecycle + context-pack + path-boundary tests. | MIPSoftware implementation; MIASI tool safety | planned |
| GSDLC-FR-015 | FR | Coding Workbench debe soportar edición manual o agent-assisted, mostrar diff antes de apply y usar operaciones atómicas/rollback cuando corresponda. | Permite escribir código con control visible y reversible. | Story activa y rol autorizado. | Apply solo tras validación/approval requerido; diff exacto y rollback evidence disponibles. | DEVPL-GSDLC-09 | M5 | Patch/apply/rollback negative tests + browser diff acceptance. | MIPSoftware implementation/review; MIASI approval | planned |
| GSDLC-FR-016 | FR | El flujo de historia debe integrar Test Impact, ejecución de tests, Quality Gate, remediation y evidencia antes de permitir cierre. | Una historia no debe cerrarse solo porque el código fue escrito. | Código aplicado. | Tests seleccionados ejecutan; blockers=0; resultados correlacionados a story y requirement. | DEVPL-GSDLC-10 | M5 | Test Impact/Quality/Evidence integration tests. | MIPSoftware quality; MIASI evaluation/evidence | planned |
| GSDLC-FR-017 | FR | Git commit debe ser una operación gobernada posterior a gates, con mensaje trazable, actor, branch y working tree verificados. | Git es columna vertebral de historial y no debe adelantarse a calidad. | Quality Gate PASS y approval cuando aplique. | Commit contiene solo paths autorizados; force-push/reset-hard/rebase automáticos siguen bloqueados. | DEVPL-GSDLC-10 | M5 | Git operation contract + negative no-go tests. | MIPSoftware configuration management; MIASI policy | planned |
| GSDLC-GOV-004 | GOV | Cada transición significativa debe emitir evidence/trace correlacionable a project/phase/step/artifact/story/approval/job/commit. | La auditoría no debe reconstruirse manualmente al final. | Workflow engine operativo. | Evidence coverage del flujo cerrado=100%; ids permiten navegar acción→policy→approval→result→commit. | DEVPL-GSDLC-10 | M5 | Evidence graph/trace coverage tests. | MIPSoftware traceability; MIASI observability | planned |
| GSDLC-FR-018 | FR | Release Workbench debe evaluar readiness y gobernar package/install/rollback/tag local desde UI. | Completa el journey hasta una versión liberable. | Stories/sprint/release gates cumplidos. | Release no progresa con blockers; package reproducible, rollback verificable y tag gobernado. | DEVPL-GSDLC-11 | M6 | Release readiness/package/install/rollback/tag tests. | MIPSoftware release/operation; MIASI security/observability | planned |
| GSDLC-NFR-003 | NFR | El estado del proyecto debe ser resumible y reconciliable después de restart, branch change o ediciones Git/IDE externas. | Uso industrial requiere recuperación fiable. | Guided workflows implementados. | Restart conserva progreso; divergencias producen reconciliación/REVALIDATION_REQUIRED, no estado silenciosamente inválido. | DEVPL-GSDLC-12 | M6 | Resume/reconcile chaos matrix + browser evidence. | MIPSoftware maintenance/change control; MIASI durable execution | planned |
| GSDLC-UX-001 | UX | En cada milestone declarado UI-complete, el normal journey debe requerir `PowerShell=0`, `external operator project writes=0` y `required unclassified CLI bridges=0`. | Diferencia una plataforma wizard de un inspector asistido externamente. | Vertical slice implementada. | Browser acceptance demuestra flujo completo sin comandos de usuario; bridges restantes son opcionales/diagnóstico y clasificados. | DEVPL-GSDLC-12 | M6 | End-to-end browser matrix + bridge register. | MIPSoftware usability/operation | planned |
| GSDLC-GOV-005 | GOV | Los contratos históricos deben quedar scoped al hito que validan y evolucionar mediante successor contracts, no por reescritura oportunista. | Evita que tests históricos congelen capacidades futuras. | Programa DEVPL-GSDLC activo. | Historical sweep clasifica impacted contracts; 0 global assertions sin scope; history facts permanecen verificables. | DEVPL-GSDLC-12 | M6 | Historical contract regression suite. | MIPSoftware governance/evidence | planned |
| GSDLC-GOV-006 | GOV | La aceptación final del programa debe demostrar `inventory-sales-local` 02-B sin que un operador externo escriba artefactos del proyecto. | El piloto debe probar el producto real y no una inyección de fixtures. | GSDLC-12 CLOSED/PASS. | 02-B alcanza sus gates desde Guided SDLC UI; operator solo audita/evidence; workspace source attribution documentada. | DEVPL-GSDLC-13 | M7 | Independent pilot acceptance + source attribution/evidence. | MIPSoftware full SDLC; MIASI governed assistance | planned |

### 9.1 Reglas de evolución

- No se renumeran `FR-MVP-*`, `FR-PLUS-*`, `FR-POST-*` ni `NFR-*` históricos.
- Un requisito GSDLC solo puede pasar de `planned` a un estado de implementación con evidencia del backlog owner.
- La ruta manual/import debe permanecer funcional aun cuando no exista modelo LLM configurado.
- Ningún requisito GSDLC autoriza arbitrary shell, enterprise IAM/tenancy/SSO, remote execution, cloud deploy o agent self-approval.
- Las capacidades actuales parciales se reconocen como precursores, no como satisfacción automática del successor requirement.

## 10. Reglas de activación MIASI

MIASI se activa desde el MVP porque DevPilot Local será una plataforma agent-assisted SDLC. Todo agente debe cumplir:

- Agent Card;
- Tool Card;
- Policy Card;
- Eval Card;
- Human Approval Card cuando aplique;
- Observability Card;
- dry-run por defecto;
- evaluación offline;
- no uso obligatorio de API externa;
- no exposición de secretos;
- trazabilidad local.

## 11. Criterios de bloqueo

Un incremento queda bloqueado si:

- requiere API key real obligatoria en MVP;
- modifica archivos sin dry-run y aprobación;
- introduce agente sin artefactos MIASI;
- agrega requerimiento crítico sin criterio de aceptación;
- rompe `pytest -q`;
- genera reportes no reproducibles;
- escanea rutas fuera del workspace permitido;
- no deja trazabilidad hacia producto, requisito o prueba.
- un requisito GSDLC carece de backlog owner, milestone, criterio de aceptación o estrategia de evidencia;
- la ruta de autoría depende obligatoriamente de un LLM/API externa;
- se declara implementada una capability GSDLC que solo existe como contrato `planned`;
- el normal journey futuro se diseña alrededor de shell arbitrario o bypass de ApplicationService/PolicyEngine.

## 12. Estado

```yaml
requirements_status: approved
gsdlc_successor_requirements_status: planned/contracted
gsdlc_delta_requirements_total: 31
gsdlc_orphan_requirements: 0
ready_for_gsdlc_00_c_after_00_b_closure: true
controlled_changes_allowed_via_docs_as_code: true
```
