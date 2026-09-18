---
doc_id: "SPRINT-DEVPL-UX-P0-E"
title: "DEVPL-UX-P0-E — Pre-pilot browser, usability and regression closure"
status: "closed-pass-windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "owner-adjudicated-composite-recovery"
precondition: "UX-P0-D CLOSED/PASS/WINDOWS-VALIDATED on repo435"
source_repo: "repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "f1e4c5b8dc1882f7dc724ba87755cdd894f274c8"
source_sha256: "3b07e305c1acf2980f9299d09a1f78c90f6420a070b9b57c3ad24d083fa32805"
successor_expected: "repo436"
---

# DEVPL-UX-P0-E — Pre-pilot browser, usability and regression closure

> Rebound baseline: `repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip` / `f1e4c5b8dc1882f7dc724ba87755cdd894f274c8` / `3b07e305c1acf2980f9299d09a1f78c90f6420a070b9b57c3ad24d083fa32805`. El repo435 histórico esperado originalmente para E fue consumido por D; E produce repo436.

## Objetivo / alcance

Real-browser matrix; no-tech usability; responsive/a11y/perf; HCA/TCR; exactamente una Full; clean RC.

## Validación mínima

browser/usability/a11y/perf + exactly one Full/composite + clean-install.

## Definition of Done

UX-S0/S1=0; terminal escape=0; Full/composite PASS; second Full=0; repo436 exact-commit/tracked-only.

## Seguridad y gobernanza

Preservar server authority, RBAC, approvals, route/API contracts, local-first/no-remote y evidencia. No acciones destructivas ni force Git. LF/CRLF no constituye autoridad.

## Operador Windows

Un único bundle reentrante/state-aware con una sola guía `.md`, pasos consecutivos y comandos PowerShell de una línea. Python preferido. Full se ejecuta solo después de gates baratos y del commit de fuente E sellado.

## Riesgos

- ejecutar Full antes de browser/usability/a11y/perf;
- intentar una segunda Full después de functional FAIL;
- contaminar source fingerprint con outputs/runtime state;
- reutilizar evidencia browser stale;
- falso drift por LF/CRLF;
- producir RC desde tree no exacto al closure commit.

## Comandos de verificación base

Los comandos exactos se resuelven contra `ui/web/package.json`, CLI registry, FRX current profile y Test Impact de repo435; no se copian contratos históricos por nombre.

## Windows composite recovery closure

UX-P0-E closes `CLOSED/PASS/WINDOWS-VALIDATED` by composite recovery. The original Full `DEVPL-UX-P0-E-FULL-01` remains immutable at 3170 PASS / 50 FAIL / 0 ERROR / 5 SKIP / 3225 accounted. Recovery proves the exact original 50/50 failed nodeids PASS, bounded impacted PASS, Historical Regression Guard PASS and deterministic post-gates PASS. Full runs remain 1/1 and second Full remains 0.
