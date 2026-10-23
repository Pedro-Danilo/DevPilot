---
doc_id: MP132-UI-FIRST-PILOT-B-179
status: OWNER_DECISION_ADOPTED_PROGRAM_AMENDMENT
approved: 2026-10-16
baseline: 735ecfd82e9604a4755fd7d4e7c386976984ed71
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Adenda 179 — Pilot B UI-first de bootstrap a release

Esta es una decisión transversal posterior y vigente. Prevalece para acciones futuras sobre redacciones históricas ambiguas sin borrar ni cambiar pruebas previas. Documento de origen: `DICTAMEN_UI_FIRST_MP132_179.md`. Decisión detallada: `ADR-MP-132-012.md`.

**Regla:** todo B0–B7, mismo workspace y toda orden de negocio/ingeniería/release nacen en la UI normal DevPilot. Operador humano usa PowerShell solo para ejecutar o auditar **DevPilot**, configurar parents de instalación preautorizados o inyectar correcciones del código de la plataforma; jamás para construir, completar, aprobar, comitear o desplegar el Pilot B. Un backend que ejecute herramientas tipadas ordenadas desde la UI sí cumple la regla.

**R02-05:** COR-178 se sustituye por COR-179: no capturar ID/nombre/target por terminal; obtener antes un snapshot del registro, crear por UI y detectar la única alta nueva, luego acreditar el mismo proyecto tras reinicio. Parent PathGuard acotado y autorizado no es target del piloto. Solo se autoriza R02-05; no se alteran R00–R02-04 ni se autoriza R02-06.

**M3–M6 y M10:** la evaluación verifica UI de pre-code, Planning, Git, release/deploy/rollback con receipts reales y el mismo ID. `PARTIAL/BLOCK` ante escapes manuales en el camino crítico. Release independiente de DevPilot significa autonomía del producto desplegado, no despliegue manual del Owner.

**Fuentes de verdad:** programa actualizado en este paquete y Git HEAD Windows `735ecfd82e9604a4755fd7d4e7c386976984ed71` hasta nueva validación. Futuras correcciones deben reconciliar las autoridades activas instaladas antes del cierre; los recibos/ADRs históricos se preservan como historia.

---

## Enmienda programática post-R02-06 · 187

La ruta `UI_FIRST_PILOT_B_V1` se extiende para **autoría Markdown de la etapa vigente**, decisión tecnológica, scaffold, planning de incrementos y aceptación integrada en Guided. «Laboratorio de modelos» sigue como herramienta diagnóstica optativa en Settings/Expert, no etapa obligatoria del workflow del Owner. Los candidatos L/E son documentos `.md` revisables con control local de cambios y feedback del mismo panel; ninguna acción exige terminal humana para escribir el proyecto. Las autorizaciones humanas se reservan para decisiones materiales (alcance/arquitectura/approval/apply/release), y los receipts/hash/readiness se verifican automáticamente.
