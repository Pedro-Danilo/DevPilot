from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .models import SCHEMA_ID, SCHEMA_VERSION, WorkspaceEngineeringState, WorkspaceEngineeringStateError

CURRENT_SCHEMA_VERSION = SCHEMA_VERSION


class WorkspaceEngineeringStateMigrationError(WorkspaceEngineeringStateError):
    pass


class WorkspaceEngineeringStateMigrator:
    """Version gate for durable engineering state.

    DEVPL-GSDLC-01-A is the first persisted schema. Therefore v1 migration is
    intentionally an identity migration after typed validation. Future versions
    must add explicit, sequential migrations; unknown/newer versions fail closed.
    """

    supported_versions = (CURRENT_SCHEMA_VERSION,)

    def migrate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        data=deepcopy(dict(payload))
        version=str(data.get("schema_version") or "")
        if version != CURRENT_SCHEMA_VERSION:
            raise WorkspaceEngineeringStateMigrationError(
                f"unsupported WorkspaceEngineeringState schema_version={version!r}; supported={self.supported_versions}"
            )
        if str(data.get("schema_id") or "") != SCHEMA_ID:
            raise WorkspaceEngineeringStateMigrationError("WorkspaceEngineeringState schema_id mismatch")
        # Typed parse is the v1 identity migration validation gate.
        return WorkspaceEngineeringState.from_payload(data).to_payload()
