---
doc_id: "DEVPL-GSDLC-13-C-01-SEMANTIC-ARTIFACT-QUALITY-CORRECTIVE-PROJECTION"
title: "DEVPL-GSDLC-13-C-01 — Corrective de calidad semántica de artefactos Pre-code"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-24"
supersedes: "DEVPL_GSDLC_13_C_01_SEMANTIC_ARTIFACT_QUALITY_CORRECTIVE_PROJECTION_v1_0_0"
source_authority: "repo442 / d6e40d96ff72d649752565ee49798990b08a3375"
checkpoint: "13-C-01"
target_mode: "bounded-corrective"
full_regression: 0
implementation_status: "IMPLEMENTED_CANDIDATE_PENDING_WINDOWS_VALIDATION"
approval: "OWNER_APPROVED_2026-09-24"
---

# DEVPL-GSDLC-13-C-01 — Corrective de calidad semántica de artefactos Pre-code

## 1. Decisión arquitectónica

Este corrective **no intentará resolver comprensión general de lenguaje natural mediante reglas heurísticas crecientes**.

La ruta baseline seguirá siendo:

`sin API externa + sin modelo obligatorio + determinística + reproducible`

pero el determinismo se aplicará sobre una **representación semántica intermedia estructurada y gobernada**, no directamente sobre fragmentos de texto libre.

Modelo:

```text
Business need libre
        ↓
extracción conservadora de candidatos
        ↓
PreCode Semantic Model — runtime, no project source
        ↓
confirmación/corrección Owner cuando exista ambigüedad
        ↓
modelo semántico confirmado
        ↓
renderers determinísticos
        ↓
Product Vision
        ↓
MVP Scope
        ↓
Requirements
        ↓
quality gates determinísticos
        ↓
review → diff → approval → apply → freeze
```

El principio es:

> DevPilot puede automatizar la estructuración y la generación, pero no debe inventar una interpretación de negocio cuando la fuente no la soporta de forma inequívoca.

## 2. Objetivo

Corregir el bloqueo semántico de `13-C-01-retest-02` y permitir que DevPilot produzca, por la ruta local sin API:

- Product Vision profesional y grounded;
- MVP Scope delimitado y trazable;
- Requirements verificables y trazables;

sin:

- depender de un LLM;
- hardcodear el piloto de inventario/ventas;
- convertir regex en un sustituto de análisis de negocio;
- requerir que el Owner escriba manualmente archivos Markdown;
- permitir que artefactos semánticamente inválidos lleguen a `FROZEN`.

## 3. Alcance y límites de la garantía

### 3.1 Lo que el baseline determinístico sí debe garantizar

- estructura documental profesional mínima;
- IDs estables;
- trazabilidad source → semantic item → artifact item;
- ausencia de fragmentos nominales presentados como capacidades/RF;
- separación entre contexto, actor, capability, constraint y open question;
- no invención de métricas, prioridades o reglas de negocio ausentes;
- propagación material Vision → Scope → Requirements;
- requirements con statement, fuente, prioridad gobernada, acceptance criterion y verification method;
- detección fail-closed de ambigüedad crítica;
- determinismo: mismo modelo semántico confirmado → mismos documentos;
- cero red/API/costo en baseline;
- revisión humana obligatoria antes de source write.

### 3.2 Lo que NO debe prometer

El baseline determinístico **no garantiza comprensión semántica general de cualquier texto libre** ni equivalencia a un analista senior de requisitos.

Cuando el input sea ambiguo, insuficiente o contenga conceptos que no puedan mapearse con seguridad, DevPilot debe:

1. conservar el contexto literal;
2. registrar la ambigüedad;
3. generar una pregunta/decisión abierta concreta;
4. impedir freeze si la ambigüedad es crítica para el artefacto;
5. pedir al Owner decidir mediante UI gobernada.

## 4. Defectos confirmados que debe resolver

1. `_business_clauses()` segmenta sintácticamente texto y convierte descripción/contexto en pseudo-capabilities.
2. Product Vision mezcla business context con capacidades.
3. Scope propaga los fragmentos defectuosos.
4. Requirements convierte fragmentos en RF mediante una plantilla sintáctica.
5. `artifact-profile` comprueba forma/headings pero no suficiencia semántica.
6. El Owner puede revisar el Markdown, pero la ruta `DEVPL_MOCK` no ofrece una corrección semántica provenance-preserving clara.
7. El diff es técnicamente correcto pero su baseline/preimage no es autoexplicativo.
8. Los tests anteriores prueban dependencia y estructura, pero no una matriz suficiente de calidad semántica.

