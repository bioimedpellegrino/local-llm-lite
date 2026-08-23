"""API contract tests."""

import asyncio
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI

from local_llm_node.api import machine_info
from local_llm_node.backends.base import InferenceBackend
from local_llm_node.exceptions import BackendUnavailableError
from local_llm_node.main import create_app
from local_llm_node.schemas import BackendHealth, Model, ModelDetails


class FakeBackend(InferenceBackend):
    """Provide deterministic backend behavior for API tests."""

    def __init__(
        self,
        backend_health: BackendHealth,
        models: list[Model] | None = None,
        list_error: BackendUnavailableError | None = None,
    ) -> None:
        """Configure the health and model-list responses."""
        self._backend_health = backend_health
        self._models = models or []
        self._list_error = list_error

    async def health(self) -> BackendHealth:
        """Return the configured backend health."""
        return self._backend_health

    async def list_models(self) -> list[Model]:
        """Return models or raise the configured error."""
        if self._list_error is not None:
            raise self._list_error
        return self._models


def get(application: FastAPI, path: str) -> httpx.Response:
    """Issue an in-process GET request to an ASGI application."""

    async def execute_request() -> httpx.Response:
        """Send the request with an asynchronous ASGI transport."""
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(path)

    return asyncio.run(execute_request())


def test_health_reports_available_backend() -> None:
    """The health endpoint reports an available Ollama backend."""
    backend = FakeBackend(
        BackendHealth(name="ollama", status="available", version="1.2.3")
    )

    response = get(create_app(inference_backend=backend), "/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "local-llm-node",
        "version": "0.1.0",
        "backend": {
            "name": "ollama",
            "status": "available",
            "version": "1.2.3",
        },
    }


def test_health_is_degraded_when_backend_is_unavailable() -> None:
    """The API stays healthy while clearly reporting backend degradation."""
    backend = FakeBackend(BackendHealth(name="ollama", status="unavailable"))

    response = get(create_app(inference_backend=backend), "/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["backend"]["status"] == "unavailable"


def test_model_list_returns_backend_models() -> None:
    """The model-list endpoint returns typed model metadata."""
    model = Model(
        name="qwen3:8b",
        model="qwen3:8b",
        modified_at=datetime(2026, 8, 23, tzinfo=UTC),
        size_bytes=5_200_000_000,
        digest="abc123",
        details=ModelDetails(
            format="gguf",
            family="qwen3",
            families=["qwen3"],
            parameter_size="8B",
            quantization_level="Q4_K_M",
        ),
    )
    backend = FakeBackend(
        BackendHealth(name="ollama", status="available"),
        models=[model],
    )

    response = get(create_app(inference_backend=backend), "/model_list")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["models"][0]["name"] == "qwen3:8b"
    assert response.json()["models"][0]["size_bytes"] == 5_200_000_000


def test_model_list_returns_503_when_backend_is_unavailable() -> None:
    """The model-list endpoint exposes backend outages as HTTP 503."""
    backend = FakeBackend(
        BackendHealth(name="ollama", status="unavailable"),
        list_error=BackendUnavailableError("Ollama is unavailable."),
    )

    response = get(create_app(inference_backend=backend), "/model_list")

    assert response.status_code == 503
    assert response.json() == {"detail": "Ollama is unavailable."}


def test_machine_info_returns_visible_resources() -> None:
    """The machine endpoint returns the documented resource groups."""
    backend = FakeBackend(BackendHealth(name="ollama", status="available"))
    application = create_app(inference_backend=backend)

    body = machine_info().model_dump(mode="json")

    assert "/machine_info" in application.openapi()["paths"]
    assert "get" in application.openapi()["paths"]["/machine_info"]
    assert body["operating_system"]
    assert body["kernel_version"]
    assert body["cpu"]["logical_cores"] >= 1
    assert body["memory"]["total_bytes"] >= 0
    assert isinstance(body["gpus"], list)
