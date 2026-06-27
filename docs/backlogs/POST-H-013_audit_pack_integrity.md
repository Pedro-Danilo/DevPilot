---

doc_id: "POST-H-013-BACKLOG"
id: "POST-H-013"
title: "POST-H-013 — Audit pack signing/encryption local opcional"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
optional_crypto: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-013-C"
next_micro_sprint: "POST-H-013-D"
---

# POST-H-013 — Audit pack signing/encryption local opcional

## 1. Objetivo

Endurecer los audit packs locales de DevPilot con **integridad verificable, checksums, manifest robusto, redacción, firma local opcional y cifrado local opcional**, sin introducir dependencias remotas ni claims de compliance certificada.

El objetivo no es crear una PKI enterprise ni cumplimiento legal certificado. El objetivo es que un audit pack local pueda verificarse como evidencia consistente, reproducible, no contaminada con secretos y opcionalmente protegida en reposo.

## 2. Contexto y justificación

DevPilot ya cuenta con módulos de auditoría y release evidence:

```text
src/devpilot_core/auditpack/
src/devpilot_core/release/
src/devpilot_core/compliance/
docs/schemas/audit_pack_manifest.schema.json
outputs/reports/
outputs/traces/
```

Post-H identificó que audit/compliance existen como baseline local, pero no deben confundirse con certificación. También se identificó la necesidad de proteger runtime artifacts, evitar secret leakage y mantener evidencia reproducible.

Problemas a resolver:

```text
- Audit packs iniciales sin política robusta de integridad end-to-end.
- Falta de redaction manifest explícito.
- Falta de firma local opcional verificable.
- Falta de cifrado local opcional controlado.
- Riesgo de incluir outputs sensibles, DB, agent_sessions o secretos.
- Riesgo de sobreclaiming compliance/enterprise.
```

## 3. Alcance

Incluye:

```text
- Audit pack manifest v2.
- Checksums por archivo incluido.
- Redaction report obligatorio.
- Verificación local de integridad.
- Firma local opcional con clave local del operador.
- Cifrado local opcional con passphrase o keyfile local.
- Reglas de exclusión de runtime artifacts sensibles.
- Documentación clara de no-certificación.
```

No incluye:

```text
- Firma remota.
- KMS cloud.
- PKI enterprise.
- Certificación SOC2/ISO real.
- Envío de audit packs a terceros.
- Plugin execution.
- Remote execution.
- Connector write.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/auditpack/
src/devpilot_core/release/
src/devpilot_core/compliance/
src/devpilot_core/security/
src/devpilot_core/policy/secrets.py
src/devpilot_core/observability/export.py        # si POST-H-010 ya existe
docs/schemas/audit_pack_manifest.schema.json
docs/03_security/post_h_security_risk_register.md
docs/04_quality/post_h_test_cost_assessment.md
docs/audits/post_h_eval_001_closure_report.md
docs/backlogs/post_h_prioritized_roadmap.md
.gitignore
```

## 5. Entregables

```text
docs/schemas/audit_pack_manifest_v2.schema.json
docs/schemas/audit_pack_integrity_report.schema.json
.devpilot/auditpack/audit_pack_policy.json
src/devpilot_core/auditpack/manifest_v2.py
src/devpilot_core/auditpack/integrity.py
src/devpilot_core/auditpack/redaction.py
src/devpilot_core/auditpack/crypto.py
src/devpilot_core/auditpack/verify_v2.py
tests/test_post_h_013_audit_pack_integrity.py
tests/test_audit_pack_manifest_v2_schema.py
docs/05_operations/audit_pack_runbook.md
outputs/auditpacks/                              # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o cli_registry cuando exista
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
docs/05_operations/runbook.md
docs/03_security/post_h_security_risk_register.md
```

## 6. Modelo de datos mínimo

### 6.1 Audit pack manifest v2

```json
{
  "schema_version": "2.0",
  "pack_id": "audit-pack-post-h-sample",
  "created_at_utc": "2026-06-23T00:00:00Z",
  "local_first": true,
  "remote_export_used": false,
  "compliance_certification_claimed": false,
  "files": [
    {
      "path": "docs/backlogs/post_h_prioritized_roadmap.md",
      "kind": "source-document",
      "sha256": "...",
      "size_bytes": 12345,
      "redaction_applied": false,
      "included": true
    }
  ],
  "excluded": [
    {
      "path": ".devpilot/devpilot.db",
      "reason": "runtime-state"
    }
  ],
  "integrity": {
    "algorithm": "sha256",
    "manifest_hash": "...",
    "signed": false,
    "encrypted": false
  }
}
```

### 6.2 Integrity report

Debe contener:

