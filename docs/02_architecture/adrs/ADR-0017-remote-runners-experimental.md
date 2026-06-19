---
title: "ADR-0017 — Remote runners experimentales deshabilitados por defecto"
doc_id: "DEVPL-ADR-0017-REMOTE-RUNNERS-EXPERIMENTAL"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-19"
sprint: "FUNC-SPRINT-98"
---

# ADR-0017 — Remote runners experimentales deshabilitados por defecto

## Contexto

La Fase H habilita capacidades enterprise, pero el backlog establece que los remote runners y cualquier control plane cloud deben permanecer experimentales/future hasta contar con una decisión explícita. DevPilot ya dispone de PolicyEngine, MIASI, RBAC, audit packs y compliance packs; sin embargo, todavía no existe un modelo de identidad distribuida, transporte seguro, aislamiento remoto, firma, cifrado ni trust model entre workspaces remotos.

## Decisión

Implementar en `FUNC-SPRINT-98` únicamente un stub metadata-only de remote runners:

- registry local `.devpilot/remote/runner_registry.json`;
- schema `SCHEMA-DEVPL-REMOTE-RUNNER-REGISTRY-V1`;
- CLI `remote runner status --json`;
- bloqueo explícito de cualquier intento de ejecución;
- `enterprise report --json` como reporte local agregado y read-only;
- suite safety `remote-enterprise`.

No se habilita ejecución remota, shell, red, API externa, cloud control plane, credenciales ni mutaciones de fuente.

## Consecuencias

### Positivas

- Permite revisar arquitectura enterprise sin introducir superficie real de ejecución remota.
- Hace verificable que los remote runners están deshabilitados por defecto.
- Añade evidencia enterprise local antes de cualquier expansión remota.
- Reduce riesgo de regresiones porque el comportamiento seguro se prueba por schema, CLI, MIASI y safety suite.

### Negativas

- No ejecuta trabajos remotos reales.
- No resuelve autenticación distribuida, cifrado, firma, cola remota, networking ni sandbox remoto.
- El enterprise report es un agregado local inicial, no un dashboard enterprise completo.

## Alternativas consideradas

1. **Habilitar remote runner real.** Rechazado: requiere seguridad, identidad y sandbox remoto no implementados.
2. **No crear ningún artefacto remote.** Rechazado: no permitiría preparar contratos ni pruebas para la evolución enterprise.
3. **Crear stub disabled-by-default.** Aprobado: maximiza aprendizaje/arquitectura sin abrir riesgo operativo.

## Criterios de habilitación futura

Un sprint futuro solo podrá habilitar remote execution si incorpora una nueva ADR con:

- autenticación y autorización distribuida;
- RBAC por runner/workspace;
- aprobación humana para ejecución;
- aislamiento/sandbox remoto;
- transporte cifrado;
- firma de jobs y resultados;
- auditoría inmutable;
- límites de costo y tiempo;
- evaluación adversarial ampliada;
- plan de revocación/kill switch.

## Estado

Aprobada para `FUNC-SPRINT-98` como decisión `implemented-initial`: remote runners siguen deshabilitados por defecto y enterprise reporting permanece local/read-only.
