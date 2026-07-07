---
title: "Cuestionario industrial para Onboarding Report de DevPilot"
doc_id: "DEVPL-ONBOARDING-QUESTIONNAIRE-INDUSTRIAL-V1"
status: "draft"
version: "1.0.0"
owner: "Ordonez"
created: "2026-07-03"
scope: "DevPilot Local onboarding, reverse engineering, operacion, arquitectura y continuidad"
---

# Cuestionario industrial para Onboarding Report de DevPilot

## 1. Proposito del documento

Este documento define la totalidad de preguntas recomendadas para construir un
Onboarding Report exhaustivo, detallado y profundo de DevPilot Local.

El objetivo es que una persona nueva, especialmente un arquitecto, desarrollador
senior, operador tecnico o auditor de ingenieria, pueda entender:

- que es DevPilot;
- para que sirve;
- como esta construido;
- que esta implementado realmente;
- que esta solo en estado inicial, de diseno o planificado;
- como se opera localmente;
- como se verifica;
- que riesgos y limites existen;
- como continuar el desarrollo de forma industrial.

El cuestionario esta disenado para responderse paulatinamente en varios prompts.
Cada bloque genera una parte del informe final. Al compilar todas las respuestas,
el resultado deberia ser un onboarding report de nivel industrial.

## 2. Contrato general de cada respuesta

Cuando aplique, cada respuesta debe incluir evidencia concreta. No basta con una
explicacion narrativa.

Cada respuesta debe incluir:

```text
- Resumen ejecutivo.
- Explicacion tecnica.
- Explicacion en lenguaje no especializado.
- Estado de madurez.
- Evidencia documental.
- Evidencia de codigo.
- Evidencia de schemas, manifests o reportes.
- Comandos CLI relacionados.
- Tests relacionados.
- Riesgos y limitaciones.
- Gaps pendientes.
- Recomendaciones o siguientes pasos.
```

Cuando la pregunta trate una capacidad concreta, usar esta clasificacion:

```text
- production-ready-local
- implemented
- implemented-initial
- partially implemented
- design-only
- read-only
- dry-run
- preview
- stub
- planned
- deprecated
- blocked
```

Cuando la pregunta trate claims del producto, distinguir explicitamente:

```text
- claim permitido;
- claim prohibido;
- claim condicionado a evidencia;
- claim que requiere ADR futura;
- claim fuera de alcance.
```

Cuando la pregunta trate evidencia, incluir rutas concretas:

```text
- archivo fuente;
- documento;
- schema;
- manifest;
- reporte;
- test;
- comando de verificacion;
- salida esperada.
```

## 3. Sugerencia de ejecucion por prompts

Para evitar respuestas superficiales y reducir riesgo de perdida de contexto,
se recomienda hacer entre 8 y 12 preguntas por prompt. Los bloques de mayor
densidad tecnica pueden dividirse en subprompts de 5 a 8 preguntas.

Orden sugerido:

| Prompt | Preguntas | Tema | Cantidad sugerida |
|---:|---|---|---:|
| 1 | 1-10 | Identidad de producto y vision | 10 |
| 2 | 11-22 | Estado real, claims y madurez ejecutiva | 12 |
| 3 | 23-36 | Arquitectura real, C4 y divergencias | 14 |
| 4 | 37-48 | DDD, bounded contexts y dominios | 12 |
| 5 | 49-62 | Runtime CLI/ApplicationService/core | 14 |
| 6 | 63-78 | Workspace, onboarding y proyecto nuevo | 16 |
| 7 | 79-96 | Capacidades CLI/API/UI | 18 |
| 8 | 97-114 | Schemas, validators, evidence y manifests | 18 |
| 9 | 115-132 | MIASI, agentes, policy engine, approvals | 18 |
| 10 | 133-150 | Seguridad, no-go gates, threat model | 18 |
| 11 | 151-168 | Testing, TCR, quality gates y test cost | 18 |
| 12 | 169-184 | Observabilidad, runtime state y operacion | 16 |
| 13 | 185-200 | Release, reproducibilidad y distribucion | 16 |
| 14 | 201-216 | UI/API local y experiencia de operador | 16 |
| 15 | 217-232 | Gap analysis y roadmap futuro | 16 |
| 16 | 233-248 | Caso piloto y guia operacional | 16 |
| 17 | 249-260 | Sintesis ejecutiva y compilacion final | 12 |

Regla practica:

```text
- Para discovery inicial: 8-10 preguntas por prompt.
- Para arquitectura profunda: 6-8 preguntas por prompt.
- Para matrices y tablas: 4-6 preguntas por prompt.
- Para guia de operador: 8-12 preguntas por prompt.
- Para compilacion final: pedir una version integrada por capitulos.
```

## 4. Bloque A - Identidad del producto

### Pregunta 1

Analiza el repositorio vigente y explica cual es el proposito de negocio de DevPilot Local.

La respuesta debe incluir:

- problema de negocio;
- contexto SDLC;
- usuario beneficiado;
- valor entregado;
- evidencia en README, roadmap, backlog y reportes de auditoria.

### Pregunta 2

Que problema concreto resuelve DevPilot dentro del ciclo de desarrollo de software?

La respuesta debe incluir:

- problema antes de DevPilot;
- flujo mejorado con DevPilot;
- limites actuales;
- evidencia de comandos, modulos y documentos.

### Pregunta 3

Quienes son los usuarios objetivo de DevPilot?

La respuesta debe distinguir:

- operador local;
- arquitecto;
- desarrollador;
- auditor;
- product owner;
- equipo de QA;
- usuario no tecnico.

### Pregunta 4

Cual es la vision de producto definida en los artefactos de ingenieria?

La respuesta debe incluir:

- vision actual;
- vision objetivo;
- supuestos;
- restricciones;
- evolucion esperada.

### Pregunta 5

Cual es la propuesta de valor de DevPilot?

La respuesta debe incluir:

- propuesta de valor tecnica;
- propuesta de valor no tecnica;
- valor para equipos pequenos;
- valor para control de calidad;
- valor para auditoria.

### Pregunta 6

Cuales son los diferenciadores de DevPilot frente a un simple CLI, un framework de agentes o una herramienta de validacion?

La respuesta debe incluir:

- evidencia de ApplicationService;
- evidence gates;
- MIASI;
- quality gates;
- onboarding;
- local-first;
- no-go gates.

### Pregunta 7

Que significa exactamente "agent-assisted SDLC" dentro de este proyecto?

La respuesta debe incluir:

