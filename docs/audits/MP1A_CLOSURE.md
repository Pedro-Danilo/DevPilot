---
doc_id: "MP1A-CLOSURE"
title: "MP-1A Deterministic Product Definition Closure"
status: "PASS / WINDOWS-VALIDATED / OWNER-ADJUDICATION-READY"
version: "1.0.0"
owner: "Ordóñez"
---
# MP-1A deterministic integration closure

## Authority

Baseline para MP-1A-04: `evolution/multiprovider-v2 @ b28a6111aad4de37b605b76223342f3eb24f77a8`.

Deterministic authority permanece separada en `official/devpilot-local @ 758b04be867ca24ed5eda2614ce4053c669076ef`.

## Acumulado MP-1A

- MP-1A-01: `CLOSED / PASS+FINDING`, audit-only, source mutations=0, Full=0.
- MP-1A-02: `CLOSED / PASS`, professional Product Definition profiles/dependencies, Full=0.
- MP-1A-03: `CLOSED / PASS`, deterministic provider extraction + pre-extraction parity, Full=0.
- MP-1A-04: integración/closure, browser acceptance selectiva y STOP gate; Full=0.

## Journey determinístico

La ruta C-01 conserva `Product Vision → MVP Scope → Requirements` a través de `DeterministicProductDefinitionProvider`, `GenerationRequest` y `ArtifactCandidateEnvelope`, reutilizando el renderer determinístico probado y el lifecycle server-authoritative `DRAFT → review/diff → approval → apply → FROZEN`.

Invariantes de cierre:

- provider authority = generation-only;
- source/apply/freeze/Git authority = false para el provider;
- real model calls = 0;
- external API/network = 0;
- ExternalModel = disabled;
- Manual/Import continúan disponibles;
- Decision Inbox y provenance existentes se preservan;
- artifacts FROZEN históricos no se reescriben.

## STOP

Al quedar MP-1A-04 `CLOSED/PASS|PASS+FINDING` y existir successor clean/pushed, se activa `STOP MULTIPROVIDER`:

`MP-1A-04 → STOP → deterministic Pilot A D05 → D06 → SYNC-1 → MP-1B`.

Mientras el STOP esté activo, `evolution/multiprovider-v2` no admite nuevas source mutations. El STOP solo se levanta por `SYNC-1 PASS` ejecutado después de D06 cerrado.

## Validation policy

Este cierre no consume Full Regression: MP-1 es el backlog y su única Full queda reservada para su micro-sprint de cierre. MP-1A-04 usa focal + bounded impact + selective browser acceptance.

## Project-context browser corrective

Windows browser acceptance exposed a fail-closed recovery dead end for authenticated principals carrying multiple historical workspace scopes and for the current nested `.devpilot/project.yaml` shape. MP-1A-04 corrective 1.0.2 keeps server authority: it binds browser acceptance read-only to the current active workspace, accepts only a server-selected workspace contained in authenticated scopes, preserves single-scope/durable fallbacks, performs no project mutation, and closes the acceptance on `/pre-code` without model or external-network execution.
