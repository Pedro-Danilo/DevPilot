---
doc_id: "DEVPL-GSDLC-13-C-01-DRAFT-FIRST-SEMANTIC-REVIEW-CORRECTIVE-PROJECTION"
title: "DEVPL-GSDLC-13-C-01 — Corrective Draft-first + Decision Inbox para revisión semántica"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-25"
source_authority: "repo443 / 7a5afa2c28fc30240ee6e347dde345231134384a"
checkpoint: "13-C-01"
source_retest: "13-C-01-retest-03"
target_mode: "bounded-corrective"
full_regression: 0
implementation_status: "IMPLEMENTED_CANDIDATE_PENDING_WINDOWS_VALIDATION"
approval_required: false
approved_by: "Owner"
approved_at: "2026-09-25"
---

# DEVPL-GSDLC-13-C-01 — Corrective Draft-first + Decision Inbox

## 1. Propósito

Corregir la experiencia y el bloqueo funcional observados en `13-C-01-retest-03` sin descartar la arquitectura semántica introducida en repo443.

La meta es que DevPilot reduzca trabajo y complejidad para el Owner, en lugar de trasladarle la administración interna del modelo semántico.

Experiencia objetivo:

```text
Project Context
      ↓
DevPilot analiza internamente
      ↓
Semantic Model interno
      ↓
DevPilot genera propuesta completa del artefacto
      ↓
Owner revisa el artefacto
      ↓
solo si hace falta:
Decision Inbox con pocas decisiones reales
      ↓
Owner edita opcionalmente
      ↓
validate / diff / approval / apply / freeze
```

El `Semantic Model` se conserva como mecanismo interno de gobernanza, trazabilidad y determinismo, pero deja de ser la interfaz principal de trabajo del Owner.

## 2. Problemas confirmados

Durante `13-C-01-retest-03` se observaron dos problemas diferentes.

### 2.1 Defecto funcional

La confirmación semántica puede terminar en HTTP `403 Forbidden` aunque la causa no sea autorización/RBAC.

Además, una fila opcional vacía creada desde la propia UI puede entrar al payload y bloquear la operación completa.

### 2.2 Defecto de producto/UX

La UI obliga al Owner a revisar y confirmar con demasiada granularidad actores, outcomes, capacidades, constraints y preguntas antes de ver el artefacto completo.

Esto invierte la responsabilidad esperada:

```text
Esperado:
Owner expresa necesidad
→ DevPilot hace el trabajo pesado
→ Owner revisa y decide

Actual:
Owner expresa necesidad
→ DevPilot descompone
→ Owner administra la descomposición interna
→ DevPilot recién genera el documento
```

## 3. Decisión de diseño

**El Semantic Model seguirá siendo autoridad interna de derivación, pero no será un artefacto que el Owner deba administrar directamente.**

El Owner trabajará principalmente con:

- Product Vision;
- MVP Scope;
- Requirements;
- un conjunto pequeño de decisiones excepcionales cuando realmente sean necesarias.

La ruta `DevPilot · Mock local / sin API` debe ser:

```text
MISSING
  ↓
Generar propuesta con DevPilot
  ↓
Semantic Model interno
  ↓
DRAFT completo visible
  ↓
Owner review
  ├── aceptar
  ├── editar
  └── resolver Decision Inbox si existen blockers reales
  ↓
Validar y preparar diff
  ↓
approval
  ↓
apply
  ↓
freeze
```

No debe existir un gate general de microconfirmación del Semantic Model antes de mostrar el DRAFT.

## 4. Alcance

El corrective cubre únicamente `13-C-01`:

- Product Vision;
- MVP Scope;
- Requirements;
- Semantic Model interno;
- Decision Inbox;
- Owner edits del DRAFT;
- manejo de findings semánticos;
- semántica HTTP/API relacionada;
- UX de `PreCodeWizardView`.

Fuera de alcance:

- Architecture;
- Security;
- Test Strategy;
- ADRs;
- Traceability;
- `13-C-02`;
- Ollama/LM Studio;
- External Agent/API;
- arquitectura multi-modelo;
- Full Regression.

## 5. Semantic Model — nuevo rol

Se conserva el schema vigente:

