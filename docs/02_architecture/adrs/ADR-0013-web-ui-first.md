---
title: "ADR-0013 — Estrategia UI/API Web first"
doc_id: "DEVPL-ADR-0013"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-64"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_78.zip"
source_backlog: "docs/devpilot_backlog_fase_F_producto_visual.md"
decision_scope: "phase_f_ui_api_strategy_and_interface_threat_model"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_64"
operationalized_by: "FUNC-SPRINT-64"
---

# ADR-0013 — Estrategia UI/API Web first

También denominada estrategia **Web UI first** para Fase F.

## Estado

`approved` y operacionalizada por `FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz`.

Esta ADR es una **decisión arquitectónica de primera versión**. No implementa servidor, frontend, autenticación, endpoints HTTP ni empaquetado. Su función es cerrar la dirección técnica para que los sprints 65-73 construyan API/Web UI sin reabrir decisiones básicas en cada sprint.

## Contexto

DevPilot Local llega a Fase F después de cerrar Fase E con AgentOps, trazas, métricas, reportes, exporter OTel dry-run y `agentops status`. El informe de avance 0-18 ya advertía que DevPilot tenía un core local sólido, pero que faltaban API local, UI real, dashboard visual, report viewer, autorización y empaquetado. También recomendaba decidir formalmente la estrategia de interfaz/API antes de implementar Desktop/Web.

La Fase F fue aprobada como **API local + Web UI local web-ready**. La discusión posterior descartó construir simultáneamente una Web UI y una Desktop UI independientes, porque duplicaría superficie de seguridad, testing, mantenimiento y decisiones de producto.

La decisión debe proteger los principios ya consolidados:

- local-first;
- dry-run-first;
- policy-first;
- ApplicationService como frontera obligatoria;
- CommandResult/ApplicationResponse como contratos de salida;
- MIASI/PolicyEngine/Approval Workflow para acciones sensibles;
- no red externa ni APIs externas por defecto;
- trazabilidad y reportes reproducibles.

## Decisión

DevPilot adopta la siguiente estrategia visual y de interfaz:

```text
CLI técnica estable
→ ApplicationService
→ API local segura en 127.0.0.1
→ Web UI local canónica de Fase F
→ Web UI real futura cuando existan auth/RBAC/operación suficientes
→ Desktop solo mediante ADR posterior, fuera de Fase F
```

### Decisiones vinculantes

1. **API local**: el stack objetivo para implementar la API local en Sprint 67 será **FastAPI**, instalado posteriormente como dependencia opcional o extra de API, no como dependencia obligatoria del core en Sprint 64.
2. **Contrato API**: la API será `/api/v1`, derivará sus respuestas de `CommandResult`/`ApplicationResponse` y se formalizará primero en Sprint 66 con OpenAPI preliminar.
3. **Host por defecto**: la API local deberá escuchar por defecto solo en `127.0.0.1`; `0.0.0.0` será BLOCK salvo decisión explícita futura y controles adicionales.
4. **Seguridad local**: los endpoints no públicos exigirán token local o mecanismo equivalente antes de exponer operaciones sensibles. CORS wildcard queda prohibido por defecto.
5. **Web UI local**: será la interfaz visual canónica de Fase F. Consumirá únicamente la API local y no importará Python/core directamente.
6. **Frontend objetivo**: la ruta base para Sprint 69 será `ui/web` con TypeScript/Vite y componentes web organizados para evolución a Web UI real. El uso de React queda permitido como decisión implementable del sprint de UI, siempre que no introduzca llamadas directas al core.
7. **Web UI real futura**: queda como evolución posterior a Fase F. Requiere ADR/plan propio para auth, RBAC, despliegue, multiusuario, TLS, auditoría y operación.
8. **Desktop**: queda diferido fuera de Fase F. No se implementará shell Tauri, Electron, PySide, PyQt ni Textual como producto visual de Fase F. Solo podrá reabrirse por ADR posterior si existe evidencia de necesidad de distribución nativa, permisos locales o experiencia de usuario.
9. **No servidor/frontend en Sprint 64**: este sprint solo decide, documenta y modela amenazas.

## Alternativas

| Alternativa | Evaluación | Veredicto |
|---|---|---|
| Solo CLI | Mantiene simplicidad, pero no resuelve producto visual, dashboard ni viewers. | Descartada como destino de Fase F; CLI se conserva como interfaz técnica. |
| FastAPI + Web UI local | Alinea Python, OpenAPI, ApplicationService, testing local y evolución a Web real. | Seleccionada. |
| Textual/TUI | Buena para consola avanzada, pero no facilita Web UI real ni dashboard visual de producto. | Descartada para Fase F. |
| PySide/PyQt | UI nativa potente, pero eleva complejidad de packaging y no facilita Web real. | Descartada. |
| Electron | Permite web en desktop, pero aumenta huella, updates, seguridad y packaging. | Diferida fuera de Fase F. |
| Tauri | Mejor opción si se necesitara desktop liviano, pero requiere Rust/toolchain y diseño de permisos. | Diferida; posible ADR futura. |
| Web UI + Desktop UI independientes | Duplica lógica, pruebas, documentación, release y superficie de ataque. | Bloqueada. |

