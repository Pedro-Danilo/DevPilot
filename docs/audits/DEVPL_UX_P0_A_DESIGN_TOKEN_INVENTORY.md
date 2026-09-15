---
doc_id: "DEVPL-UX-P0-A-DESIGN-TOKEN-INVENTORY"
title: "DevPilot UX-P0-A — Semantic design token inventory"
status: "current"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "derived_from_approved_DEVPL-UX-P0-A"
---

# Semantic design token inventory

UX-P0-A introduces `ui/web/src/design-tokens.css` without changing route/API/RBAC authority or adopting a UI framework.

Token domains: typography, surfaces/text, action/focus, operational states (`PASS/WARN/FAIL/BLOCK/ERROR/PENDING/RECOVERY`), spacing, radius/elevation and interaction target sizes.

The initial values deliberately map to repo430 values so the foundation is semantics-preserving. UX-P0-B/C/D may evolve composition and hierarchy against these semantic roles.

**PASS:** tokens exist, foundational CSS consumes them, route/authority contracts are unchanged, `test:ux-p0-a` passes.

**BLOCK:** missing operational state token, unapproved dependency, route change, or permission/policy drift.

## Risks and limitations

- The inventory covers foundation tokens only; route-specific migration remains bounded and incremental.
- A token presence check is not a substitute for browser usability acceptance in UX-P0-C/E.

## Verification commands

```text
cd ui/web && npm run test:ux-p0-a
cd ui/web && npm run test:accessibility
```

