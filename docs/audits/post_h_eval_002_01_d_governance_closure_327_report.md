---
doc_id: "POST-H-EVAL-002-01-D-GOVERNANCE-CLOSURE-327-REPORT"
title: "POST-H-EVAL-002-01-D — Governance closure 326 to 327"
status: "approved"
version: "2.1.1"
owner: "POST-H-EVAL-002-01-D"
updated: "2026-07-31"
approval: "pending-independent-windows-validation"
phase: "POST-H-EVAL-002"
priority: "P0"
source_repo: "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip"
target_repo: "repo_DevPilot_Local_327_POST_H_EVAL_002_01_D_GOVERNANCE_CLOSURE.zip"
---

# POST-H-EVAL-002-01-D — Governance closure 326 to 327

## Decision

`PILOT-E2E-001-RUN-05B-RERUN-03` is the authoritative acceptance run for repo 326. Its independently audited closed packages establish `CLOSED/PASS` for Sprint 6 and authorize the governance-only transition 326 to 327.

This patch closes `POST-H-EVAL-002-01-D` and backlog wave `POST-H-EVAL-002-01`, then transitions the governed current micro-sprint to `POST-H-EVAL-002-02-A`. It does not change product behavior.

The repository candidate is `implemented-pending-windows-validation` until the full Windows regression and all deterministic validators listed in the authoritative guide pass.

## TCR v1 recovery correction

The first Windows validation correctly stopped at TCR v1 with
`TEST_CONTRACT_GLOBAL_STATE_OWNER_INVALID`. The original candidate classified
`post-h-eval-002-01-d-governance-closure-327` as `scope=global-state`, which
created a second owner beside the canonical `project-global-state` contract.

Version 1.0.1 classifies the closure contract as `scope=integration`, matching
its TCR v2 `test_type=integration`. It still validates the project-state file
and keeps `mutable_global_state_allowed=true`, but it does not claim ownership.
The canonical owner remains `project-global-state`, and the dedicated closure
test now asserts that this is the only v1 `global-state` contract.

No validator, production source file, UI/API behavior, acceptance evidence or
Sprint 6 finalization state was changed by this recovery.

## Evidence freshness recovery correction

The second Windows validation correctly stopped at the read-only
`release-candidate evidence-freshness` gate. The registered critical evidence
item `post-h-eval-002-01-d-governance-closure-327-report` required the exact
marker `closed/PASS-authoritative-rerun03`, but version 1.0.1 of this report did
not contain that literal contractual value.

The closed acceptance status registered for `POST-H-EVAL-002-01-D` is
`closed/PASS-authoritative-rerun03`. This marker identifies the independently
audited closure of RERUN-03; it does not declare that the separate Windows
validation of the Sprint 7 repository candidate has finished.

Version 1.0.2 preserves the TCR v1 correction from version 1.0.1, adds the
missing marker with the semantic distinction above, adds a focused regression
assertion, and adds a read-only standard-library preflight that checks all
release-candidate evidence paths, JSON payloads, schema identifiers, expected
fields and required markers before the dependency-backed validators run.

No freshness rule was removed, weakened, made case-insensitive or converted
from blocking to warning. No production source file, UI/API behavior,
acceptance evidence or Sprint 6 finalization state was changed by version
1.0.2.

## Pytest environment recovery correction

The third Windows validation passed the focused evidence preflight and all five
governance validators, then stopped before executing any test in the full
regression. The global interpreter selected by the version 1.0.2 guide did not
contain `fastapi`, so pytest reported 21 collection errors, zero passed tests
and zero failed tests. This is an environment-construction defect in the guide,
not evidence of a product regression.

Version 1.0.3 creates a new virtual environment outside the repository,
installs the repository's declared `.[dev]` dependency contract without
editable mode, uses the resulting interpreter for every gate, performs an
explicit import precheck, requires `pip check`, freezes the collection at 1986
tests, makes the focused contract mandatory, records JUnit XML for the full
regression, and verifies that the candidate tree is byte-identical before and
after validation.

The only permitted `py -3` operation is virtual-environment creation. The
runner forbids global dependency installation and does not reuse the repo 326
environment. No production source file, UI/API behavior, freshness rule or TCR
rule is weakened or changed by version 1.0.3.

## HTTPX2 dependency-precheck recovery correction

The fourth Windows validation created the isolated environment, installed the
repository's declared `.[dev]` dependencies, and passed `pip check`. It then
stopped before the evidence preflight or any pytest execution because the
version 1.0.3 runner manually imported `httpx`, while `pyproject.toml` declares
`httpx2>=2.4,<3`. The installed package exposes the `httpx2` module and
Starlette 1.3.1 uses it for `TestClient`.

Version 1.0.4 keeps the declared dependency unchanged, derives the expected
HTTP client from `pyproject.toml`, imports `httpx2`, verifies the Starlette
`TestClient` implementation, and runs the 21 API/security compatibility tests
before the focused closure tests and full regression. This prevents a
handwritten precheck from diverging again from the dependency contract.