- definicion;
- capacidades actuales;
- capacidades futuras;
- diferencia entre asistencia y ejecucion autonoma.

### Pregunta 8

Que restricciones arquitectonicas tiene DevPilot?

La respuesta debe incluir:

- local-first;
- read-only/dry-run por defecto;
- no remote execution;
- no connector write;
- no plugin execution;
- no SaaS;
- no enterprise-ready claim;
- no compliance-certified claim.

### Pregunta 9

Que decisiones de producto estan explicitamente fuera de alcance hoy?

La respuesta debe incluir:

- lista de no-alcances;
- justificacion;
- condiciones para reconsiderarlos;
- ADRs necesarias.

### Pregunta 10

Como se debe explicar DevPilot a una persona no tecnica en maximo seis parrafos?

La respuesta debe incluir:

- lenguaje sencillo;
- analogia operacional;
- limites;
- valor practico.

## 5. Bloque B - Estado real, claims y madurez ejecutiva

### Pregunta 11

Cual es el estado actual del repo vigente y cual es el ultimo hito cerrado?

La respuesta debe incluir:

- last_completed_sprint;
- next_sprint;
- project_state;
- commit o ZIP fuente;
- evidencia de logs recientes.

### Pregunta 12

Que significa que DevPilot este declarado `production-ready-local`?

La respuesta debe incluir:

- alcance exacto;
- evidencia que lo soporta;
- limites;
- claims permitidos y prohibidos.

### Pregunta 13

Que capacidades estan realmente listas para uso local?

La respuesta debe clasificar:

- CLI;
- API;
- UI;
- validators;
- reports;
- quality gates;
- onboarding.

### Pregunta 14

Que capacidades estan en estado `implemented-initial`?

La respuesta debe incluir:

- que funciona;
- que falta;
- riesgo de uso;
- evolucion requerida.

### Pregunta 15

Que capacidades son `design-only`?

La respuesta debe incluir:

- remote runner;
- enterprise deployment;
- secure transport;
- compliance mapping;
- cualquier otra capacidad solo disenada.

### Pregunta 16

Que capacidades estan planificadas pero no implementadas?

La respuesta debe incluir:

- roadmap;
- backlog;
- dependencias;
- criterios de entrada.

### Pregunta 17

Que claims puede hacer DevPilot hoy?

La respuesta debe separar:

- claims permitidos;
- claims condicionados;
- claims prohibidos.

### Pregunta 18

Que claims NO puede hacer DevPilot hoy?

La respuesta debe incluir:

- enterprise-ready;
- compliance-certified;
- SaaS-ready;
- remote-ready;
- autonomous agent execution;
- production multiuser.

### Pregunta 19

Como se demuestra que el cierre `production-ready-local` no sobredeclara el producto?

La respuesta debe incluir:

- claims validator;
- no-go gates;
- final declaration;
- reportes;
- tests.

### Pregunta 20

Que cambios sustanciales ocurrieron entre el repo usado para el primer onboarding report y el repo vigente?

La respuesta debe incluir:

- capacidades nuevas;
- cambios de arquitectura;
- nuevos gates;
- cambios de madurez.

### Pregunta 21

Que significa "madurez industrial" en el contexto de DevPilot?

La respuesta debe incluir:

- criterios tecnicos;
- criterios de operacion;
- criterios de evidencia;
- criterios de seguridad.

### Pregunta 22

Que partes del producto todavia no alcanzan nivel industrial completo?

La respuesta debe incluir:

- causas;
- riesgos;
- impacto;
- prioridad.

## 6. Bloque C - Estado real vs planeado

### Pregunta 23

Compara vision, roadmap, requisitos y arquitectura contra el codigo fuente actual.

La respuesta debe producir una matriz con:

- capacidad;
- planeado;
- implementado;
- evidencia;
- estado;
- brecha.

### Pregunta 24

Identifica funcionalidades implementadas.

La respuesta debe incluir:

- descripcion;
- modulo;
- comando;
- test;
- documento;
- madurez.

### Pregunta 25

Identifica funcionalidades parcialmente implementadas.

La respuesta debe incluir:

- que parte funciona;
- que parte falta;
- riesgos;
- criterios de cierre.

### Pregunta 26

Identifica funcionalidades definidas pero aun no implementadas.

La respuesta debe incluir:

- fuente documental;
- razon de diferimiento;
- dependencias.

### Pregunta 27

Identifica funcionalidades no iniciadas.

La respuesta debe incluir:

- prioridad;
- impacto;
- orden recomendado.

### Pregunta 28

Clasifica cada capacidad como `Implemented`, `Partially Implemented`, `Stub` o `Planned`.

La respuesta debe incluir una matriz completa.

### Pregunta 29

Clasifica cada capacidad con la taxonomia ampliada de madurez.

Usar:

```text
production-ready-local
implemented
implemented-initial
design-only
read-only
dry-run
preview
stub
planned
blocked
```

### Pregunta 30

Que evidencia minima se requiere para mover una capacidad de `implemented-initial` a `production-ready-local`?

La respuesta debe incluir:

- tests;
- docs;
- schema;
- report;
- quality gate;
- runbook.

## 7. Bloque D - Arquitectura real de alto nivel

### Pregunta 31

Describe la arquitectura de alto nivel de DevPilot.

La respuesta debe incluir:

- capas;
- modulos;
- dependencias;
- boundaries;
- flujo principal.

### Pregunta 32

Cuales son los modulos principales del repo?

La respuesta debe incluir:

- responsabilidad;
- rutas;
- dependencias;
- estado.

### Pregunta 33

Cuales son las capas arquitectonicas reales?

La respuesta debe distinguir:

- CLI;
- ApplicationService;
- core domain;
- validators;
- reports;
- persistence;
- API;
- UI;
- governance.

### Pregunta 34

Que responsabilidades tiene cada capa?

La respuesta debe incluir:

- responsabilidades permitidas;
- responsabilidades prohibidas;
- bypasses detectados.

### Pregunta 35

Que patrones arquitectonicos utiliza DevPilot?

La respuesta debe incluir:

- ApplicationService;
- DTOs;
- registries;
- schemas;
- validators;
- gates;
- report builders;
- local-first adapters.

### Pregunta 36

Cual es el flujo de ejecucion principal de una operacion CLI?

La respuesta debe incluir:

- parser;
- command handler;
- ApplicationService;
- core;
- CommandResult;
- observabilidad;
- persistencia.

### Pregunta 37

Genera un mapa de dependencias de alto nivel.

La respuesta debe incluir:

