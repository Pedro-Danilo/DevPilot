---
doc_id: DEVPL-MP-SUCCESSOR-132-03_ANCLAS_CODIGO_Y_ESTANDARES_132
title: "Anclas literales del código fusionado y estándares MIPSoftware/MIASI"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Anclas literales del código fusionado y estándares MIPSoftware/MIASI

## 1. Procedimiento

Se abrieron **literalmente los bytes completos** de 28 archivos relevantes en el snapshot verificado `8db5b44694abcced3231183e05731e732f5b8f24`, incluyendo código real, políticas, contratos, estándares y UI. Esta tabla es inventario de lectura y hashes, **no** certificación de equivalencia funcional. Si cambia HEAD, toda implementación exige nueva auditoría viva.

| Ruta existente | Bytes | SHA-256 de contenido original | Términos relevantes presentes |
|---|---:|---|---|
| `.devpilot/project_state.json` | 316394 | `a08154190cc122034c31f9ea553cfffc6ca2dd1465b5ba8094fc1149de798076` | FROZEN, Ollama, MIASI, dry_run, approval, policy, workspace |
| `.devpilot/docs_governance/source_registry.json` | 1564607 | `efda3cc8ee16b1f7046e45cefa8f149c1a71adc43ca97591a8ca2d7272d5b370` | FROZEN, Ollama, MIPSoftware, MIASI, dry_run, approval, policy |
| `.devpilot/docs_governance/rebaseline_p0_overlay.json` | 10244 | `e228b2bc300b1a8595d19a89133ca0c91a9ad4fdad982a359d75c9e1540bd314` | approval, version |
| `.devpilot/miasi/applicability_policy.json` | 2963 | `0169247b776a18c0a49f058d1a65ad2197751e4793ede52202cee3510b05373e` | FROZEN, MIASI, approval, policy, version |
| `.devpilot/agents/tool_call_policy.json` | 16947 | `833e01f09fa7b025a94f793533c16ea691b5509a97756cba7cf85f6de2a1b4c0` | MIASI, dry_run, approval, policy, workspace, version |
| `docs/standards/mipsoftware/01_modelo_ingenieria_profesional_software.md` | 24520 | `30a1f573c36501816922a02dd2cbf674e4f8cb9efe8546ed5d8f2cf738d440d0` | MIPSoftware, MIASI, approval, policy, version |
| `docs/standards/mipsoftware/02_ciclo_vida_software.md` | 47949 | `96f3669aa54fdffceeadc98ac90c34fe2f7cb4f7ef3fe0f3a75e6bf4e7097c2a` | MIPSoftware, MIASI, approval, policy, version |
| `docs/standards/miasi/01_modelo_ingenieria_sistemas_agenticos.md` | 56163 | `9280e3645a989ac4a887b1694facb5268f05b3402825780b44324d0ef1427bf9` | Ollama, MIASI, dry_run, approval, policy, version |
| `docs/standards/miasi/03_agentic_sdlc.md` | 50106 | `e518a02bb086cceebc60468e60d8cc00041a6001c6420264df003f45a8a6234c` | MIASI, approval, policy, version |
| `docs/schemas/artifact_profiles.schema.json` | 4615 | `800b06ed3e3fe71edbf95cbb5ea93d42e9c5be41154db51344f6665a88e68e14` | policy, version |
| `docs/validation/artifact_profiles.json` | 16368 | `d1e9c2a4aa72bd9004b7a61b60ded908bc6e8fa03f013d7a7c66736d0ee600c8` | FROZEN, MIPSoftware, MIASI, approval, policy, workspace, version |
| `src/devpilot_core/validation/artifact_profile_registry.py` | 12299 | `00de31034f3cc14142934fb0a0ab5d591051331919fef490b8836730ea3c97d4` | policy, version |
| `src/devpilot_core/validators/artifact_profiles.py` | 18272 | `5521c8890de7a91ae514b903409a757446a9511e1522878c925855165cee54fb` | FROZEN, MIPSoftware, MIASI, approval, policy, workspace, version |
| `src/devpilot_core/generation/contracts.py` | 27731 | `176e1a4ddaa677ae75e04c9c5ae1005818429d0bcb264ce1401a55ba46927347` | FROZEN, GenerationRequest, ArtifactCandidateEnvelope, approval, policy, version |
| `src/devpilot_core/generation/runtime.py` | 38257 | `70090152e17d4b1ea48eaf9d6d141b53ec4206ef616a18675650783b4c1f23f4` | FROZEN, GenerationRequest, approval, policy, gateway, version |
| `src/devpilot_core/generation/product_definition.py` | 3576 | `7999692ae8ce90fa7e2774ba0fe2573f6d9efeddf356d584f9420bcc30e96ceb` | FROZEN, GenerationRequest, ArtifactCandidateEnvelope, approval, version |
| `src/devpilot_core/application/story_general_provider.py` | 15254 | `38782074d3648a404a7ca6614fe7a1446b797a2e6988b74f020650beb8b392d9` | FROZEN, Ollama, approval |
| `src/devpilot_core/application/story_implementation_candidate_service.py` | 74989 | `afd56f0d84f0bfce749a2b0dc7eb656f07b0d2c13be84a9f71c84de29e4082ff` | FROZEN, approval, workspace, version |
| `src/devpilot_core/application/settings_service.py` | 27865 | `632bcfb5ee37845ef237ea1316d2ecf55bb8b4c1c79e3447524ad04222addceb` | MIASI, approval, policy, workspace, gateway, version |
| `src/devpilot_core/application/model_gateway_settings_service.py` | 29541 | `da4fddc1a12cac96b89e3c9723bcaf48420222a3e2dd6f79d28013bb6ab706af` | GenerationRequest, Ollama, approval, policy, gateway, version |
| `src/devpilot_core/modeling/providers.py` | 23510 | `8a926ea2e2721523156c6dd385cf634ad0c834d961ec8abfb3f16898c7b67250` | FROZEN, Ollama, policy, version |
| `src/devpilot_core/modeling/local_provider_discovery.py` | 9695 | `3c36da068ddb9293651d51ed3081d460fc3cd0bd100d8c958d31b6cd1c54df02` | FROZEN, Ollama, policy, version |
| `src/devpilot_core/interfaces/api/routers/settings.py` | 15619 | `a9ad69a389d65ca9eb3ba2235f8f7fff8614d6102c269cd02deb526fa76c7c01` | dry_run, approval, policy, workspace, gateway |
| `ui/web/src/pages/SettingsView.ts` | 27244 | `b264e4089ff9645ae3bbe07ecba0207261430ff23015d11ac1fd037b71047682` | Ollama, MIASI, dry_run, approval, policy, workspace, gateway |
| `src/devpilot_core/application/artifact_lifecycle_service.py` | 30536 | `e1f86922b267e27e81cb6bfcf10bbbecb92cc7c12449e29633ab301c84175708` | FROZEN, approval, policy, workspace, version |
| `src/devpilot_core/application/workspace_git_operations_service.py` | 111491 | `52ffba2b578cc591363cac92ea33eb21630823e04ae82459721c4d674c6649ab` | FROZEN, dry_run, approval, policy, workspace, version |
| `src/devpilot_core/repo/governed_git_mutation.py` | 11823 | `6313a812ef9545df1e4afe0898656ab407161f608965dde95d103cd515cf4b4f` | FROZEN |
| `docs/02_architecture/adrs/ADR-0001-adoptar-mipsoftware-y-miasi.md` | 1813 | `01863f7cb39027995010aa06a2fc1f748df86192b8dcff413d209d9b974914c8` | MIPSoftware, MIASI, approval, policy, version |

## 2. Alcance limitado y pendientes

Esta auditoría de diseño no ha ejecutado APIs/Settings/Story/ModelAdapters/MIASI contra un servidor o LLM real ni comprobado nuevas mutaciones en Windows. La presencia de un símbolo, schema o documento no demuestra verticalidad; R0/R1/R2 preparan tests positivos y negativos específicos. Para operación Git se toma como dato la salida Windows histórica, no se confunde `git archive` con prueba de upstream en vivo.
