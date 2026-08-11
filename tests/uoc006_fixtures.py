from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

VALID_MD = '''---
doc_id: "UOC006-FIXTURE"
title: "UOC-006 fixture"
status: "draft"
version: "1.0.0"
owner: "owner"
updated: "2026-08-10"
approval: "pending"
---
# UOC-006 fixture
'''


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def find_approval_id(payload: Any) -> str:
    if isinstance(payload, dict):
        if payload.get("approval_id"):
            return str(payload["approval_id"])
        for value in payload.values():
            found = find_approval_id(value)
            if found:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = find_approval_id(value)
            if found:
                return found
    return ""


@pytest.fixture()
def uoc006_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    platform = tmp_path / "platform"
    workspace = tmp_path / "workspace"
    control = tmp_path / "control"
    platform.mkdir(); workspace.mkdir(); control.mkdir()
    shutil.copytree(PROJECT_ROOT / ".devpilot", platform / ".devpilot")
    shutil.copytree(PROJECT_ROOT / "docs" / "schemas", platform / "docs" / "schemas")
    # ApplicationBoundaryPolicy builds its operation catalog from platform source.
    # Keep the fixture isolated from the real checkout while exposing the exact
    # static source surfaces needed by that read-only inventory.
    shutil.copytree(PROJECT_ROOT / "src", platform / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(PROJECT_ROOT / "ui", platform / "ui", ignore=shutil.ignore_patterns("node_modules", "dist", "__pycache__", "*.pyc"))
    for candidate in (platform / ".devpilot").rglob("devpilot.db*"):
        if candidate.is_file():
            candidate.unlink()
    (workspace / ".devpilot").mkdir()
    (workspace / ".devpilot" / "project.yaml").write_text("project: uoc006-fixture\n", encoding="utf-8")
    (workspace / "docs").mkdir()

    def write_crlf(path: Path, text: str) -> None:
        # Reproduce Git for Windows checkout/worktree semantics even when the
        # test suite runs on Linux. The governed staging contract must compare
        # Git-canonical index content rather than raw worktree line endings.
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))

    write_crlf(workspace / "docs" / "review.md", VALID_MD + "baseline\n")
    git(workspace, "init", "-q")
    git(workspace, "config", "user.name", "Fixture User")
    git(workspace, "config", "user.email", "fixture@example.test")
    git(workspace, "config", "core.autocrlf", "true")
    git(workspace, "add", ".")
    git(workspace, "commit", "-qm", "fixture baseline")
    baseline = git(workspace, "rev-parse", "HEAD")
    write_crlf(workspace / "docs" / "review.md", VALID_MD + "reviewed change\n")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(workspace))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DEVPILOT_UOC006_CONTROL_ROOT", str(control))
    return {"platform": platform, "workspace": workspace, "control": control, "baseline": Path(baseline)}
