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
    (root / "pyproject.toml").write_text("[project]\nname='ollama-fixture'\n", encoding="utf-8")
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
    enabled: {str(enabled).lower()}
    default_model: "fake-llama"
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


class _FakeOllamaHandler(BaseHTTPRequestHandler):
    calls: list[str] = []

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook
        self.__class__.calls.append(f"GET {self.path}")
        if self.path == "/api/tags":
            self._send({"models": [{"name": "fake-llama"}]})
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        self.__class__.calls.append(f"POST {self.path}")
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        payload = json.loads(raw.decode("utf-8") or "{}")
        if self.path == "/api/generate":
            prompt = str(payload.get("prompt", ""))
            response = "docs" if "Clasifica" in prompt else "respuesta local fake"
            self._send({"response": response, "done": True, "prompt_eval_count": 3, "eval_count": 2})
            return
        if self.path == "/api/embed":
            self._send({"embeddings": [[0.1, 0.2, 0.3]]})
            return
        self.send_error(404)

    def _send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _FakeOllamaServer:
    def __enter__(self):
        _FakeOllamaHandler.calls = []
        self.server = HTTPServer(("127.0.0.1", 0), _FakeOllamaHandler)
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
        return list(_FakeOllamaHandler.calls)


def test_ollama_health_unavailable_is_controlled(tmp_path: Path) -> None:
    root = _workspace(tmp_path, endpoint="http://localhost:9", enabled=True)

    result = ModelAdapterRouter(root).health(provider="ollama")

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.data["summary"]["availability"] == "unavailable"
    assert result.data["summary"]["external_api_used"] is False
    assert any(finding.id == "OLLAMA_HEALTH_UNAVAILABLE" for finding in result.findings)


def test_ollama_fake_server_generate_classify_embed_pass(tmp_path: Path) -> None:
    with _FakeOllamaServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=True)
        router = ModelAdapterRouter(root)

        health = router.health(provider="ollama")
        generate = router.generate(prompt="resume este cambio", provider="ollama")
        classify = router.classify(text="documentacion tecnica", labels=("docs", "code"), provider="ollama")
        embed = router.embed(text="DevPilot", provider="ollama")

        assert health.ok is True
        assert health.data["summary"]["availability"] == "available"
        assert generate.ok is True
        assert generate.data["result"]["content"] == "respuesta local fake"
        assert generate.data["summary"]["external_api_used"] is False
        assert classify.ok is True
        assert classify.data["result"]["label"] == "docs"
        assert embed.ok is True
        assert embed.data["result"]["embedding"] == [0.1, 0.2, 0.3]
        assert "GET /api/tags" in server.calls
        assert "POST /api/generate" in server.calls
        assert "POST /api/embed" in server.calls


def test_ollama_disabled_provider_blocks_model_call_without_contacting_server(tmp_path: Path) -> None:
    with _FakeOllamaServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=False)

        result = ModelAdapterRouter(root).generate(prompt="hello", provider="ollama")

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert result.findings[0].id == "MODEL_PROVIDER_DISABLED"
        assert server.calls == []


def test_ollama_secret_prompt_is_blocked_before_provider_call(tmp_path: Path) -> None:
    with _FakeOllamaServer() as server:
        root = _workspace(tmp_path, endpoint=server.endpoint, enabled=True)

        result = ModelAdapterRouter(root).generate(prompt="api_key=sk-1234567890abcdef", provider="ollama")
        payload = json.dumps(result.to_dict())

        assert result.ok is False
        assert result.exit_code == ExitCode.BLOCK
        assert any(finding.id == "SECRETGUARD_SECRET_DETECTED" for finding in result.findings)
        assert "sk-1234567890abcdef" not in payload
        assert server.calls == []


def test_ollama_health_cli_is_parseable_without_real_ollama(tmp_path: Path, monkeypatch, capsys) -> None:
    _workspace(tmp_path, endpoint="http://localhost:9", enabled=True)
    monkeypatch.chdir(tmp_path)

    exit_code = cli.main(["model", "health", "--provider", "ollama", "--timeout-seconds", "0.1", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["provider"] == "ollama"
    assert payload["data"]["summary"]["availability"] in {"available", "unavailable"}
    assert payload["data"]["summary"]["external_api_used"] is False
