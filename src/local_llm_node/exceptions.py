"""Domain exceptions raised by Local LLM Node."""


class BackendUnavailableError(RuntimeError):
    """Raised when an inference backend cannot serve a request."""


class ModelNotFoundError(RuntimeError):
    """Raised when a requested model is not available in the backend."""