`devpilot.gsdlc13c01.pre_code_semantic_model.v1`

Debe seguir proporcionando internamente:

- source evidence;
- actores;
- outcomes;
- capabilities;
- constraints;
- open questions;
- owner decisions;
- quality state;
- hashes;
- provenance;
- resume/recovery.

### 5.1 Visibilidad

La matriz completa del Semantic Model no debe mostrarse por defecto.

Puede existir una sección secundaria:

`Ver análisis de DevPilot`

para auditoría o usuarios avanzados, colapsada por defecto.

Abrirla no puede ser requisito para completar el journey normal.

## 6. Draft-first

### 6.1 Product Vision

DevPilot debe generar primero una Product Vision completa y legible usando solo información suficientemente segura para ese nivel.

Puede mantener capacidades de alto nivel como:

- administrar productos;
- controlar existencias;
- registrar ventas;
- actualizar inventario tras una venta;
- consultar información de ventas;
- identificar productos con stock bajo.

No necesita resolver antes de Product Vision:

- CRUD exacto;
- campos del producto;
- reglas de eliminación;
- umbral exacto de stock bajo;
- estructura exacta del reporte de ventas;

salvo que alguna decisión sea imprescindible para que la propia Vision sea válida.

### 6.2 MVP Scope

Scope debe derivarse de Vision FROZEN y del Semantic Model interno.

Debe mostrar primero el documento completo.

Solo debe pedir decisiones adicionales si no es posible delimitar el MVP sin ellas.

### 6.3 Requirements

Requirements puede requerir mayor precisión.

El flujo debe ser:

1. generar todos los requisitos que puedan derivarse legítimamente;
2. identificar únicamente decisiones que bloquean requisitos verificables;
3. mostrar esas decisiones en Decision Inbox;
4. guardar respuestas;
5. regenerar únicamente lo afectado;
6. volver a mostrar el documento completo.

## 7. Decision Inbox

Introducir una interfaz compacta de `Decisiones pendientes`.

Debe contener solo preguntas que:

- no pueden resolverse sin inventar;
- son necesarias para el artefacto actual;
- afectan una capacidad o requisito real.

Reglas:

- normalmente `0–3` decisiones visibles por pantalla;
- no una pregunta por cada semantic item;
- agrupar preguntas relacionadas;
- explicar por qué importa;
- mostrar qué parte del artefacto se afecta;
- permitir respuesta directa;
- permitir posponer solo si no es bloqueante;
- una decisión crítica no resuelta sí bloquea;
- una decisión no crítica no debe bloquear innecesariamente.

Ejemplo:

```text
Decisiones pendientes (2)

1. ¿Qué información básica debe mostrar la consulta de ventas?
   [____________________________________________]

2. ¿Cómo debe decidirse que un producto tiene stock bajo?
   [____________________________________________]

[Guardar decisiones]
```

No mostrar en el flujo normal:

- `confidence_class`;
- tipos internos;
- `CANDIDATE/CONFIRMED/REJECTED`;
- IDs internos;
- payload técnico.

## 8. Owner edit del DRAFT

El Owner debe poder editar la propuesta completa antes de `Validar y preparar diff`.

```text
DevPilot genera DRAFT
      ↓
Owner pulsa Editar propuesta
      ↓
modifica contenido
      ↓
Guardar revisión
      ↓
nuevo DRAFT gobernado
      ↓
validate / diff
```

Provenance mínima:

```yaml
origin_mode: DEVPL_MOCK
generated_content_sha256:
owner_edited: true | false
owner_edited_content_sha256:
```

No cambiar silenciosamente a `MANUAL`.

Si existe plan/diff previo y el Owner modifica el DRAFT:

- invalidar plan;
- exigir nuevo validate/diff;
- invalidar approval previo asociado.

## 9. Semantic gates

Los gates de repo443 se conservan.

### Product Vision

BLOCK solo si:

- no se entiende qué producto se intenta construir;
- no existe ninguna capability útil;
- aparecen categorías/contexto como pseudo-capabilities;
- existe una ambigüedad crítica para la propia Vision;
- se inventa arquitectura/stack.

### Scope

BLOCK si:

- agrega capabilities no autorizadas;
- no delimita el MVP;
- no traza a Vision;
- una decisión crítica impide definir in/out scope.

