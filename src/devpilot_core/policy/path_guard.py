from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from devpilot_core.policy.decisions import PolicyDecision, PolicyEffect


@dataclass(frozen=True)
class PathPolicy:
    """Static path policy for the first deterministic PathGuard."""

    denied_prefixes: tuple[str, ...] = (".git", ".venv", "__pycache__", ".pytest_cache")
    denied_files: tuple[str, ...] = (".env", ".env.local", ".env.dev")
    write_allowed_prefixes: tuple[str, ...] = ("outputs", ".devpilot", "docs", "tests")
    destructive_actions: tuple[str, ...] = ("delete", "remove", "rm", "rmdir", "overwrite")
    metadata: dict[str, str] = field(default_factory=dict)


class PathGuard:
    """Guard for root-constrained filesystem access.

    PathGuard enforces the DevPilot local-first boundary: no path may escape the
    project root, destructive actions are blocked by default and sensitive repo
    internals are denied. The guard does not perform filesystem writes; it only
    evaluates a requested action/path pair.
    """

    def __init__(self, root: Path, *, policy: PathPolicy | None = None) -> None:
        self.root = root.resolve()
        self.policy = policy or PathPolicy()

    def evaluate(self, path: str | Path | None, *, action: str = "read") -> PolicyDecision:
        """Evaluate whether `action` is allowed for `path`."""

        action_normalized = action.strip().lower() or "read"
        if path is None or str(path).strip() == "":
            return PolicyDecision(
                effect=PolicyEffect.ALLOW,
                reason="No path was provided for PathGuard evaluation.",
                guard="PathGuard",
                rule_id="PATHGUARD_NO_PATH",
                metadata={"action": action_normalized},
            )

        raw = str(path).replace("\\", "/")
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        subject = _relative(resolved, self.root)

        try:
            resolved.relative_to(self.root)
        except ValueError:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="PathGuard blocked a path outside the DevPilot workspace root.",
                guard="PathGuard",
                rule_id="PATHGUARD_OUTSIDE_ROOT",
                subject=raw,
                metadata={"action": action_normalized},
            )

        if ".." in Path(raw).parts:
            return PolicyDecision(
                effect=PolicyEffect.WARN,
                reason="PathGuard normalized a path containing '..'; verify intent before execution.",
                guard="PathGuard",
                rule_id="PATHGUARD_PARENT_SEGMENT_NORMALIZED",
                subject=subject,
                metadata={"action": action_normalized},
            )

        path_parts = Path(subject).parts
        if path_parts and path_parts[0] in self.policy.denied_prefixes:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="PathGuard blocked access to a denied repository/internal directory.",
                guard="PathGuard",
                rule_id="PATHGUARD_DENIED_PREFIX",
                subject=subject,
                metadata={"action": action_normalized, "prefix": path_parts[0]},
            )

        if Path(subject).name in self.policy.denied_files:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="PathGuard blocked access to a denied secret/configuration file.",
                guard="PathGuard",
                rule_id="PATHGUARD_DENIED_FILE",
                subject=subject,
                metadata={"action": action_normalized},
            )

        if action_normalized in self.policy.destructive_actions:
            return PolicyDecision(
                effect=PolicyEffect.BLOCK,
                reason="PathGuard blocks destructive filesystem actions by default.",
                guard="PathGuard",
                rule_id="PATHGUARD_DESTRUCTIVE_ACTION_BLOCKED",
                subject=subject,
                metadata={"action": action_normalized},
            )

        if action_normalized in {"write", "create", "append"}:
            first_part = path_parts[0] if path_parts else ""
            if first_part not in self.policy.write_allowed_prefixes:
                return PolicyDecision(
                    effect=PolicyEffect.DENY,
                    reason="PathGuard denied write-like action outside approved writable prefixes.",
                    guard="PathGuard",
                    rule_id="PATHGUARD_WRITE_PREFIX_DENIED",
                    subject=subject,
                    metadata={"action": action_normalized, "allowed_prefixes": list(self.policy.write_allowed_prefixes)},
                )

        return PolicyDecision(
            effect=PolicyEffect.ALLOW,
            reason="PathGuard allowed the requested path/action.",
            guard="PathGuard",
            rule_id="PATHGUARD_PASS",
            subject=subject,
            metadata={"action": action_normalized},
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