The verified ZIP is the installation source. Compatibility and full pytest run
in separate execution copies because tests legitimately create database and
trace artifacts. Every baseline file in both copies must retain the same
SHA-256 as the canonical extraction, which remains byte-immutable.

No production source, runtime dependency declaration, validator, TCR rule,
freshness rule, UI/API behavior, or prior acceptance evidence is changed by
version 1.0.4.

## PowerShell native-argument transport recovery correction

The fifth Windows validation verified the candidate and diff sidecars, created
four clean inputs available at that stage, installed the verified candidate ZIP
with its declared `.[dev]` dependencies, and passed `pip check`. The dependency
precheck then failed before any pytest execution because Windows PowerShell 5.1
did not preserve the multiline Python program passed to `python -c`. Python
received a truncated `raise RuntimeError(dev` expression and reported an
unclosed parenthesis.

Version 1.0.5 removes all inline Python transport from the PowerShell operator.
It invokes a standalone, syntax-validated Python precheck file with simple path
arguments and requires a machine-readable environment report. Focused tests,
compatibility tests and the full regression now run in three distinct disposable
copies; the canonical extraction remains read-only, and every baseline file in
all execution copies must retain its original SHA-256.

No production source, runtime dependency declaration, validator, TCR rule,
freshness rule, UI/API behavior, or prior acceptance evidence is changed by
version 1.0.5.

## Direct transactional overlay correction

The sixth Windows validation passed the dependency contract, the `47/47`
evidence preflight, `45/45` focused tests, all five governance validators and
`21/21` TestClient/httpx2 tests. It then stopped because the v1.0.5 integrity
gate compared `.devpilot/devpilot.db` from two independent execution copies.
Those databases contain runtime command/test history and are not source
artifacts, so byte equality between them is neither expected nor a valid source
integrity rule.

Version 2.1.0 replaces the full-candidate recovery chain with a direct,
transactional governance overlay on verified Git repo 326. The overlay contains
24 modified files, 5 added files, no deletions and no functional paths. A
read-only preflight verifies Git identity and all before hashes; apply creates a
backup and uses atomic replacement; validation runs on one exact tracked-source
mirror. Source files remain frozen by SHA-256, while runtime is separately
restricted to `.devpilot/devpilot.db*`, `.devpilot/agent_sessions/` and
`outputs/`. The repo 327 ZIP is built only from the frozen source manifest, so
runtime state cannot enter the deliverable.

Historical recovery operators v1.0.3-v1.0.5 and their dependency checker are
not product-governance artifacts and are deliberately excluded from repo 327.

## Evidence consulted

| Artifact | SHA-256 | Result |
|---|---|---|
| `repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip` | `359a7e72ad39566fdf9bb40dd9a52a3c7851f969505409e8fb008f59db4bb840` | source verified |
| `RUN05B_RERUN03_BROWSER_ACCEPTANCE_EVIDENCE.zip` | `1453fb9a10ba87908ebf77a36324054d6946da07fd28bade7399af5ef67b0d88` | CRC/manifest `68/68` |
| `RUN05B_RERUN03_FINALIZATION_CONTROL_EVIDENCE.zip` | `e04a8c754cb8112a28ce79fe0135886690e7522b5642a54b65316c4ea4ed7cfb` | CRC/manifest `11/11` |
| `RUN05B_RERUN03_INDEPENDENT_PACKAGE_AUDIT.json` | `73f2a425af41725cbb26ecf5463c8b4a6b3d1d570f75d191d6e246e2775538df` | `PASS` |
| `RUN05B_RERUN03_INDEPENDENT_PACKAGE_AUDIT.md` | `b9ff5cd9c7eb93e8e8c003fe4346cd99dc058623d71f0b33e114ab6ca7e6ec78` | consistent with JSON |

## Acceptance closure

The authoritative closed packages prove:

- routes `5/5`;
- negative states `8/8`;
- UI operations `23/23`;
- manual HTTP correlations `13/13`;
- bridges `8/8`;
- viewport screenshots `13/13`;
- full-page screenshots `5/5`;
- `S0=0`, `S1=0`;
- secret exposure `0`;
- `running=false`;
- ports `8787` and `5173` free;
- `unknown_pid_killed=false`;
- DPAPI token removed and clipboard cleared;
- `Finalize` executed exactly once.

## Historical evidence rule

`PILOT-E2E-001-RUN-05B-RERUN-02` remains immutable as `BLOCK/product-contract-evidence`, `FORENSIC-ONLY`. It is not promoted, repaired or reinterpreted as acceptance evidence.

`PILOT-E2E-001-RUN-05B-RERUN-03` is the sole authoritative browser acceptance run for repo 326.

## Governance changes

The closure synchronizes:

- the pilot roadmap and backlogs 01, 02 and 03;
- the canonical pilot runbook and general runbook;
- Project State and its source-registry snapshot;
- Documentation Source Registry;
- Test Contract Registry v1 and v2;
- release-candidate freshness criteria;
- traceability matrix;
- changelog and README;
- a machine-readable closure manifest;
- a deterministic closure test.

