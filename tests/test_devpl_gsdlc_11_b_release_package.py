from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from devpilot_core.application.release_package_service import ReleasePackageJobApplicationService
from devpilot_core.release.package_builder import PackageBuildBuilder, PackageBuildOptions
from devpilot_core.release.sbom import ReleaseSbomBuilder
from devpilot_core.schemas.validator import SchemaValidator


class Resolver:
    def __init__(self, root: Path): self.root = root
    def resolve(self):
        return SimpleNamespace(configured=True, valid=True, active_workspace_root=self.root, active_workspace_id="devpilot-local")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True).stdout.strip()


def init_minimal_git_project(tmp_path: Path) -> Path:
    root = tmp_path / "repo"; root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="devpilot-local"\nversion="0.1.0"\n', encoding="utf-8")
    state = root / ".devpilot/project_state.json"; state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"gsdlc_11_a_status":"CLOSED/PASS/WINDOWS-VALIDATED","gsdlc_11_b_authorized":True}), encoding="utf-8")
    git(root, "init"); git(root, "config", "user.email", "devpilot@test.local"); git(root, "config", "user.name", "DevPilot Test")
    git(root, "add", "."); git(root, "commit", "-m", "fixture")
    return root


def test_package_builder_repo_zip_is_byte_reproducible(tmp_path: Path):
    root = tmp_path / "src"; root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="devpilot-local"\nversion="0.1.0"\n', encoding="utf-8")
    (root / "a.txt").write_text("alpha\n", encoding="utf-8")
    first = PackageBuildBuilder(root, options=PackageBuildOptions(version="0.1.0", kind="repo-zip", execute=True)).build()
    assert first.ok
    artifact = root / "dist/release/devpilot-local-0.1.0-source.zip"
    h1 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    os.utime(root / "a.txt", None)
    second = PackageBuildBuilder(root, options=PackageBuildOptions(version="0.1.0", kind="repo-zip", execute=True)).build()
    assert second.ok
    h2 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert h1 == h2


def test_package_builder_blocks_included_symlink(tmp_path: Path):
    root = tmp_path / "src"; root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname="devpilot-local"\nversion="0.1.0"\n', encoding="utf-8")
    outside = tmp_path / "outside.txt"; outside.write_text("secret", encoding="utf-8")
    try:
        (root / "escape.txt").symlink_to(outside)
    except OSError:
        return
    result = PackageBuildBuilder(root, options=PackageBuildOptions(version="0.1.0", execute=False)).build()
    assert not result.ok
    assert any(f.id == "PACKAGE_UNSAFE_LINK_BLOCKED" for f in result.findings)


def test_release_package_plan_is_role_bound_and_stale_commit_fails_closed(tmp_path: Path):
    root = init_minimal_git_project(tmp_path)
    svc = ReleasePackageJobApplicationService(root, context_resolver=Resolver(root))
    denied = svc.plan(actor="dev", actor_roles=["developer"], workspace_scopes=["devpilot-local"])
    assert not denied.ok and any(f.id == "GSDLC11B_RELEASE_ROLE_BLOCK" for f in denied.findings)
    planned = svc.plan(actor="owner", actor_roles=["owner"], workspace_scopes=["devpilot-local"])
    assert planned.ok
    plan = planned.data["plan"]
    (root / "b.txt").write_text("next\n", encoding="utf-8"); git(root, "add", "b.txt"); git(root, "commit", "-m", "advance")
    executed = svc.execute(actor="owner", actor_roles=["owner"], workspace_scopes=["devpilot-local"], plan_id=plan["plan_id"], plan_hash=plan["plan_hash"])
    assert not executed.ok and any(f.id == "GSDLC11B_ARTIFACT_COMMIT_BINDING_BLOCK" for f in executed.findings)


def test_sbom_baseline_schema_accepts_current_builder_payload():
    root = Path(__file__).resolve().parents[1]
    result = ReleaseSbomBuilder(root).build()
    assert result.ok
    payload = result.data["sbom"]
    validation = SchemaValidator(root).validate_payload(schema="GSDLC11BSbomBaseline", payload=payload, instance_label="test-sbom")
    assert validation.ok
