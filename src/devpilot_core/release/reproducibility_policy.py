from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity

DEFAULT_POLICY_PATH = Path(".devpilot/release/reproducibility_policy.json")

CRITICAL_EXCLUSIONS = {
    "outputs/",
    ".devpilot/devpilot.db",
    ".devpilot/agent_sessions/",
    ".venv/",
    "node_modules/",
}

REQUIRED_FALSE_SAFETY_FLAGS = {
    "published",
    "deployed",
    "network_used",
    "external_api_used",
    "remote_execution_used",
    "connector_write_used",
    "plugin_execution_used",
    "mutations_performed",
    "source_mutations_performed",
    "secrets_included",
}

REQUIRED_TRUE_SAFETY_FLAGS = {
    "local_first",
    "dry_run",
}


@dataclass(frozen=True)
class ReleaseReproducibilityPolicy:
    """In-memory representation of the POST-H-017-A release reproducibility policy.

    The policy is intentionally deterministic and local-first. It is not a pack
    generator and it does not execute Git, shell commands, package managers,
    network calls or external APIs. Later POST-H-017 micro-sprints consume this
    policy when generating environment snapshots, archive manifests, verifiers
    and the final release reproducibility quality gate.
    """

    path: Path
    payload: dict[str, Any]

    @property
    def critical_exclusions(self) -> set[str]:
        return {str(value) for value in self.payload.get("critical_exclusions") or []}

    @property
    def forbidden_archive_entries(self) -> set[str]:
        return {str(value) for value in self.payload.get("forbidden_archive_entries") or []}

    @property
    def required_safety_flags(self) -> dict[str, Any]:
        flags = self.payload.get("required_safety_flags")
        return flags if isinstance(flags, dict) else {}


