---
title: Manifiesto MIPSoftware
doc_id: MIPS-DOC-001-MANIFEST
doc_type: manifest
version: 0.2.0
status: reviewed
owner: AI_agents / MIPSoftware
audience:
- equipo técnico
- arquitectos
- desarrolladores
- revisores
scope: software-engineering-model
created: '2026-05-31'
updated: '2026-05-31'
related_documents:
- README.md
- adrs/ADR-0001-docs-as-code.md
- adrs/ADR-0005-miasi-como-extension-inteligente.md
---

# Manifiesto MIPSoftware

## 1. Declaración central

**MIPSoftware — Modelo de Ingeniería Profesional de Software** existe para evitar que el desarrollo de software del emprendimiento dependa de improvisación, intuición aislada o acumulación accidental de código. Todo proyecto debe nacer con propósito, alcance, arquitectura, requerimientos, criterios de calidad, seguridad, pruebas, operación, trazabilidad y estrategia de evolución.

El código es una parte del producto, no el producto completo. MIPSoftware define el sistema de trabajo que permite construir software profesional, mantenible, seguro y operable.

## 2. Principios rectores

### 2.1 Software engineering first

Todo proyecto debe abordarse primero como un problema de ingeniería de software. Antes de implementar, deben existir artefactos mínimos de producto, requerimientos, arquitectura, riesgos y calidad.

### 2.2 Documentación como activo

La documentación no es decorativa. Es parte del producto, del proceso de calidad, de la memoria técnica y de la capacidad de escalar el trabajo.

### 2.3 Arquitectura antes de implementación

Ningún proyecto debe iniciar implementación significativa sin una arquitectura mínima: contexto, contenedores, componentes principales, decisiones, restricciones y atributos de calidad.

### 2.4 Seguridad desde el diseño

La seguridad no se agrega al final. Todo proyecto debe considerar amenazas, secretos, datos sensibles, permisos, dependencias, supply chain y controles desde las primeras fases.

### 2.5 Calidad verificable

La calidad debe expresarse en criterios verificables: tests, métricas, gates, revisiones, cobertura, performance, seguridad, mantenibilidad y observabilidad.

### 2.6 Trazabilidad

Todo elemento importante debe poder trazarse:

```text
necesidad de negocio
  → requerimiento
  → diseño
  → implementación
  → prueba
  → release
  → operación
  → mantenimiento
```

### 2.7 Automatización progresiva

La automatización debe introducirse de forma incremental: primero documentación y controles manuales; luego validadores; después comandos; finalmente pipelines.

### 2.8 DevOps/SRE-ready

Todo software destinado a producción debe diseñarse para despliegue, monitoreo, incidentes, backup, restore, rollback y operación.

### 2.9 AI-ready mediante MIASI

Cuando un sistema incorpora IA o agentes, MIASI se activa como extensión obligatoria. MIPSoftware gobierna el ciclo general; MIASI gobierna la capa inteligente.

### 2.10 Independencia razonable de proveedor

El modelo no debe depender de un stack único, nube única, proveedor LLM único, framework único o base de datos única. Las decisiones tecnológicas deben justificarse por contexto.

### 2.11 Producción como objetivo, no como accidente

Un sistema no llega a producción por estar terminado funcionalmente. Llega a producción cuando cumple readiness técnico, seguridad, operación, calidad, observabilidad y soporte.

## 3. Reglas no negociables

| Regla | Descripción | Bloquea avance si se incumple |
|---|---|---:|
| No hay código serio sin requerimientos mínimos. | Debe existir necesidad, alcance y aceptación. | Sí |
| No hay release sin pruebas. | Todo cambio debe pasar gates definidos. | Sí |
| No hay producción sin observabilidad. | Logs, métricas, trazas o eventos mínimos. | Sí |
| No hay secretos en código. | Secretos deben gestionarse fuera del repositorio. | Sí |
| No hay datos sensibles sin política. | Debe existir clasificación, retención y protección. | Sí |
| No hay arquitectura invisible. | Toda decisión relevante debe documentarse. | Sí |
| No hay IA sin MIASI. | Todo sistema inteligente debe aplicar la extensión. | Sí |
| No hay despliegue sin rollback. | Debe existir plan de reversión o contención. | Sí |

## 4. Alcance

MIPSoftware aplica a:

- aplicaciones web;
- APIs;
- backends;
- frontends;
- aplicaciones móviles;
- CLIs;
- automatizaciones;
- plataformas internas;
- sistemas con agentes IA;
- sistemas transaccionales;
- productos propios del emprendimiento;
- proyectos para clientes.

## 5. Límites

MIPSoftware no pretende reemplazar:

- gestión contractual;
- dirección financiera;
- cumplimiento legal formal;
- auditorías regulatorias externas;
- certificaciones ISO;
- criterio profesional especializado por industria.

El modelo sirve como estándar operativo interno y como base para futuras auditorías o certificaciones.

## 6. Relación con MIASI

MIASI es una extensión especializada ya aprobada para sistemas inteligentes/agénticos. Su aplicación es obligatoria cuando haya:

- LLMs;
- agentes;
- RAG;
- memoria;
- tool calling;
- decisiones asistidas por IA;
- automatización inteligente;
- interacción con modelos locales o externos;
- generación automática de contenido crítico.

## 7. Criterio de éxito de MIPSoftware

MIPSoftware será exitoso si permite:

- iniciar proyectos con claridad;
- reducir retrabajo;
- tomar decisiones técnicas justificadas;
- construir software auditable;
- mejorar calidad y seguridad;
- preparar releases confiables;
- operar sistemas con evidencia;
- integrar IA sin improvisación;
- convertir conocimiento técnico en activo reutilizable.

## 8. Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1.0 | 2026-05-31 | Creación inicial del manifiesto. |