- dependencias internas;
- dependencias externas;
- restricciones;
- hotspots.

### Pregunta 38

Identifica componentes de mayor acoplamiento.

La respuesta debe incluir:

- modulo;
- razon del acoplamiento;
- riesgo;
- mitigacion.

### Pregunta 39

Identifica componentes nucleo.

La respuesta debe incluir:

- por que son nucleares;
- impacto de cambio;
- tests asociados.

### Pregunta 40

Donde estan los boundaries mas importantes?

La respuesta debe incluir:

- CLI/core;
- ApplicationService/core;
- API/ApplicationService;
- UI/API;
- PolicyEngine/actions.

### Pregunta 41

Que componentes deberian ser estabilizados antes de agregar nuevas features?

La respuesta debe incluir:

- prioridad;
- riesgo;
- evidencia.

### Pregunta 42

Que partes del codigo siguen siendo monoliticas o dificiles de mantener?

La respuesta debe incluir:

- archivos;
- sintomas;
- plan incremental.

## 8. Bloque E - Arquitectura C4 y divergencias

### Pregunta 43

Genera el diagrama conceptual C4 Context actual de DevPilot.

La respuesta debe incluir:

- actores;
- sistemas externos;
- limites;
- relaciones.

### Pregunta 44

Genera el diagrama conceptual C4 Container actual.

La respuesta debe incluir:

- CLI;
- API local;
- Web UI;
- core Python;
- store local;
- reports;
- docs/schemas.

### Pregunta 45

Genera el diagrama conceptual C4 Component actual.

La respuesta debe incluir:

- componentes principales;
- interfaces;
- responsabilidades.

### Pregunta 46

Compara C4 documentado vs C4 real.

La respuesta debe incluir:

- divergencias;
- impacto;
- prioridad de correccion.

### Pregunta 47

Que contenedores o componentes existen solo como diseno?

La respuesta debe incluir:

- remote runner;
- enterprise;
- secure transport;
- plugin execution;
- connector write.

### Pregunta 48

Que componentes reales no estan suficientemente representados en diagramas?

La respuesta debe incluir:

- evidencia;
- recomendacion de actualizacion documental.

## 9. Bloque F - Domain-Driven Design

### Pregunta 49

Analiza DevPilot usando Domain-Driven Design.

La respuesta debe identificar:

- Core Domains;
- Supporting Domains;
- Generic Domains.

### Pregunta 50

Cual es el verdadero nucleo del producto?

La respuesta debe argumentar si el nucleo es:

- agentes;
- governance;
- evidence-based SDLC;
- validators;
- workspace orchestration;
- quality gates;
- otra combinacion.

### Pregunta 51

Que bounded contexts existen actualmente?

La respuesta debe incluir:

- contexto;
- lenguaje ubicuo;
- modulos;
- boundaries.

### Pregunta 52

Que bounded contexts estan mezclados o difusos?

La respuesta debe incluir:

- sintomas;
- riesgo;
- propuesta de separacion.

### Pregunta 53

Como se relacionan Workspace, MIASI, agentes, policies y reports dentro del dominio?

La respuesta debe incluir:

- flujo conceptual;
- dependencias;
- riesgos.

### Pregunta 54

Que lenguaje ubicuo deberia estandarizarse?

La respuesta debe incluir:

- terminos;
- definiciones;
- terminos ambiguos.

### Pregunta 55

Que dominios soportan la declaracion `production-ready-local`?

La respuesta debe incluir:

- evidence map;
- quality gates;
- claims validator;
- project state.

### Pregunta 56

Que dominios deberian evolucionar primero en POST-H-026?

La respuesta debe justificar:

- impacto;
- riesgo;
- dependencia.

## 10. Bloque G - Runtime execution

### Pregunta 57

Describe paso a paso que ocurre desde que un usuario ejecuta un comando CLI hasta que obtiene un resultado.

La respuesta debe incluir:

- argparse;
- handler;
- ApplicationService;
- core;
- CommandResult;
- print_result.

### Pregunta 58

Que ocurre internamente al ejecutar un comando de validacion?

La respuesta debe incluir:

- entrada;
- reglas;
- findings;
- severidad;
- salida.

### Pregunta 59

Que ocurre internamente al ejecutar un quality gate?

La respuesta debe incluir:

- subgates;
- criticidad;
- agregacion;
- PASS/BLOCK.

### Pregunta 60

Que ocurre al ejecutar el gate `production-ready-local-final`?

La respuesta debe incluir:

- criteria;
- evidence aggregator;
- declaration gate;
- claims validator;
- final report.

### Pregunta 61

Como se modelan resultados y errores?

La respuesta debe incluir:

- CommandResult;
- Finding;
- ExitCode;
- ApplicationResponse;
- HTTP mapping.

### Pregunta 62

Como se aplica PolicyEngine en runtime?

La respuesta debe incluir:

- operaciones protegidas;
- acciones sensibles;
- approvals;
- RBAC;
- bloqueos.

### Pregunta 63

Como se maneja persistencia local?

La respuesta debe incluir:

- LocalStore;
- SQLite;
- outputs;
- .devpilot;
- limites de runtime state.

### Pregunta 64

Como se registra observabilidad?

La respuesta debe incluir:

- eventos;
- traces;
- metrics;
- redaccion;
- retencion.

### Pregunta 65

Que operaciones mutan estado y cuales son read-only?

La respuesta debe incluir una matriz.

### Pregunta 66

Como se garantiza dry-run por defecto?

La respuesta debe incluir:

- comandos;
- flags;
- policies;
- tests.

## 11. Bloque H - Workspace y onboarding

### Pregunta 67

Explica detalladamente el modelo Workspace de DevPilot.

La respuesta debe incluir:

- proposito;
- estructura;
- ciclo de vida;
- archivos relevantes.

### Pregunta 68

Como se relaciona Workspace con agentes?

La respuesta debe incluir:

- capacidades actuales;
- limites;
- evolucion.

### Pregunta 69

Como se relaciona Workspace con estandares?

La respuesta debe incluir:

- StandardsRegistry;
- templates;
- readiness.

### Pregunta 70

Como se relaciona Workspace con repositorios Git?

La respuesta debe incluir:

- estado actual;
- comandos;
- restricciones.

### Pregunta 71

Como se crea o prepara un proyecto nuevo desde una idea inicial?

La respuesta debe incluir:

- operador;
- templates;
- bootstrap;
- readiness preview;
- evidence.

### Pregunta 72

Que produce el onboarding bootstrap?

La respuesta debe incluir:

