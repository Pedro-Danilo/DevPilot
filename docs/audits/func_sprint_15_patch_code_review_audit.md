---
doc_id: devpl-audit-func-sprint-15
status: implemented-initial
version: "1.0.0"
owner: DevPilot Local
updated: 2026-06-08
---

# FUNC-SPRINT-15 — Patch review y code review en dry-run

## Propósito

Implementar una primera capacidad local, determinística y no destructiva para revisar patches/diffs y código fuente sin aplicar cambios ni invocar servicios externos. El sprint habilita análisis de riesgo previo a futuros flujos de patch review, code review, safe refactor y agentes de repositorio.

## Componentes implementados

- `src/devpilot_core/review/patch_review.py`: `PatchReviewEngine`, parser mínimo de unified diff y modelo `PatchFileChange`.
- `src/devpilot_core/review/code_review.py`: `CodeReviewEngine`, modelo `ReviewedFile` y configuración `CodeReviewConfig`.
- `src/devpilot_core/review/__init__.py`: API pública del paquete `review`.
- `tests/test_review_engines.py`: pruebas de patch review, code review y CLI.
- `docs/functional_sprint_15_manifest.json`: manifiesto estructurado del sprint.

## Funcionamiento

`PatchReviewEngine` acepta `patch_text` o `patch_file`, valida lectura mediante `PolicyEngine`, parsea cambios de archivo, contabiliza hunks, líneas agregadas/eliminadas, detecta archivos borrados/binarios, evalúa rutas destino con `PolicyEngine` y bloquea contenido tipo secreto mediante `SecretGuard`. No ejecuta `git apply`, no escribe archivos y no emite el patch crudo.

`CodeReviewEngine` acepta un archivo o directorio, aplica `PathGuard`, excluye `.git`, `.venv`, caches y `outputs`, revisa archivos de texto soportados y detecta patrones estáticos iniciales: `shell=True`, `os.system`, `eval`, `exec`, `pickle.loads`, `TODO/FIXME`, errores de sintaxis Python y contenido tipo secreto. No modifica archivos ni emite contenido crudo.

## Integración

La CLI expone:

```powershell
python -m devpilot_core patch-review --patch-file safe.patch --json
python -m devpilot_core patch-review --patch-text "<unified-diff>" --json
python -m devpilot_core code-review --target src/devpilot_core/validators --json
```

Ambos comandos devuelven `CommandResult`, pueden escribir reportes con `--write-report`, emiten eventos JSONL y persisten resultados en SQLite best-effort mediante el flujo CLI existente.

## Rol dentro de DevPilot

Este sprint abre la línea de revisión técnica de repositorios: análisis previo a patch application, code review agent, safe refactor planner y quality gates sobre cambios propuestos. Es una primera versión de seguridad preventiva, no un motor industrial completo.

## Criterios PASS

- `patch-review` analiza patches sin aplicarlos.
- `code-review` revisa archivos sin modificarlos.
- Las rutas se evalúan contra `PolicyEngine`/`PathGuard`.
- Los secretos sintéticos se bloquean o marcan sin emitir valores crudos.
- Los reportes solo se escriben bajo `outputs/reports` cuando se solicita `--write-report`.
- La suite completa de pruebas pasa.

## Criterios BLOCK

- Intentar aplicar patches automáticamente.
- Leer patch file fuera del workspace.
- Referenciar rutas denegadas como `.env` o `.git`.
- Emitir secretos crudos en JSON, reportes o trazas.
- Ejecutar comandos destructivos o dependencias externas.

## Pruebas implementadas

`tests/test_review_engines.py` cubre:

- patch seguro en dry-run sin modificar archivo destino;
- patch con secreto sintético bloqueado sin fuga del valor;
- patch contra ruta denegada bloqueado;
- CLI `patch-review --json --write-report` parseable;
- code review limpio en PASS;
- code review con `shell=True` y secreto sintético en FAIL/BLOCK sin fuga;
- CLI `code-review --json --write-report` parseable.

## Riesgos y límites

Esta es una implementación preliminar. No valida todavía si un patch aplica limpiamente, no calcula cobertura contextual completa, no sustituye SAST/SCA, no analiza dependencias vulnerables, no ejecuta linters externos, no resuelve semántica de negocio y no autoriza aplicación de patches. La evolución industrial debe incorporar AST profundo, análisis por lenguaje, integración con Git diff real, aprobación humana persistente, sandbox de aplicación y evaluación continua.

## Decisión ADR

No se abrió una ADR nueva. Se actualizó la decisión existente `ADR-0005-git-adapter-read-only-mvp-plus.md`, porque el Sprint 15 materializa la continuación natural del adapter Git read-only: revisión dry-run de patches/código sin mutación.