```text
pack_id
files_total
files_verified
files_failed
missing_files
hash_mismatches
redaction_passed
secrets_detected
signature_verified opcional
encryption_used opcional
network_used=false
external_api_used=false
compliance_certification_claimed=false
```

## 7. Principios de diseño

```text
1. Evidence integrity before cryptographic complexity.
2. Crypto local opcional, no dependencia obligatoria.
3. No secrets in packs.
4. No compliance certification claim.
5. Reproducible local verification.
6. Redaction report obligatorio.
7. Runtime artifacts excluidos salvo export redactado explícito.
8. Fail closed ante hash mismatch.
```

## 8. Micro-sprints propuestos

### POST-H-013-A — Audit pack manifest v2 y policy

Objetivo: definir manifest v2 y política local de audit packs.

Tareas:

```text
1. Crear audit_pack_manifest_v2.schema.json.
2. Crear audit_pack_integrity_report.schema.json.
3. Crear .devpilot/auditpack/audit_pack_policy.json.
4. Definir include/exclude patterns.
5. Declarar compliance_certification_claimed=false obligatorio.
6. Registrar schemas en schema_catalog.json.
```

Criterios PASS:

```text
PASS si manifest v2 valida contra schema.
PASS si policy excluye outputs, devpilot.db, agent_sessions y secretos.
PASS si compliance_certification_claimed=false.
PASS si remote_export_used=false.
```

Criterios BLOCK:

```text
BLOCK si se permite claim de certificación.
BLOCK si se incluyen secretos o .env.
BLOCK si audit pack requiere red.
```

Validación:

```powershell
python -m pytest tests/test_audit_pack_manifest_v2_schema.py -q
python -m devpilot_core schema validate --schema-id AuditPackManifestV2 --instance outputs/auditpacks/sample_manifest.json --json
```

### POST-H-013-B — Builder v2 con checksums y redaction report

Objetivo: construir audit pack local con integridad y redacción.

Tareas:

```text
1. Implementar manifest_v2.py.
2. Implementar redaction.py usando SecretGuard o patrones compatibles.
3. Calcular sha256 por archivo.
4. Generar redaction_report.
5. Excluir runtime artifacts no permitidos.
6. Agregar CLI audit-pack build-v2 --dry-run/--execute.
```

Criterios PASS:

```text
PASS si build-v2 dry-run no escribe pack.
PASS si build-v2 --execute escribe en outputs/auditpacks.
PASS si todos los archivos incluidos tienen sha256.
PASS si redaction_report existe.
PASS si secrets_detected > 0 genera BLOCK.
```

Criterios BLOCK:

```text
BLOCK si se empaqueta .env.
BLOCK si se empaqueta .devpilot/devpilot.db sin export redactado.
BLOCK si se empaqueta .devpilot/agent_sessions crudo.
```

Validación:

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --json --write-report
python -m pytest tests/test_post_h_013_audit_pack_integrity.py -q
```

### POST-H-013-C — Verifier v2 de integridad local

Objetivo: verificar audit packs con hashes y manifest v2.

Tareas:

```text
1. Implementar verify_v2.py.
2. Validar manifest contra schema.
3. Verificar existencia y sha256 de cada archivo incluido.
4. Detectar archivos extra no declarados.
5. Generar audit_pack_integrity_report.json.
6. Retornar BLOCK ante hash mismatch.
```

Criterios PASS:

```text
PASS si verifier detecta hash mismatch.
PASS si verifier detecta missing file.
PASS si verifier valida schema.
PASS si verifier no requiere red.
```

Criterios BLOCK:

```text
BLOCK si un pack modificado pasa.
BLOCK si missing file solo genera info.
BLOCK si compliance claim no permitido pasa.
```

Validación:

```powershell
python -m devpilot_core audit-pack verify-v2 --pack outputs/auditpacks/<pack>.zip --json
python -m pytest tests/test_post_h_013_audit_pack_integrity.py -q
```

### POST-H-013-D — Firma y cifrado local opcional

Objetivo: permitir protección opcional sin convertirla en dependencia obligatoria.

Tareas:

```text
1. Implementar crypto.py con backend estándar disponible o fallback no-crypto explícito.
2. Soportar signing local opcional si dependencia está disponible.
3. Soportar encryption local opcional si dependencia está disponible.
4. Reportar crypto_available, signed, encrypted, verified.
5. No fallar el hito si crypto opcional no está instalado, salvo que se pida explícitamente.
```

Criterios PASS:

```text
PASS si modo sin crypto sigue funcionando.
PASS si firma/cifrado opcional requiere bandera explícita.
PASS si verify reporta claramente estado crypto.
PASS si no hay llamadas remotas a KMS.
```

Criterios BLOCK:

```text
BLOCK si crypto requiere servicio externo.
BLOCK si claves se guardan en repo.
BLOCK si encryption oculta errores de redacción o secretos.
```

Validación:

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --sign optional --encrypt optional --json
python -m pytest tests/test_post_h_013_audit_pack_integrity.py -q
```

