from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE_PATH = Path(__file__).with_name("test_post_h_020_compliance_quality_gate.py")
_SPEC = importlib.util.spec_from_file_location("_post_h_020_compliance_quality_gate_source", _SOURCE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SOURCE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SOURCE)


def test_post_h_020_d_compliance_mapping_quality_gate_passes() -> None:
    _SOURCE.test_post_h_020_d_compliance_mapping_quality_gate_passes()


def test_post_h_020_d_quality_gate_blocks_certification_claims(tmp_path: Path) -> None:
    _SOURCE.test_post_h_020_d_quality_gate_blocks_certification_claims(tmp_path)


def test_post_h_020_d_audit_pack_manifest_includes_compliance_mapping_summary() -> None:
    _SOURCE.test_post_h_020_d_audit_pack_manifest_includes_compliance_mapping_summary()


def test_post_h_020_d_quality_gate_hardening_profile_includes_subgate() -> None:
    _SOURCE.test_post_h_020_d_quality_gate_hardening_profile_includes_subgate()
