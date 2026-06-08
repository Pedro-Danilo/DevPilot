from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devpilot_core.cli_models import CommandResult


@dataclass(frozen=True)
class EvalCase:
    """One deterministic evaluation case for DevPilot components.

    FUNC-SPRINT-13 keeps evaluation local/offline. A case declares the component
    to exercise, synthetic input payload and expected behavior. It is not an LLM
    judge and does not depend on external datasets.
    """

    case_id: str
    component: str
    description: str
    expected_ok: bool
    input: dict[str, Any] = field(default_factory=dict)
    expected_finding_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvalCase":
        expected = payload.get("expected", {}) or {}
        return cls(
            case_id=str(payload["id"]),
            component=str(payload["component"]),
            description=str(payload.get("description", "")),
            input=dict(payload.get("input", {}) or {}),
            expected_ok=bool(expected.get("ok", False)),
            expected_finding_ids=tuple(str(item) for item in expected.get("finding_ids", []) or []),
            tags=tuple(str(item) for item in payload.get("tags", []) or []),
        )


@dataclass(frozen=True)
class EvalCaseResult:
    """Result of one evaluation case.

    The result keeps both expected and actual behavior so false positives and
    false negatives can be computed deterministically without hidden state.
    """

    case_id: str
    component: str
    expected_ok: bool
    actual_ok: bool
    matched: bool
    expected_finding_ids: tuple[str, ...] = ()
    actual_finding_ids: tuple[str, ...] = ()
    missing_expected_finding_ids: tuple[str, ...] = ()
    unexpected_findings: tuple[str, ...] = ()
    command: str | None = None
    exit_code: int | None = None
    message: str | None = None
    tags: tuple[str, ...] = ()

    @classmethod
    def from_command_result(cls, case: EvalCase, result: CommandResult) -> "EvalCaseResult":
        actual_ids = tuple(finding.id for finding in result.findings)
        missing = tuple(item for item in case.expected_finding_ids if item not in actual_ids)
        matched = result.ok == case.expected_ok and not missing
        unexpected = tuple(item for item in actual_ids if case.expected_ok and item not in case.expected_finding_ids)
        return cls(
            case_id=case.case_id,
            component=case.component,
            expected_ok=case.expected_ok,
            actual_ok=result.ok,
            matched=matched,
            expected_finding_ids=case.expected_finding_ids,
            actual_finding_ids=actual_ids,
            missing_expected_finding_ids=missing,
            unexpected_findings=unexpected,
            command=result.command,
            exit_code=int(result.exit_code),
            message=result.message,
            tags=case.tags,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "component": self.component,
            "expected_ok": self.expected_ok,
            "actual_ok": self.actual_ok,
            "matched": self.matched,
            "expected_finding_ids": list(self.expected_finding_ids),
            "actual_finding_ids": list(self.actual_finding_ids),
            "missing_expected_finding_ids": list(self.missing_expected_finding_ids),
            "unexpected_findings": list(self.unexpected_findings),
            "command": self.command,
            "exit_code": self.exit_code,
            "message": self.message,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class EvalSuiteResult:
    """Aggregated deterministic evaluation result."""

    suite_id: str
    cases: tuple[EvalCaseResult, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed(self) -> int:
        return sum(1 for case in self.cases if case.matched)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return 0.0 if self.total == 0 else round(self.passed / self.total, 4)

    @property
    def false_positives(self) -> int:
        # Expected clean but component reported a defect.
        return sum(1 for case in self.cases if case.expected_ok and not case.actual_ok)

    @property
    def false_negatives(self) -> int:
        # Expected defective but component passed it as clean.
        return sum(1 for case in self.cases if not case.expected_ok and case.actual_ok)

    @property
    def missing_expected_findings(self) -> int:
        return sum(len(case.missing_expected_finding_ids) for case in self.cases)

    def summary(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "cases_total": self.total,
            "cases_passed": self.passed,
            "cases_failed": self.failed,
            "pass_rate": self.pass_rate,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "missing_expected_findings": self.missing_expected_findings,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "cases": [case.to_dict() for case in self.cases],
            "metadata": self.metadata,
        }
