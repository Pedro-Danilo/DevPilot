---
title: "Roadmap de supply chain, provenance y firma de artefactos MIASI"
version: "1.0.0"
status: "approved"
owner: "AI_agents"
scope: "engineering-model/reference"
updated: "2026-05-31"
doc_type: "reference"
---
# Roadmap de supply chain, provenance y firma de artefactos MIASI

## 1. Propósito

Extender los controles SAST/SBOM de AI_agents hacia un modelo progresivo de cadena de suministro para producción.

## 2. Niveles

| Nivel | Objetivo | Controles |
|---|---|---|
| SC-0 | Inventario educativo local. | Dependency inventory, SBOM local. |
| SC-1 | Reproducibilidad básica. | Pins, lock files, CI tests. |
| SC-2 | Vulnerability awareness. | SAST/SCA offline + opcional online. |
| SC-3 | Provenance básica. | Build metadata, hashes, artifacts. |
| SC-4 | Firma de artefactos. | Signing, verification, release gates. |
| SC-5 | Attestations y SLSA. | Provenance attestations, protected builders. |

## 3. Artefactos requeridos

| Artefacto | Desde | Ejemplo |
|---|---|---|
| SBOM | SC-0 | CycloneDX JSON. |
| Dependency inventory | SC-0 | `outputs/security/*dependency_inventory.json` |
| Build metadata | SC-3 | Commit, runner, hash, timestamp. |
| Artifact hash | SC-3 | SHA256. |
| Signature | SC-4 | Firma local o proveedor. |
| Attestation | SC-5 | SLSA provenance. |

## 4. Relación con AI_agents

- LAB-AI-076 cubre SAST/SBOM educativo.
- LAB-AI-079 cubre CI remoto sandbox.
- LAB-AI-080 consolida readiness local-first.
- La producción industrial requiere pasar de evidencia local a provenance verificable.

## 5. Criterios de bloqueo

- No liberar artefactos sin inventario de dependencias.
- No liberar versión controlada sin hashes.
- No promover a producción industrial sin plan de provenance.
