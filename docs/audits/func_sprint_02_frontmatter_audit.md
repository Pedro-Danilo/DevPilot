---
title: "Auditoría FUNC-SPRINT-02 — Validador de frontmatter"
doc_id: "DEVPL-AUD-FUNC-02"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-02"
updated: "2026-06-07"
approval: "approved_by_implementation_validation"
---

# Auditoría FUNC-SPRINT-02 — Validador de frontmatter

## 1. Propósito

Esta auditoría documenta la implementación de `FUNC-SPRINT-02 — Validador de frontmatter y metadatos documentales`.

El objetivo del sprint fue crear el primer validador documental real de DevPilot Local. Hasta FUNC-SPRINT-01, el CLI podía verificar existencia de artefactos y emitir resultados normalizados. Desde FUNC-SPRINT-02, DevPilot empieza a validar contenido mínimo de los documentos Markdown.

## 2. Componentes creados

| Componente | Propósito |
|---|---|
| `src/devpilot_core/validators/__init__.py` | Declara el paquete de validadores. |
| `src/devpilot_core/validators/frontmatter.py` | Parser y validador de frontmatter Markdown. |
| `tests/test_frontmatter_validator.py` | Pruebas herméticas del validador y del comando CLI. |
| `tests/fixtures/docs/*.md` | Documentos sintéticos válidos e inválidos para pruebas. |

## 3. Componentes ajustados

| Componente | Ajuste |
|---|---|
| `src/devpilot_core/cli.py` | Agrega comando `validate-frontmatter`. |
| `README.md` | Documenta comandos y estado del sprint. |
| `docs/05_operations/runbook.md` | Agrega operación del validador. |
| `docs/functional_sprint_02_manifest.json` | Registra archivos, comandos y criterios. |

## 4. Funcionamiento

El validador lee documentos Markdown, detecta un bloque inicial delimitado por `---`, extrae pares `clave: valor` y valida campos mínimos:

- `title`;
- `doc_id`;
- `status`;
- `version`;
- `owner`;
- `updated`.

También valida:

- `status` permitido: `draft`, `reviewed`, `approved`, `deprecated`;
- `version` con formato SemVer-like;
- `updated` con formato `YYYY-MM-DD`;
- warning si `doc_id` no sigue convención uppercase;
- warning por defecto si documento `approved` no tiene `approval`;
- fallo en modo `--strict` si documento `approved` no tiene `approval`.

## 5. Integración con DevPilot

El comando queda integrado al CLI:

```powershell
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --json
python -m devpilot_core validate-frontmatter docs/00_product/product_vision.md --strict
```

El resultado usa `CommandResult`, `Finding`, `Severity` y `ExitCode`, introducidos en FUNC-SPRINT-01.

## 6. Criterios PASS

- El comando existe.
- El comando valida documentos reales del repo.
- La salida JSON es parseable.
- Documentos sin frontmatter fallan.
- Documentos sin campo obligatorio fallan.
- Documentos válidos pasan.
- El modo `--strict` endurece documentos `approved`.
- No se agregan dependencias externas.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- No avanzar a `FUNC-SPRINT-03` si el comando no puede fallar con exit code diferente de cero ante documentos inválidos.
- No avanzar si la salida no usa `CommandResult`.
- No avanzar si los tests no cubren casos válidos e inválidos.

## 8. Riesgos

| Riesgo | Control |
|---|---|
| Parser no es YAML completo | Se declara como YAML-like simple y suficiente para los documentos actuales. |
| Falsos negativos en YAML complejo | Si se requiere YAML avanzado, crear ADR antes de incorporar dependencia. |
| Aprobados sin `approval` | Warning por defecto, fail en `--strict`. |
| Validación todavía limitada | FUNC-SPRINT-03 agregará validación de estructura de artefactos. |

## 9. Veredicto

`FUNC-SPRINT-02` queda en PASS técnico si las pruebas y comandos documentados pasan en el repo local.
