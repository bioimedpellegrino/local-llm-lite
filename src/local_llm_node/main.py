"""FastAPI application entry point."""

from fastapi import FastAPI

from local_llm_node import __version__
from local_llm_node.api import router
from local_llm_node.backends import InferenceBackend, OllamaBackend
from local_llm_node.config import Settings


def create_app(
    settings: Settings | None = None,
    inference_backend: InferenceBackend | None = None,
) -> FastAPI:
    """Create and configure the Local LLM Node application."""
    application_settings = settings or Settings.from_environment()
    backend = inference_backend or OllamaBackend(
        base_url=application_settings.ollama_url,
        timeout_seconds=application_settings.ollama_timeout_seconds,
    )

    application = FastAPI(
        title="Local LLM Node",
        description="A lightweight API layer for local inference backends.",
        version=__version__,
    )
    application.state.inference_backend = backend
    application.include_router(router)
    return application


app = create_app()