- archivos;
- reportes;
- modo dry-run;
- modo execute.

### Pregunta 73

Que valida readiness preview?

La respuesta debe incluir:

- fases;
- pending;
- warning;
- success;
- MIASI.

### Pregunta 74

Que cubrio POST-H-024?

La respuesta debe incluir:

- playbook;
- templates;
- bootstrap;
- readiness;
- quality gate.

### Pregunta 75

Que gaps quedan en onboarding?

La respuesta debe incluir:

- automatizacion;
- UX;
- templates;
- integracion UI;
- proyecto piloto.

### Pregunta 76

Como deberia evolucionar el onboarding hacia una experiencia industrial?

La respuesta debe incluir:

- pasos;
- riesgos;
- priorizacion.

### Pregunta 77

Que debe revisar un operador antes de iniciar un nuevo workspace?

La respuesta debe incluir:

- checklist;
- comandos;
- documentos.

### Pregunta 78

Como se evidencia que un workspace esta listo para iniciar desarrollo?

La respuesta debe incluir:

- reportes;
- gates;
- tests;
- findings.
 
## 12. Bloque I - Capacidades funcionales

### Pregunta 79

Relaciona todas las funcionalidades actuales y futuras de DevPilot.

La respuesta debe incluir:

- lenguaje tecnico;
- lenguaje corriente;
- estado;
- evidencia.

### Pregunta 80

Que capacidades ofrece DevPilot por CLI?

La respuesta debe incluir:

- comandos principales;
- parametros;
- salidas;
- riesgos.

### Pregunta 81

Que capacidades ofrece DevPilot por API local?

La respuesta debe incluir:

- rutas;
- proteccion;
- ApplicationService;
- limites.

### Pregunta 82

Que capacidades ofrece DevPilot por Web UI local?

La respuesta debe incluir:

- dashboard;
- reports;
- traces;
- approvals;
- settings;
- operator dashboard.

### Pregunta 83

Que capacidades existen solo como reportes o evidencia machine-readable?

La respuesta debe incluir:

- reportes;
- schemas;
- manifests;
- uso operacional.

### Pregunta 84

Que capacidades escriben reportes?

La respuesta debe incluir:

- comando;
- ruta;
- schema;
- flag necesario.

### Pregunta 85

Que capacidades son estrictamente read-only?

La respuesta debe incluir:

- razon;
- evidencia;
- tests.

### Pregunta 86

Que capacidades estan protegidas por dry-run?

La respuesta debe incluir:

- comandos;
- flags;
- defaults.

### Pregunta 87

Que flujos completos estan soportados de punta a punta?

La respuesta debe incluir:

- flujo;
- pasos;
- evidencia.

### Pregunta 88

Que flujos todavia requieren intervencion manual?

La respuesta debe incluir:

- motivo;
- riesgo;
- posible automatizacion.

### Pregunta 89

Que capacidades tienen UI pero no API completa?

La respuesta debe incluir:

- gaps;
- riesgos;
- roadmap.

### Pregunta 90

Que capacidades tienen CLI pero no UI?

La respuesta debe incluir:

- priorizacion para UI futura.

### Pregunta 91

Que capacidades tienen core pero no estan expuestas por interfaces?

La respuesta debe incluir:

- modulos;
- razon;
- criterio de exposicion.

### Pregunta 92

Que capacidades deberian bloquearse aunque existan parcialmente?

La respuesta debe incluir:

- justificacion;
- no-go gate;
- ADR requerida.

### Pregunta 93

Que capacidades deberian convertirse en producto visible en POST-H-026?

La respuesta debe incluir:

- valor;
- esfuerzo;
- riesgo.

### Pregunta 94

Que capacidades deberian permanecer solo como evidencia interna?

La respuesta debe incluir:

- razon;
- riesgo de exposicion.

### Pregunta 95

Como se debe presentar el mapa de capacidades a usuarios no tecnicos?

La respuesta debe incluir:

- categorias;
- lenguaje claro;
- ejemplos.

### Pregunta 96

Como se debe presentar el mapa de capacidades a arquitectos/desarrolladores?

La respuesta debe incluir:

- modulos;
- contratos;
- interfaces;
- tests.

## 13. Bloque J - Validadores, schemas y evidence model

### Pregunta 97

Analiza todos los validadores existentes.

La respuesta debe incluir:

- que validan;
- reglas;
- entradas;
- salidas;
- tests.

### Pregunta 98

Que falta implementar en los validadores?

La respuesta debe incluir:

- gaps;
- riesgos;
- prioridad.

### Pregunta 99

Como evolucionar hacia validacion mas basada en schemas?

La respuesta debe incluir:

- schema registry;
- JSON Schema;
- report schemas;
- artifact profiles.

### Pregunta 100

Que es Artifact Profile Registry?

La respuesta debe incluir:

- proposito;
- uso;
- integracion.

### Pregunta 101

Que es JSON Schema Registry dentro de DevPilot?

La respuesta debe incluir:

- catalogo;
- schemas registrados;
- validacion;
- CLI.

### Pregunta 102

Que schemas son criticos para operacion industrial?

La respuesta debe incluir:

- project_state;
- manifests;
- TCR;
- production_ready;
- operator dashboard;
- otros.

### Pregunta 103

Como se registra un nuevo schema?

La respuesta debe incluir:

- archivos;
- catalogo;
- tests;
- CLI.

### Pregunta 104

Como se valida un reporte?

La respuesta debe incluir:

- comando;
- schema-id;
- ruta;
- salida esperada.

### Pregunta 105

Como se relacionan manifests, source registry y test contracts?

La respuesta debe incluir:

- flujo de evidencia;
- sincronizacion;
- riesgos.

### Pregunta 106

Que es el evidence map de production-ready-local?

La respuesta debe incluir:

- criterios;
- hitos requeridos;
- evidencias;
- blockers.

### Pregunta 107

Como funciona el evidence aggregator read-only?

La respuesta debe incluir:

- fuentes;
- decision intermedia;
- limites.

### Pregunta 108

Como funciona el final declaration report?

La respuesta debe incluir:

- PASS/BLOCK;
- claims;
- no-go gates;
- schema.

### Pregunta 109

Como se evita declarar exito sin evidencia?

La respuesta debe incluir:

- gates;
- blockers;
- schemas;
- tests.

### Pregunta 110

Que evidencia deberia exigirse para cada nuevo hito?

La respuesta debe incluir:

- manifest;
- tests;
- docs;
- reportes;
- comandos.

### Pregunta 111

