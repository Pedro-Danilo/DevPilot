---
id: POST-H-EVAL-001
title: "Evaluación integral del baseline DevPilot post-Fase H"
type: "diagnostic-executable-backlog"
status: "approved"
phase: "POST-FASE-H"
source_of_truth_expected: "repo_DevPilot_Local_131.zip o repo limpio posterior al merge de POST-H-001"
recommended_branch: "post-h-eval-001-baseline-assessment"
previous_closed_hito: "POST-H-001 — Industrial hardening de tests y contratos"
recommended_next_hito: "POST-H-002 — Maturity dashboard local basado en assessment post-H"
mode: "local-first, dry-run, no external APIs"
approval: "approved_by_owner"
approved_scope: "POST-H-EVAL-001 executable diagnostic backlog"
---

# POST-H-EVAL-001 — Evaluación integral del baseline DevPilot post-Fase H

## 1. Propósito

`POST-H-EVAL-001` es un hito de diagnóstico industrial, arquitectura, priorización y decisión para evaluar integralmente el baseline DevPilot después del cierre de Fase H y de `POST-H-001`.

No es un sprint de features. Su propósito es producir una evaluación ejecutable, trazable y accionable que oriente los siguientes sprints post-H.

Debe responder con evidencia técnica:

1. Qué capacidades están realmente maduras.
2. Qué capacidades son solo `implemented-initial`.
3. Qué capacidades son experimentales.
4. Cuáles son las principales deudas arquitectónicas.
5. Cuáles son las principales deudas de testing, seguridad, operación y documentación.
6. Qué debe implementarse primero para continuar sin aumentar deuda estructural.
7. Cómo debe reformularse `POST-H-002`.
8. Qué riesgos bloquean cualquier avance hacia ejecución remota, conectores write-enabled u operación enterprise.

---

## 2. Decisión de alcance

Se determina que `POST-H-EVAL-001` debe ejecutarse como backlog de implementación paulatina y progresiva, porque el diagnóstico requerido no puede cerrarse profesionalmente como un único documento superficial.

El hito se ejecuta como una secuencia de micro-sprints documentales y de metadata, sin introducir nuevas capacidades runtime.

### 2.1 Regla central

Durante este hito:

```text
NO se implementan features nuevas.
NO se habilita remote execution.
NO se habilitan conectores write.
NO se agregan APIs externas.
NO se modifica la semántica de agentes.
NO se relajan políticas de seguridad.
NO se reemplazan quality gates existentes.
```

Sí se permite:

```text
Crear documentación industrial.
Crear manifiestos de evaluación.
Crear matrices de decisión.
Crear inventarios de capacidades.
Crear pruebas documentales mínimas.
Crear roadmap priorizado.
Actualizar README/runbook/changelog solo si es necesario para registrar el hito.
```

---

## 3. Fuente de verdad esperada

Fuente inicial:

```text
repo_DevPilot_Local_131.zip
```

Fuente recomendada para ejecución definitiva:

```text
ZIP limpio regenerado después del merge/tag de POST-H-001.
```

Artefactos que no deben entrar en el ZIP limpio:

```text
outputs/
.devpilot/devpilot.db
.devpilot/agent_sessions/
.pytest_cache/
.venv/
node_modules/
ui/web/node_modules/
ui/web/dist/
__pycache__/
Log_consola_*.txt
```

---

## 4. Rama recomendada

Después de integrar `POST-H-001` en la rama principal:

```powershell
git switch main
git pull
git switch -c post-h-eval-001-baseline-assessment
```

Si la principal es `master`:

```powershell
git switch master
git pull
git switch -c post-h-eval-001-baseline-assessment
```

No continuar nuevos hitos sobre:

```text
close/post-h-001-industrial-hardening
```

Esa rama debe quedar como rama de cierre de POST-H-001.

---

## 5. Entregables globales

Mínimos:

