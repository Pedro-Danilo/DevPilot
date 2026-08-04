from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.policy import PathGuard, PolicyEffect, configured_external_workspace_roots
from devpilot_core.workspace.registry_v2 import MultiworkspaceRegistryV2, WorkspaceRegistryV2Options

UI_WORKSPACE_REGISTRY_ENV = "DEVPILOT_UI_WORKSPACE_REGISTRY_PATH"
UI_ACTIVE_WORKSPACE_ROOT_ENV = "DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT"


@dataclass(frozen=True)
class UiWorkspaceContext:
    """Resolved read-only platform/workspace context for API and Web UI surfaces."""

    platform_root: Path
    mode: str = "platform"
    configured: bool = False
    valid: bool = True
    registry_path: Path | None = None
    active_workspace_id: str | None = None
    active_workspace_root: Path | None = None
    reports_root: Path | None = None
    traces_root: Path | None = None
    project_file: Path | None = None
    findings: tuple[Finding, ...] = field(default_factory=tuple)

    @property
    def effective_workspace_root(self) -> Path:
        return self.active_workspace_root or self.platform_root

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "configured": self.configured,
            "valid": self.valid,
            "platform_root": _display(self.platform_root),
            "registry_path": _display(self.registry_path) if self.registry_path else None,
            "active_workspace_id": self.active_workspace_id,
            "active_workspace_root": _display(self.active_workspace_root) if self.active_workspace_root else None,
            "effective_workspace_root": _display(self.effective_workspace_root),
            "reports_root": _display(self.reports_root) if self.reports_root else _display(self.platform_root / "outputs" / "reports"),
            "traces_root": _display(self.traces_root) if self.traces_root else _display(self.platform_root / "outputs" / "traces"),
            "project_file": _display(self.project_file) if self.project_file else _display(self.platform_root / ".devpilot" / "project.yaml"),
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
        }


