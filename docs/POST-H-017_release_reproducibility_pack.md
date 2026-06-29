---

doc_id: "POST-H-017-IMPLEMENTATION"
id: "POST-H-017"
title: "POST-H-017 — Release reproducibility pack"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-29"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-017-B"
next_micro_sprint: "POST-H-017-C"
---

# POST-H-017 — Release reproducibility pack

## 1. Objetivo

Diseñar e implementar un **Release Reproducibility Pack** local que permita reconstruir, verificar y auditar un release dry-run de DevPilot con evidencia suficiente: manifest, changelog, SBOM, checksums, comandos de validación, ambiente, commit, fuentes incluidas/excluidas y resultados de gates.

No se busca publicar ni desplegar. Se busca que un release local pueda verificarse de forma reproducible antes de cualquier distribución.

## 2. Contexto y justificación

DevPilot ya cuenta con módulos de release:

```text
src/devpilot_core/release/manifest.py
src/devpilot_core/release/changelog.py
src/devpilot_core/release/sbom.py
src/devpilot_core/release/checksum.py
src/devpilot_core/release/smoke.py
src/devpilot_core/release/verify.py
src/devpilot_core/release/package.py
docs/release/CHANGELOG.md
```

También se han generado ZIPs limpios con `git archive`. Sin embargo, falta un pack formal que junte la evidencia de reproducibilidad y determine si un release puede considerarse verificable localmente.

## 3. Alcance

Incluye:

```text
- Manifest v2 de reproducibilidad.
- Environment snapshot sin secretos.
- Source archive manifest.
- Lista explícita de exclusiones runtime.
- Checksums de archivos críticos.
- SBOM local básico.
- Gate de release reproducibility.
- Verificador local del pack.
- Runbook de release dry-run reproducible.
```

No incluye:

```text
- Publicación en PyPI/NPM/GitHub Releases.
- Firma remota.
- Deploy real.
- Certificación de supply chain.
- Reproducible builds binarios completos.
- Uso de servicios externos.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/release/
src/devpilot_core/package/
docs/release/CHANGELOG.md
docs/05_operations/runbook.md
.gitignore
pyproject.toml
package.json si aplica
ui/web/package.json
.devpilot/project_state.json
.devpilot/testing/test_contract_registry.json
quality-gate hardening
industrial-readiness check
```

## 5. Entregables

