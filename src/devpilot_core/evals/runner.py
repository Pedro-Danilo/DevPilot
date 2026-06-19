from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.agents import AgentRuntime
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.evals.models import EvalCase, EvalCaseResult, EvalSuiteResult
from devpilot_core.evals.safety import SAFETY_SUITE_IDS, SafetyEvalEngine, build_safety_metrics, safety_suite_findings
from devpilot_core.validators.artifact import validate_artifact_file
from devpilot_core.validators.frontmatter import validate_frontmatter_file

DEFAULT_FIXTURE_PATH = Path("evals/fixtures/documentation_eval_cases.json")
SUITE_FIXTURE_PATHS = {
    "documentation": DEFAULT_FIXTURE_PATH,
    "advanced-agentic": Path("evals/fixtures/advanced_agentic_eval_cases.json"),
    "red-team": Path("evals/fixtures/red_team_agentic_eval_cases.json"),
    "plugin-ecosystem": Path("evals/fixtures/plugin_ecosystem_eval_cases.json"),
    "multiworkspace-isolation": Path("evals/fixtures/multiworkspace_isolation_eval_cases.json"),
}
SUPPORTED_COMPONENTS = {
    "validate_frontmatter",
    "validate_artifact",
    "agent.documentation_audit",
    "agent.documentation_audit_model_aware",
    "agent.precode_documentation",
    "agent.repo_analysis",
    "agent.repo_analysis_model_aware",
    "agent.code_review",
    "agent.code_review_model_aware",
    "agent.patch_review",
    "agent.patch_review_model_aware",
    "agent.safe_refactor",
    "agent.safe_refactor_model_aware",
    "agent.test_planner",
    "agent.test_planner_model_aware",
    "agent.requirements",
    "agent.requirements_model_aware",
    "agent.architecture",
    "agent.architecture_model_aware",
    "agent.security",
    "agent.security_model_aware",
    *SafetyEvalEngine.SUPPORTED_COMPONENTS,
}


@dataclass(frozen=True)
class EvalRunnerConfig:
    """Configuration for the deterministic evaluation harness.

    The first version uses synthetic local fixtures only. It writes temporary
    evaluation material under outputs/evals/workdir and can be safely regenerated.
    """

    fixture_path: Path = DEFAULT_FIXTURE_PATH
    workdir: Path = Path("outputs/evals/workdir")


