from __future__ import annotations

from pathlib import Path

from .validator import DocumentationGovernanceValidationOptions, DocumentationGovernanceValidator


def validate_documentation_governance(root: Path, *, write_report: bool = False):
    """Facade for POST-H-009-B documentation governance validation."""

    return DocumentationGovernanceValidator(root, DocumentationGovernanceValidationOptions(write_report=write_report)).run()
