---
doc_id: DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT
version: 1.0.12+contextual-provider
status: proposed-for-owner-windows-validation
supersedes: v1.0.11+cor108
updated: 2026-10-10
---

# Operational contract v1.0.12 — ID-neutral contextual implementation proposals

This successor preserves v1.0.11 as immutable history. It **replaces the unused COR-112 artifact**, not any validated DevPilot commit. The only Windows starting authority is `8f80832370e09605ac3867ae86fe34d4540cde15` (repo_464).

## Contextual proposal boundary
A story is selected via Project Status → Story Code Workbench → Story activation & context (`Preparar contexto (recomendada/alternativa)` → `Iniciar story preparada`). Source tree + Draft editor contains `Proponer implementación desde contexto`. That button creates a proposal **only for the server-authoritative IN_PROGRESS StoryExecution**, not the next number or any browser-supplied story_id.

When source exists, `GeneralStoryProvider` selects by **capability + compatible source structure**, not ID. Known deterministic capabilities include product availability lookup and modifying opaque product attributes. For other stories, only explicitly configured LOCAL ModelAdapter routes may generate reviewable file proposals. An unconfigured local model, unsupported stack, missing test, syntax issue, unsafe path, unexpected source or incompatible baseline is a deliberate BLOCK. There is no automatic Manual fallback, and no requirement to code the story by hand as the preferred path.

The frozen Architecture gate is unchanged: currently supported source profile `fastapi-python + sqlite`. Source-empty bootstrap still uses the earlier D02 bounded contract. General models may create different implementations over **existing** compatible Python source, but completion of arbitrary stories is not guaranteed.

## Provider policy
Set `DEVPILOT_STORY_LLM_PROVIDER=ollama` (or `lmstudio` or `openai-compatible-local`) in the **API process** only when the Owner has configured and enabled that local route through DevPilot's provider registry. Local providers are disabled by default. Never set `OPENAI_API_KEY`, never permit external endpoints, never auto-fallback to mock. The local endpoint policy's bounded timeout is 90 seconds. The provider response must be strict JSON and is not trusted as code authority.

For a deterministic capability, no API key, internet, model service, external cost or model inference is used. For a generative local capability, loopback model execution uses local CPU/GPU and may consume computational resources but incurs no external token bill. Token and output limits, local endpoint policy and standard guards remain in force.

## Immutable file proposal
For a proposed change, persist provider/capability/route provenance, StoryContextPack and Architecture hashes, content hashes and exact EDIT source bindings. `ACCEPT` materializes only runtime SourceDraftBuffers, not project source. Thereafter the standard Owner review → SourceChangePlan → recheck → Dry-run → approval → final recheck → atomic apply → StoryTestPlan → typed jobs → Quality → Git path is mandatory. After apply, do not repeat earlier mutation gates. Approvals are human-only, separated by type, never inferred from a model.

## RUN_02 RF-003
RF-003 was already prepared and started before the 403; do not reactivate it. The legacy `403` proves the prior bounded incremental provider refused an unsupported story. Once platform successor passes Windows gates, return to **Source tree + Draft editor**, click `Proponer implementación desde contexto`, verify `capability_id=product.update`, review four exact paths, accept the proposal and continue governance one step at a time. RF-004 and future stories may require explicit local LLM configuration if they don't match a verified deterministic capability.

## Windows closure
Every platform correctivo requires focused tests, local commit, explicit remote promotion, clean `git archive` snapshot, ZIP self-test and SHA-256. COR-112 must not be applied. Multiprovider remains frozen. Full Regression remains 0 during D05.
