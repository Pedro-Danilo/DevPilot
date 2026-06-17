---
title: "ADR-0015 — Estrategia de instalación local e installer preliminar"
doc_id: "DEVPL-ADR-0015"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-82"
updated: "2026-06-17"
source_repo: "repo_DevPilot_Local_104.zip"
source_backlog: "docs/devpilot_backlog_fase_G_productizacion_release.md"
decision_scope: "local_installation_strategy_preliminary_installer"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_82"
operationalized_by: "FUNC-SPRINT-82"
---

# ADR-0015 — Estrategia de instalación local e installer preliminar

## Estado

`approved` y operacionalizada por `FUNC-SPRINT-82 — Estrategia de instalación e installer preliminar`.

Esta ADR es una decisión arquitectónica de primera versión. Define cómo DevPilot debe instalarse localmente mientras se evita auto-update, publicación remota, servicios persistentes y privilegios elevados por defecto.

## Contexto

Fase G está convirtiendo DevPilot en un producto local liberable. Los sprints previos ya agregaron release policy, quality gate, CI scaffolding, release manifest, changelog, packaging, SBOM, checksums y release verification.

El siguiente riesgo arquitectónico es instalar DevPilot de forma insegura o ambigua. Un instalador prematuro podría:

- requerir permisos elevados;
- instalar servicios persistentes;
- depender de red sin alternativa local;
- duplicar la Web UI local con un desktop shell inmaduro;
- ocultar mutaciones del sistema.

## Decisión

DevPilot adopta una estrategia de instalación local en cuatro rutas:

1. `editable`: ruta recomendada para desarrollo.
2. `wheel`: ruta recomendada para release candidate local.
3. `zip`: ruta soportada para auditoría y distribución fuente limpia.
4. `desktop-bridge`: ruta documentada para un futuro shell desktop, sin implementarlo en este sprint.

`FUNC-SPRINT-82` implementa solo un comando `install plan` en modo dry-run/plan-only. El comando no instala paquetes, no crea entornos virtuales, no llama red, no publica, no despliega, no firma, no etiqueta Git y no instala servicios.

## Alternativas consideradas

| Alternativa | Veredicto | Razón |
|---|---|---|
| Instalar directamente desde CLI | Rechazada para Sprint 82 | Introduce mutaciones locales y riesgo operacional. |
| Solo documentar sin comando | Rechazada | Menor trazabilidad y menos evidencia ejecutable. |
| Crear instalador desktop ahora | Rechazada | Fase F dejó Desktop diferido; Web UI local es la ruta visual vigente. |
| Usar herramienta externa de packaging | Diferida | Aumenta dependencias y complejidad antes del smoke install real. |

## Consecuencias

Positivas:

- instalación repetible documentada;
- relación clara entre editable/wheel/ZIP/Desktop bridge;
- sin privilegios elevados por defecto;
- sin servicios persistentes;
- sin dependencia obligatoria de red;
- evidencia regenerable con `outputs/reports/install_plan.*`.

Negativas o limitaciones:

- no ejecuta instalación real;
- no prueba upgrade;
- no prueba rollback;
- no firma instaladores;
- no construye desktop installer.

## Criterios de aplicación

Toda futura capacidad de instalación debe respetar:

- workspace resuelto antes de operar;
- dry-run por defecto cuando haya mutación;
- no privilegios elevados salvo ADR explícita;
- no servicios persistentes salvo ADR explícita;
- evidencia JSON/Markdown;
- pruebas de instalación, upgrade y rollback antes de considerarse producción industrial.

## Relación con Fase F

La estrategia mantiene la decisión Web UI local web-first. Un futuro desktop shell debe envolver la API/Web UI o integrarse con ellas sin duplicar lógica de negocio ni saltarse el core.