## 5. PreCode Semantic Model

Introducir un modelo runtime versionado, por ejemplo:

`devpilot.gsdlc13c01.pre_code_semantic_model.v1`

No debe escribirse como artefacto source del Greenfield. Puede persistirse bajo `outputs/pre_code_wizard/...` junto con el state/trace.

### 5.1 Estructura mínima

```yaml
schema_id:
workspace_id:
source_refs:
business_context:
actors:
outcomes:
capabilities:
constraints:
open_questions:
decisions:
quality_state:
```

### 5.2 Semantic item

Cada item derivado debe contener como mínimo:

```yaml
id: CAP-001
kind: CAPABILITY | ACTOR | OUTCOME | CONSTRAINT | CONTEXT | OPEN_QUESTION
statement:
source_excerpt:
source_ref:
confidence_class: EXPLICIT | DERIVED_SAFE | AMBIGUOUS
owner_confirmed:
status: CANDIDATE | CONFIRMED | REJECTED | OPEN
```

No utilizar un porcentaje opaco de confianza.

`EXPLICIT` y `DERIVED_SAFE` deben tener reglas documentadas.
`AMBIGUOUS` nunca se convierte automáticamente en requirement FROZEN.

## 6. Extracción baseline: conservadora, no “NLP general”

La extracción determinística inicial puede:

- normalizar el texto;
- separar oraciones completas;
- detectar construcciones explícitas de necesidad/capacidad;
- identificar constraints ya estructurados en Project Context;
- preservar evidence spans;
- proponer candidatos.

Debe evitar:

- usar cada coma como frontera semántica;
- tratar sustantivos/categorías aisladas como capability;
- expandir verbos genéricos como `administrar`, `gestionar`, `controlar` a CRUD detallado sin confirmación;
- inventar reglas, actores, métricas o prioridades;
- convertir una cláusula subordinada en requisito;
- usar listas específicas del piloto como reglas de producción.

### 6.1 Regla fail-closed

Si el sistema no puede producir un conjunto mínimo coherente de capabilities explícitas o seguras:

`SEMANTIC_MODEL_CONFIRMATION_REQUIRED`

No debe producir un documento “profesional-looking” para ocultar incertidumbre.

## 7. Confirmación Owner integrada al Guided SDLC

La confirmación semántica se integra dentro de `13-C-01`; no crea un nuevo checkpoint.

En Product Vision DRAFT la UI debe exponer una sección compacta, por ejemplo:

**Base semántica derivada**

- contexto detectado;
- capacidades candidatas;
- constraints;
- decisiones abiertas.

El Owner puede:

- confirmar;
- corregir wording;
- reclasificar item;
- rechazar item;
- resolver pregunta abierta;
- agregar una capacidad legítima que estaba implícita pero que él confirma como parte de la necesidad.

Eso es una **decisión de producto del Owner**, no escritura externa del proyecto.

### 7.1 Provenance

Registrar:

```yaml
origin_mode: DEVPL_MOCK
semantic_model_sha256:
owner_semantic_reviewed: true
owner_edits:
semantic_model_confirmed_sha256:
```

El Markdown generado sigue teniendo origen `DEVPL_MOCK`; no debe convertirse silenciosamente en `MANUAL` por una corrección del Owner dentro del flujo gobernado.

## 8. Generador v3

Nueva versión:

`deterministic-semantic-model-template-v3`

No modificar semánticamente `deterministic-context-template-v2`.

El v3 recibe **solo**:

- Project Context gobernado;
- semantic model confirmado;
- upstream FROZEN cuando corresponda.

No vuelve a interpretar el business need libre durante Scope/Requirements.

## 9. Product Vision profesional

Debe renderizar:

### Resumen ejecutivo
Qué producto es y para quién, sin diseño técnico.

### Problema
Contexto fuente preservado y sintetizado sin introducir solución.

### Usuario/actor
Solo actores `CONFIRMED`.

### Propuesta de valor
Outcome(s) `CONFIRMED`, sin métricas inventadas.

### Capacidades MVP
Solo `CAPABILITY` confirmadas, redactadas como capacidades completas.

