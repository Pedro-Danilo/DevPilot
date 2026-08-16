---
doc_id: "DEVPL-GSDLC-01-E-PROJECT-STATUS-EXPERIENCE-CONTRACT"
title: "Project Status API/UI experience contract"
status: "implemented-initial"
version: "1.0.0"
owner: "DEVPL-GSDLC-01-E"
updated: "2026-08-16"
approval: "implementation-candidate"
---

# Project Status API/UI experience contract

`GET /api/v1/guided-sdlc/status` is a protected local read-only route bound to `guided_sdlc.project_status`. It delegates to `ApplicationService -> GuidedSDLCApplicationService -> GuidedSDLCService -> ProjectProgressEngine`; HTTP/UI do not duplicate ProjectStatus or NextAction logic.

The current UI registry has ten routes including `ui.project-status` at `/project/status`. The frozen UOC-011 registry remains nine routes and 108 historical browser cases.

Project Status renders loading, ready, empty, blocked, revalidation-required, stale, API-down/error, timeout, unauthorized/forbidden and unknown states. Server-derived text is inserted using DOM `textContent`, never `innerHTML`.

`Continue` is non-mutating in GSDLC-01. It navigates only when the supplied NextAction is explicitly non-mutating, available and mapped to a safe existing UI destination; otherwise the CTA is disabled with the deterministic reason.

No browser code imports Python/core, reads filesystem/Git, or performs direct source mutation. Productive auth remains deferred to GSDLC-02.
