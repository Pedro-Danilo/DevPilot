---
doc_id: "DEVPL-GSDLC-13-GREENFIELD-ROADMAP"
title: "DEVPL-GSDLC-13 — Greenfield real-product acceptance roadmap"
status: "approved"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-21"
supersedes: "DEVPL_GSDLC_13_GREENFIELD_REAL_PRODUCT_ACCEPTANCE_ROADMAP_v1_0_0_APPROVED.md"
source_repo: "repo_DevPilot_Local_436_DEVPL_UX_P0_E_PRE_PILOT_PRODUCTIZATION_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "423e99fa38df3114328b555aff8f859740a49a01"
---

# DEVPL-GSDLC-13 — Roadmap

| Fase | Pasos journey | Modo | Resultado |
|---|---:|---|---|
| 13-A | pre-journey | ChatGPT implementation + Windows validation | successor rebind/current authority |
| 13-B | 1–8 | Owner-driven / DevPilot-executed / ChatGPT-adjudicated | proyecto nuevo + Git/environment + Project Status |
| 13-C | 9–17 | acceptance checkpoints | engineering baseline + executable plan |
| 13-D | 18–32, 34–38 | acceptance checkpoints + UX-P1 paso 33 | MVP + governed commits + recovery + local release |
| 13-E | 39 | independent audit | greenfield closure + legacy handoff |

## Checkpoint progression

`B-01 → B-02 → B-03 → C-01 → C-02 → C-03 → C-04 → D-01 → D-02 → D-03 → D-04 → D-05 → D-06 → D-07 → D-08 → E-01`.

## Successor policy

13-A crea successor porque hay source/document authority mutation. B-D no crean DevPilot repos por evidencia. Un UX-P1 corrective con DevPilot source delta sí crea successor Windows-validado y exige remote sync antes de otra mutación. Project commits del greenfield son parte normal de la app, no nuevos repos DevPilot.

## Full policy

No Full en A-D. En E: exactamente una Full lógica solo si existe DevPilot source delta no cubierto por closure policy; si no hay DevPilot source delta, registrar `NO-DEVPL-SOURCE-DELTA` y no ejecutar Full redundante.