### Success signals
Distinguir:
- `observable_signal`;
- `metric_pending_owner_decision`.

No fabricar números.

### Restricciones
Project Context + constraints confirmados.

### Preguntas abiertas
Solo las no bloqueantes. Una pregunta crítica impide freeze.

### Post-MVP
No inventar funcionalidades.

## 10. MVP Scope profesional

Debe derivarse exclusivamente de Vision FROZEN y semantic model confirmado.

Separar:

- `In scope`;
- `Out of scope`;
- `Constraints`;
- `Dependencies`;
- `Open decisions`;
- `Exit criteria`.

Cada item In Scope debe:
- tener ID estable;
- mapear a una capability Vision;
- ser una capacidad accionable;
- no ser una categoría/contexto.

No convertir automáticamente la ausencia de información en una exclusión.

## 11. Requirements profesionales

El requirement model runtime debe ser estructurado antes de renderizar Markdown.

### 11.1 Requirement record mínimo

```yaml
id:
type: FR | NFR | CONSTRAINT
statement:
source_capability_ids:
priority:
acceptance_criteria:
verification_method:
open_decisions:
```

### 11.2 Reglas

#### Functional Requirement

Debe describir comportamiento observable del sistema.

No válido:

`El sistema debe soportar: cosméticos.`

Válido en estructura, no como hardcode:

`El sistema debe <acción observable> <objeto/resultado>.`

#### Prioridad

No inferir prioridades arbitrarias.

Regla baseline:
- capability confirmada como `MVP` → `MUST`;
- fuera del MVP → no genera FR de MVP;
- cualquier excepción requiere decisión explícita.

#### Acceptance criteria

No inventar business rules.

Puede derivarse automáticamente solo cuando la fuente expresa resultado observable suficiente.

Si falta información necesaria para un criterio útil:
- generar `OPEN-QUESTION`;
- no fabricar un Given/When/Then falso;
- bloquear freeze si el requisito no es verificable sin esa decisión.

#### Verification method

Usar vocabulario cerrado:
- `TEST`;
- `DEMONSTRATION`;
- `INSPECTION`;
- `ANALYSIS`.

Asignación determinística según tipo de statement, con override gobernado por Owner.

### 11.3 NFR vs constraints

No etiquetar governance/configuration como NFR solo por conveniencia.

- constraints del Project Context → `CONSTRAINT`;
- NFR → debe expresar atributo de calidad evaluable;
- si falta métrica/umbral y es necesaria para evaluar → open decision o constraint provisional explícito.

## 12. Semantic Quality Gate

El quality gate no pretende “medir inteligencia”. Verifica invariantes observables.

Debe ejecutarse antes de `APPROVAL_REQUIRED`.

### 12.1 Gate Product Vision

BLOCK si:
- no existe actor/outcome/capability suficiente para comprender el producto;
- capability es un fragmento/contexto/categoría aislada;
- hay critical open questions sin resolver;
- una capability no tiene source evidence;
- se introduce stack/arquitectura no autorizada.

### 12.2 Gate Scope

BLOCK si:
- un item In Scope no traza a Vision FROZEN;
- no es accionable;
- Scope agrega capacidad no autorizada;
- critical open decisions impiden delimitar MVP.

### 12.3 Gate Requirements

BLOCK si:
- FR no describe comportamiento observable;
- falta source capability;
- falta prioridad;
- falta criterio de aceptación verificable;
- falta verification method;
- existen placeholders sintácticos genéricos;
- un NFR no es evaluable y debería ser constraint/open decision;
- una critical open question afecta el comportamiento requerido.

El gate devuelve findings concretos por item, no un score agregado opaco.

## 13. Revisión y edición

### 13.1 Ruta preferida

La corrección semántica se hace sobre el Semantic Model, no editando Markdown como mecanismo principal.

Flujo:

```text
DevPilot propone semantic model
        ↓
Owner confirma/corrige items
        ↓
DevPilot regenera DRAFT
        ↓
Owner revisa documento
        ↓
Validar y preparar diff
```

### 13.2 Edición Markdown

Puede mantenerse `MANUAL` como ruta explícita existente.

No es requisito de este corrective construir un editor raw Markdown con lineage complejo si la revisión semántica estructurada cubre la necesidad de corrección del baseline.

Esto reduce alcance y superficie de fallos frente a v1.0.0.

## 14. Diff explicable

Mantener el unified diff actual y su autoridad.