### Requirements

BLOCK si:

- un RF no describe comportamiento observable;
- falta trazabilidad;
- falta prioridad gobernada;
- falta acceptance criterion;
- falta verification method;
- se inventa una regla de negocio;
- una decisión crítica impide verificar el requisito.

Los findings deben indicar:

- qué está mal;
- dónde;
- por qué;
- qué debe corregir o decidir el Owner.

## 10. Corrección del 403

No usar HTTP `403` para un `BLOCK` semántico normal.

Contrato recomendado:

- `401`: no autenticado;
- `403`: autenticado pero no autorizado;
- `409`: transición/estado incompatible;
- `422`: contenido o decisión semántica inválida/incompleta;
- `200` con findings: operación válida que requiere revisión.

La elección final entre `409` y `422` debe mantenerse consistente con el API existente.

### 10.1 Filas opcionales vacías

Una fila opcional totalmente vacía:

- debe ignorarse automáticamente, o
- debe mostrar validación inline antes del envío.

Nunca debe convertir toda la operación en un `403 Forbidden`.

Mensaje esperado:

```text
Falta completar o eliminar este actor.

[________________]

[Completar] [Eliminar]
```

## 11. UX objetivo

Ejemplo para Product Vision:

```text
Product Vision · DRAFT

┌────────────────────────────────────┐
│ Documento completo                 │
│                                    │
│ Problema                           │
│ Usuario                            │
│ Propuesta de valor                 │
│ Capacidades MVP                    │
│ Restricciones                      │
└────────────────────────────────────┘

Decisiones pendientes: 0–N
[Revisar decisiones]   ← solo si existen

[Editar propuesta]
[Validar y preparar diff]

[Ver análisis de DevPilot]  ← avanzado, colapsado
```

El Owner debe poder completar el journey sin abrir `Ver análisis de DevPilot`.

## 12. Diff

Mantener el motor actual.

Mostrar:

- `Comparando source actual → DRAFT propuesto`;
- path;
- base SHA-256;
- proposed SHA-256;
- diff SHA-256;
- aviso de invalidación si se vuelve a editar.

## 13. Resume/recovery

Conservar:

- first-attempt evidence;
- reopen gobernado;
- state/trace;
- Semantic Model runtime;
- Owner decisions;
- DRAFT revisado;
- invalidación de plan/approval.

Después de reiniciar API/UI:

- recuperar DRAFT;
- recuperar Decision Inbox;
- conservar respuestas ya guardadas;
- no repetir decisiones resueltas.

## 14. Tests mínimos

### Funcionales

1. `DEVPL_MOCK` genera Product Vision DRAFT sin microconfirmación previa.
2. Semantic Model sigue existiendo internamente.
3. Vision no produce pseudo-capabilities.
4. Scope deriva de Vision FROZEN.
5. Requirements produce RF verificables.
6. una decisión crítica real genera Decision Inbox.
7. una decisión no crítica no bloquea Vision/Scope.
8. una respuesta de Decision Inbox regenera contenido afectado.
9. Owner puede editar DRAFT sin cambiar a MANUAL.
10. editar invalida plan/diff previo.
11. semantic gates siguen fallando cerrado.
12. C-02 permanece sin cambios.

### UX/API

13. fila opcional vacía no genera request inválido.
14. error semántico no se traduce a 403.
15. 403 queda reservado a autorización.
16. findings aparecen inline.
17. Semantic Model completo está colapsado por defecto.
18. journey normal termina sin abrir detalles avanzados.
19. Decision Inbox solo presenta decisiones actuales/relevantes.
20. restart/resume conserva DRAFT y decisiones.

### Regression selectiva

Mantener:

- C-01 semantic artifact tests;
- derived authoring;
- pre-code wizard;
- auth/RBAC;
- workspace/runtime;
- UI smokes;
- Vite build.

Full Regression: `0`.

## 15. Métricas UX de acceptance

En el retest posterior medir:

- `semantic_items_manually_reviewed_in_normal_flow = 0`;
- `document_first_visible_before_internal_semantic_detail = true`;
- `owner_can_complete_without_advanced_semantic_view = true`;
- `normal_user_terminal_escapes = 0`;
- `owner_can_edit_generated_draft = true`;
- `generic_403_for_semantic_block = false`.

