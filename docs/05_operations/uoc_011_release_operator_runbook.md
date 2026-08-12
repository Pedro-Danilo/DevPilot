---
doc_id: DEVPL-UOC-011-RELEASE-OPERATOR-RUNBOOK
title: UOC-011 — Local release operator runbook
status: approved
version: 1.0.0
approval: approved_by_owner
owner: Ordóñez
updated: 2026-08-12
---

# UOC-011 — Local release operator runbook

This runbook is the source-controlled product procedure. The delivery-specific Windows guide generated with the UOC-011 operator is the execution authority for the sprint closure.

The final gate requires: security/header/body/rate tests; API and UI route drift guards; accessibility/performance/state-matrix smokes; Test Impact with zero unmatched paths; focused impacted tests; browser acceptance over all nine current routes; backup/restore dry-run; clean-install smoke; upgrade/rollback dry-run; clean Git integration; clean source ZIP; and final evidence sidecars.

No operation may claim network, external API, remote execution, connector write or plugin execution. Full regression is not automatically executed after focused validation; evidence reuse must satisfy the Test Impact policy in the approved backlog.
