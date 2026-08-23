"""Ollama inference backend."""

import logging
from typing import Any

import httpx
from pydantic import ValidationError

from local_llm_node.backends.base import InferenceBackend
from local_llm_node.exceptions import BackendUnavailableError
from local_llm_node.schemas import BackendHealth, Model, ModelDetails

logger = logging.getLogger(__name__)


class OllamaBackend(InferenceBackend):
    """Access models served by an Ollama HTTP API."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        """Configure the Ollama endpoint and request timeout."""
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def health(self) -> BackendHealth:
        """Return whether Ollama is reachable and its reported version."""
        try:
            response = await self._get("/api/version")
            version = response.get("version")
        except BackendUnavailableError:
            return BackendHealth(name="ollama", status="unavailable")

        return BackendHealth(
            name="ollama",
            status="available",
            version=version if isinstance(version, str) else None,
        )

    async def list_models(self) -> list[Model]:
        """Return the models registered in Ollama."""
        response = await self._get("/api/tags")
        models = response.get("models")
        if not isinstance(models, list):
            raise BackendUnavailableError("Ollama returned an invalid response.")

        try:
            return [self._parse_model(model) for model in models]
        except (KeyError, TypeError, ValidationError) as error:
            raise BackendUnavailableError(
                "Ollama returned an invalid model list."
            ) from error

    async def _get(self, path: str) -> dict[str, Any]:
        """Request and validate a JSON object from Ollama."""
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.get(path)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("Ollama request failed: %s", type(error).__name__)
            raise BackendUnavailableError("Ollama is unavailable.") from error

        if not isinstance(payload, dict):
            raise BackendUnavailableError("Ollama returned an invalid response.")
        return payload

    @staticmethod
    def _parse_model(model: Any) -> Model:
        """Convert an Ollama model payload into the public model schema."""
        if not isinstance(model, dict):
            raise TypeError("Ollama model entries must be objects.")

        details = model.get("details") or {}
        if not isinstance(details, dict):
            raise TypeError("Ollama model details must be an object.")

        return Model(
            name=model["name"],
            model=model["model"],
            modified_at=model["modified_at"],
            size_bytes=model["size"],
            digest=model["digest"],
            details=ModelDetails.model_validate(details),
        )
