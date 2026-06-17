---
doc_id: DEVPL-OPS-INSTALL-GUIDE-001
title: DevPilot Local — Guía de instalación local e installer preliminar
status: approved
version: 1.0.0
owner: Ordóñez
updated: 2026-06-17
approval: approved_after_func_sprint_82_validation
sprint: FUNC-SPRINT-82
phase: FASE-G-PRODUCTIZACION-RELEASE
---

# DevPilot Local — Guía de instalación local e installer preliminar

## Estado

Documento aprobado como implementación inicial de `FUNC-SPRINT-82`.

Esta guía es `implemented-initial`: define instalación local repetible, matriz de estrategias y plan dry-run. No implementa auto-update, servicios persistentes, instalación con privilegios elevados, publicación remota ni instalador desktop real.

## 1. Propósito

Definir una estrategia inicial de instalación local para DevPilot que sea segura, repetible y verificable. El sprint introduce el comando:

```powershell
python -m devpilot_core install plan --mode all --json
```

El comando genera un plan de instalación, pero no ejecuta instalación. Esta decisión evita mutaciones ocultas en el equipo del usuario y mantiene el principio local-first, dry-run-first y policy-first.

## 2. Alcance

Incluye:

- instalación editable para desarrollo;
- instalación desde wheel local;
- instalación/revisión desde ZIP fuente limpio;
- puente documental hacia futuro desktop shell;
- reporte opcional `outputs/reports/install_plan.*`.

No incluye:

- no auto-update;
- no requiere privilegios elevados por defecto;
- publicación en PyPI o GitHub Releases;
- instalación como servicio persistente;
- firma de instaladores;
- instalador desktop real;
- cambios en variables globales del sistema.

## 3. Comandos principales

```powershell
python -m devpilot_core install plan --mode all --json
python -m devpilot_core install plan --mode wheel --version 0.1.0 --json
python -m devpilot_core install plan --mode zip --version 0.1.0 --json
python -m devpilot_core install plan --mode all --json --write-report
```

## 4. Matriz de instalación

| Modo | Uso recomendado | Artefacto | Estado |
|---|---|---|---|
| `editable` | Desarrollo local | Workspace fuente | Recomendado para desarrollo |
| `wheel` | Release candidate local | `dist/devpilot_local-<version>-py3-none-any.whl` | Recomendado para candidato local |
| `zip` | Auditoría y distribución fuente limpia | `dist/release/devpilot-local-<version>-source.zip` | Soportado |
| `desktop-bridge` | Puente hacia futuro shell desktop | Web UI/API local | Documentado, no construido |

## 5. Procedimiento Windows recomendado

### 5.1 Instalación editable

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m devpilot_core --version
python -m pytest -q
```

### 5.2 Instalación desde wheel local

```powershell
python -m devpilot_core package build --kind all --version 0.1.0 --execute --json --write-report
python -m devpilot_core release verify --artifact dist\release\devpilot-local-0.1.0-source.zip --json --write-report

py -3.12 -m venv .venv-install-smoke
.\.venv-install-smoke\Scripts\Activate.ps1
python -m pip install dist\devpilot_local-0.1.0-py3-none-any.whl
python -m devpilot_core --version
```

### 5.3 Instalación desde ZIP fuente limpio

```powershell
python -m devpilot_core package build --kind repo-zip --version 0.1.0 --execute --json --write-report
python -m devpilot_core release verify --artifact dist\release\devpilot-local-0.1.0-source.zip --json --write-report

Expand-Archive -Path dist\release\devpilot-local-0.1.0-source.zip -DestinationPath .\install-smoke -Force
cd .\install-smoke
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m devpilot_core --version
```

## 6. Relación con Desktop/Web

Fase F decidió avanzar con Web UI local web-first y mantener Desktop diferido. `FUNC-SPRINT-82` no construye un instalador desktop, pero deja documentada la relación:

- la Web UI local sigue siendo la experiencia visual inicial;
- un futuro desktop shell debe envolver API/Web UI sin duplicar lógica;
- cualquier instalador desktop futuro requiere ADR adicional, threat model y pruebas de instalación/rollback.

## 7. Funcionamiento técnico

`install plan` genera una salida `CommandResult` con:

- matriz de decisión;
- pasos por modo;
- artefactos esperados;
- precondiciones;
- limitaciones;
- flags de seguridad.

El comando es plan-only: no llama `pip`, no crea venvs, no modifica archivos y no instala servicios.

## 8. Criterios PASS

- `install plan --mode all --json` retorna PASS.
- La guía documenta instalación editable, wheel, ZIP y Desktop bridge.
- No hay auto-update.
- No hay servicios persistentes.
- No requiere privilegios elevados por defecto.
- No requiere red sin alternativa local.
- La relación con Fase F/Web UI queda explícita.

## 9. Criterios BLOCK

- Requerir red como único camino de instalación.
- Instalar servicios persistentes sin ADR.
- Requerir privilegios elevados por defecto.
- Ejecutar instalación desde el comando plan-only.
- Ocultar limitaciones del installer preliminar.
- Construir Desktop shell sin decisión arquitectónica adicional.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Confundir plan con instalación real | Declarar `dry-run` y `execute_supported=false`. |
| Instalación con privilegios excesivos | Bloquear privilegios elevados por defecto. |
| Duplicar Web UI en un futuro Desktop | Mantener desktop-bridge como documento, no como implementación. |
| Instalar artefacto no verificado | Exigir `package build` y `release verify` antes de instalación manual. |

## 11. Evolución pendiente

- Smoke install real en entorno temporal aislado.
- Pruebas de upgrade.
- Pruebas de rollback.
- Firma de instaladores.
- Instalador desktop real si se aprueba en una fase futura.
- Política de distribución externa.
