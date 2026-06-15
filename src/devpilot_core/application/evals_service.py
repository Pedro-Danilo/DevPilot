from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.evals import EvalRunner
from devpilot_core.modeling import ModelEvalRunner, ModelEvalRunnerConfig


class EvaluationApplicationService:
    """Application-facing offline evaluation facade."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def run_documentation(self, *, suite: str = "documentation", case_id: str | None = None) -> CommandResult:
        return EvalRunner(self.root).run(suite=suite, case_id=case_id)

    def run_model_matrix(
        self,
        *,
        suite: str = "model-local-smoke",
        provider: str = "mock",
        model: str | None = None,
        case_id: str | None = None,
        write_report: bool = False,
    ) -> CommandResult:
        return ModelEvalRunner(self.root, config=ModelEvalRunnerConfig(fallback_to_mock=False)).run(
            suite=suite,
            provider=provider,
            model=model,
            case_id=case_id,
            write_report=write_report,
        )