Como se detecta drift documental?

La respuesta debe incluir:

- docs-governance;
- source registry;
- markdown/json sync;
- roadmap sync.

### Pregunta 112

Como se detecta drift de contratos?

La respuesta debe incluir:

- TCR v1;
- TCR v2;
- schema registry;
- tests.

### Pregunta 113

Que evidencias deberian agregarse para fortalecer auditoria futura?

La respuesta debe incluir:

- propuestas;
- prioridad;
- impacto.

### Pregunta 114

Que reportes deberian ser consumibles por UI?

La respuesta debe incluir:

- reportes actuales;
- API necesaria;
- riesgos.

## 14. Bloque K - MIASI, agentes, policies y approvals

### Pregunta 115

Analiza todos los modulos relacionados con MIASI.

La respuesta debe incluir:

- implementado;
- contrato;
- diseno;
- tests.

### Pregunta 116

Que partes de MIASI son ejecutables hoy?

La respuesta debe incluir:

- comandos;
- modulos;
- limites.

### Pregunta 117

Que partes de MIASI son solo contratos?

La respuesta debe incluir:

- archivos;
- schemas;
- roadmap.

### Pregunta 118

Que capacidades agentic existen hoy?

La respuesta debe incluir:

- agentes;
- runtime;
- limites;
- madurez.

### Pregunta 119

Que capacidades agentic estan previstas para futuro?

La respuesta debe incluir:

- roadmap;
- dependencias;
- no-go gates.

### Pregunta 120

Existe actualmente un sistema multiagente funcional?

La respuesta debe distinguir:

- funcional;
- preparatorio;
- simulado;
- bloqueado.

### Pregunta 121

Cual es el nivel de madurez de ejecucion de cada agente?

La respuesta debe incluir matriz:

- agente;
- funcion;
- madurez;
- riesgos;
- tests.

### Pregunta 122

Como se gobiernan acciones sensibles?

La respuesta debe incluir:

- SensitiveActionCatalog;
- PolicyEngine;
- approvals;
- RBAC.

### Pregunta 123

Como funciona Approval/RBAC hardening?

La respuesta debe incluir:

- acciones;
- actores;
- roles;
- bindings;
- tests.

### Pregunta 124

Que acciones estan bloqueadas por politica?

La respuesta debe incluir:

- lista;
- motivo;
- evidencia.

### Pregunta 125

Como se evita prompt/tool injection?

La respuesta debe incluir:

- guardas;
- policy;
- tests;
- limites.

### Pregunta 126

Como se relaciona MIASI con observabilidad?

La respuesta debe incluir:

- trazas;
- findings;
- auditabilidad.

### Pregunta 127

Como se relaciona MIASI con evaluaciones?

La respuesta debe incluir:

- evals;
- groundedness;
- model governance.

### Pregunta 128

Que falta para habilitar agentes con mayor autonomia?

La respuesta debe incluir:

- arquitectura;
- seguridad;
- approvals;
- sandbox;
- ADRs.

### Pregunta 129

Que capacidades agentic deben permanecer bloqueadas?

La respuesta debe incluir:

- razon;
- riesgo;
- criterios de desbloqueo.

### Pregunta 130

Que evidencia demuestra que los agentes no ejecutan acciones prohibidas?

La respuesta debe incluir:

- tests;
- policies;
- no-go gates.

### Pregunta 131

Como deberia evolucionar el sistema multiagente?

La respuesta debe incluir:

- fases;
- limites;
- validaciones.

### Pregunta 132

Que rol debe tener el operador humano en flujos agent-assisted?

La respuesta debe incluir:

- aprobaciones;
- revisiones;
- decisiones;
- accountability.

## 15. Bloque L - Seguridad, no-go gates y threat model

### Pregunta 133

Cuales son los no-go gates vigentes?

La respuesta debe incluir:

- remote execution;
- connector write;
- plugin execution;
- external APIs;
- enterprise claim;
- compliance claim.

### Pregunta 134

Como se bloquea remote execution?

La respuesta debe incluir:

- codigo;
- docs;
- tests;
- ADRs.

### Pregunta 135

Como se bloquea connector write?

La respuesta debe incluir:

- policy;
- sandbox;
- tests.

### Pregunta 136

Como se bloquea plugin execution?

La respuesta debe incluir:

- plugin registry;
- permission model;
- quality gate.

### Pregunta 137

Como se controlan APIs externas?

La respuesta debe incluir:

- defaults;
- guards;
- local providers;
- exceptions.

### Pregunta 138

Como se protegen secretos?

La respuesta debe incluir:

- redaction;
- env vars;
- token handling;
- reports.

### Pregunta 139

Que threat models existen?

La respuesta debe incluir:

- enterprise;
- remote runner;
- secure transport;
- plugins;
- connectors.

### Pregunta 140

Que amenazas siguen abiertas?

La respuesta debe incluir:

- severidad;
- mitigacion;
- prioridad.

### Pregunta 141

Que requiere nueva ADR antes de habilitarse?

La respuesta debe incluir:

- decision;
- motivo;
- evidencia.

### Pregunta 142

Como se valida que una capacidad sensible sigue deshabilitada?

La respuesta debe incluir:

- tests;
- project_state;
- quality gate.

### Pregunta 143

Que controles existen para API local?

La respuesta debe incluir:

- token;
- CORS;
- localhost bind;
- policy binding.

### Pregunta 144

Que controles existen para UI local?

La respuesta debe incluir:

- API-only;
- no filesystem;
- no destructive actions;
- token.

### Pregunta 145

Como se documentan los limites de compliance?

La respuesta debe incluir:

- disclaimers;
- reports;
- no certification claim.

### Pregunta 146

Como se documentan los limites enterprise?

La respuesta debe incluir:

- design-only;
- threat model;
- blockers.

### Pregunta 147

Como se documentan los limites de secure transport?

La respuesta debe incluir:

- design-only;
- no sockets;
- no certificates;
- no secrets.

### Pregunta 148

Que riesgos de seguridad deberian priorizarse en POST-H-026?

La respuesta debe incluir:

- impacto;
- probabilidad;
- mitigacion.

### Pregunta 149

Que evidencia permitiria auditar seguridad local?

La respuesta debe incluir:

- comandos;
- reports;
- schemas;
- tests.

### Pregunta 150

Como se comunica a usuarios no tecnicos lo que DevPilot no debe hacer?

La respuesta debe incluir:

- lenguaje claro;
- ejemplos;
- riesgos.

## 16. Bloque M - Testing, TCR y quality gates

