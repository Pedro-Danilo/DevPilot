"""R00-03 historical invariants: immutable verified source, never current-active.

R03-01 inherits 57 byte-approved documents and 1,752 registry records from
R00-03. Historical assertions must be evaluated on that genuine at-close input,
while successor tests evaluate the current registry separately.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


PREFIX = "docs/programs/DEVPL_MP_SUCCESSOR_132/v1_1_0_owner_approved_133/"
ARCHIVE = "docs/audits/MP132_R00_03_AT_CLOSE_VERIFIED.zip"
SOURCE_ARCHIVE_SHA = "c5f24e5824338957d368b0310685d74afc60ad70a083d363bdb56b85cf5a784f"
APPROVED_MANIFEST_SHA = "9152eb97a87466bba06e0b358e3f379c072e61a017f12e0d8ad480690855a079"
VERIFIED_FIXTURE_SHA = "49761fbe4df17c82c994e24d9f9a01239966bb5112d2a167ce83a5ea46ac396f"
REGISTRY = ".devpilot/docs_governance/source_registry.json"
STATE = ".devpilot/project_state.json"
OVERLAY = ".devpilot/docs_governance/rebaseline_p0_overlay.json"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_verified_r00_at_close(root: Path) -> dict:
    """Independently verify SHA, CRC, 57 historical documents and strict R00 facts."""
    archive_path = root / ARCHIVE
    assert sha(archive_path.read_bytes()) == VERIFIED_FIXTURE_SHA, "Frozen archive digest differs"
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None, "Frozen archive CRC differs"
        assert len(archive.namelist()) == len(set(archive.namelist())) == 61
        payload = {name: archive.read(name) for name in archive.namelist()}

    provenance = json.loads(payload["PROVENANCE.json"])
    assert provenance["snapshot_kind"] == "R00_03_AUTHENTIC_USER_SUPPLIED_CLEAN_ZIP"
    assert provenance["source_archive_sha256"] == SOURCE_ARCHIVE_SHA
    assert provenance["source_archive_sha256_sidecar_verified"] is True
    assert provenance["approved_manifest_raw_sha256"] == APPROVED_MANIFEST_SHA
    assert provenance["historical_registry_records"] == 1752
    assert provenance["historical_program_documents"] == 57
    assert provenance["historical_approved_documents_canonical_lf_verified"] == 56
    assert provenance["raw_vs_normalized_lf_not_conflated"] is True

    registry = json.loads(payload[REGISTRY])
    state = json.loads(payload[STATE])
    overlay = json.loads(payload[OVERLAY])
    rows = [row for row in registry["documents"] if row["path"].startswith(PREFIX)]
    assert len(registry["documents"]) == registry["summary"]["documents_total"] == 1752
    assert len(rows) == len({row["doc_id"] for row in rows}) == len({row["path"] for row in rows}) == 57
    assert registry["current_micro_sprint"] == state["current_micro_sprint"] == "MP132-R00-03/AUTHORITY-PUBLICATION"
    assert registry["current_phase"] == state["current_phase"] == "DEVPL-MP-SUCCESSOR-132/R00-AUTHORITY-REBIND"
    expected = {"PROVENANCE.json", REGISTRY, STATE, OVERLAY} | {row["path"] for row in rows}
    assert set(payload) == expected
    assert set(provenance["files"]) == expected - {"PROVENANCE.json"}

    manifest_path = PREFIX + "6_trazabilidad/04_MANIFIESTO_INTEGRIDAD_132.md"
    manifest_raw = payload[manifest_path]
    assert sha(manifest_raw) == APPROVED_MANIFEST_SHA
    manifest = manifest_raw.decode("utf-8")
    verified = 0
    for name, raw in payload.items():
        if name == "PROVENANCE.json":
            continue
        entry = provenance["files"][name]
        assert entry["raw_sha256"] == sha(raw) and entry["raw_bytes"] == len(raw), name
        if name.startswith(PREFIX):
            assert raw.startswith(b"---"), name
            canonical = raw.replace(b"\r\n", b"\n")
            assert entry["canonical_lf_sha256"] == sha(canonical), name
            assert entry["canonical_lf_bytes"] == len(canonical), name
            if name != manifest_path:
                relative = name[len(PREFIX):]
                line = "| `" + relative + "` | " + str(len(canonical)) + " | `" + sha(canonical) + "` |"
                assert line in manifest, f"Historical approved content mismatch: {relative}"
                verified += 1
    assert verified == 56
    assert all(row["required_tests"] == ["tests/test_mp132_r00_03_authority.py"] for row in rows)
    return {"registry": registry, "state": state, "overlay": overlay, "rows": rows, "provenance": provenance}
