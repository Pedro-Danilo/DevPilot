# DELETE_MANIFEST — FUNC-SPRINT-47

Eliminar del workspace versionable o del ZIP entregable si existen:

- `.devpilot/providers.yaml`: configuración local/operativa no versionable. Debe regenerarse localmente desde `.devpilot/providers.yaml.example` cuando se quiera habilitar Ollama o LM Studio.
- `PATCH_COMPONENTS_MANIFEST.txt`: artefacto temporal de empaquetado heredado de Sprint 46; no forma parte del producto DevPilot.

No eliminar `.devpilot/providers.yaml.example`: es el contrato versionado seguro y mantiene `ollama`/`lmstudio` deshabilitados por defecto.
