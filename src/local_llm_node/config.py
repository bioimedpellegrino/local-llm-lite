"""Application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Define configuration values used by the application."""

    ollama_url: str = "http://localhost:11434"
    ollama_timeout_seconds: float = 3.0

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables."""
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", cls.ollama_url),
            ollama_timeout_seconds=float(
                os.getenv(
                    "OLLAMA_TIMEOUT_SECONDS",
                    str(cls.ollama_timeout_seconds),
                )
            ),
        )