```text
docs/audits/post_h_eval_001_baseline_assessment.md
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/backlogs/post_h_prioritized_roadmap.md
docs/post_h_eval_001_manifest.json
tests/test_post_h_eval_001_documentation.py
```

Opcionales recomendados:

```text
.devpilot/evals/post_h_eval_001_decision_matrix.json
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-002-test-contract-registry-2.md
docs/adr/ADR-POSTH-003-cli-modularization.md
```

---

## 6. Micro-sprints del hito

```text
POST-H-EVAL-001-A — Preparación, snapshot e inventario cuantitativo
POST-H-EVAL-001-B — Assessment integral de capacidades y madurez
POST-H-EVAL-001-C — Mapa arquitectónico actual y puntos de acoplamiento
POST-H-EVAL-001-D — Registro de riesgos de seguridad, operación y compliance
POST-H-EVAL-001-E — Evaluación de testing, costos y contratos
POST-H-EVAL-001-F — Roadmap priorizado post-H y decisiones arquitectónicas
POST-H-EVAL-001-G — Manifiesto, pruebas documentales y cierre del hito
```

Cada micro-sprint debe poder ejecutarse, validarse y commitearse de forma independiente si conviene.

---


## 6.1 Estado de ejecución del hito

| Micro-sprint | Estado actual | Evidencia principal |
|---|---|---|
| POST-H-EVAL-001-A | implemented | `docs/audits/post_h_eval_001_baseline_assessment.md`, `docs/post_h_eval_001_manifest.json` |
| POST-H-EVAL-001-B | implemented | `.devpilot/evals/post_h_eval_001_decision_matrix.json` |
| POST-H-EVAL-001-C | implemented | `docs/02_architecture/post_h_current_architecture_map.md` |
| POST-H-EVAL-001-D | implemented | `docs/03_security/post_h_security_risk_register.md` |
| POST-H-EVAL-001-E | implemented | `docs/04_quality/post_h_test_cost_assessment.md` |
| POST-H-EVAL-001-F | implemented | `docs/backlogs/post_h_prioritized_roadmap.md`, `docs/adr/ADR-POSTH-*.md` |
| POST-H-EVAL-001-G | pending | Manifest final, prueba documental global y cierre del hito |

Nota: `POST-H-EVAL-001-F` es implementación documental/metadata. No introduce features runtime, no habilita remote execution, no habilita connector write ni plugin execution. El hito completo queda pendiente de cierre formal en `POST-H-EVAL-001-G`.

# POST-H-EVAL-001-A — Preparación, snapshot e inventario cuantitativo

## Objetivo

Crear una línea base objetiva del repositorio post-H, con métricas cuantitativas, comandos de validación inicial y evidencia del estado real antes de tomar decisiones.

## Entregables

```text
docs/audits/post_h_eval_001_baseline_assessment.md
docs/post_h_eval_001_manifest.json
```

## Tareas

### A.1 Confirmar rama y estado limpio

```powershell
git branch --show-current
git status --short
git log --oneline --decorate -5
```

Criterios:

```text
PASS si la rama es post-h-eval-001-baseline-assessment.
PASS si working tree está limpio antes de iniciar.
BLOCK si hay outputs, agent_sessions, logs o caches trackeados.
```

### A.2 Ejecutar validaciones baseline

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core industrial-readiness check --json
```

### A.3 Inventariar repo

Recolectar:

```text
Número de archivos Python en src/devpilot_core.
Número aproximado de líneas Python.
Número de archivos test_*.py.
Número aproximado de líneas de tests.
Número de archivos docs.
Número aproximado de líneas docs.
Número de schemas registrados.
Número de functional manifests.
Número de audit docs.
Número de agentes MIASI.
Número de tools MIASI.
Número de reglas policy MIASI.
Número de test contracts.
Estado de .devpilot/project_state.json.
Estado de .gitignore.
Presencia o ausencia de runtime artifacts.
```

### A.4 Crear encabezado del assessment

`docs/audits/post_h_eval_001_baseline_assessment.md` debe incluir:

```markdown
# POST-H-EVAL-001 — Baseline assessment DevPilot post-Fase H

