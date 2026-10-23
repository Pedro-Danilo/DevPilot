# Plan de desagregación R01 — 15 sprints / 15 prompts

- **Programa:** MP132 v1.1.0 Owner-133, adendas propuestas post-M0.
- **Baseline vivo de referencia:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Antes de cualquier sprint, rebind al HEAD real.
- **Resultado R00:** `CLOSED_PASS_WITH_FINDINGS`, COR-151. Ocho ítems aceptados, R0-09 diferido a R2.
- **Ámbito:** exclusivamente los 16 IDs de `BACKLOG_R01_132.md`; ningún source change durante esta planificación.
- **Autoridad:** planificación propuesta, **no** `SPRINT_EXECUTION_APPROVED` ni `OWNER_APPROVED` individual.

## Matriz de sprints, IDs y gates

| Sprint | Objetivo | IDs estables | Tema | Estado |
|---|---|---|---|---|
| R01-01 | Higiene documental M0 y primer bridge Story→Envelope | MP131-R1-01 | `HIGIENE_Y_STORY_BRIDGE` | DRAFT |
| R01-02 | Estado de candidatos, idempotencia y provenance | MP131-R1-02 | `CANDIDATE_LIFECYCLE` | DRAFT |
| R01-03 | ModelAdapter y negotiation por capacidades | MP131-R1-03 | `MODEL_ADAPTER` | DRAFT |
| R01-04 | Policy/budget y GenerationRoutePolicy D/L/E | MP131-R1-04, MP132-R1-12 | `ROUTE_POLICY` | DRAFT |
| R01-05 | PESP y Artifact Profiles v2 primera vertical | MP131-R1-05, MP132-R1-08 | `PESP_PROFILES` | DRAFT |
| R01-06 | Catalog/Coverage ejecutable | MP132-R1-09 | `COVERAGE_GATE` | DRAFT |
| R01-07 | Publicación humana Markdown y Source Registry | MP132-R1-10 | `MARKDOWN_PUBLICATION` | DRAFT |
| R01-08 | Successor inmutable y ChangeImpact acotado | MP132-R1-11 | `FROZEN_SUCCESSOR` | DRAFT |
| R01-09 | Harness de evaluación de candidatos | MP131-R1-06 | `EVAL_HARNESS` | DRAFT |
| R01-10 | Settings persistente backend, policy y runtime | MP132-R1-13 | `SETTINGS_BACKEND` | DRAFT |
| R01-11 | Settings Home UX y browser contract | MP132-R1-13 | `SETTINGS_BROWSER` | DRAFT |
| R01-12 | Trazas provider/agent y coste-origen | MP131-R1-07 | `OBSERVABILITY_ORIGIN` | DRAFT |
| R01-13 | WorkflowStatusProjection compartida | MP132-R1-14 | `STATUS_PROJECTION` | DRAFT |
| R01-14 | Project Layout vs TechnologyProfile | MP132-R1-15 | `PROJECT_LAYOUT` | DRAFT |
| R01-15 | Madurez M1 y cierre de la primera vertical | MP132-R1-16 | `M1_MATURITY_GATE` | DRAFT |

## Rationale de secuenciación
1. El bridge y la reconciliación documental real M0 comparten la primera mutación R01-01, para evitar un sprint administrativo extra. El informe identifica contradicciones actuales vs referencias históricas; solo corrige las primeras, mantiene todos los recibos.
2. Candidate lifecycle y ModelAdapter preceden al routing/fallback, y los perfiles preceden Coverage y publicación.
3. FROZEN/ChangeImpact exige autoridad documental antes; Eval Harness consume candidate+routing+doc outputs.
4. Settings se divide en persistencia backend y pruebas browser, porque `NOT_TESTED` en R00-04 no equivale a UX PASS.
5. Madurez M1 se adjudica por alcance demostrable, no por cantidad de clases. No obliga full regression automáticamente.

## Gestión de cierres de ventana de herramientas
Cada sprint tiene 6 checkpoints en su documento y entrega autocontenida de tamaño acotado. El operador Python trabaja fuera de `DevPilot_Local`, conserva estados y outputs idempotentes, y nunca depende de carpetas temporales de otra conversación. Al completar cada entrega, producir `CHECKPOINT.md` y manifest de versiones/hashes. Ni pipelines recursivos ni muchas confirmaciones Owner triviales.

## Riesgos no trasladables silenciosamente
- `MP132-R0-09` diferido a R2 para GPU/VRAM/model latency con evidencia real, no realizarlo en R1.
- MP-1B y R1 ejecución NOT_AUTHORIZED. El cierre M0 únicamente habilita planificación.
- Settings persistent/UX y modelos reales no declarados completados sin prueba.
- `source_registry.json` puede seguir declarando `current_micro_sprint=MP132-R00-03` a pesar del cierre externo COR-151: reconciliar en primer sprint mutativo si auditoría confirma vigencia del campo.
- El overlay actual ya contiene `1752_ENTRIES`; no aplicar de nuevo COR-150.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- **Disposición final:** R01-01..15 `CLOSED/WINDOWS_PASS`, M1 `PASS_WITH_FINDINGS`. Este documento registra su **plan histórico** y no debe ejecutarse de nuevo. Fuente de cierre: `R01_CLOSEOUT_172.md`.
