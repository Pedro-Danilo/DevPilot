from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReviewRule:
    """One deterministic review rule declared as data.

    ReviewRule is intentionally provider-agnostic: it does not call engines,
    mutate files, open network connections or depend on an LLM. The quality gate
    maps findings emitted by existing engines into these stable rules.
    """

    rule_id: str
    source: str
    title: str
    description: str
    finding_ids: tuple[str, ...]
    default_effect: str
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_id": self.rule_id,
            "source": self.source,
            "title": self.title,
            "description": self.description,
            "finding_ids": list(self.finding_ids),
            "default_effect": self.default_effect,
            "enabled": self.enabled,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass(frozen=True)
class ReviewRulePack:
    """Versioned group of review rules for repo quality gates.

    Sprint 39 keeps rule packs deterministic and local-first. They are data
    contracts that can evolve independently from CodeReviewEngine,
    PatchReviewEngine and RepoAnalyzer internals.
    """

    pack_id: str
    version: str
    title: str
    description: str
    rules: tuple[ReviewRule, ...]
    status: str = "implemented-initial"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "rules_total": len(self.rules),
            "rules": [rule.to_dict() for rule in self.rules],
        }


def default_review_rule_packs() -> tuple[ReviewRulePack, ...]:
    """Return the Sprint 39 default local rule packs."""

    return (
        ReviewRulePack(
            pack_id="repo-health-core",
            version="1.0.0",
            title="Repository health core rules",
            description="Maps RepoAnalyzer findings into dry-run gate decisions.",
            rules=(
                ReviewRule(
                    rule_id="QG-REPO-SECRET-LIKE-CONTENT",
                    source="repo_analyzer",
                    title="Secret-like repository content",
                    description="Secret-like content is blocking because raw credentials must never reach review reports.",
                    finding_ids=("REPO_ANALYZER_SECRET_LIKE_CONTENT",),
                    default_effect="block",
                ),
                ReviewRule(
                    rule_id="QG-REPO-SYNTAX-ERROR",
                    source="dependency_graph",
                    title="Python syntax errors",
                    description="Syntax errors from static import graph analysis fail the gate.",
                    finding_ids=("DEPENDENCY_GRAPH_SYNTAX_ERROR", "CODE_REVIEW_PYTHON_SYNTAX_ERROR"),
                    default_effect="fail",
                ),
                ReviewRule(
                    rule_id="QG-REPO-WARNINGS-ADVISORY",
                    source="repo_analyzer",
                    title="Repository analyzer warnings are advisory",
                    description="Large files, TODOs and missing nearby tests are warnings by default in Sprint 39.",
                    finding_ids=(
                        "REPO_ANALYZER_LARGE_FILES",
                        "REPO_ANALYZER_TODO_MARKERS",
                        "REPO_ANALYZER_MODULES_WITHOUT_NEAR_TESTS",
                        "REPO_ANALYZER_GIT_WORKTREE_CHANGES",
                    ),
                    default_effect="warning",
                ),
            ),
        ),
        ReviewRulePack(
            pack_id="code-review-safety",
            version="1.0.0",
            title="Deterministic code review safety rules",
            description="Maps CodeReviewEngine findings into dry-run gate decisions.",
            rules=(
                ReviewRule(
                    rule_id="QG-CODE-SECRET-LIKE-CONTENT",
                    source="code_review",
                    title="Secret-like code content",
                    description="Secret-like content detected by code review blocks the gate.",
                    finding_ids=("CODE_REVIEW_SECRET_LIKE_CONTENT",),
                    default_effect="block",
                ),
                ReviewRule(
                    rule_id="QG-CODE-DANGEROUS-EXECUTION",
                    source="code_review",
                    title="Dangerous dynamic execution patterns",
                    description="shell=True, os.system, eval and exec findings fail the gate.",
                    finding_ids=("CODE_REVIEW_SHELL_TRUE", "CODE_REVIEW_OS_SYSTEM", "CODE_REVIEW_EVAL", "CODE_REVIEW_EXEC"),
                    default_effect="fail",
                ),
                ReviewRule(
                    rule_id="QG-CODE-TODO-ADVISORY",
                    source="code_review",
                    title="TODO/FIXME markers",
                    description="TODO/FIXME markers are warnings and do not block by default.",
                    finding_ids=("CODE_REVIEW_TODO",),
                    default_effect="warning",
                ),
            ),
        ),
        ReviewRulePack(
            pack_id="patch-review-safety",
            version="1.0.0",
            title="Patch review safety rules",
            description="Maps PatchReviewEngine findings when a patch is supplied.",
            rules=(
                ReviewRule(
                    rule_id="QG-PATCH-SECRET-LIKE-CONTENT",
                    source="patch_review",
                    title="Secret-like patch content",
                    description="Secret-like content in a patch blocks the gate.",
                    finding_ids=("PATCH_SECRET_LIKE_CONTENT",),
                    default_effect="block",
                ),
                ReviewRule(
                    rule_id="QG-PATCH-RISKY-CODE",
                    source="patch_review",
                    title="Risky added code",
                    description="Risky code patterns in additions fail the gate.",
                    finding_ids=("PATCH_RISKY_SHELL_TRUE", "PATCH_RISKY_OS_SYSTEM", "PATCH_RISKY_EVAL", "PATCH_RISKY_EXEC"),
                    default_effect="fail",
                ),
                ReviewRule(
                    rule_id="QG-PATCH-DESTRUCTIVE-CHANGE-ADVISORY",
                    source="patch_review",
                    title="Destructive or binary patch markers",
                    description="Deletes and binary changes are warnings in dry-run until patch preflight matures.",
                    finding_ids=("PATCH_DELETES_FILE", "PATCH_BINARY_CHANGE"),
                    default_effect="warning",
                ),
            ),
        ),
        ReviewRulePack(
            pack_id="policy-safety",
            version="1.0.0",
            title="Policy safety rules",
            description="Maps PolicyEngine findings used by repo quality gate.",
            rules=(
                ReviewRule(
                    rule_id="QG-POLICY-BLOCK",
                    source="policy",
                    title="Policy block",
                    description="Any policy block blocks the gate.",
                    finding_ids=("POLICY_DANGEROUS_ACTION_BLOCKED", "PATHGUARD_OUTSIDE_ROOT", "SECRETGUARD_SECRET_DETECTED"),
                    default_effect="block",
                ),
            ),
        ),
    )


def rule_index(packs: tuple[ReviewRulePack, ...] | None = None) -> dict[str, ReviewRule]:
    """Index enabled rules by finding id."""

    result: dict[str, ReviewRule] = {}
    for pack in packs or default_review_rule_packs():
        for rule in pack.rules:
            if not rule.enabled:
                continue
            for finding_id in rule.finding_ids:
                result[finding_id] = rule
    return result


def serialize_rule_packs(packs: tuple[ReviewRulePack, ...] | None = None) -> list[dict[str, Any]]:
    """Return JSON-serializable rule-pack declarations."""

    return [pack.to_dict() for pack in (packs or default_review_rule_packs())]
