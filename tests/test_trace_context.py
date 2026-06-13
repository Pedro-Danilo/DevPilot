from __future__ import annotations

import json

from devpilot_core.cli_models import Finding, Severity
from devpilot_core.observability.tracing import (
    REDACTED,
    SpanRecord,
    SpanStatus,
    TraceContext,
    new_run_id,
    new_span_id,
    new_trace_id,
    sanitize_span_payload,
)


def test_trace_context_is_serializable_with_injected_ids_and_redacted_metadata() -> None:
    context = TraceContext.start(
        command="agent run requirements",
        trace_id="trace_static",
        run_id="run_static",
        root_span_id="span_root",
        metadata={"access_token": "ghp_1234567890abcdef", "workspace": "demo"},
        clock=lambda: "2026-06-13T00:00:00Z",
    )

    payload = context.to_dict()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["trace_id"] == "trace_static"
    assert payload["run_id"] == "run_static"
    assert payload["root_span_id"] == "span_root"
    assert payload["metadata"]["access_token"] == REDACTED
    assert "ghp_1234567890abcdef" not in encoded


def test_span_record_supports_parent_child_and_finish_duration() -> None:
    context = TraceContext.start(
        command="model generate",
        trace_id="trace_parent",
        run_id="run_parent",
        root_span_id="span_root",
        clock=lambda: "2026-06-13T00:00:00Z",
    )
    child = context.child_span(
        name="Mock model call",
        span_type="model.call",
        span_id="span_child",
        payload={"provider": "mock", "model": "mock-deterministic-v1"},
        started_at="2026-06-13T00:00:00Z",
    )
    finished = child.finish(status=SpanStatus.OK, ended_at="2026-06-13T00:00:02Z")

    payload = finished.to_dict()

    assert payload["trace_id"] == "trace_parent"
    assert payload["run_id"] == "run_parent"
    assert payload["span_id"] == "span_child"
    assert payload["parent_span_id"] == "span_root"
    assert payload["status"] == "ok"
    assert payload["duration_ms"] == 2000
    assert payload["payload"]["provider"] == "mock"


def test_span_payload_sanitization_redacts_secrets_raw_prompts_and_outputs() -> None:
    payload = {
        "prompt": "Explain token=hf_1234567890abcdef",
        "raw_output": "secret result",
        "safe_summary": {"requirements_total": 3},
        "nested": {"authorization": "Bearer abcdefghijklmnop"},
    }

    sanitized = sanitize_span_payload(payload)
    encoded = json.dumps(sanitized, sort_keys=True)

    assert sanitized["prompt"] == REDACTED
    assert sanitized["raw_output"] == REDACTED
    assert sanitized["nested"]["authorization"] == REDACTED
    assert sanitized["safe_summary"] == {"requirements_total": 3}
    assert "hf_1234567890abcdef" not in encoded
    assert "secret result" not in encoded


def test_span_record_redacts_findings_and_metadata_before_serialization() -> None:
    span = SpanRecord(
        trace_id="trace_findings",
        run_id="run_findings",
        span_id="span_findings",
        parent_span_id=None,
        name="Policy check",
        span_type="policy.check",
        status=SpanStatus.BLOCK,
        metadata={"api_key": "sk-1234567890abcdef"},
        payload={"message": "blocked"},
        findings=[Finding(id="SECRET", message="token=hf_1234567890abcdef", severity=Severity.BLOCK)],
    )

    payload = span.to_dict()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["metadata"]["api_key"] == REDACTED
    assert "sk-1234567890abcdef" not in encoded
    assert "hf_1234567890abcdef" not in encoded
    assert payload["findings"][0]["severity"] == "block"


def test_id_helpers_are_prefixed_and_support_injected_factory() -> None:
    assert new_trace_id(lambda: "abc") == "trace_abc"
    assert new_span_id(lambda: "span_existing") == "span_existing"
    assert new_run_id(lambda: "xyz") == "run_xyz"
