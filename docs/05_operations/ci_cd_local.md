---
title: "DevPilot Local — CI/CD local y workflow scaffolding"
doc_id: "DEVPL-OPS-CI-CD-LOCAL-001"
status: "approved"
approval: "approved_after_func_sprint_76_validation"
version: "1.0.0"
owner: "Ordóñez"
sprint: "FUNC-SPRINT-76"
phase: "FASE-G-PRODUCTIZACION-RELEASE"
updated: "2026-06-17"
---

# DevPilot Local — CI/CD local y workflow scaffolding

## 0. Estado

Este artefacto queda en estado `approved` para `FUNC-SPRINT-76`. Define una primera versión de CI local y scaffolding GitHub Actions para DevPilot. Es una versión preliminar de productización: automatiza verificación, pero todavía no construye paquetes, no genera manifest de release, no calcula SBOM ni checksums y no ejecuta publicación externa.

## 1. Propósito

El propósito de Sprint 76 es hacer reproducible la verificación de DevPilot en dos rutas equivalentes:

1. ejecución local del perfil CI mediante `python -m devpilot_core quality-gate run --profile ci --json`;
2. workflow opcional `.github/workflows/devpilot-ci.yml` para revisión automatizada en repositorios GitHub.

La regla central es mantener CI como verificación segura, local-first y dry-run-first. El workflow no debe requerir secretos, credenciales, proveedores externos, despliegues ni publicación de paquetes; en términos operativos, no publica paquetes ni releases y no despliega a ningún entorno remoto.

## 2. Arquitectura operativa

El flujo de CI queda definido así:

```text
checkout
→ setup Python 3.12
→ install editable .[dev]
→ pytest -q
→ quality-gate run --profile ci
→ setup Node 20
→ npm --prefix ui/web test
```

El perfil `ci` de `QualityGate` es la fuente común entre ejecución local y workflow. Incluye los subgates del perfil `full` y validación estática del workflow. `pytest -q` se mantiene como paso explícito del procedimiento CI para evitar ejecución implícita lenta o recursiva; también puede incluirse dentro del gate con `--include-pytest` cuando se requiera una sola llamada.

## 3. Comandos locales

Verificación rápida:

```powershell
python -m devpilot_core quality-gate run --json
```

Verificación extendida:

```powershell
python -m devpilot_core quality-gate run --profile full --json
```

Verificación equivalente a CI:

```powershell
python -m devpilot_core quality-gate run --profile ci --pytest-timeout-seconds 600 --json
```

Verificación completa recomendada antes de commit:

```powershell
python -m pytest -q
python -m devpilot_core quality-gate run --profile ci --pytest-timeout-seconds 600 --json
npm --prefix ui/web test
```

## 4. Workflow opcional

El workflow queda en:

```text
.github/workflows/devpilot-ci.yml
```

Está diseñado como scaffolding seguro. Solo ejecuta verificación y no guarda artefactos de release. No contiene referencias a `secrets.*`, publicación, despliegue ni credenciales de modelos externos.

## 5. Subgates del perfil CI

El perfil `ci` ejecuta estos subgates; `pytest` se ejecuta como paso explícito del workflow y puede añadirse al gate con `--include-pytest`:

| Subgate | Propósito |
|---|---|
| `readiness-strict` | Valida baseline documental y pre-code readiness. |
| `standards-status` | Verifica catálogo MIPSoftware/MIASI. |
| `miasi-validate` | Valida agentes, herramientas y matriz de políticas. |
| `eval-harness-ready` | Verifica fixture de evaluación sin mutar `outputs/`. |
| `app-contract` | Verifica ApplicationService v2. |
| `validation-gateway-all` | Ejecuta gateway documental/contratos. |
| `visual-product-smoke` | Verifica cierre Fase F visual MVP. |
| `ci-workflow-static` | Valida seguridad estática del workflow. |

## 6. Seguridad

Controles aplicados:

- `permissions: contents: read` en workflow;
- proveedores externos deshabilitados por variable de entorno;
- sin uso de `secrets.*`;
- sin push, tags, releases, paquetes, contenedores ni entrega remota;
- sin escritura en fuente;
- reportes solo bajo `outputs/` cuando se solicita `--write-report`.

## 7. Criterios PASS

- `quality-gate run --profile ci --json` retorna `ok=true`.
- El workflow existe y referencia el perfil `ci`.
- El workflow incluye `pytest -q` de forma visible.
- El workflow no requiere secretos.
- El workflow no ejecuta acciones de entrega remota.
- El workflow mantiene permisos de solo lectura.

## 8. Criterios BLOCK

- Uso de secretos o credenciales de proveedores externos.
- Comandos de publicación, entrega remota, tags, push o releases.
- Perfil CI no reproducible localmente.
- Workflow que omita `quality-gate run --profile ci`.
- Workflow que dependa de servicios cloud para validar DevPilot.

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Divergencia entre local y CI | Perfil `ci` como contrato común. |
| CI lento por `pytest` completo | Timeout explícito y perfil `fast` disponible para uso local. |
| Falso release-ready | Documentar que Sprint 76 no crea paquetes ni release manifest. |
| Activación accidental de APIs externas | Variables de entorno y validación estática sin secretos. |

## 10. Evolución pendiente

Los siguientes sprints de Fase G deberán agregar release metadata, changelog, packaging, SBOM, checksums, smoke test de release, backup/upgrade y ReleaseAgent dry-run. Sprint 76 no cierra productización completa; solo crea el puente local/CI para verificar DevPilot antes de avanzar a release metadata.
