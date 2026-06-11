---
title: "Auditoría FUNC-SPRINT-31 — SafeSubprocessRunner y allowlist de ejecución controlada"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-31-001"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-11"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-B-SEGURIDAD-OPERACIONAL"
approval: "approved_by_owner_direction"
---

# Auditoría FUNC-SPRINT-31 — SafeSubprocessRunner y allowlist de ejecución controlada

## 1. Propósito

Auditar la implementación inicial de una capa segura para ejecutar comandos locales permitidos. Este sprint prepara `tests.run`, pero no lo implementa todavía como herramienta MIASI.

## 2. Estado

Estado: `implemented-initial`.

El sprint crea una API interna de ejecución controlada, no una interfaz pública para ejecutar comandos arbitrarios.

## 3. Funcionamiento técnico

La implementación agrega `src/devpilot_core/execution/` con:

- `CommandAllowlist`;
- `CommandAllowlistEntry`;
- `SafeSubprocessReport`;
- `SafeSubprocessRunner`.

El runner exige lista de argumentos, valida el `cwd` con `PathGuard`, verifica allowlist local, aplica timeout, ejecuta con `subprocess.run(..., shell=False)`, captura stdout/stderr, redacciona secretos con `SecretGuard`, trunca salidas largas y devuelve `CommandResult`.

## 4. Integración con DevPilot

La integración es deliberadamente interna. `FUNC-SPRINT-32` podrá usar esta capa para implementar `tests.run` como tool MIASI controlada. `PolicyEngine` y approvals ya existen desde `FUNC-SPRINT-30`, pero este sprint no ejecuta acciones críticas por sí mismo.

## 5. Comandos de uso

No hay CLI pública nueva en este sprint. Verificación recomendada:

```powershell
python -m pytest tests/test_safe_subprocess_runner.py -q
python -m pytest tests/test_sprint_31_documentation.py -q
python -m pytest -q
```

Uso interno:

```python
from pathlib import Path
import sys
from devpilot_core.execution import SafeSubprocessRunner

result = SafeSubprocessRunner(Path.cwd()).run([sys.executable, "-m", "pytest", "-q"], cwd=".", timeout_seconds=120)
```

## 6. Criterios PASS

- No usa `shell=True`.
- Bloquea strings de shell.
- Bloquea comandos fuera de allowlist.
- Bloquea `cwd` fuera del workspace.
- Aplica timeout.
- Redacta secretos en stdout/stderr.
- Trunca salidas largas.
- Devuelve estructura serializable.
- `pytest -q` pasa.

## 7. Criterios BLOCK

- Aceptar comandos como string de shell.
- Permitir comandos no allowlisted.
- Permitir cwd fuera del workspace.
- Permitir ejecución sin timeout.
- Exponer secretos crudos en stdout/stderr.
- Presentar `tests.run` como implementado antes de `FUNC-SPRINT-32`.

## 8. Riesgos

- La allowlist inicial es estrecha; ampliar entradas sin evaluación puede abrir superficie de ataque.
- La redacción es conservadora; no reemplaza secret scanning industrial.
- No hay sandbox completo de filesystem ni rollback automático.
- El runner puede ejecutar código de pruebas permitido; por eso `tests.run` debe seguir pasando por policy y approval en el siguiente sprint.

## 9. Veredicto

`FUNC-SPRINT-31` queda apto para cierre si la suite completa pasa y los artefactos de documentación permanecen sincronizados.
