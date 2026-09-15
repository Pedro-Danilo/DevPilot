---
doc_id: "DEVPL-UX-P0-B-SHELL-CONTRACT"
title: "DevPilot UX-P0-B — Product App Shell implementation contract"
status: "current"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-15"
approval: "derived_from_approved_DEVPL-UX-P0-B"
source_repo: "repo_DevPilot_Local_431_DEVPL_UX_P0_A_AUTHORITY_DESIGN_SYSTEM_FOUNDATION_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "013cc84f0df9eff1fb750b542644bfd0c7dc8717"
source_repo_sha256: "be80b6490cbbbfc7b5827fa896cbe5528a2b2d3676fb6c2ceef672820ee2f097"
architecture_decision: "incremental-presentation-extraction/no-router-framework-migration"
---

# Product App Shell implementation contract

## Scope

UX-P0-B implements the presentation shell prepared by UX-P0-A. Route authority remains in the proven main router; only presentation grouping/helpers and persistent server-derived context are extracted.

## Implemented shell slots

1. compact authenticated session + Guided/Expert utility row;
2. grouped navigation: Start, Understand & Plan, Build & Validate, Release, Recover, AI, Diagnostics, Global;
3. breadcrumb/location derived from current route presentation metadata;
4. persistent Project Context for project-scoped routes;
5. current stage/state/blocker/revalidation/recovery indicators from server-side `guided-sdlc/status` + recovery projection;
6. authoritative Next Action from server state with fail-closed fallback;
7. workbench content;
8. Expert diagnostics as progressive disclosure.

## Authority invariants

- route IDs and paths are unchanged;
- auth/project guards remain the same functions and scopes;
- browser storage remains UX preference/context only and cannot grant authority;
- Project Context refuses to invent data if the server status cannot be validated as read-only/actor-neutral/no-network/no-mutation;
- Guided/Expert change density only;
- approval handoff remains exact-ID and restricts navigation to Approval Center + Account;
- no new frontend/runtime dependency or routing framework is introduced.

## Responsive/accessibility contract

- critical interactive targets remain >=44px;
- grouped navigation remains keyboard-operable through native `details/summary` + links;
- active route preserves `aria-current=page`;
- breadcrumbs expose `aria-label=Ubicación actual`;
- Project Context uses an ARIA live region and does not hide blockers;
- desktop/tablet/mobile layouts are provided at bounded breakpoints.

## Preliminary status

This is the first structural product-shell implementation. UX-P0-C and UX-P0-D still need to productize critical-path page content and cross-surface operation patterns before the UI can be considered high-quality/industrial product UX.

## PASS/BLOCK

**PASS:** grouped shell is understandable, project/stage/state/blocker/next-action are visible on project routes, guards/handoffs are unchanged, and browser acceptance is PASS.

**BLOCK:** route/guard drift, browser-only authority, contradictory duplicated project state, unusable mobile navigation, hidden blockers or a critical accessibility regression.
