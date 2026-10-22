
## COR215 — Generación estructurada L-first y recuperación gobernada de GLOBAL (2026-10-20)

**RCA y continuidad.** COR214 Windows: 93 tests PASS y `GLOBAL` intento 3 BLOCK
por `GLOBAL_ACCEPTANCE_NOT_COVERED` (2 criterios). Siete checkpoints RF
persistidos con hashes invariantes. El motor no puede ni debe ejecutar una cuarta
llamada Markdown libre bajo el mismo contrato. La ausencia del texto rechazado
impide concluir si el error fue estrictamente semántico o de formato. No degradar
`GLOBAL` a cobertura por simple mención de IDs.

**Decisión.** Conservar generación segmentada, `PROFILE_VERSION`, `plan_hash`,
los siete checkpoints y lifecycle Pre-code. Añadir un contrato intermedio de
propuesta estructurada `r0215-segment-obligation-schema-v1`, inicialmente para
el único segmento GLOBAL. DevPilot deriva de Scope FROZEN los identificadores
`SC-AC`, la secuencia y el formato Markdown. Ollama L local devuelve JSON
con `nfrs`, `coverage`, `restrictions`, `pending_decisions`. Cada cobertura
incluye `criterion_id`, `source_anchor` literal, `control`, `verification` y
`status`. Un control por criterio, verificación específica por control,
congruencia léxica mínima, tres RNF no duplicados y seguridad. Los valores
semánticos deben ser redactados por el LLM; no se completan mediante plantillas
ni se aceptan placeholders. JSON/schema válido **no** acredita calidad
profesional: revisión Owner y Quality Gate siguen siendo obligatorios.

**Autorización y presupuesto.** Únicamente para plan/modelo/Scope inmutables
con tres recibos GLOBAL históricos válidos, el Owner activa por operador
foreground la ruta sucesora: `structured_authorization.json` vinculada al
hash SHA-256 de los tres recibos. Máximo **2 solicitudes humanas explícitas**
con recibos distintos `GLOBAL_STRUCTURED.attempt-NN.json`. La ruta heredada
mantiene su 3/3 agotado. Un BLOCK nunca dispara una segunda inferencia automática,
ni permite editar el plan, saltarse la revisión o aprobar/FROZEN. Persistir
provenance de generación `frozen_scope_structured_global_v1` en `GLOBAL.json`.

**Observabilidad contemporánea.** La misma Consola 2 captura POST 200/403,
recibos tipados, hashes, duración y avance inmediatamente; la Consola 1 sella
las capturas después sin borrar el ZIP inicial. Diagnósticos incluyen códigos
de JSON, schema, anclaje, verificación y cobertura por unidad, sin texto crudo,
prompts ni secretos en los ZIP. El almacenamiento opcional de texto rechazado
requerirá especificar ACL, retención, consentimiento y análisis de privacidad;
no se activa implícitamente aquí.

**Alcance generalizable y limitaciones.** Se introduce un contrato de
obligaciones estructuradas y se prueba con tres dominios sintéticos ajenos a
Pilot B, pero la primera implementación productiva solo conmuta GLOBAL, sin
migrar los siete RF ni declarar todos los perfiles/modelos `ELIGIBLE_FOR_TASK`.
La ruta de autoría completa y su adaptación por artefacto siguen bajo el
programa MP132 original, sin segundo candidate lifecycle ni proveedor E.
Prohibidos Full Regression anticipada, escritura en workspace por operador,
autoapproval o paso a R02-08. Cualquier 8/8 sigue en DRAFT para auditoría
profesional completa.

## COR216 — Canonical post-assembly contract and replay (2026-10-21)

After eight immutable acceptance checkpoints exist, the assembled DRAFT must be verified against both the per-segment contract and the authoritative Requirements professional-document gate. Publication canonicalizes `Requisitos no funcionales` to the artifact-profile heading `Requerimientos no funcionales` without changing the GLOBAL checkpoint; it adds platform-owned `Criterios de bloqueo` (quality-policy descriptions, not business decisions). The final gate accepts the explicitly validated plural `Excepciones` field but retains substantive field, traceability, acceptance, language, and groundedness checks. The owner must not spend another model call on completed checkpoint content. Preflight computes the full final-gate findings from persisted checkpoints without writing business documents, and automatically seals only safe error codes. If any finding persists, BLOCK before browser. Publication remains DRAFT, no auto-approval/apply/FROZEN, no R02-08.

