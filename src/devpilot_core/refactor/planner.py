from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.policy import PolicyEngine, PolicyRequest, SecretGuard
from devpilot_core.review import CodeReviewEngine

_REFACTORABLE_SUFFIXES = {".py"}
_EXCLUDED_DIRS = (".git", ".venv", "__pycache__", ".pytest_cache", "outputs")


@dataclass(frozen=True)
class RefactorCandidate:
    """One safe-refactor candidate discovered without editing code.

    Purpose:
        Keep candidate evidence compact, path-scoped and serializable.

    Functioning:
        Captures structural signals such as long functions, long classes,
        broad functions and control-flow density. It does not include raw code.

    Integration:
        Consumed by RefactorPlanner and exposed through the `refactor-plan` CLI.

    PASS/BLOCK:
        PASS when candidate metadata remains inside workspace boundaries.
        BLOCK if candidate evidence would require emitting raw source content.

    Risks:
        Heuristic metadata is preliminary and must not be treated as a semantic
        refactor prescription without human review.
    """

    path: str
    kind: str
    name: str
    line_start: int
    line_end: int
    reason: str
    risk: str
    score: int
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "name": self.name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "reason": self.reason,
            "risk": self.risk,
            "score": self.score,
            "metrics": self.metrics,
        }


@dataclass(frozen=True)
class RefactorPlanStep:
    """One plan-only safe-refactor step.

    Purpose:
        Represent a reversible, auditable refactor action without executing it.

    Functioning:
        Declares intent, target, verification commands and rollback guidance.

    Integration:
        Serialized into CommandResult data for reports, events and SQLite
        history through the CLI.

    PASS/BLOCK:
        PASS when the step is plan-only and has tests plus rollback guidance.
        BLOCK if it claims to modify files or apply patches automatically.

    Risks:
        First version; it does not create concrete code patches.
    """

    step_id: str
    title: str
    description: str
    target: str
    phase: str
    required_tests: list[str]
    rollback: list[str]
    approval_required: bool = True
    modifies_files: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "phase": self.phase,
            "required_tests": self.required_tests,
            "rollback": self.rollback,
            "approval_required": self.approval_required,
            "modifies_files": self.modifies_files,
        }


@dataclass(frozen=True)
class RefactorPlannerConfig:
    """Configuration for FUNC-SPRINT-16 safe refactor planning."""

    max_files: int = 200
    max_file_bytes: int = 256_000
    long_function_lines: int = 60
    long_class_lines: int = 220
    broad_function_args: int = 5
    complex_node_threshold: int = 12


