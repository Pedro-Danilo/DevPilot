from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE_PATH = Path(__file__).with_name("test_post_h_020_compliance_mapping_schema.py")
_SPEC = importlib.util.spec_from_file_location("_post_h_020_compliance_mapping_schema_source", _SOURCE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SOURCE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SOURCE)


def test_post_h_020_a_control_mapping_schema_is_registered_and_validates_registry() -> None:
    _SOURCE.test_post_h_020_a_control_mapping_schema_is_registered_and_validates_registry()


def test_post_h_020_a_control_mappings_require_non_certifying_claims_and_evidence() -> None:
    _SOURCE.test_post_h_020_a_control_mappings_require_non_certifying_claims_and_evidence()


def test_post_h_020_a_control_mapping_schema_blocks_certification_claim() -> None:
    _SOURCE.test_post_h_020_a_control_mapping_schema_blocks_certification_claim()
