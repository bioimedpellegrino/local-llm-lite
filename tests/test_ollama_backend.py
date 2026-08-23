"""Ollama backend tests."""

import asyncio
from typing import Any

import pytest

from local_llm_node.backends.ollama import OllamaBackend
from local_llm_node.exceptions import BackendUnavailableError


class StubOllamaBackend(OllamaBackend):
    """Return a deterministic payload without making HTTP requests."""

    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        error: BackendUnavailableError | None = None,
    ) -> None:
        """Configure the backend payload or error."""
        super().__init__(base_url="http://ollama:11434", timeout_seconds=1)
        self._payload = payload or {}
        self._error = error

    async def _get(self, path: str) -> dict[str, Any]:
        """Return the configured result for any Ollama path."""
        if self._error is not None:
            raise self._error
        return self._payload


def test_list_models_converts_ollama_payload() -> None:
    """Ollama field names are converted to the public model schema."""
    backend = StubOllamaBackend(
        payload={
            "models": [
                {
                    "name": "qwen3:8b",
                    "model": "qwen3:8b",
                    "modified_at": "2026-08-23T12:00:00Z",
                    "size": 5_200_000_000,
                    "digest": "abc123",
                    "details": {
                        "format": "gguf",
                        "family": "qwen3",
                        "families": ["qwen3"],
                        "parameter_size": "8B",
                        "quantization_level": "Q4_K_M",
                    },
                }
            ]
        }
    )

    models = asyncio.run(backend.list_models())

    assert len(models) == 1
    assert models[0].name == "qwen3:8b"
    assert models[0].size_bytes == 5_200_000_000
    assert models[0].details.quantization_level == "Q4_K_M"


def test_health_reports_unavailable_backend() -> None:
    """Health converts connection failures to an unavailable state."""
    backend = StubOllamaBackend(error=BackendUnavailableError("unavailable"))

    health = asyncio.run(backend.health())

    assert health.status == "unavailable"
    assert health.version is None


def test_list_models_rejects_invalid_payload() -> None:
    """Malformed Ollama model lists raise an explicit backend error."""
    backend = StubOllamaBackend(payload={"models": "not-a-list"})

    with pytest.raises(BackendUnavailableError) as raised_error:
        asyncio.run(backend.list_models())

    assert str(raised_error.value) == "Ollama returned an invalid response."
