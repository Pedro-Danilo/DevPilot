from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard
from devpilot_core.repo.analyzer import RepoAnalyzer
from devpilot_core.review import CodeReviewEngine, PatchReviewEngine
from devpilot_core.review.rule_packs import ReviewRule, ReviewRulePack, default_review_rule_packs, rule_index, serialize_rule_packs


@dataclass(frozen=True)
class RepoQualityGateConfig:
    """Configuration for Sprint 39 repo quality gate dry-run."""

    target: str = "."
    code_target: str | None = None
    patch_file: str | None = None
    patch_text: str | None = None
    rule_packs: tuple[ReviewRulePack, ...] = field(default_factory=default_review_rule_packs)


class RepoQualityGate:
    """Dry-run quality gate for repository changes.

    FUNC-SPRINT-39 integrates RepoAnalyzer, CodeReviewEngine, optional
    PatchReviewEngine and PolicyEngine through versioned ReviewRulePacks. It is
    read-only: no files are modified, no patch is applied, no Git write command
    is executed, no model/API/network call is performed and raw secrets are not
    emitted.
    """

    def __init__(self, root: Path, *, config: RepoQualityGateConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or RepoQualityGateConfig()
        self._rules = rule_index(self.config.rule_packs)
        self._secret_guard = SecretGuard()

    def run(self) -> CommandResult:
        target = self.config.target
        code_target = self.config.code_target or self._default_code_target()
        findings: list[Finding] = []
        components: list[dict[str, Any]] = []
        rule_hits: list[dict[str, Any]] = []

        policy_results = [
            self._policy_check("target", target),
            self._policy_check("code_target", code_target),
        ]
        if self.config.patch_file:
            policy_results.append(self._policy_check("patch_file", self.config.patch_file))
        for policy_result in policy_results:
            components.append(_component_summary("policy", policy_result, policy_result.data.get("request", {}).get("path") or policy_result.data.get("request", {}).get("subject")))
            findings.extend(_prefixed_findings(policy_result, source="policy"))

        repo_result = RepoAnalyzer(self.root).analyze(target=target)
        components.append(_component_summary("repo_analyzer", repo_result, target))
        findings.extend(_prefixed_findings(repo_result, source="repo_analyzer"))

        if self._exists_inside_root(code_target):
            code_result = CodeReviewEngine(self.root).review(code_target)
            components.append(_component_summary("code_review", code_result, code_target))
            findings.extend(_prefixed_findings(code_result, source="code_review"))
        else:
            code_result = CommandResult(
                command="code-review",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Code review skipped because code target does not exist.",
                data={"summary": {"target": code_target, "skipped": True, "dry_run": True}},
                findings=[Finding("QUALITY_GATE_CODE_REVIEW_SKIPPED", "Code review skipped: target does not exist.", Severity.INFO, path=code_target)],
            )
            components.append(_component_summary("code_review", code_result, code_target))
            findings.extend(_prefixed_findings(code_result, source="code_review"))

        if self.config.patch_file or self.config.patch_text:
            patch_result = PatchReviewEngine(self.root).review(patch_file=self.config.patch_file, patch_text=self.config.patch_text)
            components.append(_component_summary("patch_review", patch_result, self.config.patch_file or "inline-patch"))
            findings.extend(_prefixed_findings(patch_result, source="patch_review"))
        else:
            patch_result = CommandResult(
                command="patch-review",
                ok=True,
                exit_code=ExitCode.PASS,
                message="Patch review skipped because no patch was provided.",
                data={"summary": {"source": "none", "skipped": True, "dry_run": True, "patch_applied": False}},
                findings=[Finding("QUALITY_GATE_PATCH_REVIEW_SKIPPED", "Patch review skipped: no patch supplied.", Severity.INFO)],
            )
            components.append(_component_summary("patch_review", patch_result, "none"))
            findings.extend(_prefixed_findings(patch_result, source="patch_review"))

        # Rule hits are evidence that findings are not ignored. Warnings remain
        # advisory, while FAIL/BLOCK from underlying engines propagate to the gate.
        normalized_findings = []
        for finding in findings:
            rule = self._match_rule(finding)
            if rule:
                rule_hits.append(_rule_hit(rule, finding))
            normalized_findings.append(finding)

        exit_code = _derive_gate_exit_code(normalized_findings)
        status = _status_from_exit_code(exit_code)
        blocking = sum(1 for finding in normalized_findings if finding.severity == Severity.BLOCK)
        failing = sum(1 for finding in normalized_findings if finding.severity in {Severity.FAIL, Severity.ERROR})
        warnings = sum(1 for finding in normalized_findings if finding.severity == Severity.WARNING)
        summary = {
            "status": status,
            "target": target,
            "code_target": code_target,
            "patch_reviewed": bool(self.config.patch_file or self.config.patch_text),
            "components_total": len(components),
            "findings_total": len(normalized_findings),
            "blocking_findings": blocking,
            "failing_findings": failing,
            "warnings_total": warnings,
            "rule_packs_total": len(self.config.rule_packs),
            "rule_hits_total": len(rule_hits),
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "patch_applied": False,
            "preliminary": True,
        }
        data = {
            "summary": summary,
            "components": components,
            "rule_packs": serialize_rule_packs(self.config.rule_packs),
            "rule_hits": rule_hits,
            "notes": [
                "FUNC-SPRINT-39 Repo Quality Gate is dry-run and implemented-initial.",
                "Warnings are advisory by default and do not block the gate.",
                "FAIL/BLOCK findings emitted by integrated engines propagate to the gate status.",
                "PatchReviewEngine runs only when --patch-file or --patch-text is provided; no patch is ever applied.",
                "Raw source, patch content and secret values are not emitted.",
            ],
        }
        ok = exit_code == ExitCode.PASS
        message = "Repo quality gate passed in dry-run mode." if ok else f"Repo quality gate completed with status {status}."
        return CommandResult(command="repo quality-gate", ok=ok, exit_code=exit_code, message=message, data=data, findings=normalized_findings)

    def _default_code_target(self) -> str:
        # Sprint 39 defaults to the repo intelligence package to keep the gate
        # useful and fast. Whole-repo code review can be requested explicitly.
        if (self.root / "src" / "devpilot_core" / "repo").exists():
            return "src/devpilot_core/repo"
        if (self.root / "src").exists():
            return "src"
        return self.config.target

    def _exists_inside_root(self, target: str) -> bool:
        path = Path(target)
        if not path.is_absolute():
            path = self.root / path
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            return False
        return path.exists()

    def _policy_check(self, subject: str, path: str) -> CommandResult:
        return PolicyEngine(self.root).evaluate(
            PolicyRequest(
                action="read",
                path=path,
                dry_run=True,
                tool_id="repo.quality_gate",
                subject=subject,
                metadata={"sprint": "FUNC-SPRINT-39", "component": "RepoQualityGate"},
            )
        )

    def _match_rule(self, finding: Finding) -> ReviewRule | None:
        raw_id = finding.metadata.get("source_finding_id") if finding.metadata else None
        return self._rules.get(str(raw_id or finding.id))


def _prefixed_findings(result: CommandResult, *, source: str) -> list[Finding]:
    prefixed: list[Finding] = []
    for finding in result.findings:
        # Keep source findings traceable without emitting raw payloads.
        metadata = {"source": source, "source_command": result.command, "source_finding_id": finding.id, **finding.metadata}
        prefixed.append(
            Finding(
                id=f"QUALITY_GATE_{source.upper()}_{finding.id}",
                message=finding.message,
                severity=finding.severity,
                path=finding.path,
                metadata=metadata,
            )
        )
    return prefixed


def _component_summary(source: str, result: CommandResult, subject: str | None) -> dict[str, Any]:
    severities = [finding.severity for finding in result.findings]
    return {
        "source": source,
        "command": result.command,
        "subject": subject,
        "ok": result.ok,
        "exit_code": int(result.exit_code),
        "findings_total": len(result.findings),
        "blocking_findings": sum(1 for severity in severities if severity == Severity.BLOCK),
        "failing_findings": sum(1 for severity in severities if severity in {Severity.FAIL, Severity.ERROR}),
        "warnings_total": sum(1 for severity in severities if severity == Severity.WARNING),
        "dry_run": True,
    }


def _rule_hit(rule: ReviewRule, finding: Finding) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "source": rule.source,
        "finding_id": finding.metadata.get("source_finding_id") if finding.metadata else finding.id,
        "gate_finding_id": finding.id,
        "severity": finding.severity.value,
        "default_effect": rule.default_effect,
        "path": finding.path,
    }


def _derive_gate_exit_code(findings: list[Finding]) -> ExitCode:
    severities = {finding.severity for finding in findings}
    if Severity.ERROR in severities:
        return ExitCode.ERROR
    if Severity.BLOCK in severities:
        return ExitCode.BLOCK
    if Severity.FAIL in severities:
        return ExitCode.FAIL
    return ExitCode.PASS


def _status_from_exit_code(exit_code: ExitCode) -> str:
    if exit_code == ExitCode.BLOCK:
        return "BLOCK"
    if exit_code == ExitCode.FAIL:
        return "FAIL"
    if exit_code == ExitCode.ERROR:
        return "ERROR"
    return "PASS"