### POST-H-013-E — Quality gate, runbook y disclaimers

Objetivo: integrar integridad de audit packs al proceso de calidad y operación.

Tareas:

```text
1. Agregar subgate audit-pack-integrity al quality gate.
2. Actualizar test contract registry.
3. Crear docs/05_operations/audit_pack_runbook.md.
4. Actualizar runbook principal.
5. Documentar no-certificación compliance/enterprise.
6. Documentar cómo verificar un pack recibido localmente.
```

Criterios PASS:

```text
PASS si quality-gate valida manifest policy y no-go gates.
PASS si runbook explica build/verify/sign/encrypt.
PASS si test-contracts validate pasa.
PASS si docs declaran compliance_certification_claimed=false.
```

Criterios BLOCK:

```text
BLOCK si se declara cumplimiento certificado.
BLOCK si se recomienda subir packs a terceros por defecto.
BLOCK si se omite redaction report.
```

Validación:

```powershell
python -m pytest tests/test_post_h_013_audit_pack_integrity.py tests/test_audit_pack_manifest_v2_schema.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 9. Casos de uso soportados al cierre

```text
- Construir un audit pack local en dry-run.
- Construir un audit pack local real bajo outputs/auditpacks.
- Verificar integridad de un pack.
- Detectar modificaciones por hash mismatch.
- Generar redaction report.
- Firmar/cifrar localmente de forma opcional.
- Probar que no hay claim de compliance certificada.
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Secretos dentro de audit pack | Crítica | SecretGuard/redaction y BLOCK. |
| Falsa certificación compliance | Alta | compliance_certification_claimed=false obligatorio. |
| Dependencia crypto compleja | Media | crypto opcional, fallback claro. |
| Pack no reproducible | Media-alta | manifest v2, sha256 por archivo, verifier. |
| Incluir runtime state crudo | Alta | exclude policy y export redactado si aplica. |

## 11. No-go gates

```text
NO compliance certification claim.
NO remote signing/KMS.
NO secrets.
NO raw agent_sessions.
NO devpilot.db crudo.
NO outputs/traces crudos sin redaction policy.
NO plugin execution.
NO connector write.
```

## 12. Definition of Done del hito

```text
- Manifest v2 y integrity report schemas implementados.
- Audit pack policy creada.
- Builder v2 implementado con checksums y redaction.
- Verifier v2 implementado.
- Firma/cifrado local opcional documentado.
- Quality gate integrado.
- Runbook actualizado.
- Tests focales pasan.
```

## 13. Comandos finales esperados

```powershell
python -m devpilot_core audit-pack build-v2 --dry-run --json --write-report
python -m devpilot_core audit-pack build-v2 --execute --json
python -m devpilot_core audit-pack verify-v2 --pack outputs/auditpacks/<pack>.zip --json
python -m pytest tests/test_post_h_013_audit_pack_integrity.py tests/test_audit_pack_manifest_v2_schema.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```


