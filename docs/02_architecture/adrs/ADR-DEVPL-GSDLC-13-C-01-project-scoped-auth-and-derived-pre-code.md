---
doc_id: "ADR-DEVPL-GSDLC-13-C-01-PROJECT-SCOPED-AUTH-DERIVED-PRECODE"
title: "GSDLC-13-C-01 — Project-scoped auth, governed document structure and deterministic derived pre-code"
status: "approved"
version: "1.1.0"
owner: "DevPilot Local"
updated: "2026-09-24"
approval: "owner-approved-corrective-v1.0.1"
---

# Decisión

## Contexto

El piloto greenfield demostró inicialmente que el API estaba sano pero `/guided-sdlc/pre-code` devolvía 403 porque la identidad `local-owner` conservaba únicamente el scope histórico `devpilot-local`, mientras las rutas de proyecto usan `active-server-context`. La UI temprana además podía degradar ese 403 a un falso mensaje de API caída. Ese problema quedó corregido y validado en repo441.

El retest posterior de `13-C-01` descubrió una segunda brecha de composición: el bootstrap Greenfield B-02 materializaba `docs/`, `docs/standards/` y `.devpilot/`, pero Pre-code exige parents documentales gobernados (`docs/00_product`, `docs/01_requirements`, `docs/02_architecture`, `docs/03_security`, `docs/04_quality`) antes de persistir siquiera el DRAFT runtime-only. Los tests C-01 históricos ocultaban la divergencia porque precreaban esos parents.

Además, el contrato de `13-C-01` exige que DevPilot derive Vision → Scope → Requirements desde la idea persistida. Repo441 verificaba el upstream FROZEN y registraba hashes/provenance, pero el generador no consumía materialmente el contenido de Vision al producir Scope ni el contenido de Scope al producir Requirements.

## Decisión

1. Al arrancar el API, el workspace activo se resuelve desde contexto persistido validado por servidor. El owner local incorpora ese workspace a sus scopes conservando roles/scopes previos; cualquier sesión antigua se revoca por el mecanismo existente de autoridad stale. No existe self-service browser para ampliar scopes.
2. Las respuestas tempranas de seguridad incluyen CORS credential headers para que el browser preserve HTTP 401/403 y no los presente como fallo de red.
3. El `greenfield-neutral-shell` conserva su neutralidad tecnológica pero su autoridad actual pasa a `BootstrapPlanningCatalog v3`, que materializa namespaces documentales vacíos requeridos por el Guided SDLC: `docs/00_product/`, `docs/01_requirements/`, `docs/02_architecture/`, `docs/02_architecture/adrs/`, `docs/03_security/` y `docs/04_quality/`. No crea artifacts, stack, dependencias ni `.venv`.
4. Workspaces Greenfield ya creados se reconcilian mediante un reconciliador DevPilot bounded, idempotente, workspace-scoped y PathGuard-protected. Solo puede crear la allowlist de directorios; no crea contenido de proyecto y deja receipt en platform outputs. No se autoriza `mkdir` manual del operador.
5. Vision, Scope y Requirements admiten `DEVPL_MOCK` mediante `deterministic-context-template-v2`: una propuesta determinística local, sin modelo, red, API externa ni costo. Product Vision consume Project Context; Scope consume materialmente Product Vision FROZEN; Requirements consume materialmente Scope FROZEN y conserva Vision como contexto trazable. El DRAFT permanece runtime-only hasta review/diff/approval/apply.
6. Los inputs determinísticos se canonizan como JSON estable (`sort_keys`, separadores estables) y todo texto fuente se normaliza lógicamente a LF antes de hashing. Provenance registra `canonical_input_sha256`, source hashes, generated-content hash y versión del generador. CRLF/LF físico no constituye diferencia semántica.
7. `Product Vision` admite `IMPORT` porque Artifact Lifecycle ya declara `import_allowed=true`; Pre-code y Advisor deben mantener esa autoridad coherente. El selector de modo de autoría es el control canónico de cómo se produce el DRAFT.
8. `DEVPL_MOCK` permanece baseline de acceptance/fallback. Agent/RAG no se habilitan dentro de este corrective; su integración real se gobierna mediante una evolución independiente multi-modelo que reutilizará el mismo artifact lifecycle.
9. MIASI permanece `NOT_EVALUATED / DEFERRED` mientras no exista contexto de aplicabilidad. Una vez materializado el contexto, la evaluación vuelve a ser fail-closed.

## Invariantes

- No se concede filesystem authority desde input browser.
- No se relaja RBAC, CSRF, PathGuard ni protección frente a symlinks.
- No se escribe source antes de review/approval/apply.
- La reconciliación estructural solo crea directorios allowlisted y reporta `project_content_files_written=0`.
- No se selecciona stack durante C-01.
- `DEVPL_MOCK` no implica agent/model execution y reporta costo 0.
- Misma versión + mismos inputs canónicos producen el mismo contenido/hash.
- Scope depende materialmente de Vision FROZEN; Requirements depende materialmente de Scope FROZEN.
- Upstream no FROZEN produce BLOCK.
- Un upstream FROZEN debe seguir coincidiendo exactamente con su `approved_sha256`; source drift produce BLOCK antes de derivar.
- `docs/02_architecture/adrs/` forma parte del namespace estructural obligatorio aunque no sea parent directo de un artifact del catálogo C-01.
- Full Regression permanece en `0` para este corrective bounded; solo se ejecutan pruebas focales/affected y build UI.

## Consecuencias

- Los contract tests deben cubrir el recorrido B-02 real → C-01 real y no preparar artificialmente document parents.
- El catálogo histórico B-02 v2 se conserva como evidencia congelada; `BootstrapPlanningCatalog v3` es la autoridad vigente para nuevos bootstraps.
- El cambio de semántica del generador se expresa mediante una versión nueva (`deterministic-context-template-v2`), no reutilizando `v1`.
- La futura ruta Agent/Local Model/External API debe producir propuestas DRAFT bajo estos mismos gates y no puede crear una vía paralela de aprobación o source write.