## Estado ejecutivo

## Fuente de verdad analizada

## Comandos ejecutados

## Snapshot cuantitativo

## Hallazgos iniciales

## Riesgos preliminares
```

### A.5 Crear manifiesto inicial

`docs/post_h_eval_001_manifest.json` debe iniciar con:

```json
{
  "schema_version": "1.0",
  "id": "POST-H-EVAL-001",
  "type": "diagnostic-executable-backlog",
  "status": "in_progress",
  "source_of_truth": "repo_DevPilot_Local_131 or clean successor",
  "no_runtime_features_added": true,
  "no_remote_execution_enabled": true,
  "deliverables": [],
  "validations": [],
  "decisions": []
}
```

## Criterios PASS

```text
PASS si existe baseline assessment inicial.
PASS si existe manifest inicial.
PASS si las validaciones baseline pasan o quedan registradas con explicación.
PASS si se documenta fuente de verdad exacta.
PASS si se identifica si el ZIP contiene runtime artifacts.
```

## Criterios BLOCK

```text
BLOCK si se modifica código core sin justificación.
BLOCK si se ocultan validaciones fallidas.
BLOCK si se omite fuente de verdad.
BLOCK si se ignora presencia de runtime artifacts.
```

---

# POST-H-EVAL-001-B — Assessment integral de capacidades y madurez

## Objetivo

Clasificar las capacidades existentes de DevPilot por dominio, evidencia, estado de implementación, madurez industrial, riesgo y acción recomendada.

## Entregables

```text
docs/audits/post_h_eval_001_baseline_assessment.md
.devpilot/evals/post_h_eval_001_decision_matrix.json
```

## Dominios mínimos a evaluar

```text
Core CLI
Application Services
Schemas y contratos
Project state
Quality gates
Testing contracts
PolicyEngine
MIASI
Approval
RBAC / Identity
Security guards
Agent runtime
SDLC agents
MultiAgentCoordinator
Workflows multiagente
RAG local
Connectors / MCP
Plugin registry
Multiworkspace
Observability / AgentOps
Audit packs
Compliance packs
Release dry-run
Remote runner stub
Enterprise reports
UI web
API local
Documentation governance
```

## Matriz de madurez

Usar una de estas categorías:

```text
production-ready-local
implemented
implemented-initial
experimental
planned
deprecated
```

Formato mínimo:

```markdown
| Dominio | Evidencia | Madurez | Riesgo | Acción recomendada | Prioridad |
|---|---|---|---|---|---|
```

## Reglas de clasificación

### production-ready-local

```text
Tiene tests.
Tiene schemas o contratos.
Tiene documentación operativa.
Está integrado a quality gate.
No depende de red.
No requiere secretos.
Tiene comportamiento reproducible.
```

### implemented

```text
Funciona localmente.
Tiene pruebas razonables.
Tiene documentación.
Su alcance está controlado.
```

### implemented-initial

```text
Existe funcionalidad MVP.
Hay pruebas básicas.
Faltan garantías de operación, seguridad, retención, escalabilidad o UX.
```

### experimental

```text
Existe como stub, diseño o demostración.
No debe considerarse listo para uso real.
Debe permanecer deshabilitado o dry-run.
```

## Criterios PASS

```text
PASS si todos los dominios mínimos están evaluados.
PASS si cada dominio tiene evidencia concreta.
PASS si cada dominio tiene madurez asignada.
PASS si cada dominio tiene acción recomendada.
PASS si enterprise/remote queda marcado como experimental si no hay garantías completas.
```

## Criterios BLOCK

```text
BLOCK si se declara DevPilot production-ready completo.
BLOCK si remote runner queda clasificado como maduro sin threat model.
BLOCK si se omiten dominios existentes.
BLOCK si se usan afirmaciones sin evidencia.
```

---

# POST-H-EVAL-001-C — Mapa arquitectónico actual y puntos de acoplamiento

## Objetivo

Documentar la arquitectura real de DevPilot, sus capas, paquetes, dependencias conceptuales, puntos de acoplamiento y riesgos de mantenibilidad.

## Entregables

```text
docs/02_architecture/post_h_current_architecture_map.md
```

## Secciones obligatorias

```markdown
# Mapa arquitectónico actual DevPilot post-H

