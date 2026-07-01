from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE_PATH = Path(__file__).with_name("test_post_h_020_compliance_evidence_report.py")
_SPEC = importlib.util.spec_from_file_location("_post_h_020_compliance_evidence_report_source", _SOURCE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SOURCE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SOURCE)


def test_post_h_020_c_evidence_collector_is_local_and_does_not_execute_commands() -> None:
    _SOURCE.test_post_h_020_c_evidence_collector_is_local_and_does_not_execute_commands()


def test_post_h_020_c_report_is_schema_valid_and_non_certifying(tmp_path: Path) -> None:
    _SOURCE.test_post_h_020_c_report_is_schema_valid_and_non_certifying(tmp_path)


def test_post_h_020_c_report_surfaces_missing_evidence(tmp_path: Path) -> None:
    _SOURCE.test_post_h_020_c_report_surfaces_missing_evidence(tmp_path)


def test_post_h_020_c_cli_mapping_report_generates_outputs() -> None:
    _SOURCE.test_post_h_020_c_cli_mapping_report_generates_outputs()