### Pregunta 151

Como esta organizada la estrategia de pruebas?

La respuesta debe incluir:

- unit;
- integration;
- docs;
- schema;
- quality gates.

### Pregunta 152

Que es Test Contract Registry v1?

La respuesta debe incluir:

- proposito;
- estructura;
- comandos.

### Pregunta 153

Que agrega Test Contract Registry v2?

La respuesta debe incluir:

- clasificacion;
- dominios;
- criticidad;
- costo;
- impacto.

### Pregunta 154

Como se decide que pruebas ejecutar en un sprint focal?

La respuesta debe incluir:

- TCR;
- impacto;
- archivos tocados;
- riesgo.

### Pregunta 155

Cuales son los quality gates principales?

La respuesta debe incluir:

- hardening;
- industrial;
- subgates;
- criticidad.

### Pregunta 156

Que significa que `quality-gate hardening` pase?

La respuesta debe incluir:

- subgates;
- blockers;
- alcance.

### Pregunta 157

Que significa que `quality-gate industrial` pase?

La respuesta debe incluir:

- diferencias con hardening;
- alcance.

### Pregunta 158

Que pruebas son costosas?

La respuesta debe incluir:

- duracion;
- motivo;
- estrategia.

### Pregunta 159

Como se debe manejar una suite de mas de 1100 tests?

La respuesta debe incluir:

- perfiles;
- regresion focal;
- regresion final.

### Pregunta 160

Que riesgos de regresion historica existen?

La respuesta debe incluir:

- ejemplos;
- mitigacion.

### Pregunta 161

Como se valida documentacion?

La respuesta debe incluir:

- docs-governance;
- frontmatter;
- sync;
- source registry.

### Pregunta 162

Como se valida schema registry?

La respuesta debe incluir:

- catalogo;
- tests;
- CLI.

### Pregunta 163

Como se valida project_state?

La respuesta debe incluir:

- checks;
- README;
- runbook;
- roadmap;
- changelog.

### Pregunta 164

Que debe contener una evidencia de cierre de sprint?

La respuesta debe incluir:

- log;
- tests;
- CLI;
- manifest;
- ZIP.

### Pregunta 165

Como se debe analizar un fallo de pytest?

La respuesta debe incluir:

- reproduccion;
- causa raiz;
- patch minimo;
- validacion.

### Pregunta 166

Que estrategia de test impact analyzer existe?

La respuesta debe incluir:

- version actual;
- gaps;
- evolucion.

### Pregunta 167

Que pruebas deberian agregarse para POST-H-026?

La respuesta debe incluir:

- riesgo;
- cobertura;
- costo.

### Pregunta 168

Que criterios deben impedir cerrar un backlog?

La respuesta debe incluir:

- blockers;
- drift;
- tests fallidos;
- claims incorrectos.

## 17. Bloque N - Observabilidad, runtime state y operacion

### Pregunta 169

Donde se registran eventos, trazas y metricas?

La respuesta debe incluir:

- rutas;
- LocalStore;
- SQLite;
- outputs.

### Pregunta 170

Que runtime artifacts existen?

La respuesta debe incluir:

- outputs;
- .devpilot/devpilot.db;
- traces;
- reports.

### Pregunta 171

Que artifacts deben excluirse de ZIPs limpios?

La respuesta debe incluir:

- patrones;
- motivo;
- tests.

### Pregunta 172

Como se limpia runtime state?

La respuesta debe incluir:

- dry-run;
- execute;
- approvals;
- riesgos.

### Pregunta 173

Como se exporta evidencia local?

La respuesta debe incluir:

- redaction;
- reports;
- audit packs.

### Pregunta 174

Que reportes debe revisar un operador?

La respuesta debe incluir:

- prioritarios;
- interpretacion;
- frecuencia.

### Pregunta 175

Como diagnosticar fallos comunes?

La respuesta debe incluir:

- API;
- UI;
- schema;
- docs;
- quality gate.

### Pregunta 176

Como se verifica que el repo esta sano antes de entregar?

La respuesta debe incluir:

- comandos;
- resultados esperados.

### Pregunta 177

Como se manejan logs de consola y evidencia de ejecucion?

La respuesta debe incluir:

- que guardar;
- que no versionar;
- como auditar.

### Pregunta 178

Como se protegen datos sensibles en reportes?

La respuesta debe incluir:

- redaccion;
- secreto;
- limites.

### Pregunta 179

Como se consulta la historia de ejecuciones?

La respuesta debe incluir:

- API;
- LocalStore;
- UI;
- limites.

### Pregunta 180

Que gaps existen en observabilidad?

La respuesta debe incluir:

- impacto;
- prioridad.

### Pregunta 181

Que deberia automatizarse en operacion local?

La respuesta debe incluir:

- scripts;
- runbook;
- riesgos.

### Pregunta 182

Como debe operar un usuario sin conocimiento profundo del codigo?

La respuesta debe incluir:

- guia paso a paso;
- comandos minimos;
- validaciones.

### Pregunta 183

Como se debe documentar troubleshooting?

La respuesta debe incluir:

- error;
- causa;
- comando;
- solucion.

### Pregunta 184

Que indicadores operativos deben aparecer en un dashboard futuro?

La respuesta debe incluir:

- metricas;
- gates;
- riesgos;
- estado.

## 18. Bloque O - Release, reproducibilidad y distribucion

### Pregunta 185

Como se genera un ZIP limpio del repo?

La respuesta debe incluir:

- git archive;
- exclusiones;
- verificacion.

### Pregunta 186

Que archivos no deben incluirse en entregables?

La respuesta debe incluir:

- outputs;
- caches;
- DB runtime;
- entornos.

### Pregunta 187

Que evidencia de reproducibilidad existe?

La respuesta debe incluir:

- release pack;
- source archive manifest;
- checksums.

### Pregunta 188

Como se valida un release source archive?

La respuesta debe incluir:

- comandos;
- reportes;
- criterios PASS/BLOCK.

### Pregunta 189

Que checksums, manifests y reports deben acompanar una entrega?

La respuesta debe incluir:

- lista;
- uso;
- ruta.

### Pregunta 190

Que falta para un release candidate instalable por terceros?

La respuesta debe incluir:

- packaging;
- installer;
- docs;
- smoke tests.

### Pregunta 191

Como debe ser el proceso de instalacion industrial?

La respuesta debe incluir:

- prerequisitos;
- venv;
- deps;
- Node;
- verificacion.

### Pregunta 192

Como se debe validar instalacion en Windows?