Añadir únicamente copy/contexto:

- `Comparando: source actual → DRAFT propuesto`;
- path;
- `Archivo nuevo — baseline vacío` cuando aplique;
- base SHA-256;
- proposed SHA-256;
- diff SHA-256;
- aviso de invalidación si cambia el DRAFT/modelo semántico.

No introducir un segundo motor de diff.

## 15. Lifecycle/frontmatter

No mutar el Markdown después de approval para cambiar `status: draft` a `FROZEN`, porque rompería el hash aprobado.

En este corrective:

- mantener runtime state como authority de lifecycle;
- sustituir o aclarar el frontmatter de nuevas propuestas para que no afirme un lifecycle contradictorio;
- opción preferida: eliminar `status: draft` del template v3 y añadir una nota/metadata estable de que el estado gobernado se consulta en DevPilot;
- preservar compatibilidad de artifact validators.

No ampliar esto a una migración masiva de documentos históricos.

## 16. Tests: no sobreajustar al piloto

No es suficiente comprobar que desaparezcan frases específicas del piloto.

Agregar una fixture matrix pequeña y diversa.

### 16.1 Casos positivos mínimos

1. necesidad con varias capacidades explícitas;
2. necesidad con contexto empresarial + capacidades;
3. capacidad expresada con conjunciones;
4. múltiples actores explícitos;
5. constraints explícitos;
6. upstream Vision/Scope modificados;
7. requirements con criterios derivables;
8. pausa/restart con semantic model persistido.

### 16.2 Casos negativos mínimos

9. categorías nominales aisladas;
10. texto descriptivo sin capacidad;
11. verbo genérico ambiguo (`gestionar`, `administrar`) que exige confirmación;
12. requisito sin criterio verificable;
13. NFR no medible presentado como NFR;
14. capability sin source evidence;
15. critical open question sin resolver;
16. intento de hardcode del piloto detectado mediante fixture alternativa.

### 16.3 Propiedades a comprobar

- determinismo;
- provenance;
- misma entrada confirmada → mismo output;
- cambio semántico upstream → cambio downstream;
- sin red/API/costo;
- source write solo después de approval;
- restart/resume;
- no CRLF/LF como autoridad semántica;
- findings determinísticos;
- no Full Regression.

## 17. UI/UX mínima del corrective

Cambios estrictamente necesarios:

1. mostrar Semantic Model resumido/editable en etapa actual;
2. distinguir `candidate`, `confirmed`, `open`;
3. mostrar preguntas críticas;
4. impedir review cuando el semantic model no está listo;
5. explicar el diff;
6. conservar DevPilot local como ruta recomendada C-01.

No tocar todavía Architecture/Security/Test Strategy/Traceability.

`CAP-13C02-LOCAL-DERIVATION-001` permanece como forward risk de C-02.

## 18. Archivos objetivo probables

- `.devpilot/gsdlc/pre_code_wizard_catalog.json` solo si requiere declarar generator/version/capability;
- `src/devpilot_core/application/pre_code_wizard_service.py`;
- nuevo módulo pequeño y específico, recomendado:
  - `src/devpilot_core/application/pre_code_semantic_model.py`
  o equivalente;
- validator stage-specific o extensión acotada del review validator;
- `ui/web/src/pages/PreCodeWizardView.ts`;
- `ui/web/src/api/types.ts`;
- tests focales de C-01.

Evitar introducir un framework NLP, parser de dependencias, vector DB o modelo nuevo.

## 19. Persistencia y estados sobrevivientes

El operator/retest debe asumir que existen first-attempt FROZEN artifacts defectuosos y state/trace históricos.

No destruir evidencia.

La implementación debe definir una recuperación controlada del Greenfield para el nuevo retest:

- preservar `13-C-01-retest-02` intacto;
- no reutilizar los artefactos defectuosos como oracle;
- invalidar/reabrir C-01 mediante mecanismo gobernado diseñado para test;
- no usar `git reset --hard`, `git clean` ni edición manual para ocultar el first-attempt;
- semantic model/state nuevo debe ser resume-aware;
- restart entre etapas debe conservar decisiones Owner ya confirmadas.

El plan Windows concreto de recuperación se diseña al implementar el corrective; esta proyección no ejecuta ninguna mutación.

## 20. Criterios de éxito del corrective

PASS técnico local/Windows únicamente si:

