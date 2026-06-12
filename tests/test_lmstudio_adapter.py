from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from devpilot_core import cli
from devpilot_core.cli_models import ExitCode
from devpilot_core.modeling import ModelAdapterRouter


def _workspace(root: Path, *, endpoint: str, enabled: bool = True) -> Path:
    (root / ".devpilot").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='lmstudio-fixture'\n", encoding="utf-8")
    (root / ".devpilot" / "providers.yaml").write_text(
        f'''schema_version: "2.0"
providers:
  - id: "mock"
    kind: "mock"
    enabled: true
    default_model: "mock-deterministic-v1"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented"
  - id: "ollama"
    kind: "local"
    enabled: false
    default_model: "fake-llama"
    endpoint: "http://localhost:11434"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "lmstudio"
    kind: "local"
    enabled: {str(enabled).lower()}
    default_model: "fake-openai-compatible"
    endpoint: "{endpoint}"
    external_api: false
    requires_api_key: false
    estimated_cost_per_1k_tokens_usd: 0.0
    status: "implemented-initial"
  - id: "openai"
    kind: "api"
    enabled: false
    default_model: "gpt-placeholder"
    endpoint: "https://api.openai.com"
    external_api: true
    requires_api_key: true
    api_key_env: "OPENAI_API_KEY"
    estimated_cost_per_1k_tokens_usd: 0.01
    status: "disabled"
''',
        encoding="utf-8",
    )
    return root


class _FakeLMStudioHandler(BaseHTTPRequestHandler):
    calls: list[str] = []

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        self.__class__.calls.append(f"GET {self.path}")
        if self.path == "/v1/models":
            self._send({"object": "list", "data": [{"id": "fake-openai-compatible", "object": "model"}]})
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        self.__class__.calls.append(f"POST {self.path}")
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        payload = json.loads(raw.decode("utf-8") or "{}")
        if self.path == "/v1/chat/completions":
            messages = payload.get("messages") or []
            prompt = str(messages[0].get("content", "")) if messages and isinstance(messages[0], dict) else ""
            response = "docs" if "Clasifica" in prompt else "respuesta lmstudio fake"
            self._send({
                "id": "chatcmpl-fake",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": response}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            })
            return
        if self.path == "/v1/embeddings":
            self._send({"data": [{"embedding": [0.4, 0.5, 0.6]}], "usage": {"total_tokens": 3}})
            return
        self.send_error(404)

    def _send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _FakeLMStudioServer:
    def __enter__(self):
        _FakeLMStudioHandler.calls = []
        self.server = HTTPServer(("127.0.0.1", 0), _FakeLMStudioHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://localhost:{self.server.server_address[1]}"
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @property
    def calls(self) -> list[str]:
        return list(_FakeLMStudioHandler.calls)


def test_lmstudio_health_unavailable_is_controlled(tmp_path: Path) -> None:
    root = _workspace(tmp_path, endpoint="http://localhost:9", enabled=True)

    result = ModelAdapterRouter(root).health(provider="lmstudio")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["availability"] == "unavailable"
    assert result.data["summary"]["external_api_used"] is False
    assert any(finding.id == "LMSTUDIO_HEALTH_UNAVAILABLE" for finding in result.findings)


def test_lmstudio_fake_server_generate_classify_embed_pass(tmp_path: Path) -> None:
    with _FakeLMStudioServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=True)
        router = ModelAdapterRouter(root)

        health = router.health(provider="lmstudio")
        generate = router.generate(prompt="resume este cambio", provider="lmstudio")
        classify = router.classify(text="documentacion tecnica", labels=("docs", "code"), provider="lmstudio")
        embed = router.embed(text="DevPilot", provider="lmstudio")

        assert health.ok is True
        assert health.data["summary"]["availability"] == "available"
        assert health.data["summary"]["openai_compatible"] is True
        assert generate.ok is True
        assert generate.data["result"]["content"] == "respuesta lmstudio fake"
        assert generate.data["summary"]["external_api_used"] is False
        assert classify.ok is True
        assert classify.data["result"]["label"] == "docs"
        assert embed.ok is True
        assert embed.data["result"]["embedding"] == [0.4, 0.5, 0.6]
        assert "GET /v1/models" in server.calls
        assert "POST /v1/chat/completions" in server.calls
        assert "POST /v1/embeddings" in server.calls


def test_lmstudio_disabled_provider_blocks_model_call_without_contacting_server(tmp_path: Path) -> None:
    with _FakeLMStudioServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=False)

        result = ModelAdapterRouter(root).generate(prompt="hello", provider="lmstudio")

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert result.findings[0].id == "MODEL_PROVIDER_DISABLED"
        assert server.calls == []


def test_lmstudio_remote_base_url_is_blocked_before_network(tmp_path: Path) -> None:
    root = _workspace(tmp_path, endpoint="https://api.openai.com", enabled=True)

    result = ModelAdapterRouter(root).health(provider="lmstudio")

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "MODEL_PROVIDER_LOCAL_ENDPOINT_NOT_LOCAL_BLOCKED" for finding in result.findings)
    assert result.data["summary"]["external_api_used"] is False


def test_lmstudio_secret_prompt_is_blocked_before_provider_call(tmp_path: Path) -> None:
    with _FakeLMStudioServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=True)

        result = ModelAdapterRouter(root).generate(prompt="api_key=sk-1234567890abcdef", provider="lmstudio")
        payload = json.dumps(result.to_dict())

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert any(finding.id == "SECRETGUARD_SECRET_DETECTED" for finding in result.findings)
        assert "sk-1234567890abcdef" not in payload
        assert server.calls == []


def test_lmstudio_health_cli_is_parseable_without_real_lmstudio(tmp_path: Path, monkeypatch, capsys) -> None:
    _workspace(tmp_path, endpoint="http://localhost:9", enabled=True)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["model", "health", "--provider", "lmstudio", "--timeout-seconds", "0.1", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["provider"] == "lmstudio"
    assert payload["data"]["summary"]["availability"] in {"available", "unavailable"}
    assert payload["data"]["summary"]["external_api_used"] is False