## 1. Resumen arquitectónico
## 2. Vista por capas
## 3. Vista por paquetes Python
## 4. Vista CLI/API/UI
## 5. Vista de estado local .devpilot
## 6. Vista de seguridad
## 7. Vista de testing y quality gates
## 8. Vista de observabilidad
## 9. Vista de release y auditoría
## 10. Puntos de acoplamiento
## 11. Riesgos arquitectónicos
## 12. Recomendaciones de refactor
## 13. Decisiones pendientes
```

## Modelo de capas recomendado

```text
User Interfaces
 ├── CLI
 ├── API local
 └── UI web

Application Layer
 ├── Application services
 ├── Command orchestration
 └── Validation gateway

Governance Layer
 ├── PolicyEngine
 ├── Approval
 ├── RBAC / Identity
 ├── MIASI
 └── Security guards

Agentic Layer
 ├── Agent runtime
 ├── SDLC agents
 ├── MultiAgentCoordinator
 ├── Workflows
 └── Evaluators

Knowledge Layer
 ├── RAG local
 ├── Document index
 ├── Schemas
 └── Standards

Integration Layer
 ├── Connectors
 ├── MCP
 ├── Plugins
 └── Remote stubs

Operations Layer
 ├── Observability
 ├── Traceability
 ├── Audit packs
 ├── Compliance packs
 ├── Release
 └── Industrial readiness
```

## Riesgos arquitectónicos mínimos

```text
CLI monolítico.
Crecimiento acumulativo de comandos.
Posible drift entre docs/manifests/backlogs.
Testing histórico abundante pero costoso.
Runtime artifacts en fuentes ZIP antiguas.
Remote runner como stub experimental.
Plugin ecosystem sin sandbox real de ejecución.
Connectors read-only, no write-safe todavía.
UI/API implemented-initial.
```

## Criterios PASS

```text
PASS si el documento refleja arquitectura real, no aspiracional.
PASS si se identifican puntos de acoplamiento.
PASS si se registra riesgo de CLI monolítico.
PASS si se distinguen capas core, governance, agentic, knowledge, integration y operations.
```

## Criterios BLOCK

```text
BLOCK si el mapa ignora UI/API.
BLOCK si el mapa ignora seguridad.
BLOCK si el mapa ignora testing.
BLOCK si no se registran riesgos arquitectónicos.
```

---

# POST-H-EVAL-001-D — Registro de riesgos de seguridad, operación y compliance

## Objetivo

Crear un registro de riesgos industrial que guíe la evolución segura de DevPilot antes de habilitar capacidades sensibles.

## Entregables

```text
docs/03_security/post_h_security_risk_register.md
```

## Riesgos mínimos

| ID | Riesgo | Severidad mínima | Acción esperada |
|---|---|---:|---|
| SEC-001 | Activación prematura de remote execution | Crítica | ADR + threat model + sandbox antes de ejecutar |
| SEC-002 | Connector write accidental | Alta | Deny-by-default + replay tests |
| SEC-003 | Plugin execution insegura | Alta | Metadata-only hasta sandbox |
| SEC-004 | Actor spoofing local | Alta | Hardening RBAC/Approval |
| SEC-005 | Runtime artifacts en ZIP/audit packs | Alta | Export policy + tests |
| SEC-006 | Secret leakage | Alta | SecretGuard + scanning documental |
| SEC-007 | UI/API sin auth robusta | Media-alta | Session/token hardening |
| SEC-008 | Retención indefinida de traces | Media | Retention policy |
| SEC-009 | Sobreclaiming compliance | Media | Etiquetas explícitas de no-certificación |
| SEC-010 | RAG sin groundedness robusto | Media | Evals de groundedness |

## Formato de riesgo

```markdown
## SEC-001 — Activación prematura de remote execution

