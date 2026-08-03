from __future__ import annotations

from dataclasses import dataclass, field
import os
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


def configured_external_workspace_roots() -> tuple[Path, ...]:
    """Return explicit external workspace roots from DEVPILOT_ALLOWED_WORKSPACE_ROOTS.

    The variable uses the host path separator (``;`` on Windows). Empty or
    relative entries are ignored so the boundary cannot silently broaden.
    """

    raw = os.environ.get("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", "")
    roots: list[Path] = []
    for item in raw.split(os.pathsep):
        item = item.strip()
        if not item:
            continue
        candidate = Path(item)
        if not candidate.is_absolute():
            continue
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


class PathGuard:
    """Guard for root-constrained filesystem access.

    PathGuard enforces the DevPilot local-first boundary: no path may escape the
    project root, destructive actions are blocked by default and sensitive repo
    internals are denied. The guard does not perform filesystem writes; it only
    evaluates a requested action/path pair.
    """

    def __init__(
        self,
        root: Path,
        *,
        policy: PathPolicy | None = None,
        allowed_external_roots: tuple[Path, ...] = (),
    ) -> None:
        self.root = root.resolve()
        self.policy = policy or PathPolicy()
        self.allowed_external_roots = tuple(Path(item).resolve() for item in allowed_external_roots)

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
        boundary_root = self.root
        external_boundary = False
        try:
            resolved.relative_to(self.root)
        except ValueError:
            matching_external_root = next(
                (item for item in self.allowed_external_roots if _is_relative_to(resolved, item)),
                None,
            )
            if matching_external_root is None:
                return PolicyDecision(
                    effect=PolicyEffect.BLOCK,
                    reason="PathGuard blocked a path outside the DevPilot workspace root and explicit external workspace roots.",
                    guard="PathGuard",
                    rule_id="PATHGUARD_OUTSIDE_ROOT",
                    subject=raw,
                    metadata={
                        "action": action_normalized,
                        "allowed_external_roots": [str(item) for item in self.allowed_external_roots],
                    },
                )
            boundary_root = matching_external_root
            external_boundary = True

        subject = _relative(resolved, boundary_root)

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
            if not external_boundary and first_part not in self.policy.write_allowed_prefixes:
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
            reason=(
                "PathGuard allowed the requested path/action inside an explicit external workspace root."
                if external_boundary
                else "PathGuard allowed the requested path/action."
            ),
            guard="PathGuard",
            rule_id="PATHGUARD_EXTERNAL_WORKSPACE_PASS" if external_boundary else "PATHGUARD_PASS",
            subject=subject,
            metadata={
                "action": action_normalized,
                "boundary_root": str(boundary_root),
                "external_workspace_boundary": external_boundary,
            },
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
