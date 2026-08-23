"""Domain exceptions raised by Local LLM Node."""


class BackendUnavailableError(RuntimeError):
    """Raised when an inference backend cannot serve a request."""
