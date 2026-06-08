---
title: "FUNC-SPRINT-17 — ModelAdapter híbrido, proveedores y CostGuard"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-17"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-17"
updated: "2026-06-08"
---
# FUNC-SPRINT-17 — ModelAdapter híbrido, proveedores y CostGuard

## Propósito

Introducir una capa `ModelAdapter` desacoplada de proveedores, manteniendo DevPilot operativo sin API keys, sin red y sin costo externo. La implementación permite probar contratos de generación, clasificación y embeddings antes de conectar proveedores reales.

## Componentes

```text
src/devpilot_core/modeling/contracts.py
src/devpilot_core/modeling/providers.py
src/devpilot_core/modeling/mock_adapter.py
src/devpilot_core/modeling/router.py
src/devpilot_core/modeling/__init__.py
.devpilot/providers.yaml.example
tests/test_model_adapter.py
```

## Funcionamiento

`ProviderRegistry` carga metadata segura de proveedores. `ModelAdapterRouter` aplica `SecretGuard` sobre prompts/textos y `CostGuard`/`PolicyEngine` sobre rutas externas. Solo `MockModelAdapter` ejecuta una respuesta determinística. Los proveedores locales/API se registran como placeholders y no se contactan.

## Comandos

```powershell
python -m devpilot_core model providers --json
python -m devpilot_core model generate --provider mock --prompt "Diseñar agente documental" --json
python -m devpilot_core model classify --provider mock --text "bug detectado" --labels "bug,feature" --json
python -m devpilot_core model embed --provider mock --text "vector estable" --json
python -m devpilot_core model generate --provider openai --prompt "test" --json
```

## Criterios PASS

```text
MockModelAdapter determinístico.
ProviderRegistry sin secretos crudos.
CostGuard bloquea API externa por defecto.
No hay llamadas de red.
No hay API keys obligatorias.
Reportes opcionales en outputs/reports.
pytest -q en PASS.
```

## Criterios BLOCK

```text
Proveedor desconocido.
Secreto sintético en prompt/text.
API externa sin presupuesto explícito.
Configuración con valor de API key crudo.
Ejecución real de proveedor local/API en Sprint 17.
```

## Pruebas

`tests/test_model_adapter.py` valida carga segura de proveedores, generación determinística, clasificación, embeddings estables, bloqueo de secretos, bloqueo de API externa y CLI parseable con reportes opcionales.

## Riesgos

Primera versión. No hay clientes reales, streaming, retries, timeouts, conteo real de tokens, medición real de costos ni evaluación semántica. La integración de proveedores reales debe acompañarse de SecretGuard, CostGuard persistente, Eval Harness ampliado y aprobación humana cuando haya costo/red.

## ADR

Se actualizó `ADR-0006-local-first-hibrido-modeladapter-costguard.md` porque la decisión arquitectónica ya existía. No se abre nueva ADR.
