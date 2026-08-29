---
doc_id: "DEVPL-GSDLC-07-B-PROMPT"
title: "DEVPL-GSDLC-07-B — RAG context packs, provenance and budget — implementation prompt"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-08-28"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_382_DEVPL_GSDLC_07_A_CONTEXTUAL_AGENT_ROLE_BINDINGS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "807685993b9ef526d1274fd8d3440fb14f6e56cf"
source_repo_sha256: "dfde12877a1f9a96297aab42ad30a4f85a64216e42004042e43b7a51ded1e865"
validation_policy: "completion-first/selective/no-full"
---

## 0. Rebound de autoridad de ejecución

Este successor prompt reemplaza únicamente la autoridad de ejecución obsoleta del v1.0.0. GSDLC-07-A está `CLOSED/PASS`; 07-B debe ejecutarse sobre repo382 Windows-validated/commit `807685993b9ef526d1274fd8d3440fb14f6e56cf`/SHA `dfde12877a1f9a96297aab42ad30a4f85a64216e42004042e43b7a51ded1e865`. Repo379/341 permanecen como historia/origen de diseño y no son execution authority.

La política de validación no cambia: completion-first selectiva, browser focal solo en la nueva provenance UI y **no full regression**.

# 1. Misión

Implementar y cerrar **GSDLC-07-B — RAG context packs, provenance and budget**.

Objetivo: construir context packs grounded, mínimos, trazables y sujetos a presupuesto por step.

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

Implementar `ContextPack v2`, source selection policy y provenance. Cada fuente debe llevar source id/path, hash, freshness, trust tag, selection reason y citation mapping. Aplicar ContextBudget/top-k/diff-first; excluir secrets/runtime stores y fuentes fuera de policy.

Rutas sin API: lexical/local fixtures obligatorias. Embeddings/local model pueden ser opt-in. API externa real no es requisito.

# 5. Entregables verificables

- ContextPack v2
- RAG provenance panel
- source selection policy
- rag_grounding_samples.json
- context_budget_report.json

# 6. Diseño de pruebas

**No ejecutar full regression.**

Usar Test Impact v2 y construir un plan exacto antes de ejecutar. Ejecutar todos los checks planificados aunque uno falle; agregar todos los fallos y adjudicar al final. Fail-fast solo ante una precondición de seguridad o una mutación insegura.

Pruebas mínimas:
- groundedness;
- stale/missing source;
- insufficient-evidence semantics;
- secret/runtime exclusion;
- untrusted source tagging;
- budget trim/top-k/diff-first;
- deterministic lexical fallback;
- provenance hash/citation parity.

Validadores determinísticos mínimos:
- Documentation Governance;
- Project State;
- TCR v1/v2;
- Historical Contract Sweep;
- Contract Reconciliation Sweep;
- Secret differential scan;
- forbidden-path audit;
- `git diff --check` canónico LF/CRLF.

Browser policy: Como se incorpora provenance panel, ejecutar browser focal solo para las superficies nuevas/modificadas; no repetir casos 07-A byte-equivalent.

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

Candidate Windows limpio + evidencia + owner adjudication proposal. Autoriza **GSDLC-07-C** solo tras owner adjudication del presente micro-sprint.
