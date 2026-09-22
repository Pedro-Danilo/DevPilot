---
doc_id: "ADR-DEVPL-GSDLC-13-B-02-NEUTRAL-PROJECT-SHELL"
title: "Neutral Project Shell before Architecture and governed technology selection"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-22"
approval: "owner-direction/13-B-02-active-corrective"
---

# ADR — Project Shell neutral antes de Architecture

## Decisión

`CREATE_NEW` del piloto greenfield debe separar **Project Shell bootstrap** de **Technical Scaffold**.

En `13-B-02`, DevPilot capturará y persistirá la necesidad inicial, ubicación, constraints y model policy; podrá crear workspace, Git y metadata/contexto gobernado, pero mantendrá `frontend/backend/database = undecided`, `technology_decision_status = deferred-to-architecture`, `venv_required=false` y `dependency_jobs=[]`.

La selección de tecnologías se realizará después de que el Guided SDLC produzca requisitos y Architecture. El `TechnologyCatalog` actuará como catálogo de perfiles soportados, no como oracle que preselecciona un stack. DevPilot podrá generar recomendaciones gobernadas de uno o más perfiles con rationale/trade-offs; el Owner deberá revisar y aprobar la decisión antes de materializar manifests, runtimes o dependencias.

## Contexto

El acceptance `13-B-02-00` demostró que la superficie Project Entry heredada de GSDLC-03 solo ofrecía mode/id/name/path y enviaba silenciosamente React+TypeScript/FastAPI+SQLite, provider/constraints y dependency planning antes de Architecture. El contrato GSDLC-13 exige expresar la idea, confirmar constraints/model policy y que el stack se decida dentro del Guided SDLC.

## Alternativas

1. Continuar con el starter React/FastAPI/SQLite en B-02: descartado porque adelanta Architecture.
2. Omitir business need y capturarlo en Vision: descartado porque rompe trazabilidad causal del journey.
3. Project Shell neutral + Technical Scaffold posterior: seleccionada.

## Estado

Aprobado como decisión del corrective 13-B-02; la eficacia operacional queda pendiente de validación Windows y retest del checkpoint.

## Consecuencias

- Se introduce `ProjectIntake v2` solo para `CREATE_NEW` greenfield; los contratos históricos v1 de OPEN/IMPORT permanecen intactos.
- B-02 no crea `.venv`, frontend/backend, manifests ni dependency jobs.
- La necesidad inicial queda en `.devpilot/project.yaml` como seed trazable para Vision/Scope/Requirements.
- Mock/no-API es baseline de política, no una decisión de stack.
- Un futuro Technical Scaffold necesitará plan/dry-run/approval propio y deberá estar vinculado a una decisión de Architecture/ADR.

## Prompting y agentes

La necesidad de negocio es un **domain input**, no un prompt libre con autoridad. Los agentes posteriores podrán consumirla mediante `PromptRegistry` y `prompt_inputs` versionados/provenanced. Un eventual campo “instrucciones adicionales” deberá estar acotado y nunca conceder tools/permisos por texto libre.

## PASS / BLOCK

**PASS:** B-02 persiste necesidad/policies, planifica cero dependencias/red, no fija stack y produce Project Shell Git limpio.

**BLOCK:** cualquier stack/runtime/dependency manifest se materializa antes de Architecture; falta business need; external API/red se habilita silenciosamente; un prompt libre concede capacidad operativa.

## Riesgos

- La recomendación tecnológica futura puede sesgarse por los perfiles disponibles; la UI debe declarar cobertura/limitaciones del catálogo.
- Un único perfil soportado no debe presentarse como “recomendación inteligente”; debe mostrarse como restricción de capacidad.
- La decisión tecnológica debe ser reproducible, explicable y aprobada antes de scaffold.

## Verificación

`python -m pytest -q tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py`
