"""API contract tests."""

import asyncio
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI

from local_llm_node.api import machine_info
from local_llm_node.backends.base import InferenceBackend
from local_llm_node.exceptions import BackendUnavailableError, ModelNotFoundError
from local_llm_node.main import create_app
from local_llm_node.schemas import (
    BackendHealth,
    GenerateRequest,
    GenerateResponse,
    Model,
    ModelDetails,
)


class FakeBackend(InferenceBackend):
    """Provide deterministic backend behavior for API tests."""

    def __init__(
        self,
        backend_health: BackendHealth,
        models: list[Model] | None = None,
        list_error: BackendUnavailableError | None = None,
        generate_response: GenerateResponse | None = None,
        generate_error: BackendUnavailableError | ModelNotFoundError | None = None,
    ) -> None:
        """Configure the health, model-list and generation responses."""
        self._backend_health = backend_health
        self._models = models or []
        self._list_error = list_error
        self._generate_response = generate_response or GenerateResponse(
            answer="",
            time_elapsed_ms=0,
        )
        self._generate_error = generate_error
        self.generate_request: GenerateRequest | None = None

    async def health(self) -> BackendHealth:
        """Return the configured backend health."""
        return self._backend_health

    async def list_models(self) -> list[Model]:
        """Return models or raise the configured error."""
        if self._list_error is not None:
            raise self._list_error
        return self._models

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Return a generated response or raise the configured error."""
        self.generate_request = request
        if self._generate_error is not None:
            raise self._generate_error
        return self._generate_response


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


def post(application: FastAPI, path: str, body: dict[str, object]) -> httpx.Response:
    """Issue an in-process POST request to an ASGI application."""

    async def execute_request() -> httpx.Response:
        """Send the JSON request with an asynchronous ASGI transport."""
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post(path, json=body)

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


def test_generate_returns_answer_and_model_execution_time() -> None:
    """The generate endpoint forwards the prompt and returns its result."""
    backend = FakeBackend(
        BackendHealth(name="ollama", status="available"),
        generate_response=GenerateResponse(
            answer="La luce blu si disperde più delle altre frequenze.",
            time_elapsed_ms=245,
        ),
    )

    response = post(
        create_app(inference_backend=backend),
        "/generate",
        {
            "model_name": "gemma3:1b",
            "prompt": "Perché il cielo è blu?",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "La luce blu si disperde più delle altre frequenze.",
        "time_elapsed_ms": 245,
    }
    assert backend.generate_request == GenerateRequest(
        model_name="gemma3:1b",
        prompt="Perché il cielo è blu?",
        thinking=False,
    )


def test_generate_returns_404_for_an_unknown_model() -> None:
    """The generate endpoint reports unavailable model names as HTTP 404."""
    backend = FakeBackend(
        BackendHealth(name="ollama", status="available"),
        generate_error=ModelNotFoundError("The requested model was not found."),
    )

    response = post(
        create_app(inference_backend=backend),
        "/generate",
        {"model_name": "missing", "prompt": "Hello"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "The requested model was not found."}


def test_generate_rejects_an_empty_prompt() -> None:
    """The generate endpoint requires a non-empty prompt."""
    backend = FakeBackend(BackendHealth(name="ollama", status="available"))

    response = post(
        create_app(inference_backend=backend),
        "/generate",
        {"model_name": "gemma3:1b", "prompt": ""},
    )

    assert response.status_code == 422


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
