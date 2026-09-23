---
doc_id: "ADR-DEVPL-GSDLC-13-C-01-PROJECT-SCOPED-AUTH-DERIVED-PRECODE"
title: "GSDLC-13-C-01 — Project-scoped auth and deterministic derived pre-code"
status: "approved"
version: "1.0.0"
owner: "DevPilot Local"
updated: "2026-09-23"
approval: "acceptance-corrective"
---

# Decisión

## Contexto

El piloto greenfield demostró que el API estaba sano pero `/guided-sdlc/pre-code` devolvía 403 porque la identidad `local-owner` conservaba únicamente el scope histórico `devpilot-local`, mientras las rutas de proyecto usan `active-server-context`. La UI temprana además podía degradar ese 403 a un falso mensaje de API caída.

El contrato de 13-C-01 exige que DevPilot derive Vision, Scope y Requirements desde la idea persistida. El vertical slice histórico de GSDLC-05-E solo soportaba MANUAL/IMPORT.

## Decisión

1. Al arrancar el API, el workspace activo se resuelve desde contexto persistido validado por servidor. El owner local incorpora ese workspace a sus scopes conservando roles/scopes previos; cualquier sesión antigua se revoca por el mecanismo existente de autoridad stale. No existe self-service browser para ampliar scopes.
2. Las respuestas tempranas de seguridad incluyen CORS credential headers para que el browser preserve HTTP 401/403 y no los presente como fallo de red.
3. Vision, Scope y Requirements admiten `DEVPL_MOCK`: una propuesta determinística local, sin modelo, red, API externa ni costo, derivada de `.devpilot/project.yaml` y de artefactos previos FROZEN. El DRAFT permanece runtime-only hasta review/diff/approval/apply.
4. MIASI permanece `NOT_EVALUATED / DEFERRED` mientras no exista contexto de aplicabilidad. Una vez materializado el contexto, la evaluación vuelve a ser fail-closed.

## Invariantes

- No se concede filesystem authority desde input browser.
- No se relaja RBAC ni CSRF.
- No se escribe source antes de review/approval/apply.
- No se selecciona stack durante C-01.
- `DEVPL_MOCK` no implica agent/model execution y reporta costo 0.
- Scope depende de Vision FROZEN; Requirements depende de Scope FROZEN.
