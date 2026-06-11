from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.execution import SafeSubprocessRunner
from devpilot_core.policy import PolicyEngine, PolicyRequest, load_cost_policy

from .profiles import TestProfile, TestProfileRegistry


class TestsRunTool:
    __test__ = False

    """Controlled MIASI tool for local pytest execution.

    FUNC-SPRINT-32 exposes `tests.run` as an approval-gated tool. It never
    accepts arbitrary shell commands: users choose a configured profile, then
    the tool evaluates policy/approval and delegates execution to
    SafeSubprocessRunner.
    """

    tool_id = "tests.run"
    action = "execute"

    def __init__(self, root: Path, *, profiles: TestProfileRegistry | None = None) -> None:
        self.root = root.resolve()
        self.profiles = profiles or TestProfileRegistry(self.root)

    def run(
        self,
        *,
        profile_id: str,
        approval_id: str | None,
        timeout_seconds: int | None = None,
    ) -> CommandResult:
        profile = self.profiles.get(profile_id)
        if profile is None:
            return self.profiles.unknown_profile_result(profile_id)

        policy_result = self._evaluate_policy(profile=profile, approval_id=approval_id)
        if not policy_result.ok:
            return self._blocked_by_policy(profile=profile, policy_result=policy_result, approval_id=approval_id)

        effective_timeout = timeout_seconds or profile.timeout_seconds
        command_args = [sys.executable, "-m", "pytest", *profile.pytest_args]
        execution_result = SafeSubprocessRunner(self.root).run(
            command_args,
            cwd=profile.cwd,
            timeout_seconds=effective_timeout,
        )
        return self._from_execution(
            profile=profile,
            approval_id=approval_id,
            timeout_seconds=effective_timeout,
            policy_result=policy_result,
            execution_result=execution_result,
        )

    def list_profiles(self) -> CommandResult:
        return CommandResult(
            command="tests profiles",
            ok=True,
            exit_code=ExitCode.PASS,
            message="tests.run profiles listed.",
            data={
                "summary": {
                    "profiles_total": len(self.profiles.list()),
                    "preliminary": True,
                },
                "profile_registry": self.profiles.to_dict(),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=[],
        )

    def _evaluate_policy(self, *, profile: TestProfile, approval_id: str | None) -> CommandResult:
        return PolicyEngine(self.root, cost_policy=load_cost_policy(self.root)).evaluate(
            PolicyRequest(
                action=self.action,
                path=profile.cwd,
                dry_run=False,
                approval_id=approval_id,
                tool_id=self.tool_id,
                subject=profile.profile_id,
                metadata={"source": "tests-run-tool", "sprint": "FUNC-SPRINT-32", "profile": profile.profile_id},
            )
        )

    def _blocked_by_policy(self, *, profile: TestProfile, policy_result: CommandResult, approval_id: str | None) -> CommandResult:
        return CommandResult(
            command="tests run",
            ok=False,
            exit_code=policy_result.exit_code,
            message="tests.run blocked by PolicyEngine before subprocess execution.",
            data={
                "summary": {
                    "profile": profile.profile_id,
                    "executed": False,
                    "blocked_by_policy": True,
                    "approval_id": approval_id,
                    "preliminary": True,
                },
                "profile": profile.to_dict(),
                "policy": policy_result.to_dict(),
                "profile_registry": self.profiles.to_dict(),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=list(policy_result.findings),
        )

    def _from_execution(
        self,
        *,
        profile: TestProfile,
        approval_id: str | None,
        timeout_seconds: int,
        policy_result: CommandResult,
        execution_result: CommandResult,
    ) -> CommandResult:
        execution_summary: dict[str, Any] = dict((execution_result.data or {}).get("summary") or {})
        returncode = execution_summary.get("returncode")
        timed_out = bool(execution_summary.get("timed_out"))
        ok = execution_result.ok
        exit_code = execution_result.exit_code
        findings = list(execution_result.findings)
        if ok:
            findings = [
                Finding(
                    id="TESTS_RUN_PASS",
                    message="tests.run executed an approved allowlisted pytest profile successfully.",
                    severity=Severity.INFO,
                    metadata={"profile": profile.profile_id, "approval_id": approval_id, "returncode": returncode},
                )
            ]
        elif timed_out:
            findings.append(
                Finding(
                    id="TESTS_RUN_TIMEOUT",
                    message="tests.run timed out while executing the approved profile.",
                    severity=Severity.BLOCK,
                    metadata={"profile": profile.profile_id, "timeout_seconds": timeout_seconds},
                )
            )
        else:
            findings.append(
                Finding(
                    id="TESTS_RUN_FAILED",
                    message="tests.run executed the approved profile but pytest returned a non-zero exit code.",
                    severity=Severity.FAIL,
                    metadata={"profile": profile.profile_id, "returncode": returncode},
                )
            )

        return CommandResult(
            command="tests run",
            ok=ok,
            exit_code=exit_code,
            message="tests.run completed successfully." if ok else "tests.run completed with failure or block.",
            data={
                "summary": {
                    "profile": profile.profile_id,
                    "executed": bool(execution_summary.get("executed")),
                    "allowed_by_policy": bool((policy_result.data or {}).get("summary", {}).get("allowed")),
                    "approval_id": approval_id,
                    "returncode": returncode,
                    "timed_out": timed_out,
                    "timeout_seconds": timeout_seconds,
                    "redactions": execution_summary.get("redactions", 0),
                    "preliminary": True,
                },
                "profile": profile.to_dict(),
                "policy": policy_result.to_dict(),
                "execution": execution_result.to_dict(),
                "profile_registry": self.profiles.to_dict(),
                "network_used": False,
                "external_api_used": False,
                "mutations_performed": False,
                "preliminary": True,
            },
            findings=findings,
        )
