from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from devpilot_core.remote import SecureTransportDesignQualityGate, SecureTransportDesignValidationOptions, SecureTransportDesignValidator


ROOT = Path(__file__).resolve().parents[1]


def test_validator_does_not_open_socket_or_url_connection() -> None:
    with patch("socket.socket", side_effect=AssertionError("socket must not be opened")), patch(
        "urllib.request.urlopen", side_effect=AssertionError("urlopen must not be called")
    ):
        validator_result = SecureTransportDesignValidator(ROOT).validate()
        gate_result = SecureTransportDesignQualityGate(ROOT).run()

    assert validator_result.ok is True
    assert gate_result.ok is True
    assert validator_result.data["summary"]["network_used"] is False
    assert validator_result.data["summary"]["sockets_opened"] is False
    assert gate_result.data["summary"]["network_used"] is False
    assert gate_result.data["summary"]["sockets_opened"] is False


def test_static_no_network_scan_reports_remote_package_without_forbidden_hits() -> None:
    result = SecureTransportDesignValidator(ROOT).validate()

    scan = result.data["no_network_static_scan"]
    assert scan["ok"] is True
    assert scan["network_used"] is False
    assert scan["external_api_used"] is False
    assert scan["sockets_opened"] is False
    assert scan["forbidden_network_primitives_total"] == 0
    assert "src/devpilot_core/remote/transport_design.py" in scan["scanned_files"]


def test_static_no_network_scan_blocks_forbidden_socket_import(tmp_path: Path) -> None:
    bad_package = tmp_path / "remote"
    bad_package.mkdir()
    (bad_package / "bad_transport.py").write_text(
        "import socket\n\ndef connect():\n    return socket.socket()\n",
        encoding="utf-8",
    )
    options = SecureTransportDesignValidationOptions(
        requirements_path=str(ROOT / ".devpilot/remote/secure_transport_requirements.json"),
        requirements_schema_path=str(ROOT / "docs/schemas/secure_transport_requirements.schema.json"),
        protocol_matrix_path=str(ROOT / ".devpilot/remote/secure_transport_protocol_decision_matrix.json"),
        protocol_matrix_schema_path=str(ROOT / "docs/schemas/secure_transport_design.schema.json"),
        key_lifecycle_path=str(ROOT / ".devpilot/remote/secure_transport_key_lifecycle.json"),
        key_lifecycle_schema_path=str(ROOT / "docs/schemas/secure_transport_key_lifecycle.schema.json"),
        validation_report_schema_path=str(ROOT / "docs/schemas/secure_transport_validation_report.schema.json"),
        static_scan_roots=(str(bad_package),),
    )

    result = SecureTransportDesignValidator(ROOT, options=options).validate()

    assert result.ok is False
    finding_ids = {finding.id for finding in result.findings}
    assert "SECURE_TRANSPORT_FORBIDDEN_NETWORK_PRIMITIVE" in finding_ids
    assert result.data["no_network_static_scan"]["forbidden_network_primitives_total"] >= 1
