---
doc_id: "POST-H-023-SECURE-TRANSPORT-KEY-LIFECYCLE"
title: "Secure transport key/certificate lifecycle design"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-023-C"
implementation_status: "implemented-initial"
decision_status: "design-only"
lifecycle_status: "design-only-no-material"
transport_implemented: false
network_allowed: false
certificates_generated: false
secrets_required: false
secrets_stored: false
raw_secret_storage_allowed: false
private_key_material_present: false
remote_execution_enabled: false
---

# Secure Transport Key/Certificate Lifecycle Design

## 1. Propósito

POST-H-023-C define el lifecycle futuro de llaves, certificados, trust anchors y credenciales de transporte. El alcance es **design-only**: no genera certificados, no genera llaves privadas, no crea CA, no requiere secretos, no lee secretos, no escribe secretos y no habilita transporte.

Regla operativa:

```text
key lifecycle design != key generation
certificate lifecycle design != certificate creation
secret handling design != secret storage
transport lifecycle design != network allowed
```

## 2. Estado Actual

```text
transport_implemented=false
secure_transport_implemented=false
network_allowed=false
network_used=false
sockets_opened=false
certificates_generated=false
certificate_authority_created=false
private_key_material_present=false
raw_secret_storage_allowed=false
secrets_required=false
secrets_stored=false
secrets_read=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 3. Lifecycle Futuro Requerido

| Fase | Objetivo | Estado actual |
|---|---|---|
| Generation design | Definir prerrequisitos para generación futura de material criptográfico. | Diseño solamente |
| Storage design | Definir límites de almacenamiento y prohibir secretos raw en repo, logs y DB local. | Diseño solamente |
| Distribution design | Definir distribución futura vinculada a identidad, PolicyEngine y Approval. | Diseño solamente |
| Rotation design | Exigir validez acotada, overlap window, rollback y test de rotación. | Diseño solamente |
| Revocation design | Exigir revocation registry, kill-switch y fail-closed ante credenciales revocadas. | Diseño solamente |

## 4. Política de Almacenamiento

```text
raw_secret_storage_allowed=false
repo_storage_allowed=false
runtime_db_storage_allowed=false
logs_raw_secret_allowed=false
```

Una implementación futura debe usar referencias, fingerprints o identificadores de secreto, nunca valores raw en documentación, logs, reportes, audit packs ni base local.

## 5. Redaction/Audit

Requisitos mínimos:

```text
- Reportes solo pueden contener referencias, fingerprints o hashes.
- Llaves privadas, tokens, CA secrets y cuerpos completos de certificados no deben aparecer.
- Eventos deben vincular actor, role, approval_id y PolicyEngine decision.
- Rotación y revocación deben auditarse sin exponer material.
- Fallos deben registrarse como metadata, no como valores sensibles.
```

## 6. Criterios PASS

```text
lifecycle_status=design-only-no-material
certificates_generated=false
private_key_material_present=false
raw_secret_storage_allowed=false
secrets_stored=false
secrets_read=false
network_used=false
remote_execution_enabled=false
```

## 7. Criterios BLOCK

```text
Se generan certificados reales.
Se genera o almacena llave privada.
Se crea CA real.
Se guarda secreto raw en repo, logs, outputs, audit packs o DB local.
Se lee .env o secret store real.
Se abre socket/red.
Se habilita remote execution.
```

## 8. Fuentes Estructuradas

```text
docs/schemas/secure_transport_key_lifecycle.schema.json
.devpilot/remote/secure_transport_key_lifecycle.json
docs/post_h_023_c_manifest.json
```

## 9. Límites

Esta es una primera versión de diseño. No sustituye un modelo productivo de secrets management, KMS/HSM, CA interna, mTLS real, token binding real, rotation engine ni revocation service. Esos elementos requieren ADR de enablement, controles previos y quality gate posterior.
