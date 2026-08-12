---
doc_id: DEVPL-UOC-011-OPERATIONAL-THREAT-MODEL
title: UOC-011 — Operational hardening threat model
status: approved
version: 1.0.0
approval: approved_by_owner
owner: Ordóñez
updated: 2026-08-12
---

# UOC-011 — Operational hardening threat model

UOC-011 closes the UI Operational Console evolution with local-first hardening. Trust boundaries remain browser localhost → token-protected FastAPI → ApplicationService/policy → local runtime/output stores. No remote execution, connector write, plugin execution or mandatory external API is enabled.

## Threats and controls

- **Token theft/stale browser session** — sessionStorage remains non-persistent across browser sessions and gains an 8-hour maximum age with explicit expiry cleanup.
- **Oversized local request / accidental denial of service** — API request bodies are bounded to 1 MiB before route processing.
- **Request burst / local runaway UI** — process-local fixed-window rate budget of 600 requests/minute per token/client identity. This is not an enterprise distributed quota.
- **UI injection/framing** — CSP, frame denial, nosniff, no-referrer, restricted permissions and no-store are emitted by local UI dev/preview and API responses.
- **Keyboard/focus traps** — skip link, main landmark, focus-visible, 44px minimum button/navigation targets and reduced-motion behavior.
- **Operational blind spots** — all nine current UI routes are governed by the 12-state matrix: loading, empty, ready, warn, block, error, API down, 401, 403, timeout, cancelled and stale data.
- **Unsafe release/rollback** — existing backup/restore, clean-install and upgrade/rollback dry-run contracts are mandatory closure gates.

## Residual limits

This is a local product hardening baseline, not enterprise IAM, distributed rate limiting, remote telemetry, browser-farm certification or a formal WCAG audit by an accredited third party.