class EvalRunner:
    """Offline evaluation harness for validators and document agents.

    FUNC-SPRINT-13 introduces deterministic evals for DevPilot primitives. It
    measures expected pass/fail behavior, false positives, false negatives and
    missing expected findings. It does not call LLMs, external APIs or network
    services.
    """

    def __init__(self, root: Path, *, config: EvalRunnerConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or EvalRunnerConfig()

    def run(self, *, suite: str = "documentation", case_id: str | None = None) -> CommandResult:
        """Run a fixture suite and return a normalized CommandResult."""

        cases, metadata = self.load_cases(suite=suite)
        if case_id:
            cases = [case for case in cases if case.case_id == case_id]
            if not cases:
                finding = Finding(
                    id="EVAL_CASE_NOT_FOUND",
                    message="Requested evaluation case was not found in the selected suite.",
                    severity=Severity.ERROR,
                    metadata={"suite": suite, "case_id": case_id},
                )
                return CommandResult("eval run", False, ExitCode.ERROR, "Evaluation case not found.", data={"suite_id": suite}, findings=[finding])

        self._reset_workdir(suite)
        results = tuple(self._run_case(case, suite=suite) for case in cases)
        suite_result = EvalSuiteResult(
            suite_id=suite,
            cases=results,
            metadata={
                "contract": "DevPilotEvaluationHarness",
                "preliminary": True,
                "llm_required": False,
                "external_api_used": False,
                "network_used": False,
                "fixture_path": _repo_path(self._fixture_path(suite=suite), self.root),
                "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                **metadata,
            },
        )
        data = suite_result.to_dict()
        findings = self._suite_findings(suite_result)
        safety_metrics: dict[str, Any] | None = None
        if suite in SAFETY_SUITE_IDS:
            safety_metrics = build_safety_metrics(suite, cases, results)
            data["summary"].update(
                {
                    "safety_score": safety_metrics["safety_score"],
                    "safety_score_threshold": safety_metrics["safety_score_threshold"],
                    "safety_gate_passed": safety_metrics["gate_passed"],
                    "adversarial_cases_total": safety_metrics["adversarial_cases_total"],
                    "adversarial_cases_detected": safety_metrics["adversarial_cases_detected"],
                    "clean_cases_total": safety_metrics["clean_cases_total"],
                    "clean_cases_passed": safety_metrics["clean_cases_passed"],
                    "llm_judge_used": False,
                    "network_used": False,
                    "external_api_used": False,
                }
            )
            data["safety"] = safety_metrics
            findings.extend(safety_suite_findings(safety_metrics))
        ok = suite_result.failed == 0 and suite_result.false_positives == 0 and suite_result.false_negatives == 0 and suite_result.missing_expected_findings == 0
        if safety_metrics is not None:
            ok = ok and bool(safety_metrics["gate_passed"])
        return CommandResult(
            command="eval run",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.FAIL,
            message="Evaluation suite passed." if ok else "Evaluation suite failed.",
            data=data,
            findings=findings,
        )

    def load_cases(self, *, suite: str = "documentation") -> tuple[list[EvalCase], dict[str, Any]]:
        """Load fixture cases from JSON."""

        path = self._fixture_path(suite=suite)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation fixture not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        suite_id = str(payload.get("suite_id", "documentation"))
        if suite_id != suite:
            return [], {"declared_suite_id": suite_id, "fixture_path": _repo_path(path, self.root)}
        cases = [EvalCase.from_dict(item) for item in payload.get("cases", [])]
        return cases, {
            "schema_version": payload.get("schema_version"),
            "declared_suite_id": suite_id,
            "description": payload.get("description"),
            "fixture_path": _repo_path(path, self.root),
            "safety_suite": suite in SAFETY_SUITE_IDS,
        }

    def _fixture_path(self, *, suite: str = "documentation") -> Path:
        candidate = self.config.fixture_path
        if self.config.fixture_path == DEFAULT_FIXTURE_PATH:
            candidate = SUITE_FIXTURE_PATHS.get(suite, DEFAULT_FIXTURE_PATH)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        return candidate.resolve()

    def _workdir(self, suite: str) -> Path:
        candidate = self.config.workdir
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = (candidate / suite).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("EvalRunner workdir must be inside project root.") from exc
        return candidate

    def _reset_workdir(self, suite: str) -> None:
        workdir = self._workdir(suite)
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True, exist_ok=True)

    def _run_case(self, case: EvalCase, *, suite: str) -> EvalCaseResult:
        if case.component not in SUPPORTED_COMPONENTS:
            result = CommandResult(
                "eval case",
                False,
                ExitCode.ERROR,
                "Unsupported evaluation component.",
                findings=[Finding("EVAL_UNSUPPORTED_COMPONENT", "Unsupported evaluation component.", Severity.ERROR, metadata={"component": case.component})],
            )
            return EvalCaseResult.from_command_result(case, result)

        if case.component == "validate_frontmatter":
            result = self._run_frontmatter_case(case, suite=suite)
        elif case.component == "validate_artifact":
            result = self._run_artifact_case(case, suite=suite)
        elif case.component == "agent.documentation_audit":
            result = self._run_documentation_audit_case(case, suite=suite)
        elif case.component == "agent.documentation_audit_model_aware":
            result = self._run_documentation_audit_case(case, suite=suite, provider="mock")
        elif case.component == "agent.precode_documentation":
            result = self._run_precode_documentation_case(case)
        elif case.component == "agent.repo_analysis":
            result = self._run_repo_analysis_case(case, suite=suite)
        elif case.component == "agent.repo_analysis_model_aware":
            result = self._run_repo_analysis_case(case, suite=suite, provider="mock")
        elif case.component == "agent.code_review":
            result = self._run_code_review_case(case, suite=suite)
        elif case.component == "agent.code_review_model_aware":
            result = self._run_code_review_case(case, suite=suite, provider="mock")
        elif case.component == "agent.patch_review":
            result = self._run_patch_review_case(case, suite=suite)
        elif case.component == "agent.patch_review_model_aware":
            result = self._run_patch_review_case(case, suite=suite, provider="mock")
        elif case.component == "agent.safe_refactor":
            result = self._run_safe_refactor_case(case, suite=suite)
        elif case.component == "agent.safe_refactor_model_aware":
            result = self._run_safe_refactor_case(case, suite=suite, provider="mock")
        elif case.component == "agent.test_planner":
            result = self._run_test_planner_case(case, suite=suite)
        elif case.component == "agent.test_planner_model_aware":
            result = self._run_test_planner_case(case, suite=suite, provider="mock")
        elif case.component == "agent.requirements":
            result = self._run_requirements_case(case, suite=suite)
        elif case.component == "agent.requirements_model_aware":
            result = self._run_requirements_case(case, suite=suite, provider="mock")
        elif case.component == "agent.architecture":
            result = self._run_architecture_case(case, suite=suite)
        elif case.component == "agent.architecture_model_aware":
            result = self._run_architecture_case(case, suite=suite, provider="mock")
        elif case.component == "agent.security":
            result = self._run_security_case(case, suite=suite)
        elif case.component == "agent.security_model_aware":
            result = self._run_security_case(case, suite=suite, provider="mock")
        elif case.component in SafetyEvalEngine.SUPPORTED_COMPONENTS:
            result = SafetyEvalEngine().evaluate(case)
        else:  # pragma: no cover - guarded by SUPPORTED_COMPONENTS above.
            result = CommandResult("eval case", False, ExitCode.ERROR, "Unsupported evaluation component.")
        return EvalCaseResult.from_command_result(case, result)

    def _run_frontmatter_case(self, case: EvalCase, *, suite: str) -> CommandResult:
        path = self._write_single_markdown_case(case, suite=suite)
        return validate_frontmatter_file(path, root=self.root, strict=True)

    def _run_artifact_case(self, case: EvalCase, *, suite: str) -> CommandResult:
        path = self._write_single_markdown_case(case, suite=suite)
        return validate_artifact_file(path, root=self.root, strict=True)

    def _run_documentation_audit_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "artifact.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        return AgentRuntime(self.root).run("documentation-audit", target=_repo_path(case_dir, self.root), dry_run=True, provider=provider)

    def _run_precode_documentation_case(self, case: EvalCase) -> CommandResult:
        idea = str(case.input.get("idea", ""))
        return AgentRuntime(self.root).run("precode-documentation", idea=idea, dry_run=True)

    def _run_repo_analysis_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        # RepoAnalysisAgent runs repository-wide inventory components. Keep only
        # the current synthetic repo-analysis case under the eval workdir so one
        # case cannot amplify the next through accumulated generated fixtures.
        for sibling in case_dir.parent.iterdir():
            if sibling != case_dir and sibling.is_dir():
                shutil.rmtree(sibling)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "README.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            (case_dir / "README.md").write_text("# Synthetic repo\n\nLocal repo-analysis evaluation fixture.\n", encoding="utf-8")
        return AgentRuntime(self.root).run("repo-analysis", target=_repo_path(case_dir, self.root), dry_run=True, provider=provider)


    def _run_code_review_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "src/sample.py")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        review_target = case_dir
        if files:
            first_relative = Path(str(files[0].get("path", "src/sample.py")))
            review_target = (case_dir / first_relative).resolve()
        else:
            (case_dir / "src" / "sample.py").parent.mkdir(parents=True, exist_ok=True)
            (case_dir / "src" / "sample.py").write_text("def ok() -> str:\n    return 'ok'\n", encoding="utf-8")
            review_target = (case_dir / "src" / "sample.py").resolve()
        return AgentRuntime(self.root).run("code-review", target=_repo_path(review_target, self.root), dry_run=True, provider=provider)

    def _run_patch_review_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "patch_target.py")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        patch_name = str(case.input.get("patch_file", "fixture.patch"))
        patch_path = (case_dir / patch_name).resolve()
        try:
            patch_path.relative_to(case_dir)
        except ValueError as exc:
            raise ValueError("Evaluation fixture patch path escapes case directory.") from exc
        patch_text = str(case.input.get("patch_text", ""))
        if not patch_text:
            target = _repo_path(case_dir / "patch_target.py", self.root)
            (case_dir / "patch_target.py").write_text("def value():\n    return 'old'\n", encoding="utf-8")
            patch_text = (
                f"diff --git a/{target} b/{target}\n"
                f"--- a/{target}\n"
                f"+++ b/{target}\n"
                "@@ -1,2 +1,2 @@\n"
                " def value():\n"
                "-    return 'old'\n"
                "+    return 'new'\n"
            )
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(patch_text, encoding="utf-8")
        return AgentRuntime(self.root).run("patch-review", target=_repo_path(patch_path, self.root), patch_file=_repo_path(patch_path, self.root), dry_run=True, provider=provider)


    def _run_safe_refactor_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "src/sample.py")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            sample = case_dir / "src" / "sample.py"
            sample.parent.mkdir(parents=True, exist_ok=True)
            sample.write_text("def small() -> str:\n    return 'ok'\n", encoding="utf-8")
        goal = str(case.input.get("goal", "Plan safe refactor for eval fixture"))
        return AgentRuntime(self.root).run("safe-refactor", target=_repo_path(case_dir, self.root), idea=goal, dry_run=True, provider=provider)

    def _run_test_planner_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "docs/requirements.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            doc = case_dir / "docs" / "requirements.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# Requirements\n\nREQ-001 needs AC-001 and TEST-001 coverage.\n", encoding="utf-8")
        target = str(case.input.get("target", _repo_path(case_dir, self.root)))
        if target == ".case_dir":
            target = _repo_path(case_dir, self.root)
        idea = str(case.input.get("idea", "Create traceability-aware test plan"))
        return AgentRuntime(self.root).run("test-planner", target=target, idea=idea, dry_run=True, provider=provider)


    def _run_requirements_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "docs/requirements.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            doc = case_dir / "docs" / "requirements.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# Requirements\n\nFR-EVAL-001 requires AC-EVAL-001 and TEST-EVAL-001 coverage.\n", encoding="utf-8")
        target = str(case.input.get("target", ".case_dir"))
        if target == ".case_dir":
            target = _repo_path(case_dir, self.root)
        idea = str(case.input.get("idea", "Review requirements coverage"))
        return AgentRuntime(self.root).run("requirements", target=target, idea=idea, dry_run=True, provider=provider)

    def _run_architecture_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "docs/architecture.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            doc = case_dir / "docs" / "architecture.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# Architecture\n\nComponent: Synthetic Gateway implemented.\n", encoding="utf-8")
        target = str(case.input.get("target", ".case_dir"))
        if target == ".case_dir":
            target = _repo_path(case_dir, self.root)
        idea = str(case.input.get("idea", "Review architecture evidence"))
        return AgentRuntime(self.root).run("architecture", target=target, idea=idea, dry_run=True, provider=provider)

    def _run_security_case(self, case: EvalCase, *, suite: str, provider: str | None = None) -> CommandResult:
        case_dir = self._case_dir(case, suite=suite)
        files = case.input.get("files", []) or []
        for file_payload in files:
            relative = Path(str(file_payload.get("path", "docs/security.md")))
            destination = (case_dir / relative).resolve()
            try:
                destination.relative_to(case_dir)
            except ValueError as exc:
                raise ValueError("Evaluation fixture path escapes case directory.") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(file_payload.get("content", "")), encoding="utf-8")
        if not files:
            doc = case_dir / "docs" / "security.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# Security\n\nNo raw secrets here.\n", encoding="utf-8")
        target = str(case.input.get("target", ".case_dir"))
        if target == ".case_dir":
            target = _repo_path(case_dir, self.root)
        idea = str(case.input.get("idea", "Review security controls"))
        return AgentRuntime(self.root).run("security", target=target, idea=idea, dry_run=True, provider=provider)

    def _write_single_markdown_case(self, case: EvalCase, *, suite: str) -> Path:
        case_dir = self._case_dir(case, suite=suite)
        relative_path = Path(str(case.input.get("path", "artifact.md")))
        destination = (case_dir / relative_path).resolve()
        try:
            destination.relative_to(case_dir)
        except ValueError as exc:
            raise ValueError("Evaluation fixture path escapes case directory.") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(str(case.input.get("content", "")), encoding="utf-8")
        return destination

    def _case_dir(self, case: EvalCase, *, suite: str) -> Path:
        safe_case = _safe_id(case.case_id)
        case_dir = self._workdir(suite) / safe_case
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def _suite_findings(self, suite_result: EvalSuiteResult) -> list[Finding]:
        findings: list[Finding] = []
        for case in suite_result.cases:
            if case.matched:
                continue
            findings.append(
                Finding(
                    id="EVAL_CASE_MISMATCH",
                    message="Evaluation case did not match expected behavior.",
                    severity=Severity.FAIL,
                    metadata=case.to_dict(),
                )
            )
        if not findings:
            findings.append(Finding("EVAL_SUITE_PASS", "Evaluation suite matched all expected outcomes.", Severity.INFO, metadata=suite_result.summary()))
        return findings


def _safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip().lower())
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-_") or "case"


def _repo_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
