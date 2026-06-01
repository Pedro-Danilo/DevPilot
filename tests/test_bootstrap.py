from pathlib import Path

from devpilot_core.cli import check_required_artifacts


def test_required_pre_code_artifacts_exist():
    root = Path(__file__).resolve().parents[1]
    result = check_required_artifacts(root)
    assert result["ok"] is True
