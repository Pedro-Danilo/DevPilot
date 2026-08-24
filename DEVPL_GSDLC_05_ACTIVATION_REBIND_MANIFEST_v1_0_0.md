---
doc_id: "DEVPL-GSDLC-05-ACTIVATION-REBIND-MANIFEST"
title: "DEVPL-GSDLC-05 — Activation rebind manifest"
status: "approved/required-before-functional-source"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-24"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
source_repo: "repo_DevPilot_Local_369_DEVPL_GSDLC_04_E_ARTIFACT_WORKBENCH_BROWSER_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "13c2a59bbcb8adbb27f2a9be59a1e2925454fb29"
source_repo_sha256: "de62ae248dbdc9f587ef85a72c2194fc5db7f8d5758c0a1dda1f135ceb0b4be7"
---

# DEVPL-GSDLC-05 — Activation rebind manifest

## Propósito

Cerrar explícitamente la frontera entre el candidate pre-adjudication GSDLC-04 y la primera mutación de GSDLC-05.

## Autoridades externas que 05-A debe incorporar

- `DEVPL_GSDLC_04_E_FINAL_OWNER_ADJUDICATION_v1_0_0.md`;
- `DEVPL_GSDLC_04_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- `DEVPL_GSDLC_04_FINAL_OWNER_CLOSURE_CURRENT.json`;
- backlog aprobado/rebound `DEVPL-GSDLC-05_executable_mipsoftware_miasi_and_step_action_advisor_v1_2_0_APPROVED_REBOUND.md`;
- prompts 01→05 aprobados.

## Reconciliación administrativa obligatoria

Antes de source funcional, 05-A debe actualizar de forma coherente y verificable, como mínimo:

- `.devpilot/project_state.json`;
- `.devpilot/docs_governance/source_registry.json`;
- `README.md`;
- `docs/00_product/DEVPL_GSDLC_product_evolution_roadmap.md`;
- Source Registry entries para adjudicaciones/backlog/prompts nuevos;
- TCR v1/v2 solo si nuevos validators/tests de activación lo requieren.

Estado objetivo:

- GSDLC-04 = `CLOSED/PASS`;
- GSDLC-04-E = `CLOSED/PASS`;
- owner adjudication pending = `false`;
- full regression GSDLC-04 runs = `1`, original FAIL, rerun `false`, composite closure PASS;
- GSDLC-05 = `authorized/active`;
- current micro-sprint = `GSDLC-05-A`;
- execution authority = repo369/commit/SHA del frontmatter.

## Gates de activación

Debe existir `PASS` machine-readable para:

1. candidate SHA y identity;
2. owner adjudications presentes y coherentes;
3. Project State schema/semantic validation;
4. Source Registry schema + docs-governance;
5. README/roadmap/current consistency;
6. historical contract sweep de la transición;
7. no runtime DB/caches introducidos;
8. `git diff --check`;
9. dirty scope limitado al activation-rebind manifest declarado.

`BLOCK` ante cualquier contradicción. No full regression. No browser salvo que el rebind accidentalmente cambie UI, lo cual debe considerarse unexpected scope y BLOCK.