## COR217 — Source-owned canonical RF publication and actionable postgate (2026-10-21)

COR216 Windows proved 8/8 persisted checkpoints (all immutable) and 114 focal
tests PASS, but integrated postgate found 6 defects: RF_INCOMPLETE and UNTRACED.
The per-unit gate already accepts the model-authored fields. The publication
view used to concatenate unnormalized Markdown and the final gate re-parsed
section boundaries, field names and Scope origins under a distinct contract.

COR217 renders every RF with a platform-owned, stable heading, exact nine
mandatory field labels (values extracted ONLY from accepted model checkpoints),
and an explicit source-owned origin ID / acceptance criterion. It does not infer
missing model content, invent capabilities, weaken postgate, write workspace
files, alter checkpoint bytes, or reset generation attempts. Missing original
fields or untraceable sources fail closed. The snapshot of each immutable
checkpoint remains the authoritative model-authored input; the assembled
Markdown is a derived review candidate. Free prose outside the contracted
fields remains in the checkpoint, not projected as an independently verified
requirement; Owner must inspect completeness before approving the document.

The same Windows operator performs focused tests, offline replay, the exact
final gate, and safe per-RF/field diagnostics in ONE pass; it seals all BLOCK
evidence in the current run. No separate diagnostic operator or model call.
If output still fails, the per-RF reason is actionable rather than just
aggregated codes. A PASS enables only candidate DRAFT replay (no approval,
apply or FROZEN). Distinct future projects require end-to-end generation tests
under the Multiprovider contract; successful Pilot B recovery is not proof
of universal local-model reliability.


## COR218 — Autoría local de revisión focalizada y Quality Gate verificable

- Fuente: Vision/Scope FROZEN desde estado runtime; B0 desde `project.yaml`.
- Hallazgo: los checkpoints son estructuralmente válidos, pero RNF funcionales,
  verificaciones truncadas y alcance diferido pueden atravesar el gate anterior.
- Nuevo control: `r02_07_quality.inspect_requirements` produce IDs/target/campo y
  severidad. BLOCK de alta confianza; REVIEW_REQUIRED para ambigüedades.
- Revisión L-first: solo al solicitar el Owner alternativa vacía de un DRAFT local
  sin plan ni aprobación, DevPilot pide JSON a Ollama para reparar RNF defectuosos.
  El modelo escribe `control`/`verification`, DevPilot conserva IDs, alcance y
  el texto completo de los RF. Máximo dos intentos explícitos por hash de input,
  sin auto-retry y sin reset del presupuesto histórico de GLOBAL.
- La revisión genera candidato nuevo inmutable con SHA, lineage y provenance;
  **los ocho checkpoints de generación permanecen byte a byte intactos**.
- Receipts de error contienen únicamente códigos, ID y métricas. No guardan
  prompts, secretos ni texto rechazado. Solo endpoint loopback; sin API externa.
- Revisión humana: no equivale a aprobar; antes de FROZEN debe comprobar
  semántica, reglas de negocio, métricas y decisiones. Un JSON/schema válido no
  acredita calidad completa.
- COR218 es primera vertical de refinamiento. RF complejos, coverage industrial
  y evaluación cuantitativa de segundo dominio siguen pendientes de aceptación.

### COR219 — Reparación L-first condicionada al último intento COR218

La evidencia Windows COR218 documentó `R0218_REPAIR_NO_CHANGE` con `done_reason=stop`, 201719 ms y cuatro RNF objetivo. El texto de salida rechazado no está en los recibos seguros. COR219 no reinicia el presupuesto: mantiene el mismo hash de entrada `r0218-focal-local-quality-repair-v1` y utiliza solamente el intento ordinario 2/2 restante, mediante una acción Owner explícita. Se reemplaza el instructivo del modelo por una tarea de calidad no funcional más precisa y se registran indicadores booleanos de cambio por campo/ID sin almacenar propuestas crudas en evidencia compartible. Cada RNF requiere al menos un cambio real; persisten las validaciones de calidad contra el Scope FROZEN, de documento integrado y las de seguridad. El segundo rechazo es definitivo para este contrato y obliga a adjudicar otra estrategia, sin reintentos silenciosos. No se modifican checkpoints, FROZEN, RF existentes, aprobación ni estado lifecycle. La revisión manual exige diff y decisión Owner separada.


