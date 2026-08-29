---
doc_id: "DEVPL-GSDLC-07-ACTIVATION-REBIND-MANIFEST"
title: "DEVPL-GSDLC-07 — Minimal activation rebind and regression-v2 planning manifest"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-29"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_379_DEVPL_GSDLC_06_E_PROVIDER_SETTINGS_CONTROLLED_EVAL_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "7deeb043840945165205c8c1493b4f7e44d2b2ca"
source_repo_sha256: "859134adf86e3b58ef16434c4db7517be536a9caa08cf3fa493055c69a28d2e2"
---

# DEVPL-GSDLC-07 — Minimal activation rebind manifest

## 1. Propósito

Cerrar la frontera administrativa de GSDLC-06 y preparar GSDLC-07 con la menor superficie operativa posible. Este rebind **no implementa** todavía Full Regression Execution v2.1; solo deja su arquitectura, backlog/enabler y prompt formalizados para el siguiente trabajo.

## 2. Estrategia mínima

1. Partir del checkout oficial limpio en `718fa0da5d552f8bf6def39c102f0124ac7fa922`.
2. Materializar directamente el candidate final construido desde repo379 + correcciones administrativas. No se exige que el remote contenga previamente `7deeb043...`.
3. Validar únicamente:
   - los dos contratos RBAC que cierran `S2-EVIDENCE-06E-001`;
   - contratos 06-E focales;
   - `Project State`, `Documentation Governance`, TCR v1/v2;
   - `git diff --check` y guardas documentales del claim de full regression.
4. Crear **un único successor commit local** desde la rama oficial.
5. Actualizar el remote una sola vez al final y verificar entonces la reconciliación `HEAD == official/devpilot-local == origin/official/devpilot-local`.
6. Generar el ZIP limpio desde Git HEAD.

El hash `7deeb043...` se conserva como procedencia histórica de repo379, no como precondición de disponibilidad del objeto Git en el laptop.

## 3. Cierre de gaps

- `S2-DOC-06E-002`: README y documentos corrigen `full 1/1 PASS` por `FAIL/TIMEOUT/1-of-1/PRESERVED + composite recovery PASS`.
- `S2-EVIDENCE-06E-001`: la captura defectuosa queda preservada e invalidada solo para el claim RBAC mediante erratum; el enforcement se corrobora con dos tests focales existentes. **No hay recaptura browser.**

## 4. No-go

- full regression = `0`;
- no worktree adicional;
- no API/UI;
- no identidad Developer temporal;
- no modificación manual de `.git`;
- no `reset --hard`, rebase o force push;
- no remote como precondición de entrada;
- no source funcional de 07-A.

## 5. PASS/BLOCK

**PASS:** candidate materializado sobre checkout limpio, tests/validators focales PASS, gaps reconciliados, commit local creado, remote actualizado al final y ZIP limpio generado desde Git.  
**BLOCK:** repo sucio antes de materializar, HEAD inicial distinto sin explicación, test RBAC falla, validator bloquea, full regression se ejecuta o promoción remota requiere force/rewrite.
