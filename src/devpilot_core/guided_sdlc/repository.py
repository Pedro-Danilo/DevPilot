from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .migration import WorkspaceEngineeringStateMigrator
from .models import WorkspaceEngineeringState, WorkspaceEngineeringStateError, contains_secret_like_material
from .registry_binding import WorkspaceBinding, WorkspaceBindingError, WorkspaceRegistryBindingResolver

_WORKSPACE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,256}$")


class WorkspaceEngineeringStateStoreError(RuntimeError):
    pass


class WorkspaceEngineeringStateConflict(WorkspaceEngineeringStateStoreError):
    pass


class WorkspaceEngineeringStateRepository:
    """Durable local JSON repository keyed by registered workspace_id.

    Default storage is platform-local `outputs/workspaces/<workspace_id>/`.
    `outputs/` is already excluded from product source control. The managed
    workspace receives no hidden DevPilot files from this repository.

    Writes are atomic temp-file + fsync + os.replace. Existing records require
    optimistic-concurrency sequence matching to prevent silent lost updates.
    """

    def __init__(
        self,
        platform_root: Path,
        *,
        store_root: Path | str = "outputs/workspaces",
        registry_path: Path | str = ".devpilot/workspaces/workspace_registry.json",
        resolver: WorkspaceRegistryBindingResolver | None = None,
        migrator: WorkspaceEngineeringStateMigrator | None = None,
    ) -> None:
        self.platform_root=Path(platform_root).resolve()
        raw=Path(store_root)
        self.store_root=(raw if raw.is_absolute() else self.platform_root/raw).resolve()
        self.resolver=resolver or WorkspaceRegistryBindingResolver(self.platform_root, registry_path=registry_path)
        self.migrator=migrator or WorkspaceEngineeringStateMigrator()
        self._assert_store_boundary()

    def state_path(self, workspace_id: str) -> Path:
        if not _WORKSPACE_ID_RE.fullmatch(workspace_id):
            raise WorkspaceEngineeringStateStoreError("invalid workspace_id for state path")
        path=self.store_root/workspace_id/"engineering_state.json"
        try:
            path.resolve().relative_to(self.store_root)
        except ValueError as exc:
            raise WorkspaceEngineeringStateStoreError("engineering state path escaped store_root") from exc
        self._reject_store_symlink(path.parent)
        return path

    def binding(self, workspace_id: str) -> WorkspaceBinding:
        try:
            return self.resolver.resolve(workspace_id)
        except WorkspaceBindingError as exc:
            raise WorkspaceEngineeringStateStoreError(str(exc)) from exc

    def exists(self, workspace_id: str) -> bool:
        self.binding(workspace_id)
        return self.state_path(workspace_id).is_file()

    def load(self, workspace_id: str) -> WorkspaceEngineeringState:
        binding=self.binding(workspace_id)
        path=self.state_path(workspace_id)
        if not path.is_file():
            raise KeyError(f"WorkspaceEngineeringState does not exist: {workspace_id}")
        try:
            payload=json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError,json.JSONDecodeError) as exc:
            raise WorkspaceEngineeringStateStoreError(f"engineering state is corrupt/unreadable: {exc}") from exc
        if not isinstance(payload,dict):
            raise WorkspaceEngineeringStateStoreError("engineering state JSON root must be an object")
        try:
            migrated=self.migrator.migrate(payload)
            state=WorkspaceEngineeringState.from_payload(migrated)
        except WorkspaceEngineeringStateError as exc:
            raise WorkspaceEngineeringStateStoreError(str(exc)) from exc
        self._assert_binding(state,binding)
        return state

    def save(self, state: WorkspaceEngineeringState, *, expected_sequence: int | None = None) -> Path:
        binding=self.binding(state.workspace_id)
        self._assert_binding(state,binding)
        payload=state.to_payload()
        secret_paths=contains_secret_like_material(payload)
        if secret_paths:
            raise WorkspaceEngineeringStateStoreError(f"secret-like material rejected: {secret_paths[:5]}")
        path=self.state_path(state.workspace_id)
        current_sequence: int | None=None
        if path.exists():
            current=self.load(state.workspace_id)
            current_sequence=current.sequence
            if expected_sequence is None:
                raise WorkspaceEngineeringStateConflict("expected_sequence is required when updating an existing engineering state")
            if expected_sequence != current_sequence:
                raise WorkspaceEngineeringStateConflict(
                    f"stale engineering state update: expected_sequence={expected_sequence} current_sequence={current_sequence}"
                )
            if state.sequence != current_sequence + 1:
                raise WorkspaceEngineeringStateConflict("successor state sequence must increment exactly by one")
        else:
            if expected_sequence not in {None,-1}:
                raise WorkspaceEngineeringStateConflict("initial state expected_sequence must be omitted or -1")
            if state.sequence != 0:
                raise WorkspaceEngineeringStateConflict("initial engineering state sequence must be zero")
        self._atomic_write(path,payload)
        return path

    def _atomic_write(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True,exist_ok=True)
        self._reject_store_symlink(path.parent)
        fd,tmp_name=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
        tmp=Path(tmp_name)
        try:
            with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
                json.dump(payload,handle,ensure_ascii=False,indent=2,sort_keys=True)
                handle.write("\n")
                handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp,path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        finally:
            tmp.unlink(missing_ok=True)

    def _assert_binding(self,state:WorkspaceEngineeringState,binding:WorkspaceBinding) -> None:
        if state.workspace_id != binding.workspace_id:
            raise WorkspaceEngineeringStateStoreError("state workspace_id does not match registry binding")
        if state.project_id != binding.project_id:
            raise WorkspaceEngineeringStateStoreError("state project_id does not match registry binding")
        if state.workspace_root_fingerprint != binding.root_fingerprint:
            raise WorkspaceEngineeringStateStoreError("state workspace root fingerprint does not match registered workspace")

    def _assert_store_boundary(self) -> None:
        # Store may be injected outside platform root for tests/installations, but
        # it must never resolve inside a registered managed workspace as a hidden
        # source file. The default is platform outputs/, already gitignored.
        default=(self.platform_root/"outputs"/"workspaces").resolve()
        if self.store_root == default:
            ignore=self.platform_root/".gitignore"
            if ignore.is_file() and "outputs/" not in ignore.read_text(encoding="utf-8-sig"):
                raise WorkspaceEngineeringStateStoreError("default engineering store is not protected by .gitignore outputs/")

    def _reject_store_symlink(self,path:Path) -> None:
        try:
            relative=path.resolve(strict=False).relative_to(self.store_root)
        except ValueError as exc:
            raise WorkspaceEngineeringStateStoreError("engineering store path escaped store_root") from exc
        current=self.store_root
        if current.exists() and current.is_symlink():
            raise WorkspaceEngineeringStateStoreError("engineering store root cannot be a symlink")
        for part in relative.parts:
            current=current/part
            if current.exists() and current.is_symlink():
                raise WorkspaceEngineeringStateStoreError(f"engineering store symlink component is forbidden: {current}")
