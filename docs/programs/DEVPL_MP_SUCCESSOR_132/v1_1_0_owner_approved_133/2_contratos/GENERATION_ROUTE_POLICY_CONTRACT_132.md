---
doc_id: DEVPL-MP-SUCCESSOR-132-GENERATION_ROUTE_POLICY_CONTRACT_132
title: "Selección D/L/E, capacidades, fallback y semántica"
version: "1.1.1-r00-succ"
status: "SUCCESSOR_DRAFT_FOR_OWNER_REVIEW"
baseline_commit: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
historical_baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
successor_execution_authority: false
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Selección D/L/E, capacidades, fallback y semántica

## Resolución por tarea

Input `task_type`, `artifact_profile`, `project_policy`, `context_manifest`, `data_classification`, `complexity`, `requested_capabilities`, `approved_routes`, `model_preferences`, `time_budget`, `cost_budget`, `consent_ref`; output `chosen_route`, `provider/model/version`, `reasons`, `capability_evidence`, `fallback_policy`, `denied_alternatives`, `route_decision_receipt`.

D permanente para scaffolds conocidos, schemas, hashes/diffs, permisos, lifecycle y cambios gobernados. L **preferente cuando disponible, configurado, probado y permitido** para requisitos narrativos, arquitectura, planning semántico y código de historias arbitrarias. External E sólo con habilitación explicita de egreso, secretos, privacidad y presupuesto. No obligar pipeline D→L→E. Agent es flujo, no un provider con aprobación.

## Fallback

- `EQUIVALENT`: segundo método supera el mismo contrato/evals mínimos.
- `REDUCED`: sólo borrador limitado, estado `PARTIAL/NOT_READY`, revisión/consentimiento antes de continuar.
- `MODEL_REQUIRED`: sin ruta competente, STOP o autoría humana; no usar template RF-specific como solución completa.

`SUPPORTED`, `CONFIGURED`, `HEALTHY`, `EVALUATED`, `ELIGIBLE_FOR_TASK` son estados separados. Configuración global no puede debilitar restricciones de proyecto y policy security. El fallback debe registrar pérdida de calidad, razones y costos; nunca gastar API sin consentimiento específico.

## Casos negativos

Model local offline, JSON corrupto, timeout, prompt injection, context overflow, cross-workspace provider, export de PII, insufficient budget y doble candidate deben bloquear o producir estado seguro con provenance. Successful response ≠ Quality PASS.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Routing.
- **Actualización concreta:** Fijar secuencia R01-03→04 y R01-09; D/mock en fundamento/diagnóstico R01, E/egress negado; para autoría semántica futura L competente como ruta preferente y fallback no equivalente visible.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.

---

## Enmienda programática post-R02-06 · 187

**Política normal de autoría:** resolver por `artifact_type + etapa + perfil + riesgo + contexto + capacidades comprobadas`; escoger **una** ruta L elegible y generar un candidato inicial. `D` solo crea estructuras, renderiza y verifica invariantes; `DEVPL_MOCK` sirve a fixtures/diagnóstico, nunca satisface calidad profesional de Vision/Scope/Requirements ni de planning semántico. `E` solo si ADR/egreso/privacy/secret-ref/CostGuard/consent específicos están `APPROVED`; disabled-by-default.

**Fallback ordenado, sin cascadas automáticas:** `L competent` → candidato Markdown; `L insufficient` → Owner edita/refina o solicita alternativa del mismo L/otro L; si E es elegible y Owner decide, generar E; si no, Manual/Import gobernados o `MODEL_REQUIRED`. No ejecutar un segundo L ni E sin acción/consentimiento correspondiente. Todo intento acotado por `max_attempts`, timeout, contexto, presupuesto y cancellation; hashes/candidate IDs/provenance por intento. Múltiples candidatos → comparación **opcional** con criterios equivalentes, jamás gate obligatorio.

**Criterio semántico:** un resumen literal de B0 no sustituye una Vision/Scope/Requirements. La completitud y coherencia se validan por `ArtifactCatalog`, upstream FROZEN y Owner; `API 200`, `schema PASS`, español solicitado o `HEALTHY` no acreditan calidad. La historia D/L R02-06 conserva sus receipts y selecciones `REDUCED` y no se reabre.


---
## Enmienda 188 aprobada — economía y frontera candidata (ADOPTADA — autoridad programática)

`ModelAdapter` recibe un contrato resuelto por perfil; ninguna respuesta cruda del modelo es candidata admisible hasta superar parsing/schema y controles de seguridad. Generación local L elegible por tarea y perfil, `D` para orquestación/estructura/tests, reparación limitada a obligaciones defectuosas con límites `max_attempts`, latencia y recursos; cache por `profile_version + context_sha256 + model`. Agentes/E son complementos explícitos para tareas no resueltas con mejora esperada medible y privacy/egress/cost autorizados; nunca cascada D→L→E obligatoria. Exigir distinción `GENERATED`, `ADMITTED_FOR_OWNER_REVIEW`, `QUALITY_ACCEPTABLE`, `APPROVED`, `FROZEN`. No usar los IDs del piloto como exclusión universal.

**Autoridad:** `MP132-A188`, aprobada por Owner el 2026-10-22; aplicación según `ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. No constituye ejecución R02-08 ni habilitación de E.