- Severidad:
- Probabilidad:
- Impacto:
- Estado actual:
- Evidencia:
- Mitigación:
- Criterio de cierre:
- Sprint recomendado:
```

## Criterios PASS

```text
PASS si hay al menos 10 riesgos.
PASS si remote execution queda como riesgo crítico.
PASS si connectors write queda bloqueado por defecto.
PASS si plugin execution queda bloqueado hasta sandbox.
PASS si runtime artifacts quedan como riesgo de distribución.
```

## Criterios BLOCK

```text
BLOCK si se permite remote execution real.
BLOCK si se propone write connector sin nueva ADR.
BLOCK si se declara compliance certificada.
BLOCK si se ignora secret leakage.
```

---

# POST-H-EVAL-001-E — Evaluación de testing, costos y contratos

## Objetivo

Evaluar el sistema de pruebas y proponer evolución hacia un Test Contract Registry 2.0 por dominio, criticidad, riesgo e impacto.

## Entregables

```text
docs/04_quality/post_h_test_cost_assessment.md
```

## Contenido mínimo

```markdown
# Evaluación de testing y costos post-H

## 1. Resumen ejecutivo
## 2. Inventario de tests
## 3. Test Contract Registry actual
## 4. Tests históricos vs tests funcionales
## 5. Quality gates existentes
## 6. Impact analyzer actual
## 7. Costos de regresión
## 8. Brechas de cobertura por dominio
## 9. Propuesta Test Contract Registry 2.0
## 10. Matriz P0/P1/P2/P3
## 11. Roadmap de testing
## 12. Criterios de cierre
```

## Clasificación propuesta

```text
P0 — Seguridad, PolicyEngine, Approval, RBAC, PathGuard, SecretGuard, remote disabled.
P1 — Schemas, manifests, project state, quality gates, test contracts.
P2 — Agents, RAG, connectors, plugins, multiworkspace, workflows.
P3 — UI smoke, docs, reports, release artifacts.
```

## Preguntas obligatorias

```text
¿Qué pruebas son críticas para no romper seguridad?
¿Qué pruebas son históricas y documentales?
¿Qué pruebas son de producto?
¿Qué pruebas pueden correr siempre?
¿Qué pruebas deben correr por impacto?
¿Qué pruebas deben ejecutarse solo antes de release?
¿Qué dominios no están bien mapeados por impact analyzer?
```

## Criterios PASS

```text
PASS si se propone Test Contract Registry 2.0.
PASS si se clasifican pruebas por criticidad.
PASS si se evalúa costo de pytest completo.
PASS si se identifican gaps del impact analyzer.
PASS si se recomienda roadmap de testing.
```

## Criterios BLOCK

```text
BLOCK si se asume que muchos tests equivalen automáticamente a cobertura industrial.
BLOCK si no se separan tests históricos de tests críticos.
BLOCK si no se evalúa costo de ejecución.
```

---

# POST-H-EVAL-001-F — Roadmap priorizado post-H y decisiones arquitectónicas

## Objetivo

Definir la hoja de ruta que orientará los siguientes sprints, con prioridades, dependencias, riesgos, decisiones y criterios de entrada.

## Entregables

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-002-test-contract-registry-2.md
docs/adr/ADR-POSTH-003-cli-modularization.md
```

## Roadmap recomendado

### Oleada 0 — Baseline limpio y diagnóstico

| Prioridad | Hito | Objetivo |
|---|---|---|
| P0 | POST-H-EVAL-001 | Evaluación integral, roadmap y decisiones |
| P0 | Repo hygiene final | Fuente ZIP limpia sin runtime artifacts |

### Oleada 1 — Gobernanza de madurez y testing