class UiWorkspaceContextResolver:
    """Resolve an optional external active workspace without weakening PathGuard.

    The API remains platform-rooted. A workspace context is accepted only when:
    - an explicit registry path or active root is configured through environment;
    - the path is permitted by DEVPILOT_ALLOWED_WORKSPACE_ROOTS;
    - registry v2 validation and root containment checks pass;
    - reports/traces/project paths remain inside the selected workspace root.

    Invalid configuration fails safe to a marked-invalid context. Callers may keep
    platform diagnostics available, but must expose the findings instead of
    silently claiming an active project workspace.
    """

    def __init__(self, platform_root: Path) -> None:
        self.platform_root = Path(platform_root).resolve()
        self.path_guard = PathGuard(
            self.platform_root,
            allowed_external_roots=configured_external_workspace_roots(),
        )

    def resolve(self) -> UiWorkspaceContext:
        registry_raw = os.environ.get(UI_WORKSPACE_REGISTRY_ENV, "").strip()
        active_root_raw = os.environ.get(UI_ACTIVE_WORKSPACE_ROOT_ENV, "").strip()
        if registry_raw:
            return self._from_registry(Path(registry_raw))
        if active_root_raw:
            return self._from_active_root(Path(active_root_raw))
        return UiWorkspaceContext(platform_root=self.platform_root)

    def _from_registry(self, registry_path: Path) -> UiWorkspaceContext:
        registry_path = self._absolute(registry_path)
        findings: list[Finding] = []
        decision = self.path_guard.evaluate(registry_path, action="read")
        if decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(
                Finding(
                    "UI_WORKSPACE_REGISTRY_PATH_REJECTED",
                    decision.reason,
                    Severity.WARNING,
                    path=decision.subject,
                    metadata=decision.metadata,
                )
            )
            return self._invalid("configured-registry", registry_path=registry_path, findings=findings)
        if not registry_path.is_file():
            findings.append(
                Finding(
                    "UI_WORKSPACE_REGISTRY_MISSING",
                    "Configured UI workspace registry does not exist; platform context remains active.",
                    Severity.WARNING,
                    path=_display(registry_path),
                )
            )
            return self._invalid("configured-registry", registry_path=registry_path, findings=findings)

        result = MultiworkspaceRegistryV2(
            self.platform_root,
            options=WorkspaceRegistryV2Options(registry_path=str(registry_path)),
        ).validate()
        if not result.ok:
            findings.extend(_as_context_warnings(result.findings))
            return self._invalid("configured-registry", registry_path=registry_path, findings=findings)

        registry = result.data.get("registry") if isinstance(result.data, dict) else None
        registry = registry if isinstance(registry, dict) else {}
        active_id = str(registry.get("active_workspace_id") or "").strip()
        workspaces = registry.get("workspaces") if isinstance(registry.get("workspaces"), list) else []
        active = next(
            (
                item
                for item in workspaces
                if isinstance(item, dict) and str(item.get("workspace_id") or "").strip() == active_id
            ),
            None,
        )
        if not active:
            findings.append(
                Finding(
                    "UI_ACTIVE_WORKSPACE_NOT_FOUND",
                    "Configured registry has no active workspace entry; platform context remains active.",
                    Severity.WARNING,
                    path=_display(registry_path),
                    metadata={"active_workspace_id": active_id or None},
                )
            )
            return self._invalid("configured-registry", registry_path=registry_path, findings=findings)

        root = self._absolute(Path(str(active.get("root_path") or ".")))
        return self._build_context(
            mode="configured-registry",
            registry_path=registry_path,
            active_workspace_id=active_id,
            active_workspace_root=root,
            reports_path=str(active.get("reports_path") or "outputs/reports"),
            traces_path=str(active.get("traces_path") or "outputs/traces"),
            project_path=str(active.get("project_file") or ".devpilot/project.yaml"),
            findings=findings,
        )

    def _from_active_root(self, active_root: Path) -> UiWorkspaceContext:
        root = self._absolute(active_root)
        return self._build_context(
            mode="configured-root",
            registry_path=None,
            active_workspace_id=root.name,
            active_workspace_root=root,
            reports_path="outputs/reports",
            traces_path="outputs/traces",
            project_path=".devpilot/project.yaml",
            findings=[],
        )

    def _build_context(
        self,
        *,
        mode: str,
        registry_path: Path | None,
        active_workspace_id: str,
        active_workspace_root: Path,
        reports_path: str,
        traces_path: str,
        project_path: str,
        findings: list[Finding],
    ) -> UiWorkspaceContext:
        root_decision = self.path_guard.evaluate(active_workspace_root, action="read")
        if root_decision.effect in {PolicyEffect.BLOCK, PolicyEffect.DENY}:
            findings.append(
                Finding(
                    "UI_ACTIVE_WORKSPACE_ROOT_REJECTED",
                    root_decision.reason,
                    Severity.WARNING,
                    path=root_decision.subject,
                    metadata=root_decision.metadata,
                )
            )
            return self._invalid(mode, registry_path=registry_path, findings=findings)

        reports_root = self._inside(active_workspace_root, reports_path, "reports", findings)
        traces_root = self._inside(active_workspace_root, traces_path, "traces", findings)
        project_file = self._inside(active_workspace_root, project_path, "project", findings)
        if reports_root is None or traces_root is None or project_file is None:
            return self._invalid(mode, registry_path=registry_path, findings=findings)

        findings.append(
            Finding(
                "UI_WORKSPACE_CONTEXT_RESOLVED",
                "UI workspace context resolved from an explicit, PathGuard-approved local source.",
                Severity.INFO,
                path=_display(active_workspace_root),
                metadata={
                    "mode": mode,
                    "active_workspace_id": active_workspace_id,
                    "registry_path": _display(registry_path) if registry_path else None,
                },
            )
        )
        return UiWorkspaceContext(
            platform_root=self.platform_root,
            mode=mode,
            configured=True,
            valid=True,
            registry_path=registry_path,
            active_workspace_id=active_workspace_id,
            active_workspace_root=active_workspace_root,
            reports_root=reports_root,
            traces_root=traces_root,
            project_file=project_file,
            findings=tuple(findings),
        )

    def _inside(self, root: Path, value: str, label: str, findings: list[Finding]) -> Path | None:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            findings.append(
                Finding(
                    "UI_WORKSPACE_CONTEXT_PATH_ESCAPE_REJECTED",
                    f"Configured {label} path escapes the active workspace root; platform context remains active.",
                    Severity.WARNING,
                    path=_display(candidate),
                    metadata={"workspace_root": _display(root), "label": label},
                )
            )
            return None
        return candidate

    def _absolute(self, value: Path) -> Path:
        return (value if value.is_absolute() else self.platform_root / value).resolve()

    def _invalid(self, mode: str, *, registry_path: Path | None, findings: list[Finding]) -> UiWorkspaceContext:
        return UiWorkspaceContext(
            platform_root=self.platform_root,
            mode=mode,
            configured=True,
            valid=False,
            registry_path=registry_path,
            findings=tuple(findings),
        )


def _display(path: Path | None) -> str:
    return str(path).replace("\\", "/") if path is not None else ""


def _as_context_warnings(findings: list[Finding]) -> list[Finding]:
    return [
        Finding(
            id=f"UI_CONTEXT_{finding.id}_REJECTED",
            message=finding.message,
            severity=Severity.WARNING,
            path=finding.path,
            metadata={**finding.metadata, "source_severity": finding.severity.value},
        )
        for finding in findings
    ]
