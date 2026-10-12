from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/program_rebaseline_117"
OVERLAY = ROOT / ".devpilot/docs_governance/rebaseline_p0_overlay.json"
REGISTRY = ROOT / ".devpilot/docs_governance/source_registry.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_p0_overlay_preserves_stop_and_has_historical_provenance():
    doc = load(OVERLAY)
    assert doc["schema_id"] == "devpilot.program_rebaseline.p0_authority_overlay.v1"
    assert doc["authority"]["multiprovider_stop"] == "ACTIVE"
    assert doc["authority_at_sync1_merge"]["mp_registry_state"] == "PENDING_MP_IMPORT"
    assert doc["authority_at_sync1_merge"]["mp_1b"] == "BLOCKED"
    assert doc["authority_at_sync1_merge"]["g1"] == "EXTERNAL_RECEIPT_GATED"
    assert doc["prospective_override_only"] is True
    assert len(doc["historical_greenfield"]) >= 10
    assert len(doc["historical_multiprovider"]) >= 5
    assert all(len(x["sha256"]) == 64 and x["original_preserved"] for name in ("historical_greenfield", "historical_multiprovider") for x in doc[name])


def test_p0_published_docs_are_byte_identical_to_manifest():
    doc = load(OVERLAY)
    assert len(doc["published_documents"]) >= 14
    for row in doc["published_documents"]:
        p = ROOT / row["path"]
        assert p.is_file(), row["path"]
        raw = p.read_bytes()
        canonical = raw.replace(b"\r\n", b"\n")
        assert hashlib.sha256(canonical).hexdigest() == row["sha256"], row["path"]


def test_p0_source_registry_rebind_is_complete_and_unique():
    entries = load(REGISTRY)["documents"]
    ids = [row["doc_id"] for row in entries if row["doc_id"].startswith("DEVPL-REB-") or row["doc_id"] == "ADR-DEVPL-REB-117"]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 15
    for row in entries:
        if row["doc_id"] not in ids:
            continue
        assert row["lifecycle"] == "active"
        assert row["path"].startswith(("docs/", ".devpilot/docs_governance/"))
        assert (ROOT / row["path"]).is_file()
        assert "tests/test_devpl_reb_p0_authority.py" in row["required_tests"]


def test_p0_no_early_release_or_mp_unfreeze():
    bridge = (DIR / "BRIDGE_MP_117.md").read_text(encoding="utf-8")
    gf = (DIR / "BRIDGE_GF_117.md").read_text(encoding="utf-8")
    publication = (DIR / "P0_PUBLICATION_118.md").read_text(encoding="utf-8")
    assert "STOP ACTIVE" in bridge
    assert "MP-1B BLOCKED" in bridge
    assert "REBASELINED_STOP/PARTIAL_ACCEPTANCE" in gf
    assert "RF004" in gf
    assert "P3-A" in bridge and "P3-B" in bridge and "P3-C" in bridge
    assert "MP Source Registry" in publication and "PENDING_MP_IMPORT" in publication
    assert "auditoría" in publication.lower()
