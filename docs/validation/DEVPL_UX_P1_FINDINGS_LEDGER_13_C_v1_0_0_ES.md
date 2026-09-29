---
doc_id: "DEVPL-UX-P1-FINDINGS-LEDGER-13-C"
title: "DEVPL-UX-P1 — Registro de hallazgos del piloto — 13-C"
status: "active"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "working-ledger/not-source-authority"
execution_program: "DEVPL-GSDLC-13"
checkpoint: "13-C-04"
language: "es"
---
# DEVPL-UX-P1 — Registro de hallazgos — 13-C

## Regla

Este ledger registra evidencia del piloto. Un hallazgo meramente estético permanece `OBSERVE_ONLY`; una violación reproducible del contrato Guided/funcional activa corrective acotado. El ledger no sustituye la autoridad del repo ni autoriza por sí solo mutaciones.

## UX-P1-13C04-001 — Indicador de progreso Planning queda congelado en Roadmap

- Superficie: `/planning/roadmap`.
- Clasificación: `FUNCTIONAL_BUG` de estado/next-action Guided.
- Severidad: `S1` para cierre del checkpoint, porque la cabecera contradice el lifecycle server-authoritative y puede enviar al Owner a repetir Roadmap cuando Planning ya está completo.
- Evidencia: `captura_full-roadma_backlog_sprint.png`; código C04_BR_105 con steps hardcodeados `Roadmap=current`, `Backlog/Sprint=upcoming`.
- Estado real observado: Roadmap `FROZEN`, Backlog `FROZEN`, Sprint `FROZEN`, Planning `IMPLEMENTING_READY`.
- Disposición: `CLOSED-BY-C04_BR_106`.
- Evidencia de cierre: header local Planning deriva Roadmap/Backlog/Sprint del estado live y muestra los tres como `done` en `IMPLEMENTING_READY`.

## ACC-13C04-PROJ-001 — Backfill Markdown no equivale a browser E2E de generación

- Clasificación: `ACCEPTANCE_EVIDENCE_GAP`, no bug de la implementación de proyecciones.
- Hecho: C04_BR_105 creó seis `.md` mediante reconciliación del operador porque el runtime ya estaba FROZEN antes de instalar la capacidad.
- Evaluación: backfill válido como migración y hash-bound a JSON; no debe registrarse como prueba de que el flujo histórico UI generó esos archivos.
- Evidencia de producto disponible: lifecycle code escribe proyecciones en DRAFT/REVIEW/APPROVED/FROZEN; focal C04_BR_106 lo prueba sobre workspace temporal sin reconcile.
- Evidencia aún pendiente: un **fresh Planning browser journey** futuro debe observar creación de las proyecciones con `operator_project_writes=0` antes de reclamar browser-level E2E de esta capacidad.
- Disposición: no requiere ampliar C04_BR_106 con una nueva API ni descongelar el proyecto actual; preservar la deuda de aceptación de forma explícita.

## UX-P1-13C04-002 — “Siguiente acción” global contradice Planning completado

- Superficie: encabezado persistente `ShellProjectContext` + `/planning/roadmap`.
- Clasificación: `FUNCTIONAL_BUG` de composición de autoridades Guided.
- Severidad: `S1` para promoción: el encabezado global ordena volver a Roadmap aunque Planning ya está `IMPLEMENTING_READY`.
- Causa: `GuidedSDLCApplicationService` impone `PRE_CODE_READY_PLANNING_NEXT` desde Pre-code READY sin consultar Planning closure; además Planning closure conserva el histórico `GSDLC_09_REQUIRED` y Authoring recomienda `closure`.
- Disposición: `CLOSED-BY-C04_BR_107` para la contradicción global/local de label y boundary.
- Evidencia de cierre parcial: C04_BR_107 hace converger encabezado global, Planning header y Project Status en `story-context-readiness` / Story Code Workbench sin mutar MIPSoftware ni Planning runtime.
- Hallazgo sucesor: la captura full de Project Status expuso un defecto independiente de actionability, registrado como `UX-P1-13C04-003`.

## UX-P1-13C04-003 — Story Code successor visible pero no accionable y Advisor vuelve a Planning