## Consecuencias

### Positivas

- Reduce el alcance de Fase F a una ruta visual coherente y verificable.
- Evita duplicación entre Web y Desktop.
- Permite diseñar API/contratos antes de UI.
- Facilita OpenAPI, contract tests y clients tipados.
- Mantiene ApplicationService como frontera obligatoria.
- Permite evolucionar a Web UI real sin reescribir el core.

### Costos y límites

- El usuario seguirá usando CLI hasta que Sprint 67/69 implementen API/UI.
- La Web UI local no será multiusuario ni SaaS.
- La seguridad local con token/CORS no equivale a auth enterprise.
- Web UI real requiere fase posterior de auth/RBAC/deploy.
- Desktop queda fuera del alcance inmediato aunque pueda ser atractivo comercialmente.

## Modelo de integración requerido

```text
Browser local
  ↓ HTTP localhost /api/v1
API local segura
  ↓ ApplicationService
DevPilot Core
  ↓
PolicyEngine + MIASI + ReportEngine + LocalStore + Observability
```

Reglas:

- La UI no lee `outputs/`, `.devpilot/`, `docs/` ni repos directamente.
- La API no debe exponer rutas arbitrarias de filesystem.
- Toda acción write/execute requiere PolicyEngine y Approval Workflow.
- Toda respuesta debe conservar evidencia de comando, estado, findings y trazabilidad.
- Los secretos, prompts, completions, stdout/stderr, paths sensibles y tokens deben redactarse.

## Criterios PASS

- `docs/03_security/ui_api_threat_model.md` cubre localhost, CORS, token, CSRF/local origin, secrets, path traversal, report leakage y acciones críticas.
- `docs/02_architecture/c4_container.md` refleja API local y Web UI local como planned-fase-f; Desktop como deferred.
- `docs/07_interfaces/internal_application_contract.md` declara Web UI/API como consumidores canónicos y Desktop diferido.
- `python -m devpilot_core app contract --json` conserva `ok=true` y declara estrategia web-first.
- No existe servidor HTTP ni frontend productivo añadido por Sprint 64.

## Criterios BLOCK

- Implementar servidor, frontend o desktop antes de cerrar el threat model.
- Habilitar CORS wildcard por defecto.
- Escuchar en `0.0.0.0` por defecto.
- Exponer operaciones write/execute sin Approval Workflow.
- Permitir que UI importe módulos Python del core.
- Exponer secretos, tokens, prompts o outputs crudos en API/UI.
- Reabrir Desktop como entregable de Fase F sin ADR posterior.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-64-001 | API local tratada como segura por estar en localhost. | Threat model explícito; token local; CORS restringido; origin checks. |
| RISK-FUNC-64-002 | UI duplica lógica del core. | Regla UI → API → ApplicationService; tests contractuales en sprints 66-69. |
| RISK-FUNC-64-003 | Evolución a Web real rompe local-first. | Separar Web local de Web real; Web real requiere ADR de auth/RBAC/deploy. |
| RISK-FUNC-64-004 | Desktop vuelve por presión de producto sin evidencia. | Desktop diferido y condicionado a ADR posterior. |
| RISK-FUNC-64-005 | FastAPI se vuelve dependencia obligatoria del core. | Declarar dependencia opcional en sprint posterior; Sprint 64 no agrega dependencias. |

## Relación con sprints posteriores

| Sprint | Uso de esta ADR |
|---|---|
| FUNC-SPRINT-65 | Expande ApplicationService para que API/UI no llamen módulos internos. |
| FUNC-SPRINT-66 | Deriva contrato `/api/v1` y OpenAPI preliminar. |
| FUNC-SPRINT-67 | Implementa API local MVP solo después de esta decisión. |
| FUNC-SPRINT-68 | Materializa token/CORS/policy binding. |
| FUNC-SPRINT-69 | Implementa Web UI local consumiendo API. |
| FUNC-SPRINT-70 | Implementa Report/Trace Viewer sobre API. |
| FUNC-SPRINT-71 | Expone Approval Center y dry-run actions. |
| FUNC-SPRINT-72 | Expone Settings UI sin secretos. |
| FUNC-SPRINT-73 | Cierra Fase F y define evolución a Web UI real; Desktop sigue diferido. |


Nota Sprint 64: Desktop queda diferido fuera de Fase F.
