---
adr_id: ADR-13D05-CONTEXTUAL-PROVIDER
status: proposed-for-owner-windows-validation
supersedes_design: "story-specific incremental provider selection"
date: 2026-10-10
---

# ADR — Contextual incremental implementation provider

## Context and decision
The repeated D05 Story loop must not require a new hard-coded `story-rf-00N` provider. The previously delivered COR-112 is **discarded** (not the active baseline). This ADR applies instead to the complete clean platform baseline repo_464 at `8f80832370e09605ac3867ae86fe34d4540cde15`.

Choose a **single contextual implementation-proposal boundary** selected from the authoritative StoryExecution/StoryContextPack, not a story ID, index, backlog length or UI position. The normal UI first prepares the selected READY story and starts it. This boundary receives exactly that IN_PROGRESS story, frozen architecture and the platform source catalog.

1. For explicitly understood and structurally compatible capabilities, select a deterministic generator by **semantic capability** (`product.list_available`, `product.update`), verifying the exact existing source shape. These are capabilities, not universal implementations. These validated templates retain their historic RF-002/RF-003 source details; changing a story ID only changes traceability, not the supported business semantics.
2. For any other incremental requirement, route **only by explicit opt-in** to the existing ModelAdapterRouter and an enabled LOCAL provider (Ollama/LM Studio/allowlisted OpenAI-compatible local). Mock cannot fabricate a general implementation. External APIs and fallback-to-mock are blocked.
3. Require a strict JSON file proposal (CREATE/EDIT only), bounded context, bounded output, safe exact paths `src/**/*.py` or `tests/**/*.py`, code syntax, required module-docstring contract, at least one test, explicit source preimages and human review. Invalid/unavailable proposals are a BLOCK, not PASS or partial output.
4. The proposal is never authority to apply, approve, stage, execute commands, waive tests or commit. Preserve D03/D04 gates and dry-run.
5. No automatic installation or enabling of an LLM. For general requirements, actual local-model capability, code quality and adequate context remain acceptance preconditions. No claim of universal success. Bootstrap from an empty repository retains the historical bounded D02 profile and is out of scope.

## Separation and governance
This deterministic-branch change uses pre-existing local ModelAdapter contracts; it does not merge, cherry-pick or modify the frozen Multiprovider worktree. It does **not** replace the planned Multiprovider router, SYNC-1, or the authoritative MP research contracts. This narrow local opt-in is subject to Owner adjudication as a scoped D05 exception. To avoid a hidden MP fork, the follow-on integration must reconcile this adapter with the MP work after D06/SYNC-1.

## Risks and mitigations
- A local LLM can hallucinate implementation, test assumptions or output unsafe content: strict bounded parsing; mandatory Owner review, typed tests/Quality/Git gates. Passing syntax and local tests is not general correctness.
- Large projects exceed prompt budget: bounded source selection, explicit BLOCK for unread preimages; no silent fall-through to source overwrites.
- Tokens/cost: only local enabled providers accepted; no external API cost, local compute resources still consumed; bounded prompt and model timeout.
- Timeout of model generation: local-only policy now permits up to 90 seconds, while default local providers remain disabled; operations fail closed when unavailable.
- Historical test drift: never alter frozen historical ADRs, nor relax security assertions in order to force PASS.

## Consequences
A fixed story ID no longer determines the next provider. Different story functions can be handled by a genuinely general model-backed route **when configured**, or a proven deterministic capability. Unsupported/incompatible cases correctly BLOCK. At most one story is governed at a time through StoryExecution. No Full Regression in D05.
