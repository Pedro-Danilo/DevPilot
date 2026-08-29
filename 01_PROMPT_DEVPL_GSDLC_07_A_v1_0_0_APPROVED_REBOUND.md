---
doc_id: "DEVPL-GSDLC-07-A-PROMPT"
title: "DEVPL-GSDLC-07-A — Contextual engineering agent roles and step bindings — implementation prompt"
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

Implementar y cerrar **GSDLC-07-A — Contextual engineering agent roles and step bindings**.

Objetivo: materializar roles especializados y bindings explícitos por step sin transferir autoridad humana al agente.

# 2. Autoridad y entrada

Para 07-A la autoridad inicial es repo379/`7deeb043840945165205c8c1493b4f7e44d2b2ca`/`859134adf86e3b58ef16434c4db7517be536a9caa08cf3fa493055c69a28d2e2`. Para micro-sprints posteriores, resolver la autoridad únicamente desde la adjudicación owner del predecessor inmediato; nunca regresar a repo341 ni reconstruir un baseline histórico.

Antes de 07-A funcional:
- ejecutar el activation rebind administrativo;
- incorporar cierre 06-E y backlog 06;
- corregir README stale;
- registrar S2-EVIDENCE-06E-001;
- partir del activation rebind local validado; reconciliar Git/checkout/remote únicamente en la promoción final;
- Documentation Governance, Project State y TCR v1/v2 deben quedar PASS.

# 3. Invariantes no negociables

- local-first;
- mock/local mandatory; API externa real opcional y nunca requisito de PASS;
- no costo de API asumido;
- ningún SDK vendor se consume directamente desde workflows: usar Model Gateway/adapter vigente;
- `ModelRouteDecision` no concede tool authority;
- agent/model output es untrusted hasta validación;
- agent role nunca equivale a human approval role;
- dry-run por defecto para mutaciones;
- no arbitrary shell;
- no self-approval;
- límites server-side de pasos/tiempo/tokens/costo;
- runtime DB, outputs temporales, `.vite`, caches y secrets fuera de candidate;
- no loops autónomos ilimitados.

# 4. Alcance técnico

Implementar `AgentRoleBindingCatalog`, `StepAgentBinding`, `AgentRuntimeBoundary`, descriptor de capacidades requeridas/fallback y `AgentRuntimeView` en AI Control Center. Roles mínimos: Product, Requirements, Architecture, Security, Test, Planning, Coding y Review.

Cada binding debe declarar steps/artifacts permitidos, tool allowlist, Model Gateway capability requirements, límites y policy status. Si un framework externo se evalúa, crear ADR de experimento; el runtime DevPilot gobernado sigue siendo baseline.

# 5. Entregables verificables

- AgentRoleBindingCatalog
- StepAgentBinding
- AgentRuntimeBoundary contract
- AgentRuntimeView
- agent_binding_matrix.json
- framework experiment ADR/decision record

# 6. Diseño de pruebas

**No ejecutar full regression.**

Usar Test Impact v2 y construir un plan exacto antes de ejecutar. Ejecutar todos los checks planificados aunque uno falle; agregar todos los fallos y adjudicar al final. Fail-fast solo ante una precondición de seguridad o una mutación insegura.

Pruebas mínimas:
- schema/catalog/binding coverage;
- cada step soportado tiene role explícito o `none`;
- forbidden-tool negative;
- missing-capability route;
- framework/runtime cannot bypass PolicyEngine;
- model-route cannot grant tool permission;
- role cannot approve;
- targeted static/UI tests de `AgentRuntimeView`.

Validadores determinísticos mínimos:
- Documentation Governance;
- Project State;
- TCR v1/v2;
- Historical Contract Sweep;
- Contract Reconciliation Sweep;
- Secret differential scan;
- forbidden-path audit;
- `git diff --check` canónico LF/CRLF.

Browser policy: 07-A introduce una nueva sub-vista; ejecutar browser focal de esa vista una vez. Si correctives posteriores no cambian runtime UI, reutilizar por byte-equivalence.

# 7. Windows/operator

- trabajar en worktree dedicado bajo `D:\Projects\DevPilot_E2E_Evaluation\worktrees`;
- no modificar `.git`;
- no `reset --hard`, `clean` ni force;
- comandos PowerShell de futura guía: una sola línea y PASS/BLOCK visual;
- API/UI solo foreground con exactamente tres consolas cuando browser aplique;
- ninguna credencial/tokens/cookies en evidencia;
- operadores idempotentes y con receipts machine-readable;
- no detener un sweep por el primer test ordinario fallido.

# 8. Evidencia

Conservar:
- source delta manifest;
- Git pre/post;
- test plan y resultado agregado;
- S0/S1;
- network/external_api/secrets/mutations;
- browser screenshots/receipts si aplica;
- hashes/CRC de candidate y evidence;
- owner adjudication proposal.

# 9. PASS

PASS únicamente si el objetivo funcional está demostrado, S0/S1=0, no hay bypass de RBAC/Policy/Approval, no hay secrets, los tests planificados concluyen y los validadores determinísticos pasan.

# 10. BLOCK

BLOCK si aparece capability fuera de scope, source histórico reescrito para pasar tests, tool executable sin `ToolExecutionDecision`, autonomía sin límites, secret exposure, runtime DB/cache en candidate o drift determinista conocido.

# 11. Salida

Candidate Windows limpio + evidencia + owner adjudication proposal. Autoriza **GSDLC-07-B** solo tras owner adjudication del presente micro-sprint.