La respuesta debe incluir:

- comandos;
- resultados esperados.

### Pregunta 193

Como se debe validar instalacion en Linux/macOS?

La respuesta debe incluir:

- diferencias;
- riesgos.

### Pregunta 194

Que estrategia de versionado deberia usarse?

La respuesta debe incluir:

- repo;
- manifests;
- release notes;
- semver.

### Pregunta 195

Que estrategia de rollback deberia documentarse?

La respuesta debe incluir:

- git;
- outputs;
- DB;
- config.

### Pregunta 196

Como se deberian firmar o verificar audit packs?

La respuesta debe incluir:

- estado actual;
- limites;
- evolucion.

### Pregunta 197

Como se debe publicar un release local sin SaaS?

La respuesta debe incluir:

- artifact;
- checksum;
- docs;
- no external service.

### Pregunta 198

Que gaps existen en distribucion?

La respuesta debe incluir:

- impacto;
- roadmap.

### Pregunta 199

Que validaciones deben correr antes de etiquetar una version?

La respuesta debe incluir:

- focal;
- general;
- quality gates;
- release checks.

### Pregunta 200

Que evidencias debe revisar un auditor antes de aceptar un release?

La respuesta debe incluir:

- manifests;
- logs;
- reports;
- checksums.

## 19. Bloque P - UI/API local

### Pregunta 201

Que API local existe y que endpoints expone?

La respuesta debe incluir:

- rutas;
- metodos;
- proteccion;
- ApplicationService.

### Pregunta 202

Como se levanta la API local?

La respuesta debe incluir:

- token;
- comando;
- host;
- puerto;
- troubleshooting.

### Pregunta 203

Como se protege la API con token y CORS?

La respuesta debe incluir:

- header;
- origins;
- errores 401/403.

### Pregunta 204

Que vistas tiene la Web UI?

La respuesta debe incluir:

- Dashboard;
- Report Viewer;
- Trace Viewer;
- Approval Center;
- Settings;
- Operator Dashboard.

### Pregunta 205

Como se levanta la Web UI local?

La respuesta debe incluir:

- Node;
- npm;
- Vite;
- puerto;
- token.

### Pregunta 206

Como se prueba el smoke test frontend?

La respuesta debe incluir:

- npm test;
- pytest opcional;
- criterios.

### Pregunta 207

Que consume la UI desde API?

La respuesta debe incluir:

- endpoints;
- cliente TS;
- headers.

### Pregunta 208

Que no puede hacer la UI por diseno?

La respuesta debe incluir:

- no filesystem;
- no destructive actions;
- no direct core imports.

### Pregunta 209

Como maneja la UI estados loading, empty, error y BLOCK?

La respuesta debe incluir:

- componentes;
- UX;
- limites.

### Pregunta 210

Como se prueba manualmente la UI?

La respuesta debe incluir:

- pasos;
- pantallas;
- errores esperados.

### Pregunta 211

Como se prueba la API con PowerShell?

La respuesta debe incluir:

- Invoke-RestMethod;
- headers;
- endpoints.

### Pregunta 212

Que gaps tiene la UI actual?

La respuesta debe incluir:

- UX;
- routing;
- datos;
- acciones;
- seguridad.

### Pregunta 213

Que evolucion visual deberia priorizarse?

La respuesta debe incluir:

- operador;
- reportes;
- onboarding;
- quality gates.

### Pregunta 214

Como se podria convertir la UI en una consola operacional real?

La respuesta debe incluir:

- arquitectura;
- API;
- seguridad;
- roadmap.

### Pregunta 215

Que se requiere para empaquetar UI/API como producto local instalable?

La respuesta debe incluir:

- build;
- preview;
- servidor;
- config.

### Pregunta 216

Que pruebas visuales deberian agregarse?

La respuesta debe incluir:

- smoke;
- screenshot;
- accessibility;
- responsive.

## 20. Bloque Q - Gap analysis y roadmap

### Pregunta 217

Realiza un Gap Analysis completo entre vision, MVP, roadmap, requisitos, arquitectura y codigo vigente.

La respuesta debe producir una matriz.

### Pregunta 218

Que gaps residuales quedan despues de POST-H-025?

La respuesta debe clasificar:

- producto;
- arquitectura;
- seguridad;
- operacion;
- testing;
- UX.

### Pregunta 219

Que capacidades deben evolucionar primero en POST-H-026?

La respuesta debe incluir:

- prioridad;
- justificacion;
- riesgos.

### Pregunta 220

Que riesgos deben bloquear nuevas features?

La respuesta debe incluir:

- criterio;
- evidencia;
- mitigacion.

### Pregunta 221

Que olas de avance deberian seguir?

La respuesta debe incluir:

- estabilizacion;
- producto local;
- release candidate;
- agentes avanzados;
- enterprise design.

### Pregunta 222

Que hitos requieren ADR nueva?

La respuesta debe incluir:

- decision;
- razon;
- evidencia.

### Pregunta 223

Que deuda tecnica debe atacarse primero?

La respuesta debe incluir:

- impacto;
- costo;
- riesgo.

### Pregunta 224

Que deuda documental debe corregirse?

La respuesta debe incluir:

- documentos;
- inconsistencias;
- tests.

### Pregunta 225

Que deuda de testing debe corregirse?

La respuesta debe incluir:

- costo;
- cobertura;
- TCR.

### Pregunta 226

Que deuda de UX debe corregirse?

La respuesta debe incluir:

- usuario;
- flujo;
- impacto.

### Pregunta 227

Que backlog deberia abrir POST-H-026?

La respuesta debe incluir:

- objetivo;
- alcance;
- micro-sprints;
- criterios PASS/BLOCK.

### Pregunta 228

Que capacidades no deben entrar en POST-H-026?

La respuesta debe incluir:

- motivo;
- riesgo;
- backlog futuro.

### Pregunta 229

Como priorizar roadmap por riesgo/valor?

La respuesta debe incluir matriz.

### Pregunta 230

Como medir avance industrial despues de production-ready-local?

La respuesta debe incluir:

- indicadores;
- gates;
- reportes.

### Pregunta 231

Que decisiones debe tomar el owner antes de ampliar alcance?

La respuesta debe incluir:

- alternativas;
- tradeoffs;
- riesgos.

### Pregunta 232

Que criterio debe usarse para declarar un futuro `enterprise-ready`?

La respuesta debe incluir:

- requisitos;
- blockers;
- evidencia;
- no declarar prematuramente.

## 21. Bloque R - Guia de operador y caso piloto

