from __future__ import annotations

from enum import Enum
from typing import Final

from devpilot_core.cli_models import Severity


class SemanticSeverity(str, Enum):
    """Stable severity values emitted by the Policy/MIASI semantic report.

    POST-H-004-A keeps this enum intentionally aligned with DevPilot's
    normalized Finding severities while making the semantic report contract
    independent from CLI presentation details.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"


class SemanticRuleStatus(str, Enum):
    """Execution state for one semantic rule result.

    The validator is introduced later in POST-H-004-B/C/D. POST-H-004-A only
    defines the statuses so reports are machine-readable before rules exist.
    """

    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"
    NOT_APPLICABLE = "not-applicable"


SEMANTIC_SEVERITY_ORDER: Final[dict[SemanticSeverity, int]] = {
    SemanticSeverity.INFO: 0,
    SemanticSeverity.WARNING: 1,
    SemanticSeverity.ERROR: 2,
    SemanticSeverity.BLOCK: 3,
}

SEMANTIC_SEVERITY_TO_CLI_SEVERITY: Final[dict[SemanticSeverity, Severity]] = {
    SemanticSeverity.INFO: Severity.INFO,
    SemanticSeverity.WARNING: Severity.WARNING,
    SemanticSeverity.ERROR: Severity.ERROR,
    SemanticSeverity.BLOCK: Severity.BLOCK,
}

SEMANTIC_SEVERITY_TO_RULE_STATUS: Final[dict[SemanticSeverity, SemanticRuleStatus]] = {
    SemanticSeverity.INFO: SemanticRuleStatus.PASS,
    SemanticSeverity.WARNING: SemanticRuleStatus.WARNING,
    SemanticSeverity.ERROR: SemanticRuleStatus.ERROR,
    SemanticSeverity.BLOCK: SemanticRuleStatus.BLOCK,
}

VALID_SEMANTIC_SEVERITIES: Final[tuple[str, ...]] = tuple(item.value for item in SemanticSeverity)
VALID_SEMANTIC_RULE_STATUSES: Final[tuple[str, ...]] = tuple(item.value for item in SemanticRuleStatus)


def normalize_semantic_severity(value: str | SemanticSeverity | Severity) -> SemanticSeverity:
    """Normalize external severity values to the report contract enum."""

    raw = value.value if isinstance(value, (SemanticSeverity, Severity)) else str(value)
    normalized = raw.strip().lower()
    if normalized == "fail":
        # Semantic validation does not expose FAIL as a first-class report level.
        # FAIL from generic CommandResult maps to ERROR in semantic reports.
        normalized = SemanticSeverity.ERROR.value
    try:
        return SemanticSeverity(normalized)
    except ValueError as exc:
        raise ValueError(f"Unsupported semantic severity: {value!r}") from exc


def severity_to_rule_status(value: str | SemanticSeverity | Severity) -> SemanticRuleStatus:
    """Map one semantic severity to the rule status used in reports."""

    return SEMANTIC_SEVERITY_TO_RULE_STATUS[normalize_semantic_severity(value)]


def is_blocking_severity(value: str | SemanticSeverity | Severity) -> bool:
    """Return True when a semantic finding must block the gate."""

    return normalize_semantic_severity(value) in {SemanticSeverity.ERROR, SemanticSeverity.BLOCK}


def highest_semantic_severity(values: list[str | SemanticSeverity | Severity]) -> SemanticSeverity:
    """Return the strongest semantic severity in a collection."""

    if not values:
        return SemanticSeverity.INFO
    normalized = [normalize_semantic_severity(item) for item in values]
    return max(normalized, key=lambda item: SEMANTIC_SEVERITY_ORDER[item])
