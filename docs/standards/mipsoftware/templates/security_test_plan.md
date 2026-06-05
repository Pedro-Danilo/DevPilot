---
title: Security Test Plan
doc_id: MIPS-TPL-SEC-005
doc_type: template
version: 0.1.0
status: draft
owner: AI_agents / MIPSoftware
scope: security-privacy-compliance
created: '2026-05-31'
updated: '2026-05-31'
---

# Security Test Plan

## Propósito

Planificar pruebas de seguridad manuales y automatizadas por riesgo.

## Secciones obligatorias

1. Alcance.
2. Supuestos.
3. Entornos.
4. Casos authn/authz.
5. Casos input validation.
6. Casos output encoding.
7. Casos sesiones.
8. Casos datos personales.
9. Casos API/webhooks.
10. Casos CI/CD/secrets.
11. Casos MIASI si aplica.
12. Evidencia esperada.

## Ejemplo de casos

| ID | Riesgo | Prueba | Resultado esperado | Evidencia |
|---|---|---|---|---|
| ST-001 | IDOR | usuario A intenta acceder recurso B | 403/404 seguro | test report |
| ST-002 | XSS | payload HTML/script en formulario | salida codificada | screenshot/test |
| ST-003 | Secret leakage | ejecutar pipeline con secret scan | no secretos | CI artifact |
| ST-004 | Tool misuse IA | agente intenta borrar archivo sin approval | blocked | MIASI trace |

## Criterios de rechazo

- No cubre rutas críticas.
- No cubre autorización.
- No cubre datos sensibles.
- No cubre agentes si existen.

