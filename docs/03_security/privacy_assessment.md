---
title: "Privacy Assessment — DevPilot Local"
doc_id: "DEVPL-SEC-002"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "SPRINT-PRECODE-04"
updated: "2026-06-05"
approval: "approved_by_owner_direction"
source_baseline: "00_product approved + 01_requirements approved + 02_architecture approved"
change_policy: "controlled_changes_allowed_until_precode_baseline"
---

# Privacy Assessment — DevPilot Local

## 1. Propósito

Este documento evalúa los datos tratados por **DevPilot Local**, sus riesgos de privacidad, políticas de minimización, retención, redacción, uso de APIs externas y tratamiento de información sensible. Su finalidad es impedir que una plataforma agent-assisted SDLC exponga código, documentos, secretos, trazas, decisiones de arquitectura o datos personales sin controles explícitos.

DevPilot Local será **local-first híbrido**: debe funcionar localmente sin servicios externos obligatorios, pero podrá usar modelos locales o APIs externas cuando mejoren la calidad, siempre bajo consentimiento, control de costos, redacción, evaluación y política de datos.

## 2. Alcance de privacidad

| Área | Incluida | Observación |
|---|---:|---|
| Documentos pre-code | Sí | Producto, requerimientos, arquitectura, seguridad, operación. |
| Repositorios locales | Sí | MVP+ y post-MVP. |
| Código fuente | Sí | Se considera dato sensible del proyecto. |
| Git metadata | Sí | Ramas, commits, diffs, autores, mensajes. |
| Reportes | Sí | Pueden contener hallazgos sensibles. |
| Trazas JSONL | Sí | Deben minimizar y redactar datos. |
| SQLite local futura | Sí | Estado operativo y resultados. |
| Secretos `.env` | Sí | Tratamiento crítico. |
| APIs externas LLM | Sí | No obligatorias; requieren policy. |
| Datos personales de terceros | No deseados en MVP | Si aparecen, activar clasificación y minimización. |

## 3. Clasificación de datos

| Tipo de dato | Ejemplo | Sensibilidad | Política inicial |
|---|---|---|---|
| Documentos de proyecto | `product_vision.md`, ADRs | Media/Alta | Versionados, revisados, no públicos por defecto |
| Código fuente | `src/`, tests | Alta | Local, no enviar a APIs sin consentimiento |
| Configuración | `.env.example`, settings | Media | Placeholders, sin secretos |
| Secretos | API keys, tokens | Crítica | No versionar, no loggear, redactar |
| Git metadata | commits, diffs | Media/Alta | Local, reportes redactados |
| Reportes | readiness, gates | Media | Revisar antes de compartir |
| Trazas | JSONL de acciones | Alta | Redacción y minimización |
| Estado SQLite | workspaces, gates | Alta | Local, backup y permisos |
| Prompts | instrucciones y contexto | Alta | No incluir secretos; separar datos/instrucciones |
| Respuestas LLM | sugerencias, análisis | Media/Alta | No aplicar sin validación |
| Datos personales | nombres, emails, paths de usuario | Alta | Minimización y redacción cuando aplique |

## 4. Principios de privacidad

| Principio | Aplicación en DevPilot |
|---|---|
| Local-first | Datos permanecen localmente por defecto. |
| Data minimization | Solo se procesa lo necesario para el gate o agente. |
| Purpose limitation | Los datos se usan para ingeniería del proyecto, no para otros fines. |
| Consentimiento explícito | APIs externas requieren autorización y budget. |
| Redacción | Secretos y datos sensibles se ocultan en salidas. |
| Trazabilidad | Toda salida sensible debe tener origen y control. |
| Retención controlada | Trazas y reportes deben tener política de limpieza. |
| Separación | Estándares, proyecto, reportes y trazas deben distinguirse. |
| No training by default | No enviar datos a proveedores para entrenamiento sin política explícita. |

## 5. Inventario de datos por fase

| Fase | Datos tratados | Riesgo | Control |
|---|---|---|---|
| MVP | Markdown, JSON, checklists, reportes | Exposición de decisiones internas | Local-only, revisión |
| MVP | Prompts para agentes documentales | Prompt injection / datos sensibles | Redacción, no secrets |
| MVP | Resultados de validadores | Falsa confianza | Evidencia y trazabilidad |
| MVP+ | Git status, diffs, patches | Exposición de código | Local-first, read-only inicial |
| MVP+ | Entorno virtual | Paths, paquetes, versiones | Redacción de rutas sensibles |
| MVP+ | SQLite local | Estado y hallazgos | Permisos, backup |
| MVP+ | APIs LLM opcionales | Envío de código/docs | Consent, ModelAdapter, CostGuard |
| Post-MVP | Desktop/Web | Sesiones, roles, dashboards | AuthN/AuthZ y ASVS |
| Post-MVP | Multi-workspace | Cruce de datos entre proyectos | Aislamiento por workspace |

## 6. Uso de APIs externas y modelos

Las APIs externas no están prohibidas, pero tampoco son requisito. El uso de modelos externos debe cumplir:

