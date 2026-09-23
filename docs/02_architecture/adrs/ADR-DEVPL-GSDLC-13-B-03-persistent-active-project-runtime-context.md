---
doc_id: "ADR-DEVPL-GSDLC-13-B-03-PERSISTENT-ACTIVE-PROJECT-RUNTIME-CONTEXT"
title: "Persist active project runtime context and bootstrap WorkspaceEngineeringState"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-23"
approval: "owner-driven-acceptance/13-B-03-active-corrective"
---

# ADR — Contexto runtime persistente del proyecto activo

## Decisión

Un `CREATE_NEW` greenfield que termina bootstrap `PASS` debe dejar dos autoridades operacionales de plataforma, ambas fuera del source del proyecto administrado:

1. un registry runtime bajo `outputs/runtime/active_workspace_registry.json` que identifica el workspace activo; y
2. un `WorkspaceEngineeringState` inicial bajo `outputs/workspaces/<workspace_id>/engineering_state.json`.

El comando estándar `python -m devpilot_core api serve ...` debe detectar ese contexto persistido y enlazarlo automáticamente al API runtime, sin exigir launchers distintos por fase del proyecto.

## Contexto

`13-B-03-00` demostró que `.devpilot/project.yaml`, `bootstrap-execution.json` y `workspace-registration.json` del Project Shell no bastaban para Project Status. El `UiWorkspaceContextResolver` resolvió correctamente el greenfield, pero `GuidedSDLCService` siguió usando el registry histórico y no encontró un `WorkspaceEngineeringState`, por lo que devolvió `EMPTY/UNKNOWN`.

El repositorio ya contenía el precedente GSDLC-05-E BLOCK-03: Project Status externo requiere un registry Guided runtime explícito y un engineering state proyectable. El corrective de B-02 creó correctamente un shell tecnológico neutral, pero no cerró esta segunda parte del contexto operacional.

## Reglas

- El runtime registry y engineering state son estado operacional/reconstruible de DevPilot; no son artifacts funcionales del greenfield.
- Para futuros `CREATE_NEW` GSDLC-13, ambos writes de control-plane deben aparecer explícitamente en `BootstrapPlan.expected_side_effects` y quedar cubiertos por `plan_hash`/approval; no pueden ser efectos ocultos de execute.
- No se escribe `.devpilot/engineering_state.json` dentro del repo administrado.
- El estado inicial es `NEW / NOT_STARTED / idea-intake`, suficiente para una proyección determinista y una próxima transición gobernada; no inventa Vision, Requirements ni Architecture.
- El registry histórico `.devpilot/workspaces/workspace_registry.json` no se muta.
- El launcher estándar solo auto-enlaza contexto persistido validable. Si el contexto está corrupto/stale, `api serve` bloquea fail-closed.
- Variables explícitas del operador conservan precedencia; el auto-binding solo completa valores ausentes.
- No se relaja PathGuard, RBAC ni aprobación.
- La ausencia de `miasi_applicability_context.json` antes del checkpoint de Pre-code/MIASI **no** es un blocker de Project Status: se proyecta como `NOT_EVALUATED / DEFERRED`, con `project_status_authoritative=false`.
- Cuando el contexto MIASI ya existe, su evaluación vuelve a ser autoritativa para Project Status; contexto inválido, aplicabilidad ambigua o controles obligatorios incompletos continúan fail-closed.
- El servicio de Pre-code readiness conserva su regla estricta: MIASI debe evaluarse y pasar cuando ese checkpoint se vuelve obligatorio. El diferimiento aplica solo a la proyección temprana de Project Status, no desactiva MIASI.

## Consecuencias

- `Project Status` puede proyectar un proyecto recién creado antes de que existan Vision/Requirements/Architecture.
- El restart deja de depender de variables project-specific o de `sessionStorage` como única authority.
- El bootstrap GSDLC-13 incorpora dos writes control-plane adicionales bajo `outputs/`; esos writes deben aparecer en dry-run/plan/approval.
- El estado inicial no contiene contenido funcional generado: solo identidad, Git facts y `current_step=idea-intake`.
- Project Status deja de convertir una ausencia esperada de contexto MIASI en un falso blocker antes de 13-C-03; el Owner puede continuar hacia la etapa donde esa clasificación se decide con información suficiente.

## Alternativas

1. Mantener variables de entorno distintas por fase: descartado por fragilidad operativa y baja productización.
2. Guardar engineering state dentro del greenfield: descartado porque mezcla source del proyecto con runtime state de DevPilot.
3. Inferir estado completo al abrir Project Status sin persistencia: descartado porque puede sintetizar autoridad inexistente y perder continuidad tras restart.

## Estado

`APPROVED / ACTIVE-CORRECTIVE-13-B-03`.

## Producción

La instalación final debe converger en un launcher estable. La selección/autorización inicial de raíces de workspace debe convertirse en configuración persistente de instalación (setup/Global Settings) y no depender de Run Cards. Este ADR corrige la persistencia/recuperación del proyecto ya creado; no convierte una ruta escrita por el browser en permiso de filesystem.

## PASS / BLOCK

**PASS:** después de bootstrap o backfill correctivo, un restart con el mismo comando estándar de API recupera el workspace activo y Project Status no es `EMPTY/UNKNOWN`, sin modificar Git del proyecto. En un bootstrap nuevo, el dry-run declara además los dos writes de runtime state antes del approval.

**BLOCK:** el runtime depende de sessionStorage como única authority; el operador debe escribir engineering state a mano; el launcher exige variables project-specific en cada fase; o el bootstrap escribe artifacts funcionales para fabricar un estado.

## Verificación

- `tests/test_devpl_gsdlc_13_b_03_runtime_project_context_corrective.py`
- `tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py`
- guard histórico `test_block03_project_status_recovers_external_server_context_via_runtime_guided_registry`
