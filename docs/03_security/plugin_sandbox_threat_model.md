---
doc_id: "POST-H-019-PLUGIN-SANDBOX-THREAT-MODEL"
title: "POST-H-019 — Plugin sandbox threat model"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
preliminary: true
---

# POST-H-019 — Plugin sandbox threat model

## Alcance

Este documento define el threat model inicial para el futuro ecosistema de plugins de DevPilot. El alcance de POST-H-019-A es exclusivamente documental y verificable: metadata-only, validator-only y design-only. No se implementa ejecución de plugins, carga dinámica, marketplace, instalación de dependencias, red, APIs externas, `subprocess`, `importlib` ni remote execution.

## Activos protegidos

```text
- Código fuente local del workspace.
- Secretos presentes o referenciables por el operador, shell, entorno, .env y credenciales locales.
- Repositorio `.devpilot/`, policies, manifests, test contracts y registros de plugins.
- Outputs de evidencia, trazas y reportes.
- Frontera PolicyEngine / Approval / RBAC / MIASI.
- Integridad de la instalación local y de las dependencias.
```

## Boundary de seguridad

```text
plugin_execution_allowed=false
dynamic_import_allowed=false
subprocess_allowed=false
network_allowed=false
external_api_allowed=false
filesystem_write_allowed=false
pip_install_allowed=false
marketplace_enabled=false
remote_execution_allowed=false
metadata_only=true
validator_only=true
```

Un manifest válido no concede permiso de ejecución. Un plugin registrado es metadata gobernada, no código autorizado.

## Amenazas principales

| ID | Amenaza | Riesgo | Mitigación inicial POST-H-019-A |
|---|---|---:|---|
| PLG-T01 | Arbitrary code execution desde plugin malicioso | Crítico | No execution, no import dinámico, no subprocess. |
| PLG-T02 | Dependency confusion o typosquatting vía instalación automática | Alto | No `pip install`, no marketplace, no descarga remota. |
| PLG-T03 | Secret exfiltration por plugin que lee `.env`, variables o tokens | Crítico | Metadata-only, no filesystem reads arbitrarios, future SecretGuard binding. |
| PLG-T04 | Path traversal en manifest o entrypoint | Alto | Entrypoints metadata/disabled y validación estática futura. |
| PLG-T05 | Persistencia local por escritura de archivos, hooks o startup entries | Alto | filesystem_write_allowed=false y no ejecución. |
| PLG-T06 | Network abuse, callbacks o beaconing | Alto | network_allowed=false y no external APIs. |
| PLG-T07 | Supply-chain attack por plugin empaquetado con código oculto | Alto | No carga de paquetes, separación manifest vs executable state. |
| PLG-T08 | Privilege escalation vía Policy/Approval/RBAC bypass | Alto | Future binding obligatorio antes de cualquier ejecución. |
| PLG-T09 | Sandbox escape por subprocess, shell o importlib | Crítico | subprocess_allowed=false, dynamic_import_allowed=false. |
| PLG-T10 | Deserialización insegura o parsing de manifests con efectos colaterales | Alto | JSON metadata-only, no eval/exec/yaml loaders peligrosos. |
| PLG-T11 | Confundir dry-run con instalación real | Medio-alto | Reportes deben separar declared, validated, dry-run y executable. |
| PLG-T12 | Sobredeclarar soporte productivo de plugins | Medio-alto | Estado implemented-initial y no-go gates documentados. |
| PLG-T13 | Escritura destructiva o mutación de workspace | Alto | source_mutations_performed=false y no filesystem write. |
| PLG-T14 | Inyección de tool/plugin mediante nombres, descripciones o manifests | Alto | Validación estática y future policy rules/MIASI allowlist. |
| PLG-T15 | Fuga de datos en reportes de validación | Medio-alto | Redaction y evidencia mínima en futuros reportes. |
```

## No-go gates

```text
NO-GO si plugin_execution_allowed=true.
NO-GO si dynamic_import_allowed=true.
NO-GO si subprocess_allowed=true.
NO-GO si network_allowed=true o external_api_allowed=true.
NO-GO si filesystem_write_allowed=true por defecto.
NO-GO si se instala una dependencia externa.
NO-GO si un manifest se interpreta como permiso de ejecución.
NO-GO si no existe ADR futura aprobada para cualquier ejecución real.
```

## Future ADR requirements

Cualquier propuesta futura de ejecución de plugins debe crear una ADR nueva y demostrar, antes de habilitar código ejecutable, como mínimo:

```text
- Threat model ampliado y aprobado.
- Sandbox técnico con aislamiento verificable.
- Permission model deny-by-default.
- Firma/attestation local o estrategia equivalente.
- PolicyEngine + ApprovalPolicyChecker + RBAC binding.
- Redaction/SecretGuard/PathGuard/CostGuard aplicados.
- Evals adversariales y test contracts.
- Observabilidad, rollback y kill-switch.
- Quality gate plugin-sandbox passing.
```

## Estado

POST-H-019-A es `implemented-initial`. Reduce ambigüedad arquitectónica y establece límites no ejecutables; no convierte a DevPilot en host productivo de plugins ejecutables.
