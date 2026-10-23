"""R03-01 regression: immutable R00-03 evidence and current-active separation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from devpilot_core.docs_governance.mp132_historical import (
    ARCHIVE,
    SOURCE_ARCHIVE_SHA,
    load_verified_r00_at_close,
)


ROOT = Path(__file__).resolve().parents[1]


def test_original_history_and_current_counts_remain_exact() -> None:
    historical = load_verified_r00_at_close(ROOT)
    current = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    assert len(historical["registry"]["documents"]) == 1752
    assert len(historical["rows"]) == 57
    assert historical["provenance"]["source_archive_sha256"] == SOURCE_ARCHIVE_SHA
    assert len(current["documents"]) == current["summary"]["documents_total"] == 1762
    assert current["current_micro_sprint"] == "MP132-R03-01/DOC-RECONCILIATION"
    assert historical["registry"]["current_micro_sprint"] == "MP132-R00-03/AUTHORITY-PUBLICATION"


def test_corrupted_at_close_artifact_is_blocked(tmp_path: Path) -> None:
    source = ROOT / ARCHIVE
    destination = tmp_path / ARCHIVE
    destination.parent.mkdir(parents=True)
    mutated = bytearray(source.read_bytes())
    mutated[len(mutated) // 2] ^= 0x01
    destination.write_bytes(mutated)
    with pytest.raises(AssertionError, match="Frozen archive digest differs"):
        load_verified_r00_at_close(tmp_path)


def test_missing_at_close_artifact_does_not_fallback_to_live(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_verified_r00_at_close(tmp_path)