| Prioridad | Hito | Objetivo |
|---|---|---|
| P0 | POST-H-002 | Maturity dashboard local basado en assessment |
| P0 | POST-H-003 | Test Contract Registry 2.0 |
| P0 | POST-H-004 | Policy/MIASI semantic validator ampliado |
| P0 | POST-H-005 | Architecture map executable / dependency ownership |

### Oleada 2 — Mantenibilidad y arquitectura interna

| Prioridad | Hito | Objetivo |
|---|---|---|
| P1 | POST-H-006 | CLI command registry y desacoplamiento de handlers |
| P1 | POST-H-007 | ApplicationService boundary hardening |
| P1 | POST-H-008 | Runtime state lifecycle policy |
| P1 | POST-H-009 | Documentation governance y canonical sources |

### Oleada 3 — Observabilidad, RAG y seguridad operacional

| Prioridad | Hito | Objetivo |
|---|---|---|
| P1 | POST-H-010 | Observability retention local |
| P1 | POST-H-011 | RAG groundedness evals |
| P1 | POST-H-012 | Approval/RBAC hardening |
| P1 | POST-H-013 | Audit pack signing/encryption local opcional |

### Oleada 4 — Producto local industrial

| Prioridad | Hito | Objetivo |
|---|---|---|
| P1 | POST-H-014 | UI/API industrial shell |
| P1 | POST-H-015 | Local operator dashboard |
| P2 | POST-H-016 | Workspace portfolio hardening |
| P2 | POST-H-017 | Release reproducibility pack |

### Oleada 5 — Extensibilidad controlada

| Prioridad | Hito | Objetivo |
|---|---|---|
| P2 | POST-H-018 | Connector sandbox avanzado |
| P2 | POST-H-019 | Plugin sandbox design sin ejecución arbitraria |
| P2 | POST-H-020 | Compliance mapping packs ampliados |

### Oleada 6 — Remote/enterprise solo como diseño

| Prioridad | Hito | Objetivo |
|---|---|---|
| P3 | POST-H-021 | Remote Runner ADR-2 |
| P3 | POST-H-022 | Enterprise deployment threat model |
| P3 | POST-H-023 | Secure transport design sin implementación activa |

## Decisiones mínimas

### DEC-POSTH-001 — Local-first antes de remote

```text
DevPilot continuará como producto local-first industrial antes de ampliar autonomía, conectividad remota o ejecución distribuida.
```

### DEC-POSTH-002 — Maturity dashboard basado en assessment

```text
POST-H-002 se mantiene, pero debe basarse en matriz de madurez y roadmap definidos por POST-H-EVAL-001.
```

### DEC-POSTH-003 — Remote execution bloqueado

```text
No se habilitará remote execution real sin ADR nueva, threat model, RBAC fuerte, sandbox, auditoría y aprobación humana.
```

### DEC-POSTH-004 — CLI modularization

```text
El CLI monolítico entra al roadmap de refactor arquitectónico.
```

### DEC-POSTH-005 — Test Contract Registry 2.0

```text
El Test Contract Registry debe evolucionar hacia contratos por dominio, criticidad, riesgo e impacto.
```

### DEC-POSTH-006 — ZIP/audit pack hygiene

```text
Los audit packs, ZIPs y fuentes de verdad futuras deben excluir runtime artifacts.
```

## Criterios PASS

```text
PASS si el roadmap contiene prioridades P0/P1/P2/P3.
PASS si cada hito tiene objetivo claro.
PASS si se explicitan dependencias.
PASS si POST-H-002 queda refinado.
PASS si remote/enterprise queda pospuesto hasta condiciones explícitas.
```

## Criterios BLOCK

```text
BLOCK si el roadmap prioriza features sobre seguridad/testing/arquitectura.
BLOCK si remote execution queda antes del hardening local.
BLOCK si no hay decisiones arquitectónicas explícitas.
```

---


## Estado de implementación F

