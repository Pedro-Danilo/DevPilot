---
doc_id: "DEVPL-GSDLC-13-D-02-SESSION-FEEDBACK-ADJUDICATION"
title: "DEVPL-GSDLC-13-D-02 — Proposal ACCEPT 401 and feedback locality adjudication"
status: "BLOCK / FUNCTIONAL-UX / ACTIVE-CORRECTIVE-REQUIRED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_windows_validation"
checkpoint_id: "13-D-02"
run_id: "RUN_02"
---

# Observed event

The Owner reviewed proposal v2 and then pressed `Aceptar propuesta → Draft Set`. The browser appeared to do nothing at the action location. A page-level BLOCK was later found near the top of the long Story Code surface:

`Authenticated human session is required for this local API endpoint`.

The API recorded HTTP `401 Unauthorized` for the proposal decision endpoint.

# Adjudication

The proposal v2 itself remains technically acceptable and `PROPOSED`; Draft Set was not created and source was not mutated.

The server fail-closed response is correct when no valid human session can be resolved. Evidence does not contain the auth-store revocation record, so the exact invalidation reason is not proven by the browser/API message alone. The strongest technical explanation is idle expiration during the long human review: the local auth service uses a 1800-second idle timeout by default, proposal creation had succeeded earlier in the same browser journey, and the later decision was the first mutation after the review pause.

Do not weaken this security boundary.

# Functional UX defect

`FUNC-UX-13D02-SESSION-012`:

1. Story Code did not preflight a live human session immediately before the proposal decision.
2. The error was rendered only in a distant page-level status strip.
3. The Owner could reasonably interpret the button press as a no-op and had to search the page for the failure message.
4. The same pattern is a cross-application UX debt and must be registered globally; this corrective fixes the D02/Story-Code instance only.

Severity: `S1` for the active critical path because it blocks the governed human decision and obscures the recovery action.

# Corrective

- keep human-session/CSRF/RBAC fail-closed;
- call `authSession()` immediately before D02 mutations;
- render 401 locally beside the action with `Reautenticar y volver a Story Code`;
- preserve proposal/draft/plan state and never regenerate automatically;
- localize SourceChange feedback before the later D02 mutation gates;
- absorb UX-P1-13D02-009/010/011: filename-only file rows, progressive disclosure, Proposal-specific toolbar hiding.

# Recovery contract

After Windows promotion, continue the same RUN_02. Start a fresh human session, generate the current deterministic proposal v2.1 through the existing proposal action, verify the historical v2 remains unaccepted, review the four v2.1 files, then ACCEPT v2.1 once. No new StoryExecution and no new RUN number are permitted.

# CODE-13D02-PROPOSAL-V2-010 absorption

Because a new corrective is required anyway, the previously non-blocking type-precision finding is absorbed without inventing Product business fields. Generator revision `v2.1` narrows opaque attributes to a recursive JSON-compatible type contract (`JsonValue` / `ProductAttributes`). Historical v2 proposals remain evidence but are obsolete for ACCEPT after promotion.
