from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from devpilot_core.cli_models import CommandResult


@dataclass(frozen=True)
class ComponentExecutionEvent:
    component_key: str
    input_signature: str
    reused: bool


class QualityExecutionContext:
    """Ephemeral per-top-level-call component result reuse.

    The context is intentionally process-local and invocation-scoped.  It is not
    a persistent/global cache and therefore cannot reuse results across commits,
    processes or independent quality-gate invocations.
    """

    def __init__(self, *, source_identity: str) -> None:
        self.source_identity = str(source_identity)
        self._results: dict[tuple[str, str, str], CommandResult] = {}
        self._execution_counts: dict[str, int] = {}
        self._reuse_counts: dict[str, int] = {}
        self._events: list[ComponentExecutionEvent] = []

    def execute(
        self,
        component_key: str,
        runner: Callable[[], CommandResult],
        *,
        input_signature: str = "default",
    ) -> tuple[CommandResult, bool]:
        key = (self.source_identity, str(component_key), str(input_signature))
        if key in self._results:
            self._reuse_counts[component_key] = self._reuse_counts.get(component_key, 0) + 1
            self._events.append(ComponentExecutionEvent(component_key, input_signature, True))
            return self._results[key], True
        result = runner()
        self._results[key] = result
        self._execution_counts[component_key] = self._execution_counts.get(component_key, 0) + 1
        self._events.append(ComponentExecutionEvent(component_key, input_signature, False))
        return result, False

    def audit(self) -> dict[str, object]:
        duplicate_executions = {
            key: count for key, count in sorted(self._execution_counts.items()) if count > 1
        }
        return {
            "source_identity": self.source_identity,
            "components_executed_total": sum(self._execution_counts.values()),
            "components_reused_total": sum(self._reuse_counts.values()),
            "unique_components_executed": len(self._execution_counts),
            "duplicate_component_executions_total": sum(count - 1 for count in duplicate_executions.values()),
            "duplicate_component_executions": duplicate_executions,
            "execution_counts": dict(sorted(self._execution_counts.items())),
            "reuse_counts": dict(sorted(self._reuse_counts.items())),
            "events": [
                {
                    "component_key": event.component_key,
                    "input_signature": event.input_signature,
                    "reused": event.reused,
                }
                for event in self._events
            ],
        }
