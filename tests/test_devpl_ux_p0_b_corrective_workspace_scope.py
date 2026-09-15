from __future__ import annotations

import os
from pathlib import Path

import pytest

from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
from devpilot_core.application.recovery_service import RecoveryApplicationService
from devpilot_core.application.reconciliation_service import ReconciliationApplicationService
from devpilot_core.recovery.service import RecoveryStateError
from devpilot_core.reconciliation.service import ReconciliationStateError


def _write_project(root: Path, project_id: str = "devpilot-local") -> None:
    project_dir = root / ".devpilot"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.yaml").write_text(
        'project:\n  id: "' + project_id + '"\n  name: "DevPilot Local"\n',
        encoding="utf-8",
    )


def test_active_root_uses_project_id_as_canonical_workspace_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform = tmp_path / "DevPilot_Local"
    platform.mkdir()
    _write_project(platform)
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(platform))
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(platform))
    context = UiWorkspaceContextResolver(platform).resolve()
    assert context.valid is True
    assert context.active_workspace_id == "devpilot-local"
    assert context.active_workspace_root == platform.resolve()
    assert any(f.id == "UI_ACTIVE_WORKSPACE_ID_CANONICALIZED" for f in context.findings)


def test_scope_authority_uses_canonical_project_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platform = tmp_path / "DevPilot_Local"
    platform.mkdir()
    _write_project(platform)
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(platform))
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(platform))
    context = UiWorkspaceContextResolver(platform).resolve()
    assert context.active_workspace_id == "devpilot-local"

    recovery = RecoveryApplicationService(platform)
    reconciliation = ReconciliationApplicationService(platform)
    recovery._require_scope(["devpilot-local"])
    reconciliation._require_scope(["devpilot-local"])
    with pytest.raises(RecoveryStateError):
        recovery._require_scope(["some-other-workspace"])
    with pytest.raises(ReconciliationStateError):
        reconciliation._require_scope(["some-other-workspace"])


def test_project_status_keeps_primary_projection_when_auxiliaries_fail() -> None:
    source = (
        Path(__file__).parents[1]
        / "ui"
        / "web"
        / "src"
        / "pages"
        / "ProjectStatusView.ts"
    ).read_text(encoding="utf-8")
    assert "Promise.allSettled" in source
    assert "unavailable-nonblocking" in source
    assert "const response = await api.projectStatus()" in source
