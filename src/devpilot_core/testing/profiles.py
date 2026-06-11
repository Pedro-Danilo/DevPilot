from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_TEST_PROFILES_PATH = Path(".devpilot/testing/test_profiles.json")

DEFAULT_TEST_PROFILES: dict[str, Any] = {
    "schema_version": "1.0",
    "created_by": "FUNC-SPRINT-32",
    "description": "Controlled pytest profiles for DevPilot tests.run. Profiles are fixed; CLI users cannot pass arbitrary command args.",
    "profiles": [
        {
            "profile_id": "smoke",
            "description": "Very small synthetic smoke test used to validate the controlled tests.run pipeline.",
            "pytest_args": ["-q", "tests/fixtures/smoke_pytest_project"],
            "cwd": ".",
            "timeout_seconds": 60,
        },
        {
            "profile_id": "unit",
            "description": "Focused local unit verification for CLI/policy core without running the full suite.",
            "pytest_args": ["-q", "tests/test_cli_core.py", "tests/test_policy_engine.py"],
            "cwd": ".",
            "timeout_seconds": 120,
        },
        {
            "profile_id": "all",
            "description": "Full local pytest suite. This can execute project tests and should remain approval-gated.",
            "pytest_args": ["-q"],
            "cwd": ".",
            "timeout_seconds": 120,
        },
    ],
}


@dataclass(frozen=True)
class TestProfile:
    """One fixed tests.run profile backed by pytest and SafeSubprocessRunner."""

    profile_id: str
    description: str
    pytest_args: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: int = 60

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TestProfile":
        return cls(
            profile_id=str(payload.get("profile_id", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            pytest_args=tuple(str(item) for item in payload.get("pytest_args", []) if str(item).strip()),
            cwd=str(payload.get("cwd", ".") or ".").strip() or ".",
            timeout_seconds=int(payload.get("timeout_seconds", 60)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "description": self.description,
            "pytest_args": list(self.pytest_args),
            "cwd": self.cwd,
            "timeout_seconds": self.timeout_seconds,
        }


class TestProfileRegistry:
    """Load fixed local pytest profiles for tests.run.

    FUNC-SPRINT-32 deliberately makes profiles data-driven but not user-driven:
    users select a profile; they do not provide arbitrary subprocess arguments.
    """

    def __init__(self, root: Path, *, path: str | Path | None = None) -> None:
        self.root = root.resolve()
        self.path = self._resolve_path(path or DEFAULT_TEST_PROFILES_PATH)
        self._profiles = self._load_profiles()

    @property
    def relative_path(self) -> str:
        try:
            return str(self.path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(self.path).replace("\\", "/")

    def get(self, profile_id: str) -> TestProfile | None:
        key = profile_id.strip()
        return self._profiles.get(key)

    def list(self) -> list[TestProfile]:
        return [self._profiles[key] for key in sorted(self._profiles)]

    def unknown_profile_result(self, profile_id: str) -> CommandResult:
        return CommandResult(
            command="tests run",
            ok=False,
            exit_code=ExitCode.BLOCK,
            message="tests.run blocked an unknown test profile.",
            data={
                "summary": {
                    "profile": profile_id,
                    "known_profiles": sorted(self._profiles),
                    "profiles_total": len(self._profiles),
                    "blocked": True,
                    "preliminary": True,
                },
                "profiles": [profile.to_dict() for profile in self.list()],
                "config_path": self.relative_path,
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=[
                Finding(
                    id="TESTS_RUN_UNKNOWN_PROFILE",
                    message="Requested tests.run profile is not configured in the local test profile registry.",
                    severity=Severity.BLOCK,
                    metadata={"profile": profile_id, "config_path": self.relative_path},
                )
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "profiles_total": len(self._profiles),
            "profiles": [profile.to_dict() for profile in self.list()],
            "fallback_used": not self.path.exists(),
        }

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _load_profiles(self) -> dict[str, TestProfile]:
        payload = DEFAULT_TEST_PROFILES
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    payload = loaded
            except json.JSONDecodeError:
                payload = DEFAULT_TEST_PROFILES
        profiles: dict[str, TestProfile] = {}
        for item in payload.get("profiles", []):
            if not isinstance(item, dict):
                continue
            profile = TestProfile.from_dict(item)
            if profile.profile_id and profile.pytest_args and profile.timeout_seconds > 0:
                profiles[profile.profile_id] = profile
        if not profiles:
            for item in DEFAULT_TEST_PROFILES["profiles"]:
                profile = TestProfile.from_dict(item)
                profiles[profile.profile_id] = profile
        return profiles