No fijar artificialmente cuántas decisiones críticas puede haber, pero cada una debe ser necesaria para el artefacto actual.

## 16. Source delta probable

Sujeto a verificación durante implementación:

- `src/devpilot_core/application/pre_code_wizard_service.py`;
- `src/devpilot_core/application/pre_code_semantic_model.py`;
- `src/devpilot_core/interfaces/api/routers/guided_sdlc.py`;
- `ui/web/src/api/client.ts`;
- `ui/web/src/api/types.ts`;
- `ui/web/src/pages/PreCodeWizardView.ts`;
- tests C-01;
- documentación/ADR si corresponde.

No introducir dependencia NLP/LLM.

## 17. Seguridad y gobernanza

Se mantienen:

- baseline local/no API;
- generación determinística;
- no network;
- cost=0;
- revisión antes de apply;
- approval exacta;
- source write solo en apply;
- freeze posterior;
- logs/state/trace;
- Git 3-state;
- operator project writes=0;
- no destructive reset/clean;
- no edición externa como ruta de acceptance.

## 18. Decisión de empaquetado

Este corrective **puede implementarse en un único bounded corrective sprint**.

No requiere:

- nuevo backlog;
- nuevo roadmap;
- múltiples sprints;
- fase separada.

### Razones

1. afecta una sola superficie: `13-C-01 / Pre-code`;
2. el Semantic Model ya existe;
3. el cambio principal es de secuencia de interacción;
4. el 403 es localizado;
5. no se toca C-02;
6. no se agregan providers/modelos;
7. no hay nueva infraestructura;
8. puede validarse con selective tests + UI smokes/build;
9. Full Regression sigue fuera de alcance.

### Work packages internos

Sin crear sprints separados:

- **WP-A — Draft-first orchestration**
- **WP-B — Decision Inbox**
- **WP-C — Owner edit + API/UX errors**
- **WP-D — Tests + Windows validation**

## 19. Cuándo desagregar

Detener y replanificar solo si aparece necesidad real de:

- rediseñar globalmente lifecycle;
- modificar approval semantics compartidas;
- cambiar Project Context schema de forma incompatible;
- introducir LLM obligatorio;
- tocar C-02;
- migrar artefactos históricos;
- ejecutar Full Regression por impacto transversal inesperado.

## 20. Criterios de cierre

PASS/CLOSED únicamente si:

- successor parte de repo443;
- source delta exacto;
- Semantic Model sigue interno y trazable;
- DRAFT completo aparece primero;
- Semantic Model completo no requiere interacción normal;
- Decision Inbox solo presenta excepciones reales;
- Owner puede editar DRAFT;
- provenance se conserva;
- gates bloquean defectos reales;
- no existe 403 genérico por contenido;
- filas opcionales vacías no bloquean;
- tests focales PASS;
- UI smokes PASS;
- Vite build PASS;
- network/external API=false;
- operator project writes=0;
- Full Regression=0;
- C-02 unchanged;
- candidate Windows promovido con Git 3-state limpio.

## 21. Retest posterior

Después del cierre Windows debe ejecutarse un nuevo selective retest de `13-C-01`.

`13-C-01-retest-03` queda preservado como BLOCK.

El nuevo retest debe demostrar:

1. DRAFT primero;
2. propuesta completa comprensible;
3. solo decisiones realmente necesarias;
4. edición Owner disponible;
5. sin 403 semántico;
6. Vision/Scope/Requirements con calidad profesional;
7. Architecture sigue `MISSING`.

## 22. Veredicto

**APPROVED / IMPLEMENTATION AUTHORIZED.**

Decisión del Owner:

- implementar como un único bounded corrective sprint;
- no crear backlog/sprints adicionales;
- mantener `13-C-02` fuera de alcance;
- validar en Windows antes de cualquier nuevo selective retest de `13-C-01`.

Flujo previsto:

```text
repo443
   ↓
Draft-first + Decision Inbox corrective
   ↓
Windows validation
   ↓
successor repo
   ↓
nuevo selective retest 13-C-01
   ↓
PASS → 13-C-02
```