## 14. Avance de implementación — POST-H-013-A

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- Backlog POST-H-013 elevado a status approved para iniciar implementación.
- Schema `AuditPackManifestV2` registrado para manifest v2 local-first.
- Schema `AuditPackIntegrityReport` registrado para reportes futuros de verificación local.
- Política local `.devpilot/auditpack/audit_pack_policy.json` creada con include/exclude patterns, no-certification claim y no-go gates.
- Fixture versionable de manifest v2 e integrity report para validación determinística sin versionar outputs.
- Test contract registry v1/v2 actualizado para pruebas selectivas del micro-sprint.
```

Artefactos principales:

```text
docs/schemas/audit_pack_manifest_v2.schema.json
docs/schemas/audit_pack_integrity_report.schema.json
.devpilot/auditpack/audit_pack_policy.json
tests/fixtures/audit_pack_manifest_v2_sample.json
tests/fixtures/audit_pack_integrity_report_sample.json
tests/test_audit_pack_manifest_v2_schema.py
docs/audits/post_h_013_a_audit_pack_manifest_v2_policy_report.md
docs/post_h_013_a_manifest.json
```

Criterios PASS cubiertos:

```text
PASS si manifest v2 valida contra schema.
PASS si policy excluye outputs, devpilot.db, agent_sessions y secretos.
PASS si compliance_certification_claimed=false.
PASS si remote_export_used=false.
```

Límites explícitos:

```text
POST-H-013-A no implementa todavía builder v2, verifier v2, redaction report runtime, firma local ni cifrado local.
POST-H-013-A no genera ni versiona outputs/auditpacks.
POST-H-013-A no habilita remote signing, KMS cloud, APIs externas, connector write, plugin execution ni compliance certification claim.
POST-H-013-B implementa el builder v2 con checksums y redaction report bajo outputs/auditpacks; verifier v2, signing y encryption quedan pendientes.
```


## 15. Avance de implementación — POST-H-013-B

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- `AuditPackV2Builder` construye el plan y el pack v2 gobernado por `.devpilot/auditpack/audit_pack_policy.json`.
- `audit-pack build-v2 --dry-run` es el modo por defecto y no escribe ZIP, manifest ni redaction report bajo `outputs/auditpacks`.
- `audit-pack build-v2 --execute` escribe únicamente artefactos generados bajo `outputs/auditpacks`: ZIP, manifest v2 sidecar y redaction report sidecar.
- Cada archivo incluido declara `sha256`, `size_bytes`, `kind`, `included=true` y `redaction_applied`.
- El ZIP embebe `audit-pack-manifest-v2.json` y `redaction_report.json`.
- `SecretGuard` se usa como scanner compatible; ante secreto material detectado se genera BLOCK y no se escribe pack.
- La política excluye `.env`, `.devpilot/devpilot.db`, `.devpilot/agent_sessions/**`, outputs crudos, llaves y carpetas de secretos.
```

Artefactos principales:

```text
src/devpilot_core/auditpack/manifest_v2.py
src/devpilot_core/auditpack/redaction.py
src/devpilot_core/auditpack/__init__.py
src/devpilot_core/cli.py
tests/test_post_h_013_audit_pack_integrity.py
docs/audits/post_h_013_b_builder_v2_report.md
docs/post_h_013_b_manifest.json
docs/05_operations/audit_pack_runbook.md
```

Criterios PASS cubiertos:

```text
PASS si build-v2 dry-run no escribe pack.
PASS si build-v2 --execute escribe en outputs/auditpacks.
PASS si todos los archivos incluidos tienen sha256.
PASS si redaction_report existe.
PASS si secrets_detected > 0 genera BLOCK.
```

Límites explícitos:

```text
POST-H-013-B no implementa verify-v2 de packs recibidos ni detección de tampering posterior; eso queda para POST-H-013-C.
POST-H-013-B no implementa signing ni encryption; eso queda para POST-H-013-D.
POST-H-013-B no integra todavía el subgate final `audit-pack-integrity`; eso queda para POST-H-013-E.
POST-H-013-B no declara compliance certification, no usa red, no usa APIs externas, no usa KMS y no habilita connector write, plugin execution ni remote execution.
```


## 16. Avance de implementación — POST-H-013-C

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- `AuditPackV2Verifier` verifica localmente ZIPs de audit pack v2 generados por `build-v2 --execute`.
- `audit-pack verify-v2 --pack <pack>.zip --json` valida el manifest embebido contra `AuditPackManifestV2`.
- El verificador comprueba el self-hash del manifest, la existencia de cada archivo declarado y el SHA-256 real de cada miembro ZIP.
- El verificador detecta y bloquea archivos extra no declarados, archivos faltantes, hash mismatch, manifest JSON/schema inválido y drift de `compliance_certification_claimed`.
- Se genera `audit_pack_integrity_report.json` bajo `outputs/auditpacks` como evidencia runtime local, sin mutaciones de código fuente.
- El reporte valida contra `AuditPackIntegrityReport` y conserva invariantes `network_used=false`, `external_api_used=false`, `remote_export_used=false` y `compliance_certification_claimed=false`.
```

Artefactos principales:

```text
src/devpilot_core/auditpack/verify_v2.py
src/devpilot_core/auditpack/__init__.py
src/devpilot_core/cli.py
tests/test_post_h_013_audit_pack_integrity.py
docs/audits/post_h_013_c_verifier_v2_report.md
docs/post_h_013_c_manifest.json
docs/05_operations/audit_pack_runbook.md
```

Criterios PASS cubiertos:

```text
PASS si verifier detecta hash mismatch.
PASS si verifier detecta missing file.
PASS si verifier valida schema.
PASS si verifier no requiere red.
```

Criterios BLOCK cubiertos:

```text
BLOCK si un pack modificado pasa.
BLOCK si missing file solo genera info.
BLOCK si compliance claim no permitido pasa.
```

Límites explícitos:

```text
POST-H-013-C no implementa firma ni cifrado local; esos controles quedan para POST-H-013-D.
POST-H-013-C no integra todavía el subgate final `audit-pack-integrity`; eso queda para POST-H-013-E.
POST-H-013-C no habilita remote signing, KMS cloud, APIs externas, connector write, plugin execution, remote execution ni compliance certification claim.
La escritura del integrity report bajo `outputs/auditpacks` es evidencia runtime local y no debe versionarse ni incluirse en ZIPs limpios de entrega.
```
