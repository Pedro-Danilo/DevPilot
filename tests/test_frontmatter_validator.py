from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.cli import main
from devpilot_core.cli_models import ExitCode
from devpilot_core.validators.frontmatter import validate_frontmatter_file


FIXTURES = Path(__file__).parent / "fixtures" / "docs"


def test_valid_frontmatter_passes():
    result = validate_frontmatter_file(FIXTURES / "valid_frontmatter.md", root=FIXTURES)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["has_frontmatter"] is True
    assert result.data["fields"]["doc_id"] == "DEVPL-TEST-001"


def test_missing_required_doc_id_fails():
    result = validate_frontmatter_file(FIXTURES / "invalid_frontmatter_missing_doc_id.md", root=FIXTURES)

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert any(finding.id == "FRONTMATTER_REQUIRED_FIELD_MISSING" for finding in result.findings)


def test_missing_frontmatter_fails():
    result = validate_frontmatter_file(FIXTURES / "missing_frontmatter.md", root=FIXTURES)

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL
    assert result.findings[0].id == "FRONTMATTER_MISSING"


def test_approved_without_approval_warns_by_default():
    result = validate_frontmatter_file(FIXTURES / "approved_without_approval.md", root=FIXTURES)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert any(finding.id == "FRONTMATTER_APPROVED_WITHOUT_APPROVAL" for finding in result.findings)


def test_approved_without_approval_fails_in_strict_mode():
    result = validate_frontmatter_file(
        FIXTURES / "approved_without_approval.md",
        root=FIXTURES,
        strict=True,
    )

    assert result.ok is False
    assert result.exit_code == ExitCode.FAIL


def test_validate_frontmatter_cli_json_pass(capsys):
    path = FIXTURES / "valid_frontmatter.md"
    exit_code = main(["validate-frontmatter", str(path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["command"] == "validate-frontmatter"
    assert payload["ok"] is True


def test_validate_frontmatter_cli_json_fail(capsys):
    path = FIXTURES / "invalid_frontmatter_missing_doc_id.md"
    exit_code = main(["validate-frontmatter", str(path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["command"] == "validate-frontmatter"
    assert payload["ok"] is False
    assert payload["findings"]
