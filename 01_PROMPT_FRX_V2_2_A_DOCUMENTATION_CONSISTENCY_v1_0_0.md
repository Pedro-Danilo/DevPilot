---
doc_id: "01_PROMPT_FRX_V2_2_A_DOCUMENTATION_CONSISTENCY_V1_0_0"
title: "FRX-v2.2-A — Documentation consistency foundation — implementation and Windows validation prompt"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "approved_by_owner"
source_policy: "successor-of-previous-micro-sprint/windows-validated-when-applicable"
full_regression_policy: "only-closing-micro-sprint-may-consume-one-logical-full"
---
# FRX-v2.2-A — Documentation consistency foundation — Prompt

## 1. Misión

Implementar FRX-v2.2-A — Documentation consistency foundation de forma acotada, verificable, resumible y sin ampliar el alcance de testing más allá de lo autorizado.

## 2. Fuente y precondiciones

Entrada: repo386 Windows-validated (`17db6b219f5066f2df91d897a0e3ad62314a0176`, SHA-256 `0998e901...79d23`) más las adjudicaciones finales y erratum de este planning bundle. Repo386 no se altera retroactivamente; debe generarse un successor governance-only.

Precondiciones transversales:
- Git worktree limpio semánticamente: staged diff vacío, unstaged diff vacío, untracked explícitamente clasificado;
- Project State y DocumentationDriftGate PASS;
- no runtime stores/caches en source candidate;
- no modificación manual de `.git`;
- historical evidence y repo386 permanecen inmutables;
- no API externa ni network requeridos para PASS.

## 3. Alcance

Incluye reconciliación del S2 `S2-DOC-GSDLC07-POSTCLOSE-001`, autoridad/lifecycle documental, status consistency y doc-impact incremental. Excluye scheduler temporal, paralelismo, UI/API funcional y cualquier full regression.

## 4. Implementación obligatoria

1. Crear `DocumentationAuthorityGraph` con nodos `doc_id`, path, lifecycle, authority rank, historical/current/derived y successor.
2. Crear `ClosureStateConsistencyValidator` que compare Project State, backlog frontmatter, Source Registry, README current/next, changelog y adjudicación final.
3. Crear `DocImpactPlanner` que, dada la lista de changed paths y contracts, produzca documentos/registries/tests que deben reconciliarse antes de test execution.
4. Crear `DocumentationDriftLedger` con finding id, severity, authority, owner, expected/current y resolution status.
5. Crear `DerivedMetadataProjection`: counters/summaries current-active se calculan desde colección viva; snapshots históricos se leen de metadata `*_at_close`.
6. Reconciliar en el successor: backlog 07 a closed/PASS; README a closed/PASS + FRX-v2.2-A next; Source Registry con final adjudication, backlog closure y proposal histórica/superseded; Project State con GSDLC-08 authorized/deferred y FRX-v2.2 next.
7. Registrar roadmap/backlogs/prompts FRX en Documentation Governance y TCR cuando corresponda.
8. Añadir ADR solo si se cambia la jerarquía de autoridad documental global; si se mantiene la política existente, documentar como governance contract evolution.

### Diseño de estado y recuperación
- Cada operación mutante debe ser idempotente o transaccional.
- Receipts PASS terminales se reutilizan si commit/fingerprint coinciden.
- `INFRA_ABORT` permite reanudar únicamente trabajo no terminal.
- Un FAIL funcional no se oculta ni se transforma en infra failure.
- No usar hashes físicos CRLF/LF como precondición; usar Git objects, schemas y contenido semántico.

### Documentación incremental
Antes de cerrar el micro-sprint ejecutar `DocImpactPlanner` y reconciliar P0/P1 current-active. No se permite trasladar drift determinista a la full del backlog.

## 5. Pruebas y validación

- fixture negativo que reproduzca exactamente repo386: Project State closed, backlog frontmatter approved, README implementation;
- tests positivos de reconciliación successor;
- Source Registry schema/semantic tests;
- Project State schema/semantic tests;
- Documentation Governance focal;
- TCR v1/v2 focal si cambian registries;
- anti-hardcoded-current-counter tests;
- full regression = 0, browser = 0.

Reglas:
- completion-first: ejecutar todos los checks planificados salvo unsafe mutation;
- pruebas focales/impactadas únicamente, excepto la única full expresamente autorizada en el sprint de cierre;
- no full por “precaución”;
- no browser si runtime UI/API no cambia;
- comparar comportamiento, contratos y Git content, no representación física del archivo.

## 6. Evidencia obligatoria

- `documentation_authority_graph.json`;
- `documentation_drift_ledger.json` antes/después;
- `doc_impact_plan.json`;
- `closure_state_consistency_report.json`;
- source delta manifest;
- focal JUnit/logs;
- successor candidate SHA/CRC y three-state solo si se promueve.

Toda evidencia machine-readable debe registrar commit, timestamps, counts, PASS/BLOCK, S0/S1, `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed` y número de full runs consumidas.

## 7. Ingeniería del operador Windows

- Preferir un único operador Python resumible con subcomandos por fase de alto nivel, no docenas de scripts.
- PowerShell solo para invocar el operador y verificaciones externas inevitables; cada comando en una sola línea y con PASS verde/BLOCK rojo.
- API/UI foreground y tres consolas solo si este micro-sprint realmente cambia/valida browser runtime.
- No limpiar automáticamente cambios desconocidos. Reconocer estados survivores conocidos, respaldarlos y recuperar transaccionalmente.
- Packaging desde Git (`git archive`) después de validación; excluir outputs, caches, `.venv`, `.git`, runtime DB y secretos.
- Promoción Git posterior a PASS: preflight → fast-forward local → remote ancestry → push sin force → three-state review.

## 8. PASS

Drift P0/P1 current-active = 0; el fixture repo386 falla antes del fix y pasa en successor; proposal histórica no es reescrita; historical snapshots permanecen intactos; todos los focal gates PASS; full/browser runs=0.

## 9. BLOCK

Cualquier contradicción P0/P1 sin resolver; mutación retroactiva de repo386/evidence; counter current-active hard-coded; proposal histórica usada como autoridad current; full/browser ejecutado.

## 10. Salida y autorización

Autoriza FRX-v2.2-B sobre el successor administrativo Windows-validado. Commit sugerido: `chore(frx-v2.2): add incremental documentation consistency foundation`.