Implementado en este repo mediante:

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-002-test-contract-registry-2.md
docs/adr/ADR-POSTH-003-cli-modularization.md
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
tests/test_post_h_eval_001_f_prioritized_roadmap.py
```

El alcance se mantiene diagnóstico/documental. El cierre global del hito queda reservado para `POST-H-EVAL-001-G`.

# POST-H-EVAL-001-G — Manifiesto, pruebas documentales y cierre

## Objetivo

Cerrar el hito con trazabilidad, pruebas documentales, manifiesto final y validaciones.

## Entregables

```text
docs/post_h_eval_001_manifest.json
tests/test_post_h_eval_001_documentation.py
README.md
README.md solo si se registra el hito en estado del proyecto.
docs/release/CHANGELOG.md solo si aplica.
docs/05_operations/runbook.md solo si aplica.
```

## Prueba documental mínima

Crear `tests/test_post_h_eval_001_documentation.py`:

```python
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/audits/post_h_eval_001_baseline_assessment.md",
    "docs/02_architecture/post_h_current_architecture_map.md",
    "docs/03_security/post_h_security_risk_register.md",
    "docs/04_quality/post_h_test_cost_assessment.md",
    "docs/backlogs/post_h_prioritized_roadmap.md",
    "docs/post_h_eval_001_manifest.json",
]


def test_post_h_eval_001_required_docs_exist():
    for relative_path in REQUIRED_DOCS:
        assert (ROOT / relative_path).exists(), relative_path


