"""Inference backend implementations."""

from local_llm_node.backends.base import InferenceBackend
from local_llm_node.backends.ollama import OllamaBackend

__all__ = ["InferenceBackend", "OllamaBackend"]
