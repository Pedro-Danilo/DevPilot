---
doc_id: "POST-H-020-COMPLIANCE-MAPPING-RUNBOOK"
title: "Runbook — Compliance mapping packs locales"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
created_by: "POST-H-020-E"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
local_first: true
dry_run: true
certification_claimed: false
legal_advice_claimed: false
---

# Runbook — Compliance mapping packs locales

## 1. Propósito operativo

Este runbook define cómo operar los compliance mapping packs locales de DevPilot. El objetivo es mapear controles, evidencias, políticas, pruebas y documentos contra un baseline interno o referencias externas sin declarar certificación, asesoría legal ni auditoría externa completada.

El operador debe tratar los resultados como evidencia técnica local para revisión de ingeniería. No son una opinión legal, una certificación formal ni una auditoría independiente. Declaración obligatoria: no certificación, no asesoría legal y no auditoría externa.

## 2. Alcance seguro

```text
Incluido:
- Validar mappings locales de controles y evidencias.
- Generar reportes locales de cobertura.
- Revisar gaps explícitos.
- Integrar la señal con quality-gate hardening/industrial.
- Incluir summary no-certificante en AuditPackV2.

Excluido:
- Certificación compliance.
- Asesoría legal.
- Auditoría externa.
- Envío de evidencias a terceros.
- Ejecución de source_command.
- Remediación automática.
- Red, APIs externas, conectores externos, remote execution o plugin execution.
```

## 3. Interpretación de estados

```text
mapped:
  El control tiene evidencias declaradas y localmente disponibles.

partial:
  El control tiene evidencias parciales. Debe revisarse antes de usarlo como señal de readiness.

gap:
  El control no tiene evidencia suficiente o la evidencia declarada no está disponible. Es una brecha explícita, no debe ocultarse.

not-applicable:
  El control no aplica al alcance actual. Debe tener justificación documentada y revisable.
```

Un reporte con gaps puede seguir siendo útil para gestión de riesgo, pero no debe interpretarse como cumplimiento completado.

## 4. Procedimiento de verificación

Desde la raíz del repo:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core schema validate --schema-id ComplianceControlMapping --instance .devpilot/compliance/control_mappings.json --json
python -m devpilot_core schema validate --schema-id ComplianceEvidenceMapping --instance .devpilot/compliance/evidence_mappings.json --json
python -m devpilot_core compliance mapping report --json --write-report
python -m devpilot_core schema validate --schema-id ComplianceMappingReport --instance outputs/reports/compliance_mapping_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
```

Validación documental y contractual:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core cli-registry guard --json
```

## 5. Criterios PASS

```text
PASS si certification_claimed=false.
PASS si legal_advice_claimed=false.
PASS si disclaimer_present=true.
PASS si los controles críticos no tienen evidence gaps.
PASS si missing evidence se reporta como finding explícito.
PASS si source_command_values_executed=false.
PASS si network_used=false y external_api_used=false.
PASS si quality-gate hardening incluye compliance-mapping-pack.
```

## 6. Criterios BLOCK

```text
BLOCK si un reporte afirma certificación o cumplimiento certificado.
BLOCK si un documento ofrece asesoría legal.
BLOCK si se sugiere auditoría externa completada.
BLOCK si se ocultan gaps o evidencias faltantes.
BLOCK si se ejecutan source_command values.
BLOCK si se envían evidencias a terceros.
BLOCK si se usa red, API externa, connector write, remote execution o plugin execution.
```

## 7. Manejo de gaps

Cada gap debe conservarse como finding visible hasta que exista evidencia local suficiente o una justificación `not-applicable`. No se deben borrar gaps para forzar un reporte verde.

La remediación recomendada es:

```text
1. Identificar control_id y evidence_id afectados.
2. Revisar source_paths declarados.
3. Confirmar si el control es mapped, partial, gap o not-applicable.
4. Agregar evidencia local verificable o justificación explícita.
5. Regenerar el reporte.
6. Ejecutar quality-gate hardening.
```

## 8. Salidas esperadas

Los reportes runtime se generan bajo `outputs/reports/` y no deben incluirse en ZIPs entregables:

```text
outputs/reports/compliance_mapping_report.json
outputs/reports/compliance_mapping_report.md
```

AuditPackV2 incluye un bloque `compliance_mapping` como summary no-certificante. Ese bloque no exporta evidencias a terceros ni prueba cumplimiento legal.

## 9. Responsabilidad del operador

El operador debe revisar lenguaje, evidencias y gaps antes de compartir reportes. Cualquier uso regulatorio, contractual o legal requiere revisión de especialistas externos a DevPilot.