```text
docs/schemas/release_reproducibility_pack.schema.json
docs/schemas/release_environment_snapshot.schema.json
src/devpilot_core/release/reproducibility.py
src/devpilot_core/release/environment.py
src/devpilot_core/release/archive_manifest.py
src/devpilot_core/release/reproducibility_verify.py
tests/test_post_h_017_release_reproducibility_pack.py
tests/test_post_h_017_release_reproducibility_schema.py
docs/05_operations/release_reproducibility_runbook.md
outputs/release/reproducibility_pack.json       # generado, no versionable
outputs/release/environment_snapshot.json       # generado, no versionable
outputs/release/source_archive_manifest.json    # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o cli_registry
src/devpilot_core/quality/gate.py
src/devpilot_core/release/verify.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

```json
{
  "schema_version": "1.0",
  "pack_id": "devpilot-release-reproducibility-20260623",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "git": {
    "commit": "HEAD",
    "branch": "post-h",
    "dirty": false,
    "archive_method": "git archive"
  },
  "validation": {
    "pytest_summary": "not-run-in-pack",
    "quality_gate_hardening": "pass",
    "test_contracts": "pass",
    "industrial_readiness": "pass"
  },
  "artifacts": {
    "changelog": "docs/release/CHANGELOG.md",
    "manifest": "outputs/release/release_manifest.json",
    "sbom": "outputs/release/sbom.json",
    "checksums": "outputs/release/checksums.json"
  },
  "exclusions": ["outputs/", ".devpilot/devpilot.db", ".devpilot/agent_sessions/", ".venv/", "node_modules/"],
  "safety": {
    "remote_execution_used": false,
    "external_api_used": false,
    "mutations_performed": false,
    "secrets_included": false
  }
}
```

## 7. Principios

```text
1. Evidence-first: release no es solo ZIP, es evidencia reproducible.
2. Clean source: runtime artifacts excluidos.
3. Dry-run-first: no publicar ni desplegar.
4. Secret-free: snapshots de ambiente redactados.
5. Git-grounded: commit y estado limpio obligatorios.
6. Local verification: verificar sin red.
```

## 8. Micro-sprints propuestos

### POST-H-017-A — Release reproducibility schema y policy

Tareas:

```text
1. Crear release_reproducibility_pack.schema.json.
2. Crear release_environment_snapshot.schema.json.
3. Definir policy de exclusiones.
4. Registrar schemas.
5. Crear tests.
```

PASS:

```text
PASS si pack declara commit, dirty state, validations, artifacts y safety.
PASS si exclusions incluye runtime artifacts críticos.
```

### POST-H-017-B — Environment snapshot redactado

Tareas:

```text
1. Capturar versión Python, SO, package manager y dependencias mínimas.
2. Redactar variables sensibles.
3. No incluir valores de secrets.
4. Generar environment_snapshot.json.
```

PASS:

```text
PASS si secrets_included=false.
PASS si no se leen .env completos.
PASS si snapshot permite diagnóstico local.
```

### POST-H-017-C — Source archive manifest y checksums

Tareas:

```text
1. Enumerar archivos incluidos por git archive.
2. Enumerar exclusiones aplicadas.
3. Calcular checksums de artefactos críticos.
4. Detectar runtime artifacts en archivo fuente.
5. Producir source_archive_manifest.json.
```

PASS:

```text
PASS si outputs/ y .devpilot/devpilot.db están excluidos.
PASS si se detecta cualquier archivo prohibido.
```

### POST-H-017-D — Verifier local de reproducibilidad

Tareas:

```text
1. Implementar release reproducibility verify.
2. Validar schema del pack.
3. Validar checksums.
4. Validar commit/dirty state.
5. Validar gates requeridos declarados.
```

PASS:

```text
PASS si verifier falla ante checksum alterado.
PASS si falla ante dirty=true.
PASS si falla ante secrets_included=true.
```

### POST-H-017-E — Quality gate y runbook release

Tareas:

```text
1. Integrar subgate release-reproducibility.
2. Documentar runbook.
3. Agregar comandos release reproducibility pack/verify.
4. Actualizar test contract registry.
```

PASS:

```text
PASS si quality gate valida pack.
PASS si runbook explica cómo generar y verificar release local.
```

## 9. Comandos esperados

```powershell
python -m devpilot_core release reproducibility-pack --json --write-report
python -m devpilot_core release reproducibility-verify --pack outputs/release/reproducibility_pack.json --json
python -m pytest tests/test_post_h_017_release_reproducibility_pack.py -q
python -m pytest tests/test_post_h_017_release_reproducibility_schema.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Criterios BLOCK

```text
BLOCK si el repo está dirty y se intenta declarar pack reproducible.
BLOCK si se incluyen runtime artifacts.
BLOCK si se detectan secretos.
BLOCK si falta commit.
BLOCK si se usa red o API externa.
BLOCK si se presenta como release publicado.
```

## 11. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Falso release reproducible | Alta | Verifier local y checksums. |
| Incluir outputs/runtime | Alta | Archive manifest y exclusions. |
| Secret leakage | Alta | Environment redaction. |
| Confundir dry-run con publicación | Media-alta | Runbook y disclaimers. |

## 12. Definition of Done

```text
[ ] Schema pack validado.
[ ] Environment snapshot redactado.
[ ] Source archive manifest generado.
[ ] Verifier local implementado.
[ ] Quality gate integrado.
[ ] Runbook aprobado.
```

## 13. Estado de implementación acumulativo

### POST-H-017-A — Release reproducibility schema y policy

Estado: `implemented-initial`.

Implementado en esta entrega:

```text
- ReleaseReproducibilityPack schema registrado.
- ReleaseEnvironmentSnapshot schema registrado.
- Policy local de exclusiones y safety flags definida en .devpilot/release/reproducibility_policy.json.
- Validator determinístico de policy en src/devpilot_core/release/reproducibility_policy.py.
- Fixtures contractuales válidos para pack y environment snapshot.
- Tests focales de schema, policy y sincronía documental.
```

Límites explícitos:

```text
- No genera todavía outputs/release/reproducibility_pack.json.
- No captura todavía environment snapshot real.
- No enumera todavía git archive ni checksums de source archive.
- No implementa todavía verifier local ni quality gate final.
- No publica, no despliega, no firma remoto, no usa red y no lee secretos.
```

Evolución pendiente: POST-H-017-C/D/E implementarán source archive manifest/checksums, verifier local y gate/runbook de release reproducibility.

