# DevPilot Local — Agent-assisted SDLC personal

Estado inicial: `draft`  
Estándar rector: MIPSoftware v0.3.1 `approved with exceptions`  
Extensión inteligente: MIASI v1.0.0 `approved`  
Modo de trabajo: local-first, costo externo cero, dry-run por defecto.

## Propósito

DevPilot Local será una herramienta personal para gestionar el ciclo de vida completo de software mediante asistencia de agentes IA y validadores locales. El primer MVP no busca competir con Copilot, Cursor o plataformas comerciales; busca profesionalizar el flujo propio de ingeniería de software usando MIPSoftware como estándar operativo.

## MVP inicial

El MVP se concentra en producir, validar y auditar artefactos de ingeniería antes de implementar código de negocio:

- `devpilot init-project`
- `devpilot validate-artifact`
- `devpilot checklist-pre-code`
- `devpilot miasi-required`
- `devpilot readiness-check`

## Principios

- No ejecutar acciones destructivas.
- No requerir API keys.
- No depender de servicios cloud.
- Generar evidencia en Markdown/JSON.
- Validar artefactos con schemas/checklists.
- Activar MIASI cuando haya IA, agentes, LLMs, RAG, memoria o tool calling.

## Estructura

```text
DevPilot_Local/
  docs/
    00_product/
    01_requirements/
    02_architecture/
    03_security/
    04_quality/
    05_operations/
    06_miasi/
    checklists/
    reference/
  src/devpilot_core/
  tests/
  outputs/
```

## Primeros comandos

```powershell
cd D:\Projects\DevPilot_Local
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pytest -q
python -m devpilot_core --version
python -m devpilot_core readiness-check
```