class ReleaseReproducibilityPolicyValidator:
    """Validate the local POST-H-017-A release reproducibility policy.

    This validator checks the semantic policy invariants that are cheaper and
    more explicit than generic JSON Schema validation: runtime exclusions,
    safety flags, dry-run policy and secret-free environment snapshot defaults.
    It is read-only and does not inspect secrets or runtime payloads.
    """

    def __init__(self, root: Path, *, policy_path: Path | str = DEFAULT_POLICY_PATH) -> None:
        self.root = Path(root).resolve()
        self.policy_path = Path(policy_path)

    def load(self) -> ReleaseReproducibilityPolicy:
        absolute_path = self.root / self.policy_path
        payload = json.loads(absolute_path.read_text(encoding="utf-8"))
        return ReleaseReproducibilityPolicy(path=self.policy_path, payload=payload)

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        absolute_path = self.root / self.policy_path
        if not absolute_path.exists():
            finding = Finding(
                "RELEASE_REPRODUCIBILITY_POLICY_MISSING",
                "Release reproducibility policy file is missing.",
                Severity.BLOCK,
                path=str(self.policy_path),
            )
            return CommandResult(
                command="release reproducibility-policy validate",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Release reproducibility policy validation blocked.",
                data={"summary": self._summary(path_exists=False, findings_total=1, blocking_findings_total=1)},
                findings=[finding],
            )

        try:
            policy = self.load()
        except json.JSONDecodeError as exc:
            finding = Finding(
                "RELEASE_REPRODUCIBILITY_POLICY_INVALID_JSON",
                f"Release reproducibility policy is not valid JSON: {exc}",
                Severity.BLOCK,
                path=str(self.policy_path),
            )
            return CommandResult(
                command="release reproducibility-policy validate",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Release reproducibility policy validation blocked.",
                data={"summary": self._summary(path_exists=True, findings_total=1, blocking_findings_total=1)},
                findings=[finding],
            )

        findings.extend(self.validate_payload(policy.payload))
        blocking = [finding for finding in findings if finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL}]
        ok = not blocking
        summary = self._summary(
            path_exists=True,
            findings_total=len(findings) or 1,
            blocking_findings_total=len(blocking),
            policy=policy,
        )
        return CommandResult(
            command="release reproducibility-policy validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="Release reproducibility policy validation passed." if ok else "Release reproducibility policy validation blocked.",
            data={"summary": summary, "policy": policy.payload},
            findings=findings or [
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_PASS",
                    "Release reproducibility policy declares required exclusions, dry-run mode and secret-free safety flags.",
                    Severity.INFO,
                    path=str(self.policy_path),
                    metadata=summary,
                )
            ],
        )

    def validate_payload(self, payload: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        exclusions = {str(value) for value in payload.get("critical_exclusions") or []}
        missing_exclusions = sorted(CRITICAL_EXCLUSIONS - exclusions)
        if missing_exclusions:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_EXCLUSIONS_MISSING",
                    "Release reproducibility policy is missing critical runtime exclusions.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                    metadata={"missing_exclusions": missing_exclusions},
                )
            )

        if payload.get("dirty_repo_blocks_reproducible_release") is not True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_DIRTY_REPO_NOT_BLOCKED",
                    "Dirty repositories must block verified reproducible release declarations.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                )
            )
        if payload.get("secret_free_required") is not True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_SECRET_FREE_NOT_REQUIRED",
                    "Release reproducibility policy must require secret-free evidence.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                )
            )
        if payload.get("dry_run_only") is not True:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_DRY_RUN_DISABLED",
                    "Release reproducibility policy must remain dry-run-only.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                )
            )

        safety = payload.get("required_safety_flags") if isinstance(payload.get("required_safety_flags"), dict) else {}
        missing_true = sorted(flag for flag in REQUIRED_TRUE_SAFETY_FLAGS if safety.get(flag) is not True)
        missing_false = sorted(flag for flag in REQUIRED_FALSE_SAFETY_FLAGS if safety.get(flag) is not False)
        if missing_true or missing_false:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_SAFETY_FLAGS_INVALID",
                    "Release reproducibility policy has invalid required safety flags.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                    metadata={"required_true_invalid": missing_true, "required_false_invalid": missing_false},
                )
            )

        env_policy = payload.get("environment_snapshot_policy") if isinstance(payload.get("environment_snapshot_policy"), dict) else {}
        if env_policy.get("env_files_read") is not False or env_policy.get("secret_values_read") is not False or env_policy.get("secret_values_included") is not False:
            findings.append(
                Finding(
                    "RELEASE_REPRODUCIBILITY_POLICY_ENV_REDACTION_INVALID",
                    "Environment snapshot policy must not read env files, secret values or include secrets.",
                    Severity.BLOCK,
                    path=str(self.policy_path),
                )
            )

        return findings

    def _summary(
        self,
        *,
        path_exists: bool,
        findings_total: int,
        blocking_findings_total: int,
        policy: ReleaseReproducibilityPolicy | None = None,
    ) -> dict[str, Any]:
        payload = policy.payload if policy is not None else {}
        return {
            "created_by": "POST-H-017-A",
            "status": "implemented-initial",
            "preliminary": True,
            "policy_path": str(self.policy_path),
            "policy_exists": path_exists,
            "critical_exclusions_total": len(payload.get("critical_exclusions") or []),
            "required_safety_flags_total": len(payload.get("required_safety_flags") or {}),
            "dirty_repo_blocks_reproducible_release": payload.get("dirty_repo_blocks_reproducible_release") is True,
            "secret_free_required": payload.get("secret_free_required") is True,
            "dry_run_only": payload.get("dry_run_only") is True,
            "runtime_artifacts_forbidden": payload.get("runtime_artifacts_forbidden") is True,
            "findings_total": findings_total,
            "blocking_findings_total": blocking_findings_total,
            "local_first": True,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "remote_execution_enabled": False,
            "connector_write_enabled": False,
            "plugin_execution_enabled": False,
            "secrets_read": False,
        }
