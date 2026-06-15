from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.review import CodeReviewEngine, PatchReviewEngine


class ReviewApplicationService:
    """Application-facing review facade for dry-run/static review flows."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def code_review(self, *, target: str | Path = ".") -> CommandResult:
        return CodeReviewEngine(self.root).review(target)

    def patch_review(self, *, patch_file: str | Path | None = None, patch_text: str | None = None) -> CommandResult:
        return PatchReviewEngine(self.root).review(patch_file=patch_file, patch_text=patch_text)
