#!/usr/bin/env python3
"""Normalize Cline/OpenAI content blocks before forwarding to OpenWebUI."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import urljoin
from urllib import error, request

HOST = os.getenv("CLINE_PROXY_HOST", "127.0.0.1")
PORT = int(os.getenv("CLINE_PROXY_PORT", "4011"))
OPENWEBUI_CHAT_URL = os.getenv(
    "OPENWEBUI_CHAT_URL", "http://localhost:3000/api/chat/completions"
)
OPENWEBUI_BASE_URL = os.getenv("OPENWEBUI_BASE_URL")
WEBUI_API_KEY = os.getenv("WEBUI_API_KEY", "")
UPSTREAM_TIMEOUT_SECONDS = int(os.getenv("CLINE_PROXY_UPSTREAM_TIMEOUT", "300"))

# Performance caps — keep context window small to avoid CPU offload
_DEFAULT_NUM_CTX = int(os.getenv("PROXY_DEFAULT_NUM_CTX", "4096"))
_DEFAULT_MAX_TOKENS = int(os.getenv("PROXY_DEFAULT_MAX_TOKENS", "512"))

if not OPENWEBUI_BASE_URL:
    marker = "/api/chat/completions"
    if marker in OPENWEBUI_CHAT_URL:
        OPENWEBUI_BASE_URL = OPENWEBUI_CHAT_URL.split(marker, 1)[0]
    else:
        OPENWEBUI_BASE_URL = "http://localhost:3000"


def normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                continue

            block_type = str(block.get("type", "")).lower()
            if block_type in {"text", "input_text"}:
                text_value = block.get("text") or block.get("input_text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value)

        return "\n".join(parts).strip()

    if isinstance(content, dict):
        for key in ("text", "content", "value"):
            value = content.get(key)
            if isinstance(value, str):
                return value

    return ""


def apply_perf_caps(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce sane context and token limits so inference stays fully on GPU."""
    original_model = payload.get("model")

    options = payload.get("options")
    if not isinstance(options, dict):
        options = {}

    # Hard-cap num_ctx even if clients send larger values (e.g., 32768).
    try:
        current_num_ctx = int(options.get("num_ctx", _DEFAULT_NUM_CTX))
    except (TypeError, ValueError):
        current_num_ctx = _DEFAULT_NUM_CTX
    options["num_ctx"] = min(current_num_ctx, _DEFAULT_NUM_CTX)

    # Cap max_tokens at top level (OpenAI-compatible payloads).
    try:
        current_max_tokens = int(payload.get("max_tokens", _DEFAULT_MAX_TOKENS))
    except (TypeError, ValueError):
        current_max_tokens = _DEFAULT_MAX_TOKENS
    payload["max_tokens"] = min(current_max_tokens, _DEFAULT_MAX_TOKENS)

    # Always set/cap num_predict for Ollama, even when client omits it.
    try:
        current_num_predict = int(options.get("num_predict", payload["max_tokens"]))
    except (TypeError, ValueError):
        current_num_predict = payload["max_tokens"]
    options["num_predict"] = min(current_num_predict, _DEFAULT_MAX_TOKENS)

    payload["options"] = options

    # Some clients use max_completion_tokens.
    if "max_completion_tokens" in payload:
        try:
            payload["max_completion_tokens"] = min(
                int(payload["max_completion_tokens"]), _DEFAULT_MAX_TOKENS
            )
        except (TypeError, ValueError):
            payload["max_completion_tokens"] = _DEFAULT_MAX_TOKENS

    # Temporary diagnostics: print effective caps sent upstream.
    print(
        "[proxy] caps"
        f" model={payload.get('model')}"
        f" model_in={original_model}"
        f" num_ctx={payload.get('options', {}).get('num_ctx')}"
        f" num_predict={payload.get('options', {}).get('num_predict')}"
        f" max_tokens={payload.get('max_tokens')}"
        f" max_completion_tokens={payload.get('max_completion_tokens')}",
        flush=True,
    )

    return payload


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return payload

    normalized_messages: List[Dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        normalized = dict(message)
        normalized["content"] = normalize_content(message.get("content", ""))
        normalized_messages.append(normalized)

    payload["messages"] = normalized_messages
    return payload


def _parse_json_object(value: Any) -> Dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


def unwrap_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Cline may wrap OpenAI payload under data/request fields.
    candidate = payload
    for key in ("data", "request"):
        nested = _parse_json_object(candidate.get(key))
        if nested:
            candidate = nested

    normalized = dict(candidate)

    if "model" not in normalized and isinstance(payload.get("modelId"), str):
        normalized["model"] = payload["modelId"]
    if "provider" not in normalized and isinstance(payload.get("providerId"), str):
        normalized["provider"] = payload["providerId"]

    if "messages" not in normalized and isinstance(payload.get("messages"), list):
        normalized["messages"] = payload["messages"]

    if "stream" not in normalized and isinstance(payload.get("stream"), bool):
        normalized["stream"] = payload["stream"]

    return normalized


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "ClineOpenWebUIProxy/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[proxy] " + fmt % args)

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _resolve_auth_header(self) -> str | None:
        auth_header = self.headers.get("Authorization")
        if not auth_header and WEBUI_API_KEY:
            auth_header = f"Bearer {WEBUI_API_KEY}"
        return auth_header

    def _forward(self, method: str, url: str, body: bytes | None = None) -> None:
        headers: Dict[str, str] = {}
        auth_header = self._resolve_auth_header()
        if auth_header:
            headers["Authorization"] = auth_header
        if body is not None:
            headers["Content-Type"] = "application/json"

        upstream_request = request.Request(url, data=body, headers=headers, method=method)

        with request.urlopen(upstream_request, timeout=UPSTREAM_TIMEOUT_SECONDS) as response:
            response_body = response.read()
            response_status = response.getcode()
            response_content_type = response.headers.get("Content-Type", "application/json")

        self.send_response(response_status)
        self.send_header("Content-Type", response_content_type)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_GET(self) -> None:  # noqa: N802
        try:
            allowed_prefixes = ("/api/models", "/api/v1/models", "/v1/models", "/models")
            if not self.path.startswith(allowed_prefixes):
                self._send_json(404, {"error": "not_found", "detail": self.path})
                return

            # OpenAI-compatible clients commonly call /v1/models; map it to OpenWebUI's models endpoint.
            target_path = self.path
            if self.path.startswith("/v1/models"):
                target_path = self.path.replace("/v1/models", "/api/models", 1)
            elif self.path.startswith("/models"):
                target_path = self.path.replace("/models", "/api/models", 1)

            target_url = urljoin(OPENWEBUI_BASE_URL, target_path)
            self._forward("GET", target_url)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._send_json(exc.code, {"error": "upstream_http_error", "detail": detail})
        except Exception as exc:  # pragma: no cover
            self._send_json(500, {"error": "proxy_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            raw_text = raw_body.decode("utf-8")
            payload = json.loads(raw_text)
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")

            payload = unwrap_payload(payload)
            payload = normalize_payload(payload)
            payload = apply_perf_caps(payload)
            self._forward("POST", OPENWEBUI_CHAT_URL, json.dumps(payload).encode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._send_json(exc.code, {"error": "upstream_http_error", "detail": detail})
        except Exception as exc:  # pragma: no cover
            self._send_json(
                500,
                {
                    "error": "proxy_error",
                    "detail": str(exc),
                    "hint": "Invalid wrapped payload. Expected OpenAI chat body or JSON object in data/request.",
                },
            )


if __name__ == "__main__":
    print(f"[proxy] listening on http://{HOST}:{PORT}")
    print(f"[proxy] forwarding to {OPENWEBUI_CHAT_URL}")
    ThreadingHTTPServer((HOST, PORT), ProxyHandler).serve_forever()
