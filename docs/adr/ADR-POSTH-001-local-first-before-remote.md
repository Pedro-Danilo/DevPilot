---
doc_id: "ADR-POSTH-001"
title: "Local-first antes de remote execution"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "accepted_by_owner"
decision_state: "accepted"
micro_sprint: "POST-H-EVAL-001-F"
---

# ADR-POSTH-001 — Local-first antes de remote execution

## Contexto

DevPilot ya contiene capacidades locales amplias: PolicyEngine, MIASI, RBAC/Approval inicial, RAG local, conectores read-only, plugins metadata-first, UI/API local, observabilidad y remote runner stub experimental. El risk register post-H clasifica la activación prematura de remote execution como riesgo crítico.

La plataforma todavía no tiene garantías suficientes para ejecución distribuida: falta threat model enterprise completo, sandbox remoto, identidad fuerte, aprobación humana endurecida, transporte seguro, auditoría robusta, rollback y pruebas adversariales suficientes.

## Decisión

DevPilot continuará como producto **local-first industrial** antes de ampliar autonomía, conectividad remota o ejecución distribuida.

Remote execution real queda bloqueada hasta que exista una ADR posterior, threat model específico, RBAC fuerte, sandbox, auditoría, approval workflow, evaluación de seguridad y criterio explícito de go/no-go.

## Alternativas consideradas

| Alternativa | Resultado | Motivo |
|---|---|---|
| Habilitar remote runner experimental como feature activa | Rechazada | Riesgo crítico sin sandbox, transporte seguro ni threat model completo |
| Permitir remote solo para dry-run | Rechazada por ahora | Aun en dry-run introduce superficie de identidad, red y auditoría |
| Mantener remote como diseño P3 | Aceptada | Preserva aprendizaje y diseño sin riesgo operacional inmediato |

## Consecuencias

- `POST-H-002` debe enfocarse en dashboard local read-only.
- Conectividad remota no puede ser usada como atajo para madurez enterprise.
- Los sprints P0/P1 deben priorizar testing, Policy/MIASI, approval/RBAC, runtime lifecycle y observabilidad.
- Remote queda en Oleada 6 como diseño, no como implementación activa.

## Criterios PASS

```text
remote_runner_enabled=false
remote_execution_used=false
cloud_control_plane_enabled=false
network_used=false en comandos diagnósticos
no_external_apis_used=true
risk SEC-001 referenciado en roadmap
```

## Criterios BLOCK

```text
remote execution enabled sin ADR posterior
runner remoto con credenciales, red o shell
conectores write habilitados por dependencia remota
claim enterprise basado en stub experimental
```

## Riesgos

El riesgo principal es que el roadmap futuro confunda diseño remote con disponibilidad de producto. La mitigación es mantener no-go gates explícitos y validar `industrial-readiness check` antes de cualquier hito que toque remote.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core industrial-readiness check --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m pytest tests	est_post_h_eval_001_f_prioritized_roadmap.py -q
```

## Estado

Aceptada en `POST-H-EVAL-001-F`. Debe revisarse únicamente cuando P0/P1 post-H estén implementados y exista un threat model remoto específico.