### Pregunta 233

Como instala DevPilot un operador nuevo?

La respuesta debe incluir:

- prerequisitos;
- comandos;
- validaciones.

### Pregunta 234

Como verifica que el repo esta sano?

La respuesta debe incluir:

- project-state;
- docs-governance;
- schemas;
- TCR;
- quality gate.

### Pregunta 235

Como levanta API y Web UI?

La respuesta debe incluir:

- token;
- comandos;
- endpoints;
- troubleshooting.

### Pregunta 236

Como crea o evalua un proyecto nuevo desde una idea?

La respuesta debe incluir:

- idea;
- workspace;
- templates;
- readiness.

### Pregunta 237

Como ejecuta onboarding bootstrap?

La respuesta debe incluir:

- dry-run;
- execute;
- reportes.

### Pregunta 238

Como interpreta readiness preview?

La respuesta debe incluir:

- pending;
- warning;
- blockers;
- next steps.

### Pregunta 239

Como genera reportes?

La respuesta debe incluir:

- comandos;
- rutas;
- schemas.

### Pregunta 240

Como sabe si una accion esta bloqueada, en dry-run o permitida?

La respuesta debe incluir:

- policy;
- findings;
- UI;
- CLI.

### Pregunta 241

Como prepara un paquete de evidencia para revision?

La respuesta debe incluir:

- ZIP;
- logs;
- reports;
- checksums.

### Pregunta 242

Usando la idea "Sistema agent-assisted de ventas e inventario para microemprendimientos locales", como se modela el proyecto piloto?

La respuesta debe incluir:

- alcance;
- usuarios;
- requerimientos;
- limites.

### Pregunta 243

Que documentos iniciales genera DevPilot para ese caso piloto?

La respuesta debe incluir:

- templates;
- outputs;
- evidencias.

### Pregunta 244

Que estandares aplica DevPilot al caso piloto?

La respuesta debe incluir:

- MIPSoftware;
- MIASI;
- readiness.

### Pregunta 245

Que validaciones ejecuta DevPilot sobre el caso piloto?

La respuesta debe incluir:

- comandos;
- reportes;
- resultados esperados.

### Pregunta 246

Que gaps reporta DevPilot para el caso piloto?

La respuesta debe incluir:

- gaps tecnicos;
- gaps de negocio;
- gaps documentales.

### Pregunta 247

Que tareas recomienda DevPilot para avanzar el caso piloto?

La respuesta debe incluir:

- backlog;
- prioridades;
- criterios de cierre.

### Pregunta 248

Que partes del desarrollo puede asistir hoy DevPilot y cuales siguen siendo manuales?

La respuesta debe incluir:

- capacidades actuales;
- limites;
- futuro.

## 22. Bloque S - Sintesis, compilacion y entrega final

### Pregunta 249

Construye una Capability Maturity Matrix completa.

La respuesta debe incluir:

- capacidad;
- estado;
- madurez;
- cobertura de pruebas;
- riesgo;
- evidencia.

### Pregunta 250

Identifica los 20 architectural hotspots principales.

La respuesta debe incluir:

- modulo;
- responsabilidad;
- dependencias;
- riesgo de cambio;
- impacto.

### Pregunta 251

Construye una matriz de riesgos residuales.

La respuesta debe incluir:

- riesgo;
- severidad;
- probabilidad;
- mitigacion;
- owner sugerido.

### Pregunta 252

Construye una matriz de comandos operativos principales.

La respuesta debe incluir:

- comando;
- proposito;
- salida;
- cuando usarlo;
- riesgo.

### Pregunta 253

Construye una matriz de reportes y evidencias.

La respuesta debe incluir:

- reporte;
- ruta;
- schema;
- generador;
- consumidor.

### Pregunta 254

Construye una matriz de documentos canonicos.

La respuesta debe incluir:

- documento;
- owner;
- estado;
- source-of-truth;
- pruebas asociadas.

### Pregunta 255

Construye una matriz de no-go gates.

La respuesta debe incluir:

- gate;
- estado;
- evidencia;
- riesgo mitigado.

### Pregunta 256

Construye una matriz de interfaces.

La respuesta debe incluir:

- CLI;
- API;
- UI;
- ApplicationService;
- estado.

### Pregunta 257

Compila todas las respuestas anteriores en un informe de onboarding final por capitulos.

La respuesta debe incluir:

- indice;
- resumen ejecutivo;
- cuerpo tecnico;
- anexos;
- matrices.

### Pregunta 258

Genera una version ejecutiva corta del onboarding report.

La respuesta debe incluir:

- maximo 6 parrafos;
- sin jerga excesiva;
- estado real y limites.

### Pregunta 259

Genera una version tecnica profunda para arquitectos/desarrolladores.

La respuesta debe incluir:

- arquitectura;
- flujos;
- modulos;
- riesgos;
- roadmap.

### Pregunta 260

Genera una guia de continuidad para el siguiente desarrollador.

La respuesta debe incluir:

- como levantar entorno;
- que leer primero;
- que comandos correr;
- que no tocar;
- que implementar despues.

## 23. Recomendacion final de compilacion

Cuando todas las preguntas hayan sido respondidas, el informe final deberia
organizarse asi:

```text
1. Resumen ejecutivo.
2. Identidad y vision de producto.
3. Estado actual y declaracion production-ready-local.
4. Arquitectura real.
5. Arquitectura objetivo.
6. Modelo de dominio.
7. Runtime y flujos de ejecucion.
8. Workspace y onboarding.
9. Capacidades funcionales.
10. MIASI, agentes y politicas.
11. Seguridad y no-go gates.
12. Schemas, validators y evidence model.
13. Quality gates y testing.
14. UI/API local.
15. Observabilidad y operacion.
16. Release y reproducibilidad.
17. Gap analysis.
18. Roadmap recomendado.
19. Guia de operador.
20. Caso piloto.
21. Riesgos residuales.
22. Anexos de evidencia.
```

## 24. Regla de calidad para aceptar el informe final

El informe final solo debe considerarse completo si cumple estas condiciones:

```text
- Cada afirmacion importante tiene evidencia.
- Cada capacidad tiene estado de madurez.
- Cada claim esta delimitado.
- Cada riesgo tiene mitigacion.
- Cada gap tiene prioridad.
- Cada comando critico tiene salida esperada.
- Cada documento canonico relevante esta citado por ruta.
- Cada modulo critico esta explicado.
- Cada interfaz relevante esta cubierta.
- El reporte distingue claramente producto actual vs producto objetivo.
```

