---
doc_id: "DEVPL-GSDLC-09-C-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-09-C — SourceChangePlan, approval-bound atomic apply and rollback — implementation report"
status: "closed/pass/windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "approved_by_owner/windows_live_browser_pass"
---

# DEVPL-GSDLC-09-C — Implementation report

## Objetivo
09-C convierte uno o más `SourceDraftBuffer` de 09-B en una operación tipada, revisable, approval-bound y reversible. No implementa CodingAgent/TestAgent, Git commit ni arbitrary shell.

## Autoridad
- Parent: `repo_DevPilot_Local_409_DEVPL_GSDLC_09_B_CODE_WORKBENCH_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Parent commit: `3c06d72445525e9b6d246726e5d6c6eb58fd20d4`.
- Parent SHA-256: `857084478f2661c471bc3421e23a68dfb027855e3321f52bd05ac21a7db64573`.
- FRX current profile: `frx-v2.4-current`; Full Regression 09-C = `0`.

## Implementación
- `SourceChangeApplicationService`: `draft → immutable plan → dry-run → approval → preimage revalidation → atomic execute → verify → evidence`.
- Multi-file CREATE/EDIT/RENAME con exact path allowlist, full unified diff, Test Impact preview, risk `high`, required role `owner`, pre/postimage SHA-256 y verified backups.
- Fault injection después de la primera mutación demuestra compensating rollback y `partial_residue=false`.
- Rollback manual es una segunda operación gobernada con approval diferente y source hash parity.
- API agrega 11 rutas tipadas bajo `/api/v1/story/code/change-*`; solo apply/rollback escriben source.
- UI `/story/code` muestra plan hash, full diff, Test Impact, risk/approver, dry-run, approval, apply manifest y rollback evidence.

## Seguridad
`patch.apply`, arbitrary shell/terminal, agent/multiagent self-apply, Git stage/commit, connector/plugin/remote interfaces y writes fuera del exact-path allowlist continúan bloqueados. Runtime stores y secrets no forman parte de plan/evidence/package.

## FRX-v2.4 / drift histórico
El hecho histórico UOC-005 de exactamente dos source-write routes se congela en `.devpilot/testing/fixtures/uoc005_source_mutation_routes_at_close.json` y `tests/test_uoc005_source_mutation_routes_at_close.py`. La API current-active puede crecer mediante successor contracts sin convertir el pasado en falso. Historical Contract Authority acepta cardinalidad sucesora (`>=`) en vez de fijar eternamente el primer registry.

## Validación local ejecutada
- Focal 09-C: `14/14 PASS`.
- Historical Contract Authority + UOC-005 frozen: `13/13 PASS`.
- Bounded current A–C/dependencies: `69/69 PASS`.
- Bounded historical: `26/26 PASS` (`95/95` bounded total).
- Test Impact v2: `PASS/47 paths/209 contracts/317 tests/unmatched=0`.
- Project State, TCR v1/v2, Documentation Governance, Evidence Freshness, API Contract Drift: `PASS`.
- Historical Regression Guard: `PASS/owner-approved-waiver/5-of-5`.
- UI static contract: `PASS`.
- 3 JSON Schemas Draft 2020-12: `PASS`.
- Full Regression: `0`.
- Browser live Windows: `PASS/7-of-7`; apply y rollback approval-bound demostrados con source restoration.\n- Windows closure gates: `PASS`; Full Regression permaneció `0`.

## Riesgos y limitaciones
Primera versión del source apply de Story Workbench. La atomicidad se implementa como operación all-or-nothing con reemplazos bounded + compensating restore verificado; no es una transacción filesystem nativa. Crash/power-loss fuera del proceso entre writes requiere evolución futura con journal durable. 09-D añadirá propuestas agentic sin heredar write authority.

## PASS/BLOCK
PASS solo si stale preimage, wrong role, unexpected path y tampered plan bloquean; fault injection deja cero residue; writes coinciden con plan aprobado; rollback restaura hash parity; browser Windows demuestra el journey; S0/S1=0. BLOCK ante partial residue, stale apply, path no aprobado, self-apply, generic patch/shell o browser no demostrado.


## Windows browser corrective before closure — bundle v1.0.2

La primera corrida browser Windows alcanzó el apply HTTP `200` y confirmó que la mutación approval-bound ocurrió, pero la vista sobrescribía inmediatamente el notice de éxito de apply/rollback al refrescar el source tree. Esto producía un falso `BLOCK` de aceptación UX aunque el servicio atómico hubiese respondido correctamente.

El corrective v1.0.2 mantiene el payload funcional y de seguridad de `SourceChangeApplicationService` y corrige únicamente la estabilidad observable de la UI:

- `refresh({preserveNotice:true})` actualiza story/source sin reemplazar el resultado de la operación;
- apply deja como estado final visible `PASS · apply exacto verificado; manifest disponible.`;
- rollback deja como estado final visible `PASS · rollback limpio; source_hash_parity=true.`;
- el browser runner exige simultáneamente notice final + cambio/paridad semántica + evidence payload;
- LF/CRLF continúa fuera del dominio de bloqueo mediante hash semántico UTF-8 normalizado.

La corrida `browser_prep_id=d086cd60-29f9-4b63-b2f1-48350f221d3b` permanece evidencia forense `BLOCK`; no se reescribe. El retest debe usar un nuevo `browser_prep_id`.

## Cierre Windows
`GSDLC-09-C=CLOSED/PASS/WINDOWS-VALIDATED`; `GSDLC-09-D authorized=true`. El repositorio canónico sucesor es `repo_DevPilot_Local_410_DEVPL_GSDLC_09_C_SOURCE_CHANGE_APPLY_WINDOWS_VALIDATED_CANDIDATE.zip`.
