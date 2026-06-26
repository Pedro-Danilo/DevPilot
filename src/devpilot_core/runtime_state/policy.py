from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.runtime_state.models import RuntimeStatePolicy

DEFAULT_RUNTIME_STATE_POLICY = Path(".devpilot/runtime_state_policy.json")


class RuntimeStatePolicyLoader:
    """Load the source-controlled runtime-state lifecycle policy.

    The loader is intentionally local-only and dependency-free. It validates only
    basic file loading; structural JSON schema validation remains owned by
    SchemaValidator and the POST-H-008-A contract.
    """

    def __init__(self, root: Path, policy_path: str | Path = DEFAULT_RUNTIME_STATE_POLICY) -> None:
        self.root = Path(root).resolve()
        self.policy_path = Path(policy_path)

    @property
    def resolved_policy_path(self) -> Path:
        return self.root / self.policy_path

    def load(self) -> RuntimeStatePolicy:
        payload = json.loads(self.resolved_policy_path.read_text(encoding="utf-8"))
        return RuntimeStatePolicy.from_dict(payload)
