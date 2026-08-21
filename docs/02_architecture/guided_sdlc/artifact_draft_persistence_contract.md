---
doc_id: "DEVPL-GSDLC-04-B-ARTIFACT-DRAFT-PERSISTENCE-CONTRACT"
title: "GSDLC-04-B — Artifact draft persistence, MANUAL authoring and version history contract"
status: "implemented/ready-for-windows"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "pending_windows_validation_and_owner_adjudication"
---

# GSDLC-04-B — Artifact draft persistence contract

## 1. Propósito

Definir la autoridad, persistencia, concurrencia y límites de seguridad del editor MANUAL de Markdown/JSON introducido por GSDLC-04-B.

## 2. Autoridades

- Source aprobado: el archivo real del workspace activo, leído mediante `WorkspaceDocumentsApplicationService` y su `sha256` server-side.
- Draft: estado runtime local bajo `outputs/drafts/gsdlc_04_b/`; nunca es source aprobado ni evidence.
- Actor/rol/sesión: principal autenticado del servidor; el browser no puede autoasignarse autoridad.
- Apply al source: sigue perteneciendo al pipeline UOC-004/UOC-005 `plan → recheck → approval → atomic apply → verify`; 04-B no crea segundo writer.

## 3. Modelo runtime

Cada documento Markdown/JSON puede tener un record `ArtifactDraftStoreRecord` con `source_type=MANUAL`, `lifecycle_state=DRAFT`, `source_preimage_sha256`, commit base, actor/rol/sesión, revisiones inmutables y eventos de descarte. El store se valida con `SCHEMA-DEVPL-GSDLC-04-B-ARTIFACT-DRAFT-STORE-RECORD-V1`.

Persistencia física:

```text
outputs/drafts/gsdlc_04_b/<workspace-hash>/<document-hash>.json
```

`outputs/` es runtime, no source; se excluye de ZIPs limpios, fixtures y commits.

## 4. Operaciones

| Operación | Mutación runtime | Mutación source | Regla |
|---|---:|---:|---|
| GET draft | no | no | human session + workspace scope |
| GET history | no | no | historial resumido, sin promoción |
| SAVE/AUTOSAVE | sí | no | exact source preimage + expected revision |
| DISCARD | sí | no | desactiva draft, conserva history |
| RECOVER | sí | no | crea revisión nueva desde revisión histórica |

Autosave usa debounce UI de 1100 ms y es idempotente si el contenido no cambió.

## 5. Optimistic concurrency

Cada mutación exige dos preimágenes cuando corresponda:

1. `expected_source_sha256`: debe coincidir con el source leído actualmente.
2. `expected_revision_sha256`: debe coincidir con la revisión runtime activa.

Cualquier drift produce `BLOCK`; nunca se aplica last-write-wins silencioso. Si el source externo cambia, el draft queda en conflicto y debe revisarse antes de continuar.

## 6. Seguridad

- allowlist `.md`/`.json` y tamaño máximo 1 MiB;
- `SecretGuard` antes de persistir;
- store validado por JSON Schema y corrupción fail-closed;
- preview de contenido con DOM seguro (`textContent`/`createElement`), no raw HTML;
- human session obligatoria para las cinco rutas; legacy token no confiere autoridad;
- route/project scope heredado de GSDLC-03;
- sin red, API externa, shell libre, remote execution, connector write o plugin execution.

## 7. Integración con UOC-004/UOC-005

Para Markdown/JSON, `DocumentEditPlanner` consume el draft runtime gobernado mediante `setDraftContent`; `sessionStorage` deja de ser autoridad de draft. La compatibilidad heredada de `sessionStorage` queda limitada a YAML/YML en la superficie de planning histórica.

## 8. PASS/BLOCK

**PASS** si guardar/reiniciar/recuperar conserva el draft runtime, history es inmutable, el source aprobado permanece byte-identical durante save/autosave/discard/recover y los stale updates quedan bloqueados.

**BLOCK** si un draft sobrescribe source, si legacy token puede autorizar draft write, si se acepta XSS/raw HTML, si se ignora preimage hash, si se persiste un secreto o si un runtime DB/store entra al ZIP fuente.

## 9. Riesgos residuales

- La validación semántica/artifact-profile completa se integra en 04-D; 04-B ofrece JSON parse hints, no sustituye validators.
- La conciliación de edit/rename/delete externo con UX final pertenece a 04-E; 04-B bloquea por hash drift, pero no resuelve merges.
- El apply final al source conserva la UX/política de UOC-005 y evolucionará en 04-D con findings/approval/freeze.

## 10. Verificación

La guía operativa `GUIA_UNICA_IMPLEMENTACION_VALIDACION_DEVPL_GSDLC_04_B_v1_0_5.md` contiene los comandos Windows autoritativos. En 04-B está prohibido ejecutar full regression por rutina; solo focal, acumulativa, Test Impact y reconciliación.


### Runtime browser Windows

La validación browser 04-B usa obligatoriamente tres consolas separadas: control, API y UI. La API debe recibir un `DEVPILOT_API_TOKEN` explícito generado solo en memoria por el launcher Python; el secreto no se persiste ni se imprime. El browser continúa autorizado por sesión humana/RBAC para las rutas draft. El control de readiness y stop se ejecuta desde la consola de control mediante PIDs registrados, sin matar procesos por nombre. Para browser acceptance, el proceso API reemplaza cualquier lista heredada de raíces externas por el fixture disposable exacto, lo fija también como `DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT`, limpia la selección registry heredada y exige un precheck read-only de PathGuard + Project Entry dry-run + UI workspace context antes de abrir el navegador.
