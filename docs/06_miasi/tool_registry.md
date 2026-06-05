---
title: "Tool Registry — DevPilot Local"
doc_id: "DEVPL-MIASI-TOOL-REGISTRY"
status: "reviewed"
version: "0.6.0"
owner: "Ordóñez"
standard: "MIASI"
phase: "SPRINT-PRECODE-06"
updated: "2026-06-05"
approval: "ready_for_owner_approval"
---

# Tool Registry — DevPilot Local

| Tool ID | Nombre | Fase | Side effect | Riesgo | Estado |
|---|---|---|---|---:|---|
| `artifact.read` | read_artifact | MVP | lectura | Bajo | Planned |
| `artifact.frontmatter.validate` | validate_frontmatter | MVP | ninguno | Bajo | Planned |
| `artifact.structure.validate` | validate_artifact_structure | MVP | ninguno | Bajo | Planned |
| `checklist.precode.run` | run_precode_checklist | MVP | ninguno | Bajo | Planned |
| `miasi.required` | miasi_required | MVP | ninguno | Bajo | Existing/minimal |
| `report.write` | write_report | MVP | escritura controlada | Medio | Planned |
| `trace.append` | append_trace_event | MVP | escritura controlada | Medio | Planned |
| `document.draft.generate` | generate_draft_document | MVP | escritura opcional | Medio | Planned |
| `documentation.audit` | audit_documentation | MVP | reporte | Medio | Planned |
| `git.status` | git_status | MVP+ | lectura | Medio | Planned |
| `git.diff` | git_diff | MVP+ | lectura | Medio | Planned |
| `repo.inventory` | repo_inventory | MVP+ | lectura | Medio | Planned |
| `patch.parse` | parse_patch | MVP+ | ninguno | Medio | Planned |
| `patch.dry_run` | patch_dry_run | MVP+ | simulación | Alto | Planned |
| `code.review` | code_review | MVP+ | reporte | Alto | Planned |
| `tests.run` | run_tests_controlled | MVP+ | ejecución controlada | Alto | Planned |
| `model.call.mock` | call_mock_model | MVP | ninguno | Bajo | Planned |
| `model.call.local` | call_local_model | MVP+ | cómputo local | Medio | Planned |
| `model.call.external` | call_external_model | MVP+ | red/costo | Alto | Disabled by default |

## Política

Toda herramienta nueva debe agregarse a este registro antes de implementarse.
