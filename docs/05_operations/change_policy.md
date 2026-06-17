---
title: "DevPilot Local — Política de cambios y changelog"
doc_id: "DEVPL-OPS-CHANGE-POLICY-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
sprint: "FUNC-SPRINT-78"
updated: "2026-06-17"
approval: "approved_by_owner_direction"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---

# DevPilot Local — Política de cambios y changelog

## 0. Estado

Documento aprobado como primera versión operacional para `FUNC-SPRINT-78 — Changelog generator y política de cambios`.

Esta política es preliminar e industrializable: define el contrato de cambios para Fase G, pero aún no reemplaza futuros controles de packaging, SBOM, checksums, firma, tags Git o publicación externa.

## 1. Propósito

Definir cómo DevPilot documenta cambios de versión de forma trazable, legible para humanos y compatible con un proceso de release local reproducible.

La política evita que el changelog sea un volcado crudo de commits o una lista inventada. Cada entrada debe estar respaldada por una fuente local verificable: manifests funcionales, documentos de auditoría, release manifest, commits locales o documentación aprobada.

## 2. Fuente de verdad

La fuente primaria de `FUNC-SPRINT-78` son los manifests locales:

```text
/docs/functional_sprint_*_manifest.json
```

Fuentes complementarias futuras:

- commits Git locales;
- auditorías de sprint;
- release manifest;
- reportes de quality gate;
- evidencias de packaging, SBOM, checksums y smoke tests.

## 3. Formato

El changelog debe usar una estructura compatible con Keep a Changelog:

- `Added`;
- `Changed`;
- `Deprecated`;
- `Removed`;
- `Fixed`;
- `Security`.

Cuando una categoría no tenga evidencia local, debe indicarse explícitamente que no hay entradas declaradas, en lugar de inventar cambios.

## 4. Reglas de generación

El comando autorizado es:

```powershell
python -m devpilot_core release changelog --version 0.1.0 --json
python -m devpilot_core release changelog --version 0.1.0 --json --write-report
```

Reglas:

1. El comando debe operar en modo local-first.
2. No debe llamar red, APIs externas, GitHub, GitLab, PyPI ni LLMs.
3. No debe publicar, desplegar, firmar ni etiquetar Git; en términos operativos: no publica releases ni artefactos externos y no despliega servicios.
4. No debe sobrescribir `docs/release/CHANGELOG.md` desde CLI.
5. `--write-report` solo puede escribir bajo `outputs/reports`.
6. La salida JSON debe seguir `CommandResult`.
7. La salida debe incluir trazabilidad a manifests.

## 5. Criterios PASS

- El changelog es legible por humanos.
- Usa categorías consistentes.
- Incluye trazabilidad a sprints/manifests.
- No inventa cambios sin evidencia local.
- No modifica archivos fuente.
- Genera reportes solo con `--write-report`.
- No usa red, secretos, proveedores externos ni publicación.

## 6. Criterios BLOCK

- El changelog inventa cambios no soportados por manifests, commits o docs aprobados.
- El CLI sobrescribe manualmente `docs/release/CHANGELOG.md` sin confirmación o mecanismo gobernado.
- El comando depende de outputs preexistentes no regenerables.
- El comando llama red o APIs externas.
- El comando etiqueta Git, publica, despliega o firma artefactos.
- El comando incluye secretos o runtime state.

## 7. Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-78-001 | Changelog incompleto | Generar desde manifests y reportar rango de sprints. |
| RISK-FUNC-78-002 | Entradas inventadas | Bloquear cambios sin fuente local. |
| RISK-FUNC-78-003 | Sobrescritura accidental | CLI report-only; `docs/release/CHANGELOG.md` se mantiene como artefacto controlado. |
| RISK-FUNC-78-004 | Confundir changelog con release final | Documentar que packaging/SBOM/checksums/smoke quedan para sprints posteriores. |

## 8. Evolución pendiente

Versiones posteriores deberían agregar:

- schema dedicado de changelog;
- integración opcional con commits locales;
- comparación entre releases;
- changelog incremental por tag;
- validación contra release manifest;
- integración con packaging y checksums;
- actualización gobernada de `docs/release/CHANGELOG.md` con aprobación explícita.