## Functional boundary

No file under `src/`, `ui/`, API contracts, schemas that govern runtime behavior, database code, policies that enable sensitive capabilities, or executable product behavior may differ between repo 326 and repo 327.

If the independent diff reports any such change, the result is `BLOCK` and the artifact must not be called repo 327 governance closure.

## PASS criteria

Sprint 7 may close only when all of the following are true:

1. repo 327 ZIP and sidecar match;
2. diff 326 to 327 contains only approved governance/documentation/test paths;
3. dedicated closure contract passes;
4. full `pytest -q` passes;
5. Project State, Documentation Governance, TCR v1, TCR v2 and evidence-freshness validators pass;
6. ZIP extraction and second validation pass;
7. no forbidden runtime artifacts or secrets are packaged;
8. `S0=0`, `S1=0`.

## BLOCK criteria

Any functional delta, failed test, failed validator, hash mismatch, secret, raw
HAR, SQLite file packaged as source, runtime file outside the validation
allowlist, cache packaged as source, `node_modules`, `.venv`, `.git`, or
contradiction between Project State and canonical documents is blocking.

## Safety

This closure does not enable network access, external APIs, remote execution, connector writes, plugin execution, enterprise deployment, SaaS or compliance-certified claims. It does not require starting API/UI, creating a token or repeating browser captures.

## Next authorized work

After Windows validation returns `PASS`, the governed current micro-sprint is:

```text
POST-H-EVAL-002-02-A — Workspace onboarding and isolation
```

The next planned micro-sprint is `POST-H-EVAL-002-02-B`.

## 16. Correctivo de preflight v2.1.0

El primer preflight directo v2.0.0 fue bloqueado antes de aplicar el overlay porque
comparó SHA-256 de bytes físicos de `traceability_matrix.md` con una copia ZIP.
Ese criterio no distinguía una normalización Git CRLF/LF de una edición real y el
reporte de fallo tampoco incluía el hash actual ni el blob Git.

El operador v2.1.0 usa la identidad canónica de Git (`HEAD:<path>` y
`git hash-object --path`) para decidir `BASE_326`, conserva SHA-256 físico para
integridad/backup y bloquea cualquier drift lógico real. También restablece como
única raíz operativa `D:\Projects\DevPilot_E2E_Evaluation`. Este correctivo no
cambia `src/`, `ui/`, la evidencia autoritativa ni los criterios de cierre.

## 17. Correctivo de contrato histórico y gate focal v2.1.1

La validación Windows v2.1.0 superó preflight, aplicación transaccional, dependency probe, `pip check`, evidencia `47/47`, contrato focal `45/45`, Project State, Documentation Governance, TCR v1/v2, Evidence Freshness, compatibilidad API y collection `1986`. La regresión completa terminó con `1985 passed, 1 failed, 0 errors, 0 skipped` en `7864.03` segundos.

El único fallo fue:

```text
tests/test_post_h_034_closure_regression_reconciliation.py::test_closure_state_and_backlog_are_administratively_closed
```

Ese contrato histórico todavía exigía que `current_micro_sprint` perteneciera únicamente a `POST-H-EVAL-002-01-A..01-D`. El cierre 327, en cambio, actualiza correctamente el estado gobernado a `POST-H-EVAL-002-02-A`, coherente con el cierre de backlog 01 y la autorización del backlog 02. El estado nuevo ya había sido validado por el contrato 327 dedicado, Project State y la evidencia release candidate; por tanto el hallazgo se clasifica como **stale historical regression contract**, no como regresión funcional ni inconsistencia de `project_state`.

La causa de proceso adicional fue que el gate focal v2.1.0 ejecutó 45 pruebas pero omitió el contrato POST-H-034 que TCR y runbook siguen usando como guard de reconciliación. La regresión completa lo detectó correctamente, aunque demasiado tarde.

v2.1.1 corrige ambos puntos:

1. reemplaza la allowlist cerrada por el patrón completo aprobado del roadmap `POST-H-EVAL-002` (`01-A..D`, `02-A..E`, `03-A..E`);
2. registra `test_post_h_034_closure_regression_reconciliation.py` dentro del contrato de cierre 327 en TCR v1/v2;
3. amplía el gate focal de `45/45` a `51/51` y lo ejecuta antes de la regresión completa;
4. conserva producto, no-go gates, aceptación browser, evidencia final y las 29 rutas v2.1.0 ya aplicadas;
5. eleva el diff acumulado 326→327 a `25 modified + 5 added = 30 paths`, sin cambios bajo `src/` ni `ui/`.

El Sprint 7 permanece `BLOCK-RECOVERED/IMPLEMENTED-PENDING-WINDOWS-REVALIDATION` hasta que v2.1.1 obtenga `51/51` focal y `1986/1986` en la regresión completa.

