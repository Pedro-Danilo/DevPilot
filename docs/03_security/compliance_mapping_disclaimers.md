---
doc_id: "POST-H-020-COMPLIANCE-MAPPING-DISCLAIMERS"
title: "Disclaimers — Compliance mapping packs"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
created_by: "POST-H-020-E"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
local_first: true
certification_claimed: false
legal_advice_claimed: false
---

# Disclaimers — Compliance mapping packs

## Declaración obligatoria

Los compliance mapping packs de DevPilot son una herramienta local de mapeo técnico y evidencia de ingeniería. No constituyen certificación compliance, asesoría legal, auditoría externa ni dictamen regulatorio.

## Límites explícitos

```text
certification_claimed=false
legal_advice_claimed=false
external_audit_claimed=false
third_party_submission=false
source_command_values_executed=false
network_used=false
external_api_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Lenguaje permitido

```text
Permitido:
- mapped
- partial
- gap
- not-applicable
- evidence available
- evidence missing
- local technical mapping
- non-certifying report
- engineering readiness signal
```

## Lenguaje prohibido

```text
Prohibido:
- certified compliant
- compliance certified
- legally compliant
- legal advice
- external audit completed
- guaranteed compliance
- regulatory approval
- third-party attestation completed
```

## Interpretación segura

`mapped` significa que un control tiene evidencias declaradas y verificables localmente. No significa que la organización esté certificada.

`partial` significa que existe evidencia incompleta o cobertura parcial. Requiere revisión.

`gap` significa que falta evidencia o que la evidencia no es suficiente. Debe permanecer visible.

`not-applicable` significa que el control se excluye del alcance actual con justificación explícita.

## Requisito de revisión humana

Antes de usar un reporte en contexto contractual, regulatorio, auditoría externa o comunicación ejecutiva, debe existir revisión humana especializada. DevPilot no reemplaza consultores, abogados, auditores ni autoridades certificadoras.

