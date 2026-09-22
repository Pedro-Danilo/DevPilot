---
doc_id: "DEVPL-GSDLC-13-B-02-BLOCK-ADJUDICATION"
title: "DEVPL-GSDLC-13-B — 13-B-02-00 acceptance BLOCK and corrective activation"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-22"
approval: "chatgpt-adjudicated/from-owner-evidence"
checkpoint_id: "13-B-02"
attempt_id: "13-B-02-00"
authority: "repo437/d9d120c26a0e38487d353bd8715d5b1935f7fa6b"
---

# Decisión

`13-B-02-00 = BLOCK / DEVPL_PRODUCT_CONTRACT_GAP / ACTIVE-CORRECTIVE-REQUIRED`.

El piloto queda pausado en el mismo checkpoint. No se autoriza dry-run/approval/execute de la implementación repo437 ni se reescribe el Run Card para omitir 7.2/7.3.

## Evidencia vinculante

- Authority/preflight PASS: repo437 local/origin, tracked limpio y workspace greenfield ausente.
- API/UI PASS y autenticación humana PASS.
- `01_create_project_entry.png` muestra Project Entry con modo, Project ID, nombre y target, pero sin ruta normal para capturar una necesidad de negocio ni para definir/confirmar constraints/model policy.
- Source audit de `ProjectEntryDryRunView.ts` confirma que `buildIntake()` inyecta silenciosamente stack React+TypeScript/FastAPI+SQLite, provider `none` y restricciones fijas.
- Los contratos de GSDLC-13 exigen en B-02 `expresar idea de negocio → definir workspace/constraints/model policy`; el Pilot Brief exige que el stack se decida dentro del Guided SDLC.

## Clasificación

## F-13B02-001 — Missing business-need capture

`FUNCTIONAL_BUG / UX-S1`: falta una acción obligatoria del journey. La necesidad inicial es seed de trazabilidad para Vision/Scope/Requirements y debe existir antes de esas derivaciones; puede refinarse después, pero no inventarse retroactivamente.

## F-13B02-002 — Missing constraints/model-policy confirmation

`FUNCTIONAL_BUG / UX-S1`: el Owner no puede expresar/confirmar explícitamente local-first, mock/no-API baseline, límites de red/cloud/operator writes y gobernanza de external API antes del bootstrap.

## F-13B02-003 — Premature technology/dependency binding

`ARCHITECTURE_GAP + FUNCTIONAL_CONTRACT_VIOLATION / UX-S1`: CREATE_NEW selecciona un perfil React/FastAPI/SQLite y planifica manifests/.venv/dependency jobs antes de Architecture. Diferir la descarga de paquetes evita red no aprobada, pero no corrige la decisión tecnológica prematura.

## Corrective autorizado

1. ProjectIntake successor v2 para CREATE_NEW greenfield; mantener v1 histórico para OPEN/IMPORT.
2. Campo requerido `business_need` orientado al problema, no a la solución.
3. Confirmación visible de constraints/model policy del piloto.
4. `technology_decision_status=deferred-to-architecture` y stack `undecided`.
5. Project Shell neutral: workspace + Git + metadata/contexto; sin `.venv`, frontend/backend, manifests o dependency jobs.
6. ADR vinculante que separa Project Shell de Technical Scaffold.
7. Persistir business need/policies en `.devpilot/project.yaml` para consumo trazable por 13-C.
8. Mantener plan/dry-run/preimage/approval/rollback y server-side authority existentes.

## Prompt/model boundary

B-02 necesita un **domain input** para la necesidad, no un prompt libre universal. DevPilot ya posee PromptRegistry versionado, `prompt_inputs`, model service y superficies con instrucciones humanas acotadas. Los agentes posteriores deben transformar inputs de dominio mediante prompts gobernados/provenanced; texto libre no puede otorgar tools ni permisos.

## PASS/BLOCK del corrective

PASS local candidate si las pruebas focales demuestran contrato v2, shell neutral, cero dependency jobs/network, Git limpio y compatibilidad v1.

BLOCK si se reescriben contratos históricos, se fija stack antes de Architecture, se requiere red/API externa, se crea `.venv`/manifests tecnológicos en B-02 o se habilita un prompt libre con autoridad operativa.

## Riesgos

- El posterior recomendador tecnológico debe distinguir recomendación de limitación del catálogo.
- La Architecture debe producir decisión justificable y aprobada antes del Technical Scaffold.
- Windows/browser retest sigue siendo obligatorio; este documento no adjudica PASS del corrective en Windows.

## Verificación

`python -m pytest -q tests/test_devpl_gsdlc_13_b_02_greenfield_intake_corrective.py tests/test_devpl_gsdlc_03_a_project_intake_contracts.py tests/test_devpl_gsdlc_03_b_environment_discovery_planning.py tests/test_devpl_gsdlc_03_c_project_entry_dry_run.py tests/test_devpl_gsdlc_03_d_bootstrap_execution.py`