class RefactorPlanner:
    """Plan-only safe refactor planner for DevPilot Local.

    Purpose:
        Produce reversible refactor plans without modifying code, applying
        patches, invoking models, executing tests or calling external services.

    Functioning:
        Validates the target with PolicyEngine, scans Python files using the
        standard-library AST, optionally runs the local CodeReviewEngine as a
        precondition, derives structural candidates and generates a plan with
        required tests and rollback commands.

    Integration:
        Exposed by the `refactor-plan` CLI. Results follow CommandResult and
        can be persisted as reports, events and SQLite history through the CLI.

    Role in DevPilot:
        Bridge between dry-run patch/code review and future safe refactor
        automation. It makes refactor intent explicit before any execution.

    Commands:
        `python -m devpilot_core refactor-plan --target src/devpilot_core/review --goal "Extract shared path helpers" --json`

    PASS:
        Target is allowed, plan is generated, dry_run=true, files_modified=0,
        patch_generated=false, tests and rollback are declared.

    BLOCK:
        Target outside workspace, denied file/path, secret-like goal, unreadable
        target or any attempt to execute/apply changes.

    Risks:
        Preliminary heuristic planner. It is not a semantic refactoring engine,
        not an IDE refactorer, not a type checker and not a patch generator.
    """

    def __init__(self, root: Path, *, config: RefactorPlannerConfig | None = None) -> None:
        self.root = root.resolve()
        self.config = config or RefactorPlannerConfig()
        self.secret_guard = SecretGuard()

    def plan(self, target: str | Path = ".", *, goal: str = "", include_code_review: bool = True) -> CommandResult:
        findings: list[Finding] = []
        target_display = str(target).replace("\\", "/")

        goal_scan = self.secret_guard.scan_text(goal, subject="refactor-goal")
        if goal_scan.effect.value in {"block", "deny"}:
            return CommandResult(
                command="refactor-plan",
                ok=False,
                exit_code=ExitCode.BLOCK,
                message="Refactor planning blocked by policy before analysis.",
                data={"summary": {"target": target_display, "dry_run": True, "files_modified": 0, "patch_generated": False}},
                findings=[goal_scan.to_finding()],
            )

        policy = PolicyEngine(self.root).evaluate(PolicyRequest(action="read", path=str(target), dry_run=True))
        if not policy.ok:
            return CommandResult(
                command="refactor-plan",
                ok=False,
                exit_code=policy.exit_code,
                message="Refactor planning blocked by path policy.",
                data={"summary": {"target": target_display, "dry_run": True, "files_modified": 0, "patch_generated": False}, "policy": policy.data},
                findings=policy.findings,
            )

        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.root / target_path
        target_path = target_path.resolve()
        if not target_path.exists():
            return CommandResult(
                command="refactor-plan",
                ok=False,
                exit_code=ExitCode.FAIL,
                message="Refactor planning target does not exist.",
                data={"summary": {"target": _display_path(target_path, self.root), "dry_run": True, "files_modified": 0, "patch_generated": False}},
                findings=[Finding("REFACTOR_TARGET_NOT_FOUND", "Target path does not exist.", Severity.FAIL, path=_display_path(target_path, self.root))],
            )

        files = self._candidate_files(target_path)
        if not files:
            findings.append(Finding("REFACTOR_NO_REFACTORABLE_FILES", "No refactorable Python files were found for the target.", Severity.WARNING, path=_display_path(target_path, self.root)))

        candidates: list[RefactorCandidate] = []
        for path in files:
            candidates.extend(self._analyze_python_file(path, findings))

        code_review_summary: dict[str, Any] | None = None
        if include_code_review:
            review = CodeReviewEngine(self.root).review(_display_path(target_path, self.root))
            code_review_summary = review.data.get("summary", {}) if isinstance(review.data, dict) else {}
            for finding in review.findings:
                if finding.severity in {Severity.BLOCK, Severity.FAIL}:
                    findings.append(
                        Finding(
                            "REFACTOR_PRECONDITION_CODE_REVIEW_FINDING",
                            "Code review found blocking/failing issues; remediate before refactor execution.",
                            Severity.WARNING,
                            path=finding.path,
                            metadata={"source_finding_id": finding.id},
                        )
                    )

        plan_steps = self._build_steps(target_path, goal=goal, candidates=candidates)
        if not candidates:
            findings.append(Finding("REFACTOR_PLAN_CONSERVATIVE", "No structural candidates were found; generated a conservative validation-first plan.", Severity.INFO, path=_display_path(target_path, self.root)))

        exit_code = exit_code_for_findings(findings)
        ok = exit_code == ExitCode.PASS
        summary = {
            "target": _display_path(target_path, self.root),
            "goal": goal or "General safe refactor planning",
            "files_analyzed": len(files),
            "candidates_total": len(candidates),
            "steps_total": len(plan_steps),
            "findings_total": len(findings),
            "dry_run": True,
            "plan_only": True,
            "files_modified": 0,
            "patch_generated": False,
            "tests_required": True,
            "approval_required_for_execution": True,
        }
        data = {
            "summary": summary,
            "candidates": [candidate.to_dict() for candidate in candidates],
            "plan": [step.to_dict() for step in plan_steps],
            "verification": _verification_commands(_display_path(target_path, self.root)),
            "rollback": _rollback_guidance(_display_path(target_path, self.root)),
            "preconditions": {
                "code_review_summary": code_review_summary,
                "policy_checked": True,
                "llm_required": False,
                "external_api_used": False,
            },
            "preliminary": True,
            "notes": [
                "FUNC-SPRINT-16 Safe Refactor Planner is plan-only and never modifies files.",
                "The plan must be reviewed by a human before any future apply/refactor flow.",
                "No raw source contents are emitted in the CommandResult.",
            ],
        }
        return CommandResult(
            command="refactor-plan",
            ok=ok,
            exit_code=exit_code,
            message="Safe refactor plan generated in plan-only mode." if ok else "Safe refactor plan generated with findings.",
            data=data,
            findings=findings or [Finding("REFACTOR_PLAN_PASS", "Safe refactor plan generated without blocking/failing findings.", Severity.INFO)],
        )

    def _candidate_files(self, target: Path) -> list[Path]:
        if target.is_file():
            return [target] if _is_refactorable(target) and target.stat().st_size <= self.config.max_file_bytes else []
        files: list[Path] = []
        for path in sorted(target.rglob("*")):
            if _is_inside_excluded_dir(path, self.root):
                continue
            if path.is_file() and _is_refactorable(path) and path.stat().st_size <= self.config.max_file_bytes:
                files.append(path)
            if len(files) >= self.config.max_files:
                break
        return files

    def _analyze_python_file(self, path: Path, findings: list[Finding]) -> list[RefactorCandidate]:
        rel = _display_path(path, self.root)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError as exc:
            findings.append(Finding("REFACTOR_PYTHON_SYNTAX_ERROR", "Python syntax error blocks safe refactor planning for this file.", Severity.FAIL, path=rel, metadata={"line": exc.lineno or 0}))
            return []
        except OSError as exc:
            findings.append(Finding("REFACTOR_FILE_READ_FAILED", str(exc), Severity.WARNING, path=rel))
            return []

        candidates: list[RefactorCandidate] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidates.extend(self._function_candidates(node, rel))
            elif isinstance(node, ast.ClassDef):
                candidates.extend(self._class_candidates(node, rel))
        return sorted(candidates, key=lambda item: (-item.score, item.path, item.line_start))

    def _function_candidates(self, node: ast.FunctionDef | ast.AsyncFunctionDef, path: str) -> list[RefactorCandidate]:
        start = int(getattr(node, "lineno", 0) or 0)
        end = int(getattr(node, "end_lineno", start) or start)
        length = max(0, end - start + 1)
        args_count = len(node.args.args) + len(node.args.kwonlyargs) + len(node.args.posonlyargs)
        complexity_nodes = sum(1 for child in ast.walk(node) if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match, ast.BoolOp)))
        candidates: list[RefactorCandidate] = []
        if length >= self.config.long_function_lines:
            candidates.append(
                RefactorCandidate(
                    path=path,
                    kind="function",
                    name=node.name,
                    line_start=start,
                    line_end=end,
                    reason="Long function; consider extracting cohesive helper functions.",
                    risk="medium",
                    score=length,
                    metrics={"lines": length, "args": args_count, "complexity_nodes": complexity_nodes},
                )
            )
        if args_count > self.config.broad_function_args:
            candidates.append(
                RefactorCandidate(
                    path=path,
                    kind="function",
                    name=node.name,
                    line_start=start,
                    line_end=end,
                    reason="Broad function signature; consider parameter object or clearer boundary.",
                    risk="medium",
                    score=args_count * 10,
                    metrics={"lines": length, "args": args_count, "complexity_nodes": complexity_nodes},
                )
            )
        if complexity_nodes >= self.config.complex_node_threshold:
            candidates.append(
                RefactorCandidate(
                    path=path,
                    kind="function",
                    name=node.name,
                    line_start=start,
                    line_end=end,
                    reason="High control-flow density; consider splitting decision branches.",
                    risk="medium_high",
                    score=complexity_nodes * 10,
                    metrics={"lines": length, "args": args_count, "complexity_nodes": complexity_nodes},
                )
            )
        return candidates

    def _class_candidates(self, node: ast.ClassDef, path: str) -> list[RefactorCandidate]:
        start = int(getattr(node, "lineno", 0) or 0)
        end = int(getattr(node, "end_lineno", start) or start)
        length = max(0, end - start + 1)
        methods = [child for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if length < self.config.long_class_lines and len(methods) < 12:
            return []
        return [
            RefactorCandidate(
                path=path,
                kind="class",
                name=node.name,
                line_start=start,
                line_end=end,
                reason="Large class boundary; consider extracting services, policies or value objects.",
                risk="medium_high",
                score=length + len(methods) * 10,
                metrics={"lines": length, "methods": len(methods)},
            )
        ]

    def _build_steps(self, target: Path, *, goal: str, candidates: list[RefactorCandidate]) -> list[RefactorPlanStep]:
        target_rel = _display_path(target, self.root)
        tests = _verification_commands(target_rel)
        rollback = _rollback_guidance(target_rel)
        steps: list[RefactorPlanStep] = [
            RefactorPlanStep(
                step_id="RF-001",
                title="Freeze baseline and inspect current behavior",
                description="Run the current quality gates before changing code and capture current git status.",
                target=target_rel,
                phase="baseline",
                required_tests=tests,
                rollback=rollback,
            )
        ]
        top_candidates = candidates[:5]
        for index, candidate in enumerate(top_candidates, start=2):
            steps.append(
                RefactorPlanStep(
                    step_id=f"RF-{index:03d}",
                    title=f"Plan focused refactor for {candidate.kind} `{candidate.name}`",
                    description=f"Address candidate at {candidate.path}:{candidate.line_start}-{candidate.line_end}. Reason: {candidate.reason}",
                    target=candidate.path,
                    phase="plan",
                    required_tests=tests,
                    rollback=rollback,
                )
            )
        final_index = len(steps) + 1
        steps.append(
            RefactorPlanStep(
                step_id=f"RF-{final_index:03d}",
                title="Define implementation boundary and approval gate",
                description="Convert this plan into a reviewed patch only after human approval; keep changes small, reversible and covered by tests.",
                target=target_rel,
                phase="approval",
                required_tests=tests,
                rollback=rollback,
            )
        )
        steps.append(
            RefactorPlanStep(
                step_id=f"RF-{final_index + 1:03d}",
                title="Post-refactor verification and rollback decision",
                description="After a future manual refactor, rerun all gates and rollback if tests, policy, MIASI or evaluation fail.",
                target=target_rel,
                phase="verification",
                required_tests=tests,
                rollback=rollback,
            )
        )
        return steps


def _verification_commands(target: str) -> list[str]:
    return [
        "python -m pytest -q",
        "python -m devpilot_core code-review --target " + target + " --json",
        "python -m devpilot_core patch-review --patch-file <future-reviewed.patch> --json",
        "python -m devpilot_core miasi validate --json",
        "python -m devpilot_core eval run --json",
    ]


def _rollback_guidance(target: str) -> list[str]:
    return [
        "git status --short",
        "git diff -- " + target,
        "git restore --source=HEAD -- " + target,
        "python -m pytest -q",
    ]


def _is_refactorable(path: Path) -> bool:
    return path.suffix.lower() in _REFACTORABLE_SUFFIXES


def _is_inside_excluded_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in _EXCLUDED_DIRS for part in parts[:-1] if part)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")