def test_post_h_eval_001_manifest_contract():
    manifest = json.loads((ROOT / "docs/post_h_eval_001_manifest.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "POST-H-EVAL-001"
    assert manifest["type"] == "diagnostic-executable-backlog"
    assert manifest["no_runtime_features_added"] is True
    assert manifest["no_remote_execution_enabled"] is True


def test_post_h_eval_001_docs_have_required_sections():
    expectations = {
        "docs/audits/post_h_eval_001_baseline_assessment.md": [
            "Estado ejecutivo",
            "Snapshot cuantitativo",
            "Capacidades por dominio",
            "Riesgos",
            "Roadmap",
        ],
        "docs/02_architecture/post_h_current_architecture_map.md": [
            "Vista por capas",
            "Puntos de acoplamiento",
            "Riesgos arquitectónicos",
        ],
        "docs/03_security/post_h_security_risk_register.md": [
            "SEC-001",
            "remote execution",
            "Connector",
            "Plugin",
        ],
        "docs/04_quality/post_h_test_cost_assessment.md": [
            "Test Contract Registry",
            "Impact analyzer",
            "P0",
            "P1",
        ],
        "docs/backlogs/post_h_prioritized_roadmap.md": [
            "Oleada 0",
            "Oleada 1",
            "POST-H-002",
            "Remote",
        ],
    }

    for relative_path, required_terms in expectations.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for term in required_terms:
            assert term in content, f"{term} missing from {relative_path}"
```

## Validaciones finales

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core industrial-readiness check --json

python -m pytest tests\test_post_h_eval_001_documentation.py -q
python -m pytest tests\test_project_global_state.py tests\test_test_contract_registry.py tests\test_test_impact.py -q
python -m pytest tests\test_sprint_*_documentation.py -q
```

Validación completa recomendada:

```powershell
python -m pytest -q
```

## Criterios PASS globales

```text
PASS si los seis documentos principales existen.
PASS si el manifiesto existe y declara modo diagnóstico.
PASS si hay matriz de capacidades.
PASS si hay mapa arquitectónico.
PASS si hay risk register.
PASS si hay evaluación de testing.
PASS si hay roadmap priorizado.
PASS si hay decisiones arquitectónicas explícitas.
PASS si hay prueba documental mínima.
PASS si los quality gates focales pasan.
PASS si no se habilitó remote execution.
PASS si no se agregaron features runtime.
```

## Criterios BLOCK globales

```text
BLOCK si el hito implementa features nuevas.
BLOCK si modifica agentes, conectores, plugins o remote runner.
BLOCK si declara DevPilot production-ready enterprise.
BLOCK si no clasifica madurez por dominio.
BLOCK si no registra riesgos de seguridad.
BLOCK si no produce roadmap accionable.
BLOCK si no define criterios de entrada para POST-H-002.
BLOCK si los documentos son narrativos pero no ejecutables.
```

---

# 7. Criterios de entrada para POST-H-002

`POST-H-002 — Maturity dashboard local` solo debe iniciar si:

```text
POST-H-EVAL-001 está cerrado.
Existe roadmap priorizado.
Existe matriz de madurez.
Existe assessment baseline.
Existe risk register.
Existe test cost assessment.
Existe architecture map.
El repo fuente está limpio de runtime artifacts.
project-state validate pasa.
test-contracts validate pasa.
quality-gate hardening pasa.
```

## Redefinición recomendada de POST-H-002

Nombre recomendado:

```text
POST-H-002 — Maturity dashboard local basado en assessment post-H
```

Objetivo refinado:

```text
Construir un dashboard local read-only que consuma project_state, industrial readiness, test contracts, quality gates y la matriz de evaluación POST-H-EVAL-001 para visualizar madurez, riesgos, deuda y roadmap.
```

No debe ser:

```text
Un dashboard ornamental.
Un panel solo de score.
Un sustituto del roadmap.
Una vía para habilitar features.
```

---

# 8. Orden recomendado de commits

## Opción A — Un solo commit del hito

```powershell
git add docs/audits/post_h_eval_001_baseline_assessment.md
git add docs/02_architecture/post_h_current_architecture_map.md
git add docs/03_security/post_h_security_risk_register.md
git add docs/04_quality/post_h_test_cost_assessment.md
git add docs/backlogs/post_h_prioritized_roadmap.md
git add docs/post_h_eval_001_manifest.json
git add tests/test_post_h_eval_001_documentation.py

git commit -m "POST-H-EVAL-001 add post-H baseline assessment and roadmap"
```

## Opción B — Commits por micro-sprint

```powershell
git commit -m "POST-H-EVAL-001-A add baseline snapshot"
git commit -m "POST-H-EVAL-001-B add capability maturity assessment"
git commit -m "POST-H-EVAL-001-C add architecture map"
git commit -m "POST-H-EVAL-001-D add security risk register"
git commit -m "POST-H-EVAL-001-E add testing cost assessment"
git commit -m "POST-H-EVAL-001-F add prioritized roadmap and decisions"
git commit -m "POST-H-EVAL-001-G add manifest and documentation tests"
```

---

# 9. Checklist de cierre

```text
[ ] Rama creada desde main/master limpio.
[ ] Fuente de verdad definida.
[ ] Runtime artifacts excluidos.
[ ] Assessment baseline creado.
[ ] Architecture map creado.
[ ] Security risk register creado.
[ ] Test cost assessment creado.
[ ] Roadmap priorizado creado.
[ ] Manifest creado.
[ ] Prueba documental creada.
[ ] Validaciones baseline ejecutadas.
[ ] Quality gate hardening ejecutado.
[ ] Tests focales ejecutados.
[ ] Decisiones arquitectónicas documentadas.
[ ] POST-H-002 redefinido.
[ ] Commit limpio realizado.
[ ] Tag opcional creado si aplica.
```

---

# 10. Resultado esperado

Al cerrar `POST-H-EVAL-001`, DevPilot debe contar con:

```text
Estado real conocido.
Madurez por capacidad.
Riesgos identificados.
Deuda priorizada.
Roadmap accionable.
Criterios de entrada para POST-H-002.
Límites de seguridad claros.
Estrategia de testing futura.
Dirección arquitectónica post-H.
```

Este hito evita que DevPilot siga creciendo por acumulación de funcionalidades y establece una gobernanza técnica adecuada para continuar con una línea profesional e industrial.