### COR220 — evitar falsos PASS en calidad semántica (propuesta focal)
- La clasificación RF/RNF no puede depender solo de `el sistema debe` ni de una palabra como `consistencia`: se reconocen funciones nominalizadas sin atributo de calidad.
- Una función de IA explícitamente diferida en Scope sigue siendo diferida aunque aparezca nominalizada como RNF. No se altera la autoridad del Scope.
- Los RNF de integridad con pruebas que no verifican las relaciones de estado relevantes reciben REVIEW_REQUIRED, no BLOCK automático, porque la equivalencia semántica necesita evaluación del contexto.
- Un PASS léxico/estructural no constituye aprobación Owner ni calificación profesional.
- Este cambio NO habilita inferencias, presupuestos, edición FROZEN ni promoción Git.


### COR220 — Integración de evaluación y autoría por obligación (2026-10-21)

- Operación sucesora `COR220.one-task-per-rnf.v1`: input_hash nuevo, ligado a
  DRAFT predecesor y fuentes FROZEN. **No** reinicia el presupuesto 2/2 de
  COR218/COR219 ni modifica los ocho checkpoints segmentados.
- Quality Gate detecta funcionalidades nominalizadas y capacidades IA diferidas;
  las verificaciones débiles de integridad y riesgos RF se mantienen como
  REVIEW_REQUIRED, no se convierten en evidencia de calidad profesional.
- La ruta Multiprovider actual solicita al **mismo Ollama local** a lo sumo
  DOS obligaciones RNF independientes en una acción Owner. Solo publica nuevo
  candidato DRAFT si ambas propuestas pasan schema, cambios, calidad y postgate.
  Cuando hay más de dos targets BLOQUEA antes de llamar al modelo.
- Recibo seguro persistido ANTES de cada llamada; no hay retry silencioso tras
  interrupción. Una operación con intento iniciado no se reinicia por otro clic.
  Los recibos contienen IDs/códigos/hashes y nunca el texto privado.
- Un PASS técnico sigue condicionado a revisión Owner del documento integral,
  correspondencia Vision/Scope, decisiones empresariales y riesgos; no auto-FROZEN.
- La capacidad aquí validada es una vertical correctiva (dos RNF) y NO demuestra
  generalización multi-dominio; corresponde evaluarla antes de promoción.

## COR221 — successor governed after COR220 RNF-003 BLOCK (2026-10-21)

- COR220 produced an authoritative `R0220.structured_repair.v1` receipt: `BLOCK`, `model_calls_started=1`, target `RNF-003`; `RNF-004` was not attempted. Replaying COR220 is forbidden.
- COR221 has an independent input hash/receipt (`R0221.structured_repair.v1`), only enabled if the exact former COR220 input context has that failed receipt. The previous response is not stored and cannot be used to reconstruct rejected content.
- A single explicit Owner UI action authorizes at most two local model calls. Objectives are bound to the current Pilot B Scope: consistency of low-stock classification for RNF-003 (SC-IN-04, SC-AC-05); confidentiality of operational queries for RNF-004 (SC-AC-07, SC-AC-08). This is focused remediation, not a general RNF classifier.
- If the source lacks these obligations, block *before* any model call. Persist per-target attempt receipts before calling Ollama, store exact gate finding IDs but no prompt or response, stop upon first failure and never publish partial content. A failed/unknown COR221 receipt is consumed and must not be replayed.
- Neither candidate DRAFT nor eight segment checkpoints nor frozen Vision/Scope are modified by the patch operator. The model may propose a new DRAFT, which must pass the existing quality/postgate checks and Owner review. No apply/FROZEN/Architecture/R02-08 permission derives from this correction.
- The UI's `unidad 1 de total por confirmar` during focal repair describes old segmented progress and is a UX finding, not an authoritative count of COR221 model calls. The runtime receipt is authoritative.
