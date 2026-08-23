"""Common interface for inference backends."""

from abc import ABC, abstractmethod

from local_llm_node.schemas import BackendHealth, Model


class InferenceBackend(ABC):
    """Define the operations exposed by an inference backend."""

    @abstractmethod
    async def health(self) -> BackendHealth:
        """Return the current backend health."""

    @abstractmethod
    async def list_models(self) -> list[Model]:
        """Return the models available through the backend."""