- generator v3 no usa `_business_clauses()` como capability authority;
- semantic model existe y es trazable;
- ambigüedad crítica bloquea en lugar de inventar;
- Owner puede confirmar/corregir el modelo desde UI;
- Vision/Scope/Requirements se renderizan determinísticamente;
- semantic quality gate bloquea ejemplos inválidos;
- fixture matrix positiva/negativa pasa;
- downstream dependency sigue siendo material;
- diff continúa approval-bound;
- operator project writes=0;
- external API/model required=false;
- network=false;
- cost=0;
- Full Regression=0;
- build/smokes afectados PASS.

## 21. Retest de `13-C-01`

Después de Windows validation y promoción del successor:

1. preservar evidence de retest-02;
2. ejecutar recuperación gobernada C-01;
3. iniciar retest nuevo desde Product Vision;
4. usar baseline `DevPilot local / sin API`;
5. revisar Semantic Model;
6. resolver preguntas críticas como Owner;
7. generar/revisar Vision;
8. capturar DRAFT y diff legibles;
9. approve/apply/freeze;
10. repetir para Scope;
11. repetir para Requirements;
12. evaluar calidad de los tres documentos antes de adjudicar PASS;
13. solo si `13-C-01 PASS`, autorizar `13-C-02`.

## 22. Estrategia multi-modelo

Este corrective no requiere LLM.

La arquitectura debe quedar abierta a que, después del baseline determinístico:

```text
SemanticCandidateProvider
    ├── DeterministicProvider   ← obligatorio / gratis / baseline
    ├── LocalModelProvider      ← futuro / Ollama-LM Studio
    └── ExternalModelProvider   ← futuro / policy + approval + cost
```

Todos deben producir el mismo `PreCode Semantic Model` schema y pasar los mismos quality gates.

No implementar Local/External providers dentro de este corrective.

## 23. Decisión de empaquetado del trabajo

Este corrective puede implementarse como **un único bounded corrective sprint** bajo `SPRINT_DEVPL_GSDLC_13_C_v1_1_0_APPROVED`.

No requiere:
- nuevo backlog;
- nueva fase;
- múltiples sprints;
- replanificación del roadmap.

Razones:

- un solo checkpoint bloqueado (`13-C-01`);
- una sola superficie funcional (`Guided Pre-code C-01`);
- una misma cadena de datos Vision → Scope → Requirements;
- un único propósito de acceptance;
- no hay cambio de arquitectura global de modelos;
- no se toca C-02;
- Full Regression sigue fuera de alcance.

### 23.1 Work packages internos del mismo sprint

Para control de implementación, sin crear sprints separados:

- **WP-A — Semantic Model + persistencia/resume**;
- **WP-B — Generator v3 + semantic quality gates**;
- **WP-C — UI de confirmación + diff explainability**;
- **WP-D — fixture matrix + selective tests/build + Windows operator**.

Estos WP son orden interno de ejecución, no nuevos backlogs/sprints.

## 24. Condiciones que obligarían a desagregar

Detener y replanificar solo si durante implementación aparece alguno:

- necesidad de un parser NLP general o dependencia pesada;
- necesidad de introducir un LLM obligatorio para baseline;
- cambios invasivos al lifecycle/approval engine compartido;
- migración de documentos históricos;
- expansión a Architecture/Security/Test Strategy;
- cambio incompatible del Project Context schema;
- Full Regression requerido por impacto transversal real.

En ausencia de estas condiciones, mantener un solo corrective.

## 25. Veredicto de esta proyección

`v1.0.0`: **NO APROBAR TAL COMO ESTÁ**.

Motivo: dirección correcta, pero sobreconfía en heurísticas de extracción semántica desde texto libre y mezcla el blocker S1 con una ampliación raw-Markdown edit que no es necesaria para resolverlo.

`v1.1.0`: **APPROVED PARA IMPLEMENTACIÓN**.

La v1.1.0 conserva el baseline sin API y determinístico, pero cambia la unidad de autoridad:

```text
texto libre
≠
artefacto profesional directo

texto libre
→ candidato semántico
→ confirmación Owner cuando corresponda
→ modelo semántico gobernado
→ compilación determinística
→ quality gate
→ artefacto profesional
```

Aprobación explícita concedida por el Owner el 2026-09-24. La implementación se materializa como candidate sujeto a validación Windows antes de promoción.