1. API key configurada fuera del código.
2. Consentimiento explícito por workspace o ejecución.
3. Presupuesto definido.
4. Redacción previa de secretos.
5. Selección de proveedor mediante ModelAdapter.
6. Registro de costo estimado/real.
7. Trazabilidad de qué datos se enviaron, de forma resumida y sin revelar secretos.
8. Posibilidad de usar alternativa local/mock.

| Ruta | Privacidad | Regla |
|---|---|---|
| Mock/no LLM | Máxima | Default para tests y gates determinísticos |
| Modelo local | Alta | Permitido si datos no salen del equipo |
| API externa | Variable | Requiere policy, budget y consentimiento |
| Cloud workspace futuro | Mayor riesgo | Requiere diseño específico de privacidad |

## 7. Datos que no deben enviarse a LLM externo sin aprobación

- secretos o tokens;
- `.env` real;
- claves privadas;
- credenciales de repos;
- código propietario completo;
- archivos con datos personales;
- configuraciones de producción;
- logs con datos sensibles;
- trazas completas;
- documentos contractuales o confidenciales;
- dumps de base de datos.

## 8. Retención y eliminación

| Artefacto | Retención inicial | Eliminación |
|---|---|---|
| Documentos pre-code | Permanente mientras el proyecto exista | Manual/versionada |
| Reportes de gates | Mantener últimos N por workspace | Política futura |
| Trazas JSONL | Rotación futura | Purge por workspace |
| SQLite | Persistente local | Backup + purge |
| Prompts/respuestas LLM | No persistir completos por defecto | Guardar resumen seguro |
| Approval requests | Mantener por auditoría | Retención configurable |
| Hallazgos de seguridad | Mantener hasta cierre | Archivar con evidencia |
| Cost events | Mantener para control | Resumen mensual futuro |

## 9. Evaluación de riesgos de privacidad

| ID | Riesgo | Impacto | Prob. | Nivel | Mitigación |
|---|---|---:|---:|---:|---|
| P-001 | Código enviado a API externa sin consentimiento | Alto | Media | Alto | ModelAdapter + consentimiento |
| P-002 | Secretos en logs/reportes | Crítico | Media | Crítico | SecretGuard + redacción |
| P-003 | Trazas demasiado detalladas | Alto | Media | Alto | Minimización y clasificación |
| P-004 | Mezcla de datos entre workspaces | Alto | Baja | Medio | Workspace isolation |
| P-005 | Reportes compartidos con datos sensibles | Medio | Media | Medio | Revisión previa |
| P-006 | Retención indefinida de prompts | Alto | Media | Alto | No persistir prompts completos |
| P-007 | Datos personales en Git metadata | Medio | Media | Medio | Redacción parcial |
| P-008 | Base SQLite expuesta | Alto | Baja | Medio | Permisos y ubicación local |
| P-009 | Uso de proveedor LLM con políticas no revisadas | Alto | Media | Alto | ProviderPolicy |
| P-010 | RAG/memoria conserva información sensible | Alto | Media futura | Alto | Retention + purge |

## 10. Política de redacción

Los reportes, trazas y salidas deben redactar:

| Patrón | Ejemplo redactado |
|---|---|
| API keys | `sk-...REDACTED` |
| Tokens JWT | `eyJ...REDACTED` |
| Passwords | `PASSWORD=***REDACTED***` |
| Connection strings | `postgres://...REDACTED` |
| Paths sensibles | `C:\Users\<USER>\...` |
| Emails | `p***@domain.com` cuando aplique |
| Nombres personales | Minimizar si no son necesarios |
| Diffs sensibles | Resumir sin exponer secreto |

## 11. Privacy gates

| Gate | Criterio PASS | Criterio BLOCK |
|---|---|---|
| Data classification gate | Datos clasificados por sensibilidad | Datos sensibles sin clasificación |
| Secret gate | No hay secretos visibles | Secreto sin redacción |
| External API gate | Hay consentimiento, budget y provider policy | Envío externo no autorizado |
| Trace gate | Trazas minimizadas | Trazas con datos sensibles |
| Workspace gate | Datos aislados por workspace | Mezcla de proyectos |
| Retention gate | Política mínima definida | Persistencia indefinida sin justificación |
| Report sharing gate | Reporte revisado | Reporte con datos confidenciales |

## 12. Relación con threat model

Este documento complementa `security_threat_model.md`. Seguridad responde a “qué puede salir mal y cómo se controla”. Privacidad responde a “qué datos se procesan, quién los ve, dónde quedan y bajo qué condiciones pueden salir del entorno local”.

## 13. Relación con MIASI

MIASI se activa porque DevPilot usará agentes y modelos. Por tanto:

- todo agente debe tener límites de datos;
- toda tool debe declarar datos que lee/escribe;
- toda evaluación debe evitar exponer secretos;
- toda memoria/RAG futura debe tener política de retención;
- toda llamada a modelo externo debe quedar controlada por ModelAdapter, CostGuard y SecretGuard;
- toda acción crítica requiere Human Approval.

## 14. Estado del documento

Este documento queda en `reviewed`. Puede promoverse a `approved` cuando:

- el owner acepte la política de datos;
- `security_threat_model.md` quede alineado;
- `06_miasi` concrete data handling de agentes;
- se definan pruebas mínimas de redacción y secret scanning en `04_quality`.