- Superficie: `/project/status` + `Step Action Advisor`.
- Clasificación: `FUNCTIONAL_BUG` de actionability/authority ordering.
- Severidad: `S1` para promoción, porque la siguiente acción server-authoritative existe y la ruta UI está implementada, pero el botón `Continuar` se deshabilita falsamente y el Advisor recomienda volver a Planning.
- Evidencia: `02_c04_107_project_status_build_current.png` y captura full de C04_BR_107.
- Causa UI: `ProjectStatusView` mantiene un map local incompleto en vez de reutilizar `navigationPathFromServerTarget`; `ui.story-code-workbench` no se resuelve a `/story/code`.
- Causa server: `step_actions_primary()` prioriza `pre_code_profile.all_stages_frozen` sobre el boundary reconciliado `story-context-readiness`.
- Disposición: `ACTIVE-CORRECTIVE` → C04_BR_108.
- Criterio de cierre: `Continuar` habilitado hacia Story Code Workbench, Advisor coherente con Story Code, y Planning/runtime/proyecciones byte-identical.

## GOV-13C04-001 — Revisión intencional de artefactos FROZEN no es uniforme

- Clasificación: `PRODUCT_GOVERNANCE_HARDENING_GAP`, no defecto activado por el checkpoint actual.
- Planning: ya exige versión semántica sucesora después de FROZEN.
- Artifact lifecycle genérico: drift externo APPROVED/FROZEN invalida approval y pasa a `REVALIDATION_REQUIRED`; la lineage incrementa `artifact_version`.
- Pre-code Wizard: no expone todavía una ruta general Owner-driven “crear versión sucesora” para cualquiera de los siete artefactos FROZEN; existe reapertura C-01 acotada a retest y reconciliation por drift.
- Disposición: preservar como hardening antes de declarar madurez industrial completa y activar corrective específico si 13-D descubre una necesidad real de cambiar Requirements/Architecture/Security FROZEN. No ampliar C04_BR_107 con ese workflow.

## TPL-13C04-001 — Profiles actuales son mínimos, no exhaustivos universales

- Clasificación: `DESIGN_HARDENING`.
- Hecho: `ArtifactProfile` define `required_headings` como mínimo y `recommended_headings`; el catálogo Pre-code está `implemented-initial`.
- Implicación: las plantillas actuales validan estructura mínima y, para C-01/C-02, se complementan con validaciones semánticas/técnicas, pero no garantizan todos los apartados posibles de todo proyecto profesional.
- Disposición: evolucionar a perfiles v2 con secciones `required/recommended/conditional`, condicionadas por tipo de producto, datos, riesgo, despliegue, AI/agentic, compliance y arquitectura. No reabrir artefactos FROZEN del piloto sin una necesidad material demostrada.

## Estado del checkpoint

- C04_BR_107 post-UI técnico: PASS para sus assertions declaradas, pero promoción bloqueada por `UX-P1-13C04-003`.
- Promoción acumulada: detenida hasta C04_BR_108.
- Full regression: no autorizada; sigue en 0.
- Hallazgos funcionales activos: 1 (`UX-P1-13C04-003`); `UX-P1-13C04-001` y `UX-P1-13C04-002` cerrados por 106/107 respectivamente.
- Gaps de evidencia abiertos: 1 (`ACC-13C04-PROJ-001`).

## PASS/BLOCK

PASS del checkpoint solo cuando C04_BR_108 haga accionable el successor Story Code tanto en `Próxima acción` como en `Qué puedes hacer ahora`, manteniendo Planning FROZEN y sin modificar runtime/proyecciones. BLOCK si cualquier superficie Guided vuelve a ordenar Planning, deshabilita falsamente una ruta disponible o convierte el backfill del operador en evidencia E2E normal-user.

## Riesgos

- Confundir migración correctiva con capacidad recorrida por el Owner.
- Repetir mutaciones Planning para obtener evidencia y romper FROZEN.
- Sobredimensionar el corrective con una nueva API de reconciliación que no es necesaria para resolver el defecto actual.

## Comandos de verificación

La verificación ejecutable pertenece a `C04_BR_106/GUIA.md`; este ledger no introduce un segundo operador.
