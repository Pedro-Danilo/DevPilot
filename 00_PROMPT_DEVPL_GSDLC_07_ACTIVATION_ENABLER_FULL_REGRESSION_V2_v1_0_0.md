---
doc_id: "DEVPL-GSDLC-07-ACTIVATION-ENABLER-FRX2-PROMPT"
title: "DEVPL-GSDLC-07 activation enabler — implementation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-28"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_379_DEVPL_GSDLC_06_E_PROVIDER_SETTINGS_CONTROLLED_EVAL_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "7deeb043840945165205c8c1493b4f7e44d2b2ca"
source_repo_sha256: "859134adf86e3b58ef16434c4db7517be536a9caa08cf3fa493055c69a28d2e2"
validation_policy: "completion-first/selective/no-full"
---

# 1. Misión

Implementar y cerrar el activation enabler de GSDLC-07: reconciliar el cierre de 06 y construir Full Regression Execution v2.1 sin consumir la full del backlog 07.

# 2. Orden no negociable

1. confirmar repo379/commit/SHA y ancestry;
2. sincronizar referencia oficial local / checkout Windows / remote mediante fast-forward gobernado, sin reset destructivo;
3. materializar adjudicaciones 06-E/06 y cerrar `S2-DOC-06E-002`;
4. registrar erratum y corroborar `S2-EVIDENCE-06E-001` mediante los contratos RBAC focales existentes;
5. ejecutar validators administrativos;
6. implementar Full Regression Execution v2.1;
7. ejecutar tests focales/sintéticos y canary bounded; **no full**;
8. empaquetar successor candidate limpio y evidencia.

# 3. Invariantes

- no segundo full 06-E;
- no full de 07 en este enabler;
- no pytest-xdist;
- no reducción de nodeids/coverage;
- no arbitrary shell;
- no modificación `.git` desde scripts;
- no runtime state en source ZIP;
- no secrets/raw tokens;
- local-first, no external API/network requerida;
- failure funcional ordinario no aborta checks restantes;
- resume solo con fingerprints idénticos.

# 4. Componentes mínimos

- contracts/models para `FullRegressionSession`, `CollectedNode`, `ShardPlan`, `ShardReceipt`, `TerminalOutcome`;
- deterministic collector sobre pytest nodeids;
- immutable plan builder;
- typed subprocess runner para shards;
- receipt writer + hashes;
- resume planner;
- aggregate adjudicator;
- schemas JSON;
- CLI local-first;
- docs/runbook y tests.

# 5. Tests mínimos

- collection stable y hash determinista;
- no duplicates/missing nodeids;
- plan deterministic;
- receipt integrity;
- ordinary FAIL completion-first;
- infra abort + resume same session;
- fingerprint mismatch BLOCK;
- source mutation BLOCK;
- partial receipt cannot be adjudicated PASS;
- all terminal outcomes accounted;
- bounded real canary session;
- docs/project-state/TCR/history/contracts/secrets PASS.

# 6. Windows

No levantar API/UI durante el activation rebind. La implementación posterior del enabler seguirá la política normal de consolas únicamente si una capacidad futura modifica runtime browser. Todos los comandos PowerShell de la guía deben ser una sola línea y terminar con PASS verde o BLOCK rojo.

# 7. Salida

- successor repo candidate limpio;
- component delta ZIP;
- evidence ZIP + checksums;
- owner adjudication proposal;
- 07-A rebound metadata apuntando al successor solo después de owner adjudication.
