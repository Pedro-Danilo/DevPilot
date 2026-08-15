---
doc_id: "DEVPL-GSDLC-R01-A-REFRESH-PROTOCOL"
title: "DEVPL-GSDLC-R01-A — Source coverage and refresh protocol"
status: "implemented-controlled/pending-windows-validation"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-14"
backlog_id: "DEVPL-GSDLC-R01"
micro_sprint: "DEVPL-GSDLC-R01-A"
source_repo: "repo_DevPilot_Local_342_DEVPL_GSDLC_00_PROGRAM_ACTIVATION_REBASELINE.zip"
source_git_commit: "90d4f4b76168aab1f2e74c86213cf7d4e4831186"
research_basis: "deep-research-report_DEVPL-GSDLC-R01-A-PROMP.md"
---

# Source coverage and refresh protocol

## 1. Unit of cataloging

Cada claim debe poder atribuirse a una combinación inequívoca de `model_family/model_id`, `provider`, `access_route`, `adapter_protocol`, `hosting/deployment region`, `target_region`, `license/terms class`, `capabilities`, `official_source`, `retrieved_at`, `freshness_class` y `evidence_status`.

## 2. Source hierarchy

1. documentación oficial del provider/runtime;
2. repositorio/model card oficial para open weights;
3. mediciones reproducibles DevPilot (R01-C/D);
4. fuente independiente solo para descubrimiento/contraste.

Una fuente independiente nunca reemplaza un hecho contractual, de autenticación, licencia, privacidad o región.

## 3. Freshness classes

| Clase | Claim típico | Edad máxima | Cadencia |
|---|---|---:|---|
| F0-volatile | model IDs, availability, deprecations, pricing | 7 días | semanal |
| F1-route | endpoints, protocols, tool support, regions | 14 días | quincenal |
| F2-contractual | terms, privacy, retention, auth | 30 días | mensual + event-driven |
| F3-license | model card / licencia open-weight | 30 días | mensual + release |
| F4-stable | arquitectura / protocol concepts | 90 días | trimestral |

## 4. Invalidators

Una recomendación deja de ser fresca si cambia cualquiera de: model ID/version, deprecation, endpoint, auth mechanism, region availability, privacy/retention/training term, license, price used by a benchmark, tool/structured-output support, runtime version o provider final de un broker.

## 5. Coverage metrics

`source_freshness_report.json` debe calcular o declarar con evidencia:

- `official_source_ratio`;
- `fresh_claim_ratio`;
- `class_coverage`;
- `route_coverage`;
- `region_resolution`;
- `license_resolution`;
- `unresolved_critical_count`;
- `stale_critical_count`;
- `unsupported_route_count`.

Gate R01-A: `official_source_ratio >= 0.95`, `class_coverage=1.0`, `route_coverage=1.0`, `stale_critical_count=0`, `unsupported_route_count=0`, `S0=0`, `S1=0`.

## 6. Workflow

`discover -> primary source -> split model/provider/route -> capture capabilities/version -> capture license/terms -> capture jurisdiction/region -> assign freshness -> record source/date/hash -> candidate|conditional|unknown -> human review -> publish snapshot -> scheduled/event refresh`.

## 7. Unknown policy

`UNKNOWN` no es fallo de catalogación si está documentado, tiene owner y fase de resolución, y no se convierte en `allowed`. Los unknowns contractuales/regionales son entradas para R01-B; comportamiento local/hardware para R01-C; fitness/cost para R01-D.

## 8. Human verification

Las capturas de fuentes oficiales son suplementarias. Nunca deben exponer API keys, cookies, billing, correo o identificadores personales y nunca sustituyen el source register. Una captura tampoco convierte automáticamente un `unknown` en `verified`.
