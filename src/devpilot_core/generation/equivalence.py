from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from .contracts import canonical_sha256


class EquivalenceMode(str, Enum):
    EXACT_HASH = "exact-hash"
    STRUCTURAL = "structural"
    SEMANTIC_PROJECTION = "semantic-projection"


@dataclass(frozen=True)
class EquivalenceContract:
    contract_id: str
    mode: EquivalenceMode
    ignored_paths: tuple[str, ...] = ()
    unordered_paths: tuple[str, ...] = ()
    normalize_line_endings: bool = True

    def __post_init__(self) -> None:
        if not str(self.contract_id or "").strip():
            raise ValueError("contract_id must be non-empty")
        if self.mode == EquivalenceMode.EXACT_HASH and (self.ignored_paths or self.unordered_paths):
            raise ValueError("exact-hash contract cannot ignore/reorder paths")


@dataclass(frozen=True)
class EquivalenceResult:
    contract_id: str
    mode: EquivalenceMode
    equivalent: bool
    baseline_sha256: str
    candidate_sha256: str
    drift_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "mode": self.mode.value,
            "equivalent": self.equivalent,
            "baseline_sha256": self.baseline_sha256,
            "candidate_sha256": self.candidate_sha256,
            "drift_paths": list(self.drift_paths),
        }


class DeterministicEquivalenceHarness:
    """Compare deterministic behavior without making prose snapshots universal."""

    def compare(
        self,
        *,
        baseline: Any,
        candidate: Any,
        contract: EquivalenceContract,
        projector: Callable[[Any], Any] | None = None,
    ) -> EquivalenceResult:
        if contract.mode == EquivalenceMode.EXACT_HASH:
            left = baseline
            right = candidate
        elif contract.mode == EquivalenceMode.STRUCTURAL:
            left = self._normalize(baseline, contract, path="")
            right = self._normalize(candidate, contract, path="")
        else:
            if projector is None:
                raise ValueError("semantic-projection equivalence requires a projector")
            left = self._normalize(projector(baseline), contract, path="")
            right = self._normalize(projector(candidate), contract, path="")
        left_hash = canonical_sha256(left)
        right_hash = canonical_sha256(right)
        drift = tuple(self._diff(left, right, path="")[:50])
        return EquivalenceResult(
            contract_id=contract.contract_id,
            mode=contract.mode,
            equivalent=left_hash == right_hash,
            baseline_sha256=left_hash,
            candidate_sha256=right_hash,
            drift_paths=drift,
        )

    def _normalize(self, value: Any, contract: EquivalenceContract, *, path: str) -> Any:
        if path and path in contract.ignored_paths:
            return "<IGNORED>"
        if isinstance(value, str):
            return value.replace("\r\n", "\n").replace("\r", "\n") if contract.normalize_line_endings else value
        if isinstance(value, Mapping):
            return {
                str(key): self._normalize(item, contract, path=f"{path}.{key}" if path else str(key))
                for key, item in sorted(value.items(), key=lambda row: str(row[0]))
                if (f"{path}.{key}" if path else str(key)) not in contract.ignored_paths
            }
        if isinstance(value, (list, tuple)):
            items = [self._normalize(item, contract, path=f"{path}[]") for item in value]
            if path in contract.unordered_paths:
                return sorted(items, key=canonical_sha256)
            return items
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return self._normalize(value.to_dict(), contract, path=path)
        return value

    def _diff(self, left: Any, right: Any, *, path: str) -> list[str]:
        if type(left) is not type(right):
            return [path or "$type"]
        if isinstance(left, dict):
            findings: list[str] = []
            for key in sorted(set(left) | set(right)):
                child = f"{path}.{key}" if path else str(key)
                if key not in left or key not in right:
                    findings.append(child)
                else:
                    findings.extend(self._diff(left[key], right[key], path=child))
            return findings
        if isinstance(left, list):
            findings: list[str] = []
            if len(left) != len(right):
                findings.append(f"{path}.length" if path else "$length")
            for index, (lval, rval) in enumerate(zip(left, right)):
                findings.extend(self._diff(lval, rval, path=f"{path}[{index}]"))
            return findings
        return [] if left == right else [path or "$value"]
